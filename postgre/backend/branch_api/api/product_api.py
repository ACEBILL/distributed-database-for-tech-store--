from flask import Blueprint, current_app, jsonify, request

from middleware.auth import require_auth, require_role
from services.product_service import (
    create_product,
    get_product_by_id_for_api,
    get_products_from_branch_database_for_api,
    import_product_from_hq,
    list_hq_catalog_for_branch,
    soft_delete_product,
    update_product,
)
from services.product_sync_service import (
    apply_product_sync_batch,
    apply_product_sync_event,
    create_branch_sync_event,
    get_branch_sync_events_for_api,
    get_local_product_sync_version,
    get_product_sync_log_for_api,
    retry_branch_event_by_id,
    retry_branch_failed_events,
)

product_api_bp = Blueprint("branch_product_api", __name__, url_prefix="/api")


def _branch_code():
    return (current_app.config.get("BRANCH_CODE") or "").upper()


def _service_authorized():
    return request.headers.get("X-Service-Token") == current_app.config["SERVICE_TOKEN"]


def _service_forbidden():
    return jsonify({"success": False, "message": "Invalid service token"}), 403


@product_api_bp.route("/san-pham")
@require_auth
def api_san_pham():
    """Danh sách sản phẩm của chi nhánh hiện tại
    ---
    tags:
      - Sản phẩm chi nhánh
    security:
      - bearerAuth: []
    responses:
      200:
        description: Danh sách sản phẩm đọc từ DB chi nhánh
    """
    payload = get_products_from_branch_database_for_api(_branch_code())
    if payload is None:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(payload)


@product_api_bp.route("/internal/products/apply-change", methods=["POST"])
def api_internal_apply_product_change():
    """API nội bộ apply một event đồng bộ sản phẩm
    ---
    tags:
      - Đồng bộ sản phẩm nội bộ
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        schema: {type: string}
    responses:
      200:
        description: Event đã được xử lý
      403:
        description: Service token không hợp lệ
    """
    if not _service_authorized():
        return _service_forbidden()

    payload = request.get_json(silent=True) or {}
    try:
        result = apply_product_sync_event(payload)
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

    message = (
        "Event already applied"
        if result.get("status") == "ignored"
        else "Product change applied successfully"
    )
    return jsonify({"success": True, "message": message, "data": result})


@product_api_bp.route("/internal/products/apply-batch", methods=["POST"])
def api_internal_apply_product_batch():
    """API nội bộ apply nhiều event đồng bộ sản phẩm
    ---
    tags:
      - Đồng bộ sản phẩm nội bộ
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        schema: {type: string}
    responses:
      200:
        description: Batch đã được xử lý
    """
    if not _service_authorized():
        return _service_forbidden()

    result = apply_product_sync_batch(request.get_json(silent=True) or {})
    return jsonify({"success": result["failed_count"] == 0, "message": "Batch processed", "data": result})


@product_api_bp.route("/internal/products/local-version")
def api_internal_product_local_version():
    """API nội bộ xem version đồng bộ sản phẩm hiện tại
    ---
    tags:
      - Đồng bộ sản phẩm nội bộ
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        schema: {type: string}
    responses:
      200:
        description: Version đồng bộ hiện tại
    """
    if not _service_authorized():
        return _service_forbidden()

    return jsonify(
        {
            "success": True,
            "message": "Local sync version retrieved",
            "data": get_local_product_sync_version(),
        }
    )


@product_api_bp.route("/internal/products/sync-log")
def api_internal_product_sync_log():
    """API nội bộ xem log đồng bộ sản phẩm
    ---
    tags:
      - Đồng bộ sản phẩm nội bộ
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        schema: {type: string}
      - name: ma_sp
        in: query
        schema: {type: string}
      - name: from_version
        in: query
        schema: {type: integer}
      - name: to_version
        in: query
        schema: {type: integer}
    responses:
      200:
        description: Log xử lý event đồng bộ
    """
    if not _service_authorized():
        return _service_forbidden()

    return jsonify(
        {
            "success": True,
            "message": "Sync log retrieved",
            "data": get_product_sync_log_for_api(request.args),
        }
    )


@product_api_bp.route("/san-pham/from-hq")
@require_role("admin", "giam_doc", "truong_phong")
def api_san_pham_available_from_hq():
    """Catalog SP đầy đủ của trụ sở, mỗi dòng kèm cờ `already_imported` cho chi nhánh này.

    UI bên chi nhánh hiển thị toàn bộ catalog, nút "Nhập" cho SP chưa nhập,
    badge "Đã có" cho SP đã có trên chi nhánh.
    ---
    tags:
      - Sản phẩm chi nhánh
    security:
      - bearerAuth: []
    responses:
      200:
        description: Toàn bộ catalog HQ kèm cờ đã nhập
      502:
        description: Không gọi được API trụ sở
    """
    try:
        return jsonify({"data": list_hq_catalog_for_branch()})
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502


