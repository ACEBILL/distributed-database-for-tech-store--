from flask import Blueprint, current_app, g, jsonify, request

from middleware.auth import require_auth, require_branch_access, require_role
from db import query_db
from services.branch_product_failover_service import (
    import_product_to_branch_via_central,
    list_hq_catalog_for_branch_via_central,
    remove_product_from_branch_via_central,
)
from services.product_service import (
    create_product,
    get_product_by_id_for_api,
    get_products_by_branch_for_api,
    get_products_for_api,
    get_products_from_branch_database_for_api,
    soft_delete_product,
    update_product,
)
from services.product_sync_service import (
    apply_product_from_branch,
    create_product_sync_event,
    get_branch_received_events_for_api,
    get_product_sync_events_for_api,
    retry_event_by_id,
    retry_failed_events,
)


product_api_bp = Blueprint("product_api", __name__, url_prefix="/api")


def _reject_branch_token_on_tru_so_alias():
    if request.path.startswith("/api/tru-so/") and g.current_user.get("scope") != "central":
        return jsonify({"error": "Central access required"}), 403
    return None


@product_api_bp.route("/san-pham")
@product_api_bp.route("/tru-so/san-pham")
@require_auth
def api_san_pham():
    """Danh sách sản phẩm trụ sở hoặc sản phẩm chi nhánh theo token
    ---
    tags:
      - Sản phẩm
    security:
      - bearerAuth: []
    parameters:
      - name: keyword
        in: query
        schema: {type: string}
      - name: ma_loai_sp
        in: query
        schema: {type: string}
      - name: ma_ncc
        in: query
        schema: {type: integer}
      - name: trang_thai
        in: query
        schema: {type: integer}
      - name: gia_min
        in: query
        schema: {type: number}
      - name: gia_max
        in: query
        schema: {type: number}
      - name: page
        in: query
        schema: {type: integer, default: 1}
      - name: limit
        in: query
        schema: {type: integer, default: 50}
    responses:
      200:
        description: Danh sách sản phẩm kèm pagination
    """
    forbidden = _reject_branch_token_on_tru_so_alias()
    if forbidden:
        return forbidden

    if g.current_user.get("scope") == "branch":
        return jsonify(
            get_products_from_branch_database_for_api(
                g.current_user.get("branch_code")
            )
        )
    return jsonify(get_products_for_api(request.args))


@product_api_bp.route("/san-pham/resync-all", methods=["POST"])
@product_api_bp.route("/tru-so/san-pham/resync-all", methods=["POST"])
@require_role("admin", "giam_doc")
def api_resync_all_products_to_branches():
    """Backfill: phát PRODUCT_UPDATED cho TẤT CẢ SP của HQ xuống mọi chi nhánh.

    Hữu ích khi:
    - Bootstrap chi nhánh mới
    - Khôi phục sau khi DB chi nhánh bị mất dữ liệu
    - Đồng bộ lại SP được seed trực tiếp vào HQ chứ không qua API
    ---
    tags:
      - Đồng bộ sản phẩm
    security:
      - bearerAuth: []
    responses:
      200:
        description: Số SP đã enqueue, số event đã dispatch
    """
    rows = query_db(
        """
        SELECT sp.*, lsp.ma_chi_nhanh, ncc.ten_NCC
        FROM SAN_PHAM sp
        JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
        JOIN NCC ncc ON sp.ma_ncc = ncc.ma_NCC
        ORDER BY sp.ma_sp
        """
    )
    total_sp = len(rows)
    total_events = 0
    errors = []

    for product in rows:
        try:
            dispatched = create_product_sync_event("PRODUCT_UPDATED", product)
            total_events += len(dispatched or [])
        except Exception as exc:
            errors.append({"ma_sp": product.get("ma_sp"), "error": str(exc)})

    return jsonify({
        "products_processed": total_sp,
        "events_dispatched": total_events,
        "errors": errors,
    })


@product_api_bp.route("/san-pham/sync-events")
@product_api_bp.route("/tru-so/san-pham/sync-events")
@require_role("admin", "giam_doc")
def api_san_pham_sync_events():
    """Danh sách event đồng bộ sản phẩm phát sinh từ trụ sở
    ---
    tags:
      - Đồng bộ sản phẩm
    security:
      - bearerAuth: []
    parameters:
      - name: ma_sp
        in: query
        schema: {type: string}
      - name: status
        in: query
        schema: {type: string, enum: [pending, sent, failed, dead_letter]}
      - name: target_branch
        in: query
        schema: {type: string}
      - name: event_type
        in: query
        schema: {type: string}
    responses:
      200:
        description: Danh sách event đồng bộ sản phẩm
    """
    return jsonify(get_product_sync_events_for_api(request.args))


