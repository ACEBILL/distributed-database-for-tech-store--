from flask import Blueprint, current_app, g, jsonify, request

from middleware.auth import require_auth
from services.auth_service import login_branch


auth_api_bp = Blueprint("branch_auth_api", __name__, url_prefix="/api/auth")


def _configured_branch_code():
    return (current_app.config.get("BRANCH_CODE") or "").upper()


@auth_api_bp.route("/login", methods=["POST"])
def api_login():
    branch_code = _configured_branch_code()
    if not branch_code:
        return jsonify({"error": "BRANCH_CODE is required for branch API"}), 500

    data = request.get_json(silent=True) or {}
    try:
        result = login_branch(
            branch_code,
            data.get("ma_nhan_vien"),
            data.get("mat_khau"),
        )
    except (NotImplementedError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    if not result:
        return jsonify({"error": "Sai ma nhan vien hoac mat khau"}), 401
    return jsonify(result)


@auth_api_bp.route("/me")
@require_auth
def api_me():
    return jsonify(
        {
            "ma_nhan_vien": g.current_user.get("sub"),
            "ho_ten": g.current_user.get("ho_ten"),
            "chuc_vu": g.current_user.get("chuc_vu"),
            "ma_phong_ban": g.current_user.get("ma_phong_ban"),
            "scope": g.current_user.get("scope", "branch"),
            "branch_code": g.current_user.get("branch_code"),
            "source_engine": g.current_user.get("source_engine"),
            "exp": g.current_user.get("exp"),
        }
    )
