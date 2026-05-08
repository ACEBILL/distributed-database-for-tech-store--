from flask import Blueprint, jsonify, request

from middleware.auth import require_auth, require_role
from services.department_service import (
    create_department,
    delete_department,
    get_all_departments_for_api,
    get_department_by_id_for_api,
    update_department,
)


department_api_bp = Blueprint("department_api", __name__, url_prefix="/api")


@department_api_bp.route("/phong-ban")
def api_phong_ban_list():
    """
    Lấy danh sách phòng ban
    ---
    tags:
      - Phòng ban
    parameters:
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
        description: Danh sách phòng ban + pagination
    """
    return jsonify(get_all_departments_for_api(request.args))


@department_api_bp.route("/phong-ban/<int:ma_pb>")
def api_phong_ban_detail(ma_pb):
    """
    Lấy chi tiết phòng ban
    ---
    tags:
      - Phòng ban
    parameters:
      - name: ma_pb
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Chi tiết phòng ban
      404:
        description: Không tìm thấy phòng ban
    """
    department = get_department_by_id_for_api(ma_pb)
    if not department:
        return jsonify({"error": "Department not found"}), 404
    return jsonify(department)


@department_api_bp.route("/phong-ban", methods=["POST"])
@require_role("admin", "giam_doc")
def api_create_phong_ban():
    """
    Tạo phòng ban
    ---
    tags:
      - Phòng ban
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - ten_pb
            properties:
              ten_pb:
                type: string
              ma_nv:
                type: integer
    responses:
      201:
        description: Phòng ban đã được tạo
      400:
        description: Dữ liệu không hợp lệ
    """
    department = create_department(request.get_json(silent=True) or {})
    return jsonify(department), 201


@department_api_bp.route("/phong-ban/<int:ma_pb>", methods=["PUT"])
@require_role("admin", "giam_doc")
def api_update_phong_ban(ma_pb):
    """
    Cập nhật phòng ban
    ---
    tags:
      - Phòng ban
    parameters:
      - name: ma_pb
        in: path
        required: true
        schema:
          type: integer
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              ten_pb:
                type: string
              ma_nv:
                type: integer
    responses:
      200:
        description: Phòng ban đã được cập nhật
      404:
        description: Không tìm thấy phòng ban
    """
    department = update_department(ma_pb, request.get_json(silent=True) or {})
    if not department:
        return jsonify({"error": "Department not found"}), 404
    return jsonify(department)


@department_api_bp.route("/phong-ban/<int:ma_pb>", methods=["DELETE"])
@require_role("admin", "giam_doc")
def api_delete_phong_ban(ma_pb):
    """
    Xóa phòng ban
    ---
    tags:
      - Phòng ban
    parameters:
      - name: ma_pb
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Phòng ban đã được xóa
      404:
        description: Không tìm thấy phòng ban
    """
    deleted = delete_department(ma_pb)
    if not deleted:
        return jsonify({"error": "Department not found"}), 404
    return jsonify({"message": "Department deleted", "ma_pb": ma_pb})
