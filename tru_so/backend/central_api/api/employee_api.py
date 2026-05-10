from flask import Blueprint, g, jsonify, request

from middleware.auth import require_auth, require_branch_access
from services.employee_service import (
    create_employee_in_branch,
    create_employee,
    get_all_employees_distributed_for_api,
    get_all_employees_for_api,
    get_employee_by_id_for_api,
    get_employee_by_id_from_branch_database_for_api,
    get_employees_by_department_id_for_api,
    get_employees_from_branch_database_for_api,
    mask_employees_list,
    mask_sensitive_employee_fields,
    soft_delete_employee_in_branch,
    soft_delete_employee,
    update_employee_in_branch,
    update_employee,
)


employee_api_bp = Blueprint("employee_api", __name__, url_prefix="/api")


def _is_admin_user():
    return g.current_user.get("chuc_vu") in ("admin", "giam_doc")


def _can_manage_employees():
    role = g.current_user.get("chuc_vu")
    scope = g.current_user.get("scope", "central")

    if scope == "branch":
        return role in ("admin", "giam_doc", "truong_phong")
    return role in ("admin", "giam_doc")


def _reject_branch_token_on_tru_so_alias():
    if request.path.startswith("/api/tru-so/") and g.current_user.get("scope") != "central":
        return jsonify({"error": "Central access required"}), 403
    return None


@employee_api_bp.route("/nhan-vien")
@employee_api_bp.route("/tru-so/nhan-vien")
@require_auth
def api_nhan_vien():
    """Danh sách nhân viên trụ sở hoặc nhân viên chi nhánh theo token
    ---
    tags:
      - Nhân viên
    security:
      - bearerAuth: []
    parameters:
      - name: keyword
        in: query
        schema: {type: string}
      - name: chuc_vu
        in: query
        schema: {type: string}
      - name: trang_thai
        in: query
        schema: {type: integer}
      - name: ma_phong_ban
        in: query
        schema: {type: integer}
      - name: page
        in: query
        schema: {type: integer, default: 1}
      - name: limit
        in: query
        schema: {type: integer, default: 50}
    responses:
      200:
        description: Danh sách nhân viên kèm pagination
    """
    forbidden = _reject_branch_token_on_tru_so_alias()
    if forbidden:
        return forbidden

    if g.current_user.get("scope") == "branch":
        result = get_employees_from_branch_database_for_api(
            g.current_user.get("branch_code"),
            request.args,
        )
    else:
        result = get_all_employees_for_api(request.args)

    if not _is_admin_user():
        result["data"] = mask_employees_list(result["data"], False)

    return jsonify(result)


@employee_api_bp.route("/nhan-vien/tat-ca-chi-nhanh")
@employee_api_bp.route("/tru-so/nhan-vien/tat-ca-chi-nhanh")
@require_auth
def api_nhan_vien_tat_ca_chi_nhanh():
    """Distributed query: nhân viên từ tất cả node (SQL Server + MySQL + PostgreSQL)
    ---
    tags:
      - Nhân viên
    security:
      - bearerAuth: []
    responses:
      200:
        description: >
          Danh sách nhân viên gộp từ tất cả node, kèm source_node và db_engine.
          Thể hiện distributed query qua query_branch_db().
        content:
          application/json:
            schema:
              type: object
              properties:
                query_type:
                  type: string
                  example: distributed_query
                total:
                  type: integer
                nodes:
                  type: object
                data:
                  type: array
      403:
        description: Chỉ tài khoản trụ sở (scope=central) mới được truy cập
    """
    if g.current_user.get("scope") != "central":
        return jsonify({"error": "Central access required"}), 403
    result = get_all_employees_distributed_for_api()
    if not _is_admin_user():
        result["data"] = mask_employees_list(result["data"], False)
        for node_data in result.get("nodes", {}).values():
            if isinstance(node_data.get("data"), list):
                node_data["data"] = mask_employees_list(node_data["data"], False)
    return jsonify(result)


