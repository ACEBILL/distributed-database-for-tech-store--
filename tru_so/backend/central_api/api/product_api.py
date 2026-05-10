from flask import Blueprint, g, jsonify, request
#test
from middleware.auth import require_auth, require_branch_access, require_role
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