@product_api_bp.route("/san-pham/import-from-hq", methods=["POST"])
@require_role("admin", "giam_doc", "truong_phong")
def api_san_pham_import_from_hq():
    """Nhập 1 SP từ catalog trụ sở vào chi nhánh hiện tại.

    KHÔNG phát outbox event — trụ sở đã có bản gốc.
    ---
    tags:
      - Sản phẩm chi nhánh
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
        description: SP đã được nhập về chi nhánh
      400:
        description: SP đã tồn tại hoặc payload không hợp lệ
      404:
        description: Không tìm thấy SP ở trụ sở
      502:
        description: Không gọi được API trụ sở
    """
    data = request.get_json(silent=True) or {}
    ma_sp = (data.get("ma_sp") or "").strip()
    try:
        product = import_product_from_hq(ma_sp)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        msg = str(exc)
        status = 404 if msg.startswith("HQ 404") else 502
        return jsonify({"error": msg}), status
    return jsonify(product), 201


@product_api_bp.route("/san-pham", methods=["POST"])
@require_role("admin", "giam_doc", "truong_phong")
def api_create_san_pham():
    """Tạo sản phẩm tại chi nhánh và đồng bộ lên trụ sở
    ---
    tags:
      - Sản phẩm chi nhánh
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
        description: Sản phẩm đã được tạo và đồng bộ lên trụ sở
    """
    product = create_product(request.get_json(silent=True) or {})
    try:
        create_branch_sync_event("PRODUCT_CREATED", product)
    except Exception:
        pass
    return jsonify(product), 201


@product_api_bp.route("/san-pham/<ma_sp>", methods=["PUT"])
@require_role("admin", "giam_doc", "truong_phong")
def api_update_san_pham(ma_sp):
    """Cập nhật sản phẩm tại chi nhánh và đồng bộ lên trụ sở
    ---
    tags:
      - Sản phẩm chi nhánh
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
        description: Sản phẩm đã được cập nhật và đồng bộ lên trụ sở
      404:
        description: Không tìm thấy sản phẩm
    """
    product = update_product(ma_sp, request.get_json(silent=True) or {})
    if not product:
        return jsonify({"error": "Product not found"}), 404
    try:
        create_branch_sync_event("PRODUCT_UPDATED", product)
    except Exception:
        pass
    return jsonify(product)


@product_api_bp.route("/san-pham/<ma_sp>", methods=["DELETE"])
@require_role("admin", "giam_doc", "truong_phong")
def api_delete_san_pham(ma_sp):
    """Ngưng bán sản phẩm tại chi nhánh và đồng bộ lên trụ sở
    ---
    tags:
      - Sản phẩm chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: ma_sp
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Sản phẩm đã được ngưng bán và đồng bộ lên trụ sở
      404:
        description: Không tìm thấy sản phẩm
    """
    deleted = soft_delete_product(ma_sp)
    if not deleted:
        return jsonify({"error": "Product not found"}), 404
    product = get_product_by_id_for_api(ma_sp)
    try:
        create_branch_sync_event("PRODUCT_DELETED", product)
    except Exception:
        pass
    return jsonify({"message": "Product disabled", "ma_sp": ma_sp})


@product_api_bp.route("/san-pham/sync-events")
@require_role("admin", "giam_doc")
def api_branch_sync_events():
    """Danh sách event đồng bộ sản phẩm phát sinh từ chi nhánh lên trụ sở
    ---
    tags:
      - Đồng bộ chi nhánh → Trụ sở
    security:
      - bearerAuth: []
    parameters:
      - name: status
        in: query
        schema: {type: string, enum: [pending, sent, failed, dead_letter]}
      - name: ma_sp
        in: query
        schema: {type: string}
      - name: event_type
        in: query
        schema: {type: string}
    responses:
      200:
        description: Danh sách event đồng bộ từ chi nhánh lên trụ sở
    """
    return jsonify(get_branch_sync_events_for_api(request.args))


@product_api_bp.route("/san-pham/sync-events/retry-failed", methods=["POST"])
@require_role("admin", "giam_doc")
def api_branch_retry_failed():
    """Retry tất cả event đồng bộ lên trụ sở đang bị failed
    ---
    tags:
      - Đồng bộ chi nhánh → Trụ sở
    security:
      - bearerAuth: []
    responses:
      200:
        description: Kết quả retry
    """
    return jsonify(retry_branch_failed_events())


@product_api_bp.route("/san-pham/sync-events/<event_id>/retry", methods=["POST"])
@require_role("admin", "giam_doc")
def api_branch_retry_event(event_id):
    """Retry một event đồng bộ lên trụ sở theo event_id
    ---
    tags:
      - Đồng bộ chi nhánh → Trụ sở
    security:
      - bearerAuth: []
    parameters:
      - name: event_id
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Kết quả retry
      404:
        description: Không tìm thấy event
    """
    result = retry_branch_event_by_id(event_id)
    if result is None:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(result)


@product_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/san-pham")
@require_auth
def api_san_pham_from_branch_database(ma_chi_nhanh):
    """Danh sách sản phẩm theo namespace chi nhánh
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
        description: Danh sách sản phẩm của chi nhánh
      403:
        description: Backend này không phục vụ chi nhánh được yêu cầu
    """
    if ma_chi_nhanh.upper() != _branch_code():
        return jsonify({"error": "This API only serves its configured branch"}), 403

    payload = get_products_from_branch_database_for_api(ma_chi_nhanh)
    if payload is None:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(payload)