@product_api_bp.route("/san-pham/sync-events/retry-failed", methods=["POST"])
@product_api_bp.route("/tru-so/san-pham/sync-events/retry-failed", methods=["POST"])
@require_role("admin", "giam_doc")
def api_retry_failed_sync_events():
    """Retry tất cả event đồng bộ đang ở trạng thái failed (chưa quá 5 lần thử)
    ---
    tags:
      - Đồng bộ sản phẩm
    security:
      - bearerAuth: []
    responses:
      200:
        description: Kết quả retry từng event
    """
    result = retry_failed_events()
    return jsonify(result)


@product_api_bp.route("/san-pham/sync-events/<event_id>/retry", methods=["POST"])
@product_api_bp.route("/tru-so/san-pham/sync-events/<event_id>/retry", methods=["POST"])
@require_role("admin", "giam_doc")
def api_retry_sync_event(event_id):
    """Retry một event đồng bộ cụ thể theo event_id
    ---
    tags:
      - Đồng bộ sản phẩm
    security:
      - bearerAuth: []
    parameters:
      - name: event_id
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Kết quả retry event
      404:
        description: Không tìm thấy event
    """
    result = retry_event_by_id(event_id)
    if result is None:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(result)


@product_api_bp.route("/san-pham/<ma_sp>")
@product_api_bp.route("/tru-so/san-pham/<ma_sp>")
@require_auth
def api_san_pham_detail(ma_sp):
    """Chi tiết sản phẩm trụ sở
    ---
    tags:
      - Sản phẩm
    security:
      - bearerAuth: []
    parameters:
      - name: ma_sp
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Chi tiết sản phẩm
      404:
        description: Không tìm thấy sản phẩm
    """
    forbidden = _reject_branch_token_on_tru_so_alias()
    if forbidden:
        return forbidden

    product = get_product_by_id_for_api(ma_sp)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@product_api_bp.route("/san-pham", methods=["POST"])
@product_api_bp.route("/tru-so/san-pham", methods=["POST"])
@require_role("admin", "giam_doc", "truong_phong")
def api_create_san_pham():
    """Tạo sản phẩm ở trụ sở
    ---
    tags:
      - Sản phẩm
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [ma_sp, ten_sp, gia, ma_loai_sp, ma_ncc]
            properties:
              ma_sp: {type: string}
              ten_sp: {type: string}
              gia: {type: number}
              ti_le_loi_nhuan: {type: number}
              ti_le_giam_gia: {type: number}
              mo_ta: {type: string}
              ma_loai_sp: {type: string}
              ma_ncc: {type: integer}
              trang_thai: {type: integer}
    responses:
      201:
        description: Sản phẩm đã được tạo
    """
    product = create_product(request.get_json(silent=True) or {})
    return jsonify(product), 201


@product_api_bp.route("/san-pham/<ma_sp>", methods=["PUT"])
@product_api_bp.route("/tru-so/san-pham/<ma_sp>", methods=["PUT"])
@require_role("admin", "giam_doc", "truong_phong")
def api_update_san_pham(ma_sp):
    """Cập nhật sản phẩm ở trụ sở
    ---
    tags:
      - Sản phẩm
    security:
      - bearerAuth: []
    parameters:
      - name: ma_sp
        in: path
        required: true
        schema: {type: string}
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
    responses:
      200:
        description: Sản phẩm đã được cập nhật
      404:
        description: Không tìm thấy sản phẩm
    """
    product = update_product(ma_sp, request.get_json(silent=True) or {})
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@product_api_bp.route("/san-pham/<ma_sp>", methods=["DELETE"])
@product_api_bp.route("/tru-so/san-pham/<ma_sp>", methods=["DELETE"])
@require_role("admin", "giam_doc", "truong_phong")
def api_delete_san_pham(ma_sp):
    """Ngưng bán sản phẩm ở trụ sở
    ---
    tags:
      - Sản phẩm
    security:
      - bearerAuth: []
    parameters:
      - name: ma_sp
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Sản phẩm đã được ngưng bán
      404:
        description: Không tìm thấy sản phẩm
    """
    deleted = soft_delete_product(ma_sp)
    if not deleted:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product disabled", "ma_sp": ma_sp})


