from flask import Blueprint, current_app, jsonify

from middleware.auth import require_auth
from services.branch_service import check_branch_health, get_branch_stats_for_api


stats_api_bp = Blueprint("branch_stats_api", __name__, url_prefix="/api")


def _branch_code():
    return (current_app.config.get("BRANCH_CODE") or "").upper()


@stats_api_bp.route("/thong-ke")
@require_auth
def api_thong_ke():
    branch_code = _branch_code()
    stats = [
        item
        for item in get_branch_stats_for_api()
        if item["ma_chi_nhanh"].upper() == branch_code
    ]
    return jsonify(stats)


@stats_api_bp.route("/thong-ke/health")
@require_auth
def api_thong_ke_health():
    result = check_branch_health(_branch_code())
    if not result:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(result)