@employee_api_bp.route("/nhan-vien/<ma_nhan_vien>")
@employee_api_bp.route("/tru-so/nhan-vien/<ma_nhan_vien>")
@require_auth
def api_nhan_vien_detail(ma_nhan_vien):
    """Chi tiết nhân viên trụ sở hoặc chi nhánh theo token
    ---
    tags:
      - Nhân viên
    security:
      - bearerAuth: []
    parameters:
      - name: ma_nhan_vien
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Chi tiết nhân viên
      404:
        description: Không tìm thấy nhân viên
    """
    forbidden = _reject_branch_token_on_tru_so_alias()
    if forbidden:
        return forbidden

    if g.current_user.get("scope") == "branch":
        employee = get_employee_by_id_from_branch_database_for_api(
            g.current_user.get("branch_code"),
            ma_nhan_vien,
        )
    else:
        employee = get_employee_by_id_for_api(ma_nhan_vien)

    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    return jsonify(mask_sensitive_employee_fields(employee, _is_admin_user()))


@employee_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/nhan-vien")
@require_branch_access
def api_branch_nhan_vien(ma_chi_nhanh):
    """Danh sách nhân viên đọc trực tiếp từ DB chi nhánh
    ---
    tags:
      - Nhân viên chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
      - name: page
        in: query
        schema: {type: integer, default: 1}
      - name: limit
        in: query
        schema: {type: integer, default: 50}
    responses:
      200:
        description: Danh sách nhân viên chi nhánh kèm pagination
    """
    result = get_employees_from_branch_database_for_api(ma_chi_nhanh, request.args)
    if not _is_admin_user():
        result["data"] = mask_employees_list(result["data"], False)
    return jsonify(result)


@employee_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/nhan-vien/<ma_nhan_vien>")
@require_branch_access
def api_branch_nhan_vien_detail(ma_chi_nhanh, ma_nhan_vien):
    """Chi tiết nhân viên đọc trực tiếp từ DB chi nhánh
    ---
    tags:
      - Nhân viên chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
      - name: ma_nhan_vien
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Chi tiết nhân viên chi nhánh
      404:
        description: Không tìm thấy nhân viên
    """
    employee = get_employee_by_id_from_branch_database_for_api(
        ma_chi_nhanh,
        ma_nhan_vien,
    )
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(mask_sensitive_employee_fields(employee, _is_admin_user()))