@product_api_bp.route("/internal/products/list", methods=["GET"])
def api_internal_products_list():
    """API nội bộ — liệt kê toàn bộ SP của trụ sở (dùng cho chi nhánh "import from HQ").
    ---
    tags:
      - Đồng bộ chi nhánh ← Trụ sở
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        schema: {type: string}
      - name: only_active
        in: query
        schema: {type: integer, enum: [0, 1]}
    responses:
      200:
        description: Danh sách SP đầy đủ kèm join loai_sp + NCC
      403:
        description: Service token không hợp lệ
    """
    if request.headers.get("X-Service-Token") != current_app.config.get("SERVICE_TOKEN"):
        return jsonify({"success": False, "message": "Invalid service token"}), 403

    only_active = request.args.get("only_active", "1") == "1"
    where_clause = " WHERE sp.trang_thai = 1" if only_active else ""
    products = query_db(
        f"""
        SELECT sp.ma_sp, sp.ten_sp, sp.gia, sp.ti_le_loi_nhuan, sp.ti_le_giam_gia,
               sp.mo_ta, sp.ma_loai_sp, sp.ma_ncc, sp.trang_thai,
               lsp.ten_loai_sp, lsp.ma_chi_nhanh, ncc.ten_NCC
        FROM SAN_PHAM sp
        JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
        JOIN NCC ncc ON sp.ma_ncc = ncc.ma_NCC
        {where_clause}
        ORDER BY sp.ma_sp
        """
    )
    for product in products:
        for field in ("gia", "ti_le_loi_nhuan", "ti_le_giam_gia"):
            if field in product and product[field] is not None:
                product[field] = float(product[field])
    return jsonify({"success": True, "data": products})


@product_api_bp.route("/internal/products/<ma_sp>", methods=["GET"])
def api_internal_product_detail(ma_sp):
    """API nội bộ — chi tiết 1 SP của trụ sở (service-token).
    ---
    tags:
      - Đồng bộ chi nhánh ← Trụ sở
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        schema: {type: string}
      - name: ma_sp
        in: path
        required: true
        schema: {type: string}
    responses:
      200: {description: Chi tiết SP}
      403: {description: Service token không hợp lệ}
      404: {description: Không tìm thấy SP}
    """
    if request.headers.get("X-Service-Token") != current_app.config.get("SERVICE_TOKEN"):
        return jsonify({"success": False, "message": "Invalid service token"}), 403

    product = get_product_by_id_for_api(ma_sp)
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404
    return jsonify({"success": True, "data": product})


@product_api_bp.route("/internal/products/apply-change", methods=["POST"])
def api_internal_apply_from_branch():
    """API nội bộ — nhận event từ chi nhánh và áp dụng vào MSSQL trụ sở
    ---
    tags:
      - Đồng bộ chi nhánh → Trụ sở
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        schema: {type: string}
    responses:
      200:
        description: Event từ chi nhánh đã được xử lý
      403:
        description: Service token không hợp lệ
    """
    if request.headers.get("X-Service-Token") != current_app.config.get("SERVICE_TOKEN"):
        return jsonify({"success": False, "message": "Invalid service token"}), 403

    event = request.get_json(silent=True) or {}
    try:
        result = apply_product_from_branch(event)
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

    msg = "Event already applied" if result.get("status") == "ignored" else "Branch change applied to HQ"
    return jsonify({"success": True, "message": msg, "data": result})


@product_api_bp.route("/san-pham/branch-received-events")
@product_api_bp.route("/tru-so/san-pham/branch-received-events")
@require_role("admin", "giam_doc")
def api_branch_received_events():
    """Danh sách event nhận từ chi nhánh vào trụ sở
    ---
    tags:
      - Đồng bộ chi nhánh → Trụ sở
    security:
      - bearerAuth: []
    parameters:
      - name: status
        in: query
        schema: {type: string}
      - name: source_branch
        in: query
        schema: {type: string}
      - name: ma_sp
        in: query
        schema: {type: string}
    responses:
      200:
        description: Danh sách event nhận từ chi nhánh
    """
    return jsonify(get_branch_received_events_for_api(request.args))


@product_api_bp.route("/san-pham-theo-chi-nhanh")
@product_api_bp.route("/tru-so/san-pham-theo-chi-nhanh")
def api_san_pham_theo_chi_nhanh():
    """Danh sách sản phẩm theo chi nhánh từ view trung tâm
    ---
    tags:
      - Sản phẩm
    responses:
      200:
        description: Dữ liệu từ view v_san_pham_theo_chi_nhanh
    """
    return jsonify(get_products_by_branch_for_api())


@product_api_bp.route("/san-pham/chi-nhanh/<ma_chi_nhanh>")
@product_api_bp.route("/tru-so/san-pham/chi-nhanh/<ma_chi_nhanh>")
def api_san_pham_by_chi_nhanh(ma_chi_nhanh):
    """Sản phẩm theo mã chi nhánh từ view trung tâm
    ---
    tags:
      - Sản phẩm
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Sản phẩm theo chi nhánh
    """
    return jsonify(get_products_by_branch_for_api(ma_chi_nhanh))


