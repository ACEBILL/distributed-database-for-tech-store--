from flask import Blueprint, current_app, jsonify, request

from middleware.auth import require_auth
from services.product_service import get_products_from_branch_database_for_api
from services.product_sync_service import (
    apply_product_sync_batch,
    apply_product_sync_event,
    get_local_product_sync_version,
    get_product_sync_log_for_api,
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
