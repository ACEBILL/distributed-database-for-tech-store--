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
    payload = get_products_from_branch_database_for_api(_branch_code())
    if payload is None:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(payload)


@product_api_bp.route("/internal/products/apply-change", methods=["POST"])
def api_internal_apply_product_change():
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
    if not _service_authorized():
        return _service_forbidden()

    result = apply_product_sync_batch(request.get_json(silent=True) or {})
    return jsonify({"success": result["failed_count"] == 0, "message": "Batch processed", "data": result})


@product_api_bp.route("/internal/products/local-version")
def api_internal_product_local_version():
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
    if ma_chi_nhanh.upper() != _branch_code():
        return jsonify({"error": "This API only serves its configured branch"}), 403

    payload = get_products_from_branch_database_for_api(ma_chi_nhanh)
    if payload is None:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(payload)