@employee_api_bp.route("/nhan-vien", methods=["POST"])
@employee_api_bp.route("/tru-so/nhan-vien", methods=["POST"])
@require_auth
def api_create_nhan_vien():
    """Tạo nhân viên trụ sở hoặc chi nhánh theo token
    ---
    tags:
      - Nhân viên
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [ma_nhan_vien, ho_ten, mat_khau, ma_phong_ban]
            properties:
              ma_nhan_vien: {type: string}
              ho_ten: {type: string}
              mat_khau: {type: string}
              cccd: {type: string}
              sdt: {type: string}
              luong: {type: number}
              ma_phong_ban: {type: integer}
              chuc_vu: {type: string}
    responses:
      201:
        description: Nhân viên đã được tạo
    """
    forbidden = _reject_branch_token_on_tru_so_alias()
    if forbidden:
        return forbidden

    if not _can_manage_employees():
        return jsonify({"error": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    if g.current_user.get("scope") == "branch":
        employee = create_employee_in_branch(g.current_user.get("branch_code"), payload)
    else:
        employee = create_employee(payload)
    return jsonify(employee), 201


@employee_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/nhan-vien", methods=["POST"])
@require_branch_access
def api_create_branch_nhan_vien(ma_chi_nhanh):
    """Tạo nhân viên trong DB chi nhánh
    ---
    tags:
      - Nhân viên chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      201:
        description: Nhân viên chi nhánh đã được tạo
    """
    if not _can_manage_employees():
        return jsonify({"error": "Forbidden"}), 403

    employee = create_employee_in_branch(
        ma_chi_nhanh,
        request.get_json(silent=True) or {},
    )
    return jsonify(employee), 201


@employee_api_bp.route("/nhan-vien/<ma_nhan_vien>", methods=["PUT"])
@employee_api_bp.route("/tru-so/nhan-vien/<ma_nhan_vien>", methods=["PUT"])
@require_auth
def api_update_nhan_vien(ma_nhan_vien):
    """Cập nhật nhân viên trụ sở hoặc chi nhánh theo token
    ---
    tags:
      - Nhân viên
    security:
      - bearerAuth: []
    parameters:
      - name: ma_nhan_vien
        in: path
        required: true
        schema: {type: string}
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
    responses:
      200:
        description: Nhân viên đã được cập nhật
      404:
        description: Không tìm thấy nhân viên
    """
    forbidden = _reject_branch_token_on_tru_so_alias()
    if forbidden:
        return forbidden

    if not _can_manage_employees():
        return jsonify({"error": "Forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    if g.current_user.get("scope") == "branch":
        employee = update_employee_in_branch(
            g.current_user.get("branch_code"),
            ma_nhan_vien,
            payload,
        )
    else:
        employee = update_employee(ma_nhan_vien, payload)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(employee)


@employee_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/nhan-vien/<ma_nhan_vien>", methods=["PUT"])
@require_branch_access
def api_update_branch_nhan_vien(ma_chi_nhanh, ma_nhan_vien):
    """Cập nhật nhân viên trong DB chi nhánh
    ---
    tags:
      - Nhân viên chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
      - name: ma_nhan_vien
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Nhân viên chi nhánh đã được cập nhật
      404:
        description: Không tìm thấy nhân viên
    """
    if not _can_manage_employees():
        return jsonify({"error": "Forbidden"}), 403

    employee = update_employee_in_branch(
        ma_chi_nhanh,
        ma_nhan_vien,
        request.get_json(silent=True) or {},
    )
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(employee)


@employee_api_bp.route("/nhan-vien/<ma_nhan_vien>", methods=["DELETE"])
@employee_api_bp.route("/tru-so/nhan-vien/<ma_nhan_vien>", methods=["DELETE"])
@require_auth
def api_delete_nhan_vien(ma_nhan_vien):
    """Xóa mềm/ngưng nhân viên theo token
    ---
    tags:
      - Nhân viên
    security:
      - bearerAuth: []
    parameters:
      - name: ma_nhan_vien
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Nhân viên đã được ngưng
      404:
        description: Không tìm thấy nhân viên
    """
    forbidden = _reject_branch_token_on_tru_so_alias()
    if forbidden:
        return forbidden

    if not _can_manage_employees():
        return jsonify({"error": "Forbidden"}), 403

    if g.current_user.get("scope") != "branch":
        return jsonify({"error": "Headquarter portal supports create/update only"}), 403

    if g.current_user.get("scope") == "branch":
        deleted = soft_delete_employee_in_branch(
            g.current_user.get("branch_code"),
            ma_nhan_vien,
        )
    else:
        deleted = soft_delete_employee(ma_nhan_vien)
    if not deleted:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify({"message": "Employee disabled", "ma_nhan_vien": ma_nhan_vien})


@employee_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/nhan-vien/<ma_nhan_vien>", methods=["DELETE"])
@require_branch_access
def api_delete_branch_nhan_vien(ma_chi_nhanh, ma_nhan_vien):
    """Xóa mềm/ngưng nhân viên trong DB chi nhánh
    ---
    tags:
      - Nhân viên chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
      - name: ma_nhan_vien
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Nhân viên chi nhánh đã được ngưng
      404:
        description: Không tìm thấy nhân viên
    """
    if not _can_manage_employees():
        return jsonify({"error": "Forbidden"}), 403

    deleted = soft_delete_employee_in_branch(ma_chi_nhanh, ma_nhan_vien)
    if not deleted:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify({"message": "Employee disabled", "ma_nhan_vien": ma_nhan_vien})


@employee_api_bp.route("/nhan-vien/phong-ban/<int:ma_pb>")
@employee_api_bp.route("/tru-so/nhan-vien/phong-ban/<int:ma_pb>")
def api_nhan_vien_by_phong_ban(ma_pb):
    """Nhân viên theo phòng ban trụ sở
    ---
    tags:
      - Nhân viên
    parameters:
      - name: ma_pb
        in: path
        required: true
        schema: {type: integer}
    responses:
      200:
        description: Danh sách nhân viên theo phòng ban
    """
    return jsonify(get_employees_by_department_id_for_api(ma_pb))
