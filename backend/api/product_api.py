from flask import Blueprint, jsonify

from services.product_service import get_products_for_api


product_api_bp = Blueprint("product_api", __name__, url_prefix="/api")


@product_api_bp.route("/san-pham")
def api_san_pham():
    return jsonify(get_products_for_api())
