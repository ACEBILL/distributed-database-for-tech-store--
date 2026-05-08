from flask import Blueprint, current_app, g, jsonify, request

from middleware.auth import require_auth, require_branch_access
from services.employee_service import (
    create_employee_in_branch,
    get_employee_by_id_from_branch_database_for_api,
    get_employees_from_branch_database_for_api,
    mask_employees_list,
    mask_sensitive_employee_fields,
    soft_delete_employee_in_branch,
    update_employee_in_branch,
)


employee_api_bp = Blueprint("branch_employee_api", __name__, url_prefix="/api")


def _branch_code():
    return (current_app.config.get("BRANCH_CODE") or "").upper()


def _is_admin_user():
    return g.current_user.get("chuc_vu") in ("admin", "giam_doc")


def _can_manage_employees():
    return g.current_user.get("chuc_vu") in ("admin", "giam_doc", "truong_phong")


@employee_api_bp.route("/nhan-vien")
@require_auth
def api_nhan_vien():
    result = get_employees_from_branch_database_for_api(_branch_code(), request.args)
    if not _is_admin_user():
        result["data"] = mask_employees_list(result["data"], False)
    return jsonify(result)


@employee_api_bp.route("/nhan-vien/<ma_nhan_vien>")
@require_auth
def api_nhan_vien_detail(ma_nhan_vien):
    employee = get_employee_by_id_from_branch_database_for_api(
        _branch_code(),
        ma_nhan_vien,
    )
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


@employee_api_bp.route("/nhan-vien", methods=["POST"])
@require_auth
def api_create_nhan_vien():
    if not _can_manage_employees():
        return jsonify({"error": "Forbidden"}), 403

    employee = create_employee_in_branch(
        _branch_code(),
        request.get_json(silent=True) or {},
    )
    return jsonify(employee), 201


@employee_api_bp.route("/nhan-vien/<ma_nhan_vien>", methods=["PUT"])
@require_auth
def api_update_nhan_vien(ma_nhan_vien):
    if not _can_manage_employees():
        return jsonify({"error": "Forbidden"}), 403

    employee = update_employee_in_branch(
        _branch_code(),
        ma_nhan_vien,
        request.get_json(silent=True) or {},
    )
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(employee)


@employee_api_bp.route("/nhan-vien/<ma_nhan_vien>", methods=["DELETE"])
@require_auth
def api_delete_nhan_vien(ma_nhan_vien):
    if not _can_manage_employees():
        return jsonify({"error": "Forbidden"}), 403

    deleted = soft_delete_employee_in_branch(_branch_code(), ma_nhan_vien)
    if not deleted:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify({"message": "Employee disabled", "ma_nhan_vien": ma_nhan_vien})
