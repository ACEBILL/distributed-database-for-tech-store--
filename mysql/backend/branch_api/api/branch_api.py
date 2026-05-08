from flask import Blueprint, current_app, jsonify

from middleware.auth import require_auth, require_branch_access
from services.branch_service import check_branch_health, get_branch_by_id


branch_api_bp = Blueprint("branch_branch_api", __name__, url_prefix="/api")


def _branch_code():
    return (current_app.config.get("BRANCH_CODE") or "").upper()


@branch_api_bp.route("/chi-nhanh")
@require_auth
def api_chi_nhanh_list():
    branch = get_branch_by_id(_branch_code())
    if not branch:
        return jsonify({"data": [], "pagination": {"page": 1, "limit": 50, "total": 0}})
    return jsonify({"data": [branch], "pagination": {"page": 1, "limit": 50, "total": 1}})


@branch_api_bp.route("/chi-nhanh/<ma_chi_nhanh>")
@require_branch_access
def api_chi_nhanh_detail(ma_chi_nhanh):
    branch = get_branch_by_id(ma_chi_nhanh)
    if not branch:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(branch)


@branch_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/health")
@require_branch_access
def api_chi_nhanh_health(ma_chi_nhanh):
    result = check_branch_health(ma_chi_nhanh)
    if not result:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(result)


@branch_api_bp.route("/internal/health")
def api_internal_health():
    branch_code = _branch_code()
    result = check_branch_health(branch_code)
    if not result:
        return jsonify({"branch_code": branch_code, "status": "not_found"}), 404
    return jsonify(result)
