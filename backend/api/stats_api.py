from flask import Blueprint, jsonify

from services.branch_service import get_branch_stats_for_api


stats_api_bp = Blueprint("stats_api", __name__, url_prefix="/api")


@stats_api_bp.route("/thong-ke")
def api_thong_ke():
    return jsonify(get_branch_stats_for_api())
