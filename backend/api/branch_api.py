from flask import Blueprint, jsonify, request

from middleware.auth import require_auth, require_role
from services.branch_service import (
    check_branch_health,
    create_branch,
    delete_branch,
    get_branch_by_id,
    get_branches_for_api,
    update_branch,
)


branch_api_bp = Blueprint("branch_api", __name__, url_prefix="/api")


@branch_api_bp.route("/chi-nhanh")
def api_chi_nhanh_list():
    """Lấy danh sách chi nhánh
    ---
    tags:
      - Chi nhánh
    parameters:
      - name: keyword
        in: query
        schema: {type: string}
        description: Tìm theo ma_chi_nhanh / ten_chi_nhanh
      - name: page
        in: query
        schema: {type: integer, default: 1}
      - name: limit
        in: query
        schema: {type: integer, default: 50, maximum: 200}
    responses:
      200:
        description: Danh sách chi nhánh + pagination
    """
    return jsonify(get_branches_for_api(request.args))


@branch_api_bp.route("/chi-nhanh/<ma_chi_nhanh>")
def api_chi_nhanh_detail(ma_chi_nhanh):
    """Lấy chi tiết chi nhánh
    ---
    tags:
      - Chi nhánh
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Chi tiết chi nhánh
      404:
        description: Không tìm thấy chi nhánh
    """
    branch = get_branch_by_id(ma_chi_nhanh)
    if not branch:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(branch)


@branch_api_bp.route("/chi-nhanh", methods=["POST"])
@require_role("admin", "giam_doc")
def api_create_chi_nhanh():
    """Tạo chi nhánh
    ---
    tags:
      - Chi nhánh
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - ma_chi_nhanh
              - ten_chi_nhanh
            properties:
              ma_chi_nhanh: {type: string}
              ten_chi_nhanh: {type: string}
    responses:
      201:
        description: Chi nhánh đã được tạo
      400:
        description: Dữ liệu không hợp lệ
      409:
        description: Trùng mã chi nhánh
    """
    branch = create_branch(request.get_json(silent=True) or {})
    return jsonify(branch), 201


@branch_api_bp.route("/chi-nhanh/<ma_chi_nhanh>", methods=["PUT"])
@require_role("admin", "giam_doc")
def api_update_chi_nhanh(ma_chi_nhanh):
    """Cập nhật chi nhánh
    ---
    tags:
      - Chi nhánh
    parameters:
      - name: ma_chi_nhanh
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
              ten_chi_nhanh: {type: string}
    responses:
      200:
        description: Chi nhánh đã được cập nhật
      404:
        description: Không tìm thấy chi nhánh
    """
    branch = update_branch(ma_chi_nhanh, request.get_json(silent=True) or {})
    if not branch:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(branch)


@branch_api_bp.route("/chi-nhanh/<ma_chi_nhanh>", methods=["DELETE"])
@require_role("admin", "giam_doc")
def api_delete_chi_nhanh(ma_chi_nhanh):
    """Xóa chi nhánh
    ---
    tags:
      - Chi nhánh
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Chi nhánh đã được xóa
      404:
        description: Không tìm thấy chi nhánh
      409:
        description: Còn dữ liệu liên kết (ví dụ loại sản phẩm) không thể xóa
    """
    deleted = delete_branch(ma_chi_nhanh)
    if not deleted:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify({"message": "Branch deleted", "ma_chi_nhanh": ma_chi_nhanh})


@branch_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/health")
def api_chi_nhanh_health(ma_chi_nhanh):
    """Kiểm tra kết nối tới DB của chi nhánh
    ---
    tags:
      - Chi nhánh
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Trạng thái kết nối DB chi nhánh
        content:
          application/json:
            schema:
              type: object
              properties:
                ma_chi_nhanh: {type: string}
                ten_chi_nhanh: {type: string}
                he_quan_tri_csdl: {type: string}
                status:
                  type: string
                  description: ok / not_configured / unsupported_engine / unreachable
                error:
                  type: string
                  nullable: true
      404:
        description: Không tìm thấy chi nhánh
    """
    result = check_branch_health(ma_chi_nhanh)
    if not result:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(result)
