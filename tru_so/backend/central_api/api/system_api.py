import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from flask import Blueprint, current_app, jsonify

from services.branch_service import check_branch_health, get_branches
from services.product_sync_service import get_pending_event_counts_per_branch


system_api_bp = Blueprint("system_api", __name__, url_prefix="/api")


def _get_with_token(url):
    token = current_app.config.get("SERVICE_TOKEN", "")
    try:
        req = Request(url, headers={"X-Service-Token": token}, method="GET")
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode()), None
    except (OSError, URLError, TimeoutError) as exc:
        return None, str(exc)


def _parse_branch_service_map():
    raw = os.getenv("BRANCH_SERVICE_MAP", "CN01=mysql,CN02=postgre")
    mapping = {}
    for item in raw.split(","):
        if "=" in item:
            branch_code, peer_name = item.split("=", 1)
            mapping[branch_code.strip().upper()] = peer_name.strip()
    return mapping


@system_api_bp.get("/system/health")
def api_system_health():
    """Trạng thái sức khỏe tổng hợp toàn hệ thống phân tán
    ---
    tags:
      - Hệ thống
    responses:
      200:
        description: Trạng thái của tất cả node (trụ sở + chi nhánh)
        content:
          application/json:
            schema:
              type: object
              properties:
                overall:
                  type: string
                  enum: [ok, degraded]
                nodes:
                  type: object
    """
    service_url = os.getenv("SERVICE_API_URL", "").rstrip("/")
    branch_service_map = _parse_branch_service_map()

    hq_svc_data, _ = _get_with_token(f"{service_url}/api/service/ping")
    hq_service_status = (
        hq_svc_data.get("status", "unreachable") if hq_svc_data else "unreachable"
    )

    peer_data, _ = _get_with_token(f"{service_url}/api/service/peers/health")
    peer_health = peer_data if isinstance(peer_data, dict) else {}

    branches = get_branches()
    pending_counts = get_pending_event_counts_per_branch()

    nodes = {
        "tru_so": {
            "db_engine": "sqlserver",
            "db": "ok",
            "service": hq_service_status,
            "pending_events": sum(pending_counts.values()),
        }
    }

    for branch in branches:
        ma = branch["ma_chi_nhanh"]
        db_result = check_branch_health(ma)
        peer_name = branch_service_map.get(ma.upper())
        peer_info = peer_health.get(peer_name, {}) if peer_name else {}
        service_status = (
            peer_info.get("status", "unreachable")
            if isinstance(peer_info, dict)
            else "unreachable"
        )

        nodes[ma] = {
            "db_engine": db_result.get("he_quan_tri_csdl", "unknown") if db_result else "unknown",
            "db": db_result.get("status", "unreachable") if db_result else "unreachable",
            "service": service_status,
            "pending_events": pending_counts.get(ma, 0),
        }

    all_statuses = [
        v
        for node in nodes.values()
        for v in [node.get("db", ""), node.get("service", "")]
    ]
    overall = "ok" if all(s == "ok" for s in all_statuses) else "degraded"

    return jsonify({"overall": overall, "nodes": nodes})
