from flask import Blueprint, jsonify, request

from services.product_service import (
    create_product,
    get_product_by_id_for_api,
    get_products_by_branch_for_api,
    get_products_for_api,
    soft_delete_product,
    update_product,
)


product_api_bp = Blueprint("product_api", __name__, url_prefix="/api")


@product_api_bp.route("/san-pham")
def api_san_pham():
    """
    Lấy danh sách sản phẩm đang bán
    ---
    tags:
      - Sản phẩm
    responses:
      200:
        description: Danh sách sản phẩm, có thông tin nguồn cache/database
        content:
          application/json:
            schema:
              type: object
              properties:
                source:
                  type: string
                  example: database
                data:
                  type: array
                  items:
                    type: object
                    properties:
                      ma_sp:
                        type: string
                      ten_sp:
                        type: string
                      gia:
                        type: number
                      ti_le_giam_gia:
                        type: number
                      ten_loai_sp:
                        type: string
                      ten_NCC:
                        type: string
    """
    return jsonify(get_products_for_api())


@product_api_bp.route("/san-pham/<ma_sp>")
def api_san_pham_detail(ma_sp):
    """Lấy chi tiết sản phẩm
    ---
    tags:
      - Sản phẩm
    responses:
      200:
        description: Chi tiết sản phẩm
    """
    product = get_product_by_id_for_api(ma_sp)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@product_api_bp.route("/san-pham", methods=["POST"])
def api_create_san_pham():
    """Tạo sản phẩm
    ---
    tags:
      - Sản phẩm
    responses:
      201:
        description: Sản phẩm đã được tạo
    """
    product = create_product(request.get_json(silent=True) or {})
    return jsonify(product), 201


@product_api_bp.route("/san-pham/<ma_sp>", methods=["PUT"])
def api_update_san_pham(ma_sp):
    """Cập nhật sản phẩm
    ---
    tags:
      - Sản phẩm
    responses:
      200:
        description: Sản phẩm đã được cập nhật
    """
    product = update_product(ma_sp, request.get_json(silent=True) or {})
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@product_api_bp.route("/san-pham/<ma_sp>", methods=["DELETE"])
def api_delete_san_pham(ma_sp):
    """Ngưng bán sản phẩm
    ---
    tags:
      - Sản phẩm
    responses:
      200:
        description: Sản phẩm đã được ngưng bán
    """
    deleted = soft_delete_product(ma_sp)
    if not deleted:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product disabled", "ma_sp": ma_sp})


@product_api_bp.route("/san-pham-theo-chi-nhanh")
def api_san_pham_theo_chi_nhanh():
    """Lấy sản phẩm theo chi nhánh
    ---
    tags:
      - Sản phẩm
    responses:
      200:
        description: Dữ liệu từ view v_san_pham_theo_chi_nhanh
    """
    return jsonify(get_products_by_branch_for_api())


@product_api_bp.route("/san-pham/chi-nhanh/<ma_chi_nhanh>")
def api_san_pham_by_chi_nhanh(ma_chi_nhanh):
    """Lấy sản phẩm theo mã chi nhánh
    ---
    tags:
      - Sản phẩm
    responses:
      200:
        description: Dữ liệu sản phẩm thuộc một chi nhánh
    """
    return jsonify(get_products_by_branch_for_api(ma_chi_nhanh))
