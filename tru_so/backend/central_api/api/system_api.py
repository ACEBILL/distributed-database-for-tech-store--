from flask import Blueprint, jsonify

from middleware.auth import require_role
from services.system_health_service import get_system_health_for_api


system_api_bp = Blueprint("system_api", __name__, url_prefix="/api")


@system_api_bp.route("/system/health")
@system_api_bp.route("/tru-so/system/health")
@require_role("admin", "giam_doc")
def api_system_health():
    """Health tổng hợp toàn hệ thống phân tán
    ---
    tags:
      - System health
    security:
      - bearerAuth: []
    responses:
      200:
        description: Trạng thái backend/service/DB và đồng bộ sản phẩm của từng node
    """
    return jsonify(get_system_health_for_api())
