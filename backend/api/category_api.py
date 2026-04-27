from flask import Blueprint, jsonify, request

from services.category_service import (
    create_category,
    delete_category,
    get_all_categories_for_api,
    get_category_by_id_for_api,
    update_category,
)


category_api_bp = Blueprint("category_api", __name__, url_prefix="/api")


@category_api_bp.route("/loai-san-pham")
def api_loai_san_pham_list():
    """Lấy danh sách loại sản phẩm
    ---
    tags:
      - Loại sản phẩm
    responses:
      200:
        description: Danh sách loại sản phẩm
    """
    return jsonify(get_all_categories_for_api())


@category_api_bp.route("/loai-san-pham/<ma_loai_sp>")
def api_loai_san_pham_detail(ma_loai_sp):
    """Lấy chi tiết loại sản phẩm
    ---
    tags:
      - Loại sản phẩm
    responses:
      200:
        description: Chi tiết loại sản phẩm
    """
    category = get_category_by_id_for_api(ma_loai_sp)
    if not category:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(category)


@category_api_bp.route("/loai-san-pham", methods=["POST"])
def api_create_loai_san_pham():
    """Tạo loại sản phẩm
    ---
    tags:
      - Loại sản phẩm
    responses:
      201:
        description: Loại sản phẩm đã được tạo
    """
    category = create_category(request.get_json(silent=True) or {})
    return jsonify(category), 201


@category_api_bp.route("/loai-san-pham/<ma_loai_sp>", methods=["PUT"])
def api_update_loai_san_pham(ma_loai_sp):
    """Cập nhật loại sản phẩm
    ---
    tags:
      - Loại sản phẩm
    responses:
      200:
        description: Loại sản phẩm đã được cập nhật
    """
    category = update_category(ma_loai_sp, request.get_json(silent=True) or {})
    if not category:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(category)


@category_api_bp.route("/loai-san-pham/<ma_loai_sp>", methods=["DELETE"])
def api_delete_loai_san_pham(ma_loai_sp):
    """Xóa loại sản phẩm
    ---
    tags:
      - Loại sản phẩm
    responses:
      200:
        description: Loại sản phẩm đã được xóa
    """
    deleted = delete_category(ma_loai_sp)
    if not deleted:
        return jsonify({"error": "Category not found"}), 404
    return jsonify({"message": "Category deleted", "ma_loai_sp": ma_loai_sp})
