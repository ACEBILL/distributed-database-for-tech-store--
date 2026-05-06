from flask import Blueprint, g, jsonify, request

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


product_api_bp = Blueprint("product_api", __name__, url_prefix="/api")


@product_api_bp.route("/san-pham")
@require_auth
def api_san_pham():
    if g.current_user.get("scope") == "branch":
        return jsonify(
            get_products_from_branch_database_for_api(
                g.current_user.get("branch_code")
            )
        )
    return jsonify(get_products_for_api(request.args))


@product_api_bp.route("/san-pham/<ma_sp>")
@require_auth
def api_san_pham_detail(ma_sp):
    product = get_product_by_id_for_api(ma_sp)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@product_api_bp.route("/san-pham", methods=["POST"])
@require_role("admin", "giam_doc", "truong_phong")
def api_create_san_pham():
    product = create_product(request.get_json(silent=True) or {})
    return jsonify(product), 201


@product_api_bp.route("/san-pham/<ma_sp>", methods=["PUT"])
@require_role("admin", "giam_doc", "truong_phong")
def api_update_san_pham(ma_sp):
    product = update_product(ma_sp, request.get_json(silent=True) or {})
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@product_api_bp.route("/san-pham/<ma_sp>", methods=["DELETE"])
@require_role("admin", "giam_doc", "truong_phong")
def api_delete_san_pham(ma_sp):
    deleted = soft_delete_product(ma_sp)
    if not deleted:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product disabled", "ma_sp": ma_sp})


@product_api_bp.route("/san-pham-theo-chi-nhanh")
def api_san_pham_theo_chi_nhanh():
    return jsonify(get_products_by_branch_for_api())


@product_api_bp.route("/san-pham/chi-nhanh/<ma_chi_nhanh>")
def api_san_pham_by_chi_nhanh(ma_chi_nhanh):
    return jsonify(get_products_by_branch_for_api(ma_chi_nhanh))


@product_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/san-pham")
@require_branch_access
def api_san_pham_from_branch_database(ma_chi_nhanh):
    try:
        payload = get_products_from_branch_database_for_api(ma_chi_nhanh)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if payload is None:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(payload)


@product_api_bp.route("/san-pham/loai/<ma_loai_sp>")
@require_auth
def api_san_pham_by_loai(ma_loai_sp):
    args = request.args.to_dict()
    args["ma_loai_sp"] = ma_loai_sp
    return jsonify(get_products_for_api(args))


@product_api_bp.route("/san-pham/ncc/<int:ma_ncc>")
@require_auth
def api_san_pham_by_ncc(ma_ncc):
    args = request.args.to_dict()
    args["ma_ncc"] = str(ma_ncc)
    return jsonify(get_products_for_api(args))
