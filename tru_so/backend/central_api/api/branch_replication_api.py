from flask import Blueprint, current_app, g, jsonify, request

from middleware.auth import require_auth
from services.branch_replication_service import apply_branch_replication_event
from services.failover_replay_service import replay_pending_events_for_branch


branch_replication_api_bp = Blueprint(
    "branch_replication_api",
    __name__,
    url_prefix="/api",
)


@branch_replication_api_bp.route("/internal/branch-replication/apply-event", methods=["POST"])
def api_internal_apply_branch_replication_event():
    if request.headers.get("X-Service-Token") != current_app.config.get("SERVICE_TOKEN"):
        return jsonify({"success": False, "message": "Invalid service token"}), 403

    try:
        result = apply_branch_replication_event(request.get_json(silent=True) or {})
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    return jsonify(result)


@branch_replication_api_bp.route("/internal/failover/replay/<ma_chi_nhanh>", methods=["POST"])
def api_internal_failover_replay(ma_chi_nhanh):
    """Replay all pending central_failover_events tu central xuong branch DB.

    Yeu cau service token. Goi truc tiep cho debugging — auto-replay chay nen.
    ---
    tags:
      - Failover
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        schema: {type: string}
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Ket qua replay
      403:
        description: Service token khong hop le
    """
    if request.headers.get("X-Service-Token") != current_app.config.get("SERVICE_TOKEN"):
        return jsonify({"success": False, "message": "Invalid service token"}), 403
    summary = replay_pending_events_for_branch(ma_chi_nhanh)
    return jsonify({"success": summary["failed"] == 0, "summary": summary})


@branch_replication_api_bp.route("/failover/replay/<ma_chi_nhanh>", methods=["POST"])
@require_auth
def api_failover_replay_admin(ma_chi_nhanh):
    """Replay manual cho admin tru so. Khong can service token nhung yeu cau scope=central.
    ---
    tags:
      - Failover
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Ket qua replay
      403:
        description: Yeu cau scope=central
    """
    if g.current_user.get("scope") != "central":
        return jsonify({"error": "Central access required"}), 403
    summary = replay_pending_events_for_branch(ma_chi_nhanh)
    return jsonify({"success": summary["failed"] == 0, "summary": summary})
