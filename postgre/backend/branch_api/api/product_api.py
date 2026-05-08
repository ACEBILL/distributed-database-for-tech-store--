from flask import Blueprint, current_app, jsonify

from middleware.auth import require_auth
from services.product_service import get_products_from_branch_database_for_api


product_api_bp = Blueprint("branch_product_api", __name__, url_prefix="/api")


def _branch_code():
    return (current_app.config.get("BRANCH_CODE") or "").upper()


@product_api_bp.route("/san-pham")
@require_auth
def api_san_pham():
    payload = get_products_from_branch_database_for_api(_branch_code())
    if payload is None:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(payload)


@product_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/san-pham")
@require_auth
def api_san_pham_from_branch_database(ma_chi_nhanh):
    if ma_chi_nhanh.upper() != _branch_code():
        return jsonify({"error": "This API only serves its configured branch"}), 403

    payload = get_products_from_branch_database_for_api(ma_chi_nhanh)
    if payload is None:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(payload)
