from flask import Blueprint, g, jsonify, request

from middleware.auth import require_auth, require_branch_access
from services.employee_service import (
    create_employee_in_branch,
    create_employee,
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


@employee_api_bp.route("/nhan-vien/<ma_nhan_vien>")
@employee_api_bp.route("/tru-so/nhan-vien/<ma_nhan_vien>")
@require_auth
def api_nhan_vien_detail(ma_nhan_vien):
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
    result = get_employees_from_branch_database_for_api(ma_chi_nhanh, request.args)
    if not _is_admin_user():
        result["data"] = mask_employees_list(result["data"], False)
    return jsonify(result)


@employee_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/nhan-vien/<ma_nhan_vien>")
@require_branch_access
def api_branch_nhan_vien_detail(ma_chi_nhanh, ma_nhan_vien):
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
    if not _can_manage_employees():
        return jsonify({"error": "Forbidden"}), 403

    deleted = soft_delete_employee_in_branch(ma_chi_nhanh, ma_nhan_vien)
    if not deleted:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify({"message": "Employee disabled", "ma_nhan_vien": ma_nhan_vien})


@employee_api_bp.route("/nhan-vien/phong-ban/<int:ma_pb>")
@employee_api_bp.route("/tru-so/nhan-vien/phong-ban/<int:ma_pb>")
def api_nhan_vien_by_phong_ban(ma_pb):
    return jsonify(get_employees_by_department_id_for_api(ma_pb))
