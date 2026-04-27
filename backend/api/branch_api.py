from flask import Blueprint, jsonify, request

from services.branch_service import (
    create_branch,
    delete_branch,
    get_branch_by_id,
    get_branches,
    update_branch,
)


branch_api_bp = Blueprint("branch_api", __name__, url_prefix="/api")


@branch_api_bp.route("/chi-nhanh")
def api_chi_nhanh_list():
    """Lấy danh sách chi nhánh
    ---
    tags:
      - Chi nhánh
    responses:
      200:
        description: Danh sách chi nhánh
    """
    return jsonify(get_branches())


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
def api_create_chi_nhanh():
    """Tạo chi nhánh
    ---
    tags:
      - Chi nhánh
    responses:
      201:
        description: Chi nhánh đã được tạo
    """
    branch = create_branch(request.get_json(silent=True) or {})
    return jsonify(branch), 201


@branch_api_bp.route("/chi-nhanh/<ma_chi_nhanh>", methods=["PUT"])
def api_update_chi_nhanh(ma_chi_nhanh):
    """Cập nhật chi nhánh
    ---
    tags:
      - Chi nhánh
    responses:
      200:
        description: Chi nhánh đã được cập nhật
    """
    branch = update_branch(ma_chi_nhanh, request.get_json(silent=True) or {})
    if not branch:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(branch)


@branch_api_bp.route("/chi-nhanh/<ma_chi_nhanh>", methods=["DELETE"])
def api_delete_chi_nhanh(ma_chi_nhanh):
    """Xóa chi nhánh
    ---
    tags:
      - Chi nhánh
    responses:
      200:
        description: Chi nhánh đã được xóa
    """
    deleted = delete_branch(ma_chi_nhanh)
    if not deleted:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify({"message": "Branch deleted", "ma_chi_nhanh": ma_chi_nhanh})
