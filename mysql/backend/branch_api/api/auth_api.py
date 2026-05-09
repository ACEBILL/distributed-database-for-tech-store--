from flask import Blueprint, current_app, g, jsonify, request

from middleware.auth import require_auth
from services.auth_service import login_branch


auth_api_bp = Blueprint("branch_auth_api", __name__, url_prefix="/api/auth")


def _configured_branch_code():
    return (current_app.config.get("BRANCH_CODE") or "").upper()


def _branch_code_matches(ma_chi_nhanh):
    return (ma_chi_nhanh or "").upper() == _configured_branch_code()


def _login_for_configured_branch():
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


@auth_api_bp.route("/login", methods=["POST"])
def api_login():
    """Đăng nhập chi nhánh hiện tại
    ---
    tags:
      - Xác thực
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [ma_nhan_vien, mat_khau]
            properties:
              ma_nhan_vien:
                type: string
                example: NV001
              mat_khau:
                type: string
                example: pass123
    responses:
      200:
        description: JWT token chi nhánh. Swagger tự lưu token này cho các request sau.
      401:
        description: Sai thông tin đăng nhập
    """
    return _login_for_configured_branch()


@auth_api_bp.route("/branches/<ma_chi_nhanh>/login", methods=["POST"])
def api_branch_login(ma_chi_nhanh):
    """Đăng nhập chi nhánh theo namespace
    ---
    tags:
      - Xác thực
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
        example: CN01
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [ma_nhan_vien, mat_khau]
            properties:
              ma_nhan_vien:
                type: string
                example: NV001
              mat_khau:
                type: string
                example: pass123
    responses:
      200:
        description: JWT token chi nhánh. Swagger tự lưu token này cho các request sau.
      403:
        description: Backend này không phục vụ chi nhánh được yêu cầu
    """
    if not _branch_code_matches(ma_chi_nhanh):
        return jsonify({"error": "This API only serves its configured branch"}), 403
    return _login_for_configured_branch()


@auth_api_bp.route("/me")
@require_auth
def api_me():
    """Thông tin người dùng chi nhánh hiện tại
    ---
    tags:
      - Xác thực
    security:
      - bearerAuth: []
    responses:
      200:
        description: Thông tin user lấy từ JWT hiện tại
      401:
        description: Thiếu hoặc sai token
    """
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


@auth_api_bp.route("/branches/<ma_chi_nhanh>/me")
@require_auth
def api_branch_me(ma_chi_nhanh):
    """Thông tin người dùng theo namespace chi nhánh
    ---
    tags:
      - Xác thực
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Thông tin user chi nhánh lấy từ JWT hiện tại
      403:
        description: Backend này không phục vụ chi nhánh được yêu cầu
    """
    if not _branch_code_matches(ma_chi_nhanh):
        return jsonify({"error": "This API only serves its configured branch"}), 403
    return api_me()