@product_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/san-pham")
@require_branch_access
def api_san_pham_from_branch_database(ma_chi_nhanh):
    """Đọc sản phẩm trực tiếp từ DB chi nhánh
    ---
    tags:
      - Sản phẩm chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Sản phẩm đọc từ DB chi nhánh
      404:
        description: Không tìm thấy chi nhánh
    """
    try:
        payload = get_products_from_branch_database_for_api(ma_chi_nhanh)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if payload is None:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(payload)


@product_api_bp.route("/san-pham/loai/<ma_loai_sp>")
@product_api_bp.route("/tru-so/san-pham/loai/<ma_loai_sp>")
@require_auth
def api_san_pham_by_loai(ma_loai_sp):
    """Sản phẩm theo loại sản phẩm
    ---
    tags:
      - Sản phẩm
    security:
      - bearerAuth: []
    parameters:
      - name: ma_loai_sp
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Danh sách sản phẩm theo loại
    """
    args = request.args.to_dict()
    args["ma_loai_sp"] = ma_loai_sp
    return jsonify(get_products_for_api(args))


@product_api_bp.route("/san-pham/from-hq")
@require_auth
def api_san_pham_from_hq_for_branch_failover():
    """Branch-compatible: catalog HQ + cờ already_imported cho chi nhánh hiện tại.

    Phục vụ trường hợp branch backend chết, frontend chi nhánh fallback qua nginx
    về central API. Token PHẢI là branch scope (đăng nhập chi nhánh qua trụ sở).
    ---
    tags:
      - Sản phẩm chi nhánh (failover)
    security:
      - bearerAuth: []
    responses:
      200:
        description: HQ catalog kèm already_imported / pending_import cho chi nhánh
      403:
        description: Endpoint này chỉ dành cho token chi nhánh
    """
    branch_code = (g.current_user.get("branch_code") or "").upper()
    if g.current_user.get("scope") != "branch" or not branch_code:
        return jsonify({"error": "Branch token required"}), 403
    return jsonify(list_hq_catalog_for_branch_via_central(branch_code))


@product_api_bp.route("/san-pham/import-from-hq", methods=["POST"])
@require_auth
def api_san_pham_import_from_hq_for_branch_failover():
    """Branch-compatible: import 1 SP từ catalog HQ vào chi nhánh hiện tại.

    Nếu branch DB còn reachable từ trụ sở, ghi trực tiếp vào SAN_PHAM của chi nhánh.
    Nếu branch DB không reachable, queue event PRODUCT_IMPORT trong
    central_failover_events để replay khi backend chi nhánh sống lại.
    ---
    tags:
      - Sản phẩm chi nhánh (failover)
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [ma_sp]
            properties:
              ma_sp: {type: string}
    responses:
      201:
        description: SP đã nhập vào branch DB hoặc vào queue failover
      400:
        description: Payload sai hoặc SP đã tồn tại
      403:
        description: Endpoint này chỉ dành cho token chi nhánh
      404:
        description: Không tìm thấy SP ở trụ sở
    """
    branch_code = (g.current_user.get("branch_code") or "").upper()
    if g.current_user.get("scope") != "branch" or not branch_code:
        return jsonify({"error": "Branch token required"}), 403

    data = request.get_json(silent=True) or {}
    ma_sp = (data.get("ma_sp") or "").strip()
    try:
        result = import_product_to_branch_via_central(branch_code, ma_sp)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify(result), 201


@product_api_bp.route("/san-pham/import-from-hq/<ma_sp>", methods=["DELETE"])
@require_auth
def api_san_pham_remove_imported_from_hq_for_branch_failover(ma_sp):
    """Branch-compatible: bo 1 SP khoi catalog cua chi nhanh hien tai."""
    branch_code = (g.current_user.get("branch_code") or "").upper()
    if g.current_user.get("scope") != "branch" or not branch_code:
        return jsonify({"error": "Branch token required"}), 403

    try:
        result = remove_product_from_branch_via_central(branch_code, ma_sp)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify(result)


@product_api_bp.route("/san-pham/ncc/<int:ma_ncc>")
@product_api_bp.route("/tru-so/san-pham/ncc/<int:ma_ncc>")
@require_auth
def api_san_pham_by_ncc(ma_ncc):
    """Sản phẩm theo nhà cung cấp
    ---
    tags:
      - Sản phẩm
    security:
      - bearerAuth: []
    parameters:
      - name: ma_ncc
        in: path
        required: true
        schema: {type: integer}
    responses:
      200:
        description: Danh sách sản phẩm theo nhà cung cấp
    """
    args = request.args.to_dict()
    args["ma_ncc"] = str(ma_ncc)
    return jsonify(get_products_for_api(args))
