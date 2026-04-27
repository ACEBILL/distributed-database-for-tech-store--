from flask import Blueprint, jsonify

from services.employee_service import get_all_employees_for_api


employee_api_bp = Blueprint("employee_api", __name__, url_prefix="/api")


@employee_api_bp.route("/nhan-vien")
def api_nhan_vien():
    return jsonify(get_all_employees_for_api())
