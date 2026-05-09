from flask import Blueprint, current_app, jsonify, request

from middleware.auth import require_auth, require_branch_access, require_role
from services.category_service import (
    create_category,
    delete_category,
    get_all_categories_for_api,
    get_category_by_id_for_api,
    update_category,
)


category_api_bp = Blueprint("category_api", __name__, url_prefix="/api")


def _branch_code():
    return (current_app.config.get("BRANCH_CODE") or "").upper()


@category_api_bp.route("/loai-san-pham")
def api_loai_san_pham_list():
    """Lấy danh sách loại sản phẩm
    ---
    tags:
      - Loại sản phẩm
    parameters:
      - name: keyword
        in: query
        schema: {type: string}
      - name: ma_chi_nhanh
        in: query
        schema: {type: string}
      - name: page
        in: query
        schema: {type: integer, default: 1}
      - name: limit
        in: query
        schema: {type: integer, default: 50, maximum: 200}
    responses:
      200:
        description: Danh sách loại sản phẩm + pagination
    """
    return jsonify(get_all_categories_for_api(request.args))


@category_api_bp.route("/loai-san-pham/<ma_loai_sp>")
def api_loai_san_pham_detail(ma_loai_sp):
    """Lấy chi tiết loại sản phẩm
    ---
    tags:
      - Loại sản phẩm
    parameters:
      - name: ma_loai_sp
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Chi tiết loại sản phẩm
      404:
        description: Không tìm thấy
    """
    category = get_category_by_id_for_api(ma_loai_sp)
    if not category:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(category)


@category_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/loai-san-pham")
@require_branch_access
def api_loai_san_pham_by_branch(ma_chi_nhanh):
    """Danh sách loại sản phẩm theo namespace chi nhánh
    ---
    tags:
      - Loại sản phẩm chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
      - name: keyword
        in: query
        schema: {type: string}
      - name: page
        in: query
        schema: {type: integer, default: 1}
      - name: limit
        in: query
        schema: {type: integer, default: 50, maximum: 200}
    responses:
      200:
        description: Danh sách loại sản phẩm của chi nhánh
      403:
        description: Backend này không phục vụ chi nhánh được yêu cầu
    """
    if ma_chi_nhanh.upper() != _branch_code():
        return jsonify({"error": "This API only serves its configured branch"}), 403

    args = request.args.to_dict()
    args["ma_chi_nhanh"] = ma_chi_nhanh
    return jsonify(get_all_categories_for_api(args))


@category_api_bp.route("/loai-san-pham", methods=["POST"])
@require_role("admin", "giam_doc", "truong_phong")
def api_create_loai_san_pham():
    """Tạo loại sản phẩm
    ---
    tags:
      - Loại sản phẩm
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - ma_loai_sp
              - ten_loai_sp
              - ma_chi_nhanh
            properties:
              ma_loai_sp: {type: string}
              ten_loai_sp: {type: string}
              ma_chi_nhanh: {type: string}
    responses:
      201:
        description: Loại sản phẩm đã được tạo
      400:
        description: Dữ liệu không hợp lệ
      409:
        description: Trùng mã hoặc vi phạm khóa ngoại ma_chi_nhanh
    """
    category = create_category(request.get_json(silent=True) or {})
    return jsonify(category), 201


@category_api_bp.route("/loai-san-pham/<ma_loai_sp>", methods=["PUT"])
@require_role("admin", "giam_doc", "truong_phong")
def api_update_loai_san_pham(ma_loai_sp):
    """Cập nhật loại sản phẩm
    ---
    tags:
      - Loại sản phẩm
    parameters:
      - name: ma_loai_sp
        in: path
        required: true
        schema: {type: string}
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              ten_loai_sp: {type: string}
              ma_chi_nhanh: {type: string}
    responses:
      200:
        description: Loại sản phẩm đã được cập nhật
      404:
        description: Không tìm thấy
    """
    category = update_category(ma_loai_sp, request.get_json(silent=True) or {})
    if not category:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(category)


@category_api_bp.route("/loai-san-pham/<ma_loai_sp>", methods=["DELETE"])
@require_role("admin", "giam_doc", "truong_phong")
def api_delete_loai_san_pham(ma_loai_sp):
    """Xóa loại sản phẩm
    ---
    tags:
      - Loại sản phẩm
    parameters:
      - name: ma_loai_sp
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Loại sản phẩm đã được xóa
      404:
        description: Không tìm thấy
      409:
        description: Còn sản phẩm liên kết, không thể xóa
    """
    deleted = delete_category(ma_loai_sp)
    if not deleted:
        return jsonify({"error": "Category not found"}), 404
    return jsonify({"message": "Category deleted", "ma_loai_sp": ma_loai_sp})
