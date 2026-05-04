from flask import Blueprint, g, jsonify, request

from middleware.auth import require_auth
from services.auth_service import login


auth_api_bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")


@auth_api_bp.route("/login", methods=["POST"])
def api_login():
    """Đăng nhập và lấy JWT
    ---
    tags:
      - Auth
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - ma_nhan_vien
              - mat_khau
            properties:
              ma_nhan_vien: {type: string}
              mat_khau: {type: string}
    responses:
      200:
        description: Đăng nhập thành công, trả về JWT
        content:
          application/json:
            schema:
              type: object
              properties:
                token: {type: string}
                expires_in_hours: {type: integer}
                user:
                  type: object
                  properties:
                    ma_nhan_vien: {type: string}
                    ho_ten: {type: string}
                    chuc_vu: {type: string}
                    ma_phong_ban: {type: integer}
      400:
        description: Thiếu thông tin
      401:
        description: Sai thông tin đăng nhập
    """
    data = request.get_json(silent=True) or {}
    result = login(data.get("ma_nhan_vien"), data.get("mat_khau"))
    if not result:
        return jsonify({"error": "Sai mã nhân viên hoặc mật khẩu"}), 401
    return jsonify(result)


@auth_api_bp.route("/me")
@require_auth
def api_me():
    """Trả thông tin user trong JWT đang dùng
    ---
    tags:
      - Auth
    security:
      - bearerAuth: []
    responses:
      200:
        description: Thông tin user
      401:
        description: Token không hợp lệ hoặc hết hạn
    """
    return jsonify({
        "ma_nhan_vien": g.current_user.get("sub"),
        "ho_ten": g.current_user.get("ho_ten"),
        "chuc_vu": g.current_user.get("chuc_vu"),
        "ma_phong_ban": g.current_user.get("ma_phong_ban"),
        "exp": g.current_user.get("exp"),
    })
