from flask import Blueprint, g, jsonify

from middleware.auth import require_auth, require_branch_access
from services.branch_service import (
    get_branch_analysis_for_api,
    get_branch_stats_for_api,
    get_fragmentation_stats_for_api,
    get_products_by_branch_for_api,
)
from services.department_service import get_salary_stats_by_department_for_api
from services.employee_service import get_employees_by_branch_for_api


stats_api_bp = Blueprint("stats_api", __name__, url_prefix="/api")


@stats_api_bp.route("/thong-ke")
@stats_api_bp.route("/tru-so/thong-ke")
@require_auth
def api_thong_ke():
    """
    Lấy danh sách chi nhánh và trạng thái cấu hình DB chi nhánh
    ---
    tags:
      - Thống kê
    responses:
      200:
        description: Danh sách chi nhánh, engine DB và trạng thái cấu hình
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  ma_chi_nhanh:
                    type: string
                  ten_chi_nhanh:
                    type: string
                  he_quan_tri_csdl:
                    type: string
                    example: sqlserver
                  trang_thai_ket_noi:
                    type: string
                    example: not_configured
                  data:
                    nullable: true
    """
    stats = get_branch_stats_for_api()
    if g.current_user.get("scope") == "branch":
        branch_code = (g.current_user.get("branch_code") or "").upper()
        stats = [item for item in stats if item["ma_chi_nhanh"].upper() == branch_code]
    return jsonify(stats)


@stats_api_bp.route("/thong-ke/phan-manh")
@stats_api_bp.route("/tru-so/thong-ke/phan-manh")
@require_auth
def api_thong_ke_phan_manh():
    """Thống kê phân mảnh ngang: số bản ghi trên từng node trong hệ thống phân tán
    ---
    tags:
      - Thống kê
    security:
      - bearerAuth: []
    responses:
      200:
        description: >
          Số lượng san_pham và NHAN_VIEN trên từng node (trụ sở + chi nhánh).
          Thể hiện horizontal fragmentation - mỗi node giữ phân mảnh riêng.
        content:
          application/json:
            schema:
              type: object
              properties:
                fragmentation_type:
                  type: string
                  example: horizontal
                description:
                  type: string
                nodes:
                  type: object
      403:
        description: Chỉ tài khoản trụ sở (scope=central) mới được truy cập
    """
    if g.current_user.get("scope") != "central":
        return jsonify({"error": "Central access required"}), 403
    return jsonify(get_fragmentation_stats_for_api())


@stats_api_bp.route("/thong-ke/chi-nhanh")
@stats_api_bp.route("/tru-so/thong-ke/chi-nhanh")
@require_auth
def api_thong_ke_chi_nhanh():
    """Lấy thống kê chi nhánh
    ---
    tags:
      - Thống kê
    responses:
      200:
        description: Dữ liệu từ view v_thong_ke_chi_nhanh
    """
    if g.current_user.get("scope") != "central":
        return jsonify({"error": "Central access required"}), 403
    return jsonify(get_branch_analysis_for_api())


@stats_api_bp.route("/thong-ke/luong-phong-ban")
@stats_api_bp.route("/tru-so/thong-ke/luong-phong-ban")
@require_auth
def api_thong_ke_luong_phong_ban():
    """Lấy thống kê lương theo phòng ban
    ---
    tags:
      - Thống kê
    responses:
      200:
        description: Dữ liệu từ view v_luong_phong_ban
    """
    if g.current_user.get("scope") != "central":
        return jsonify({"error": "Central access required"}), 403
    return jsonify(get_salary_stats_by_department_for_api())


@stats_api_bp.route("/thong-ke/san-pham-theo-chi-nhanh/<ma_chi_nhanh>")
@stats_api_bp.route("/tru-so/thong-ke/san-pham-theo-chi-nhanh/<ma_chi_nhanh>")
@require_branch_access
def api_thong_ke_san_pham_theo_chi_nhanh(ma_chi_nhanh):
    """Lấy thống kê sản phẩm theo chi nhánh
    ---
    tags:
      - Thống kê
    parameters:
      - in: path
        name: ma_chi_nhanh
        required: true
        schema:
          type: string
        description: Mã chi nhánh
    responses:
      200:
        description: Danh sách sản phẩm theo chi nhánh từ v_san_pham_theo_chi_nhanh
    """
    return jsonify(get_products_by_branch_for_api(ma_chi_nhanh))


@stats_api_bp.route("/thong-ke/nhan-vien-theo-chi-nhanh/<ma_chi_nhanh>")
@stats_api_bp.route("/tru-so/thong-ke/nhan-vien-theo-chi-nhanh/<ma_chi_nhanh>")
@require_branch_access
def api_thong_ke_nhan_vien_theo_chi_nhanh(ma_chi_nhanh):
    """Lấy danh sách nhân viên theo chi nhánh
    ---
    tags:
      - Thống kê
    parameters:
      - in: path
        name: ma_chi_nhanh
        required: true
        schema:
          type: string
        description: Mã chi nhánh
    responses:
      200:
        description: Danh sách nhân viên. Lưu ý schema hiện không hỗ trợ liên kết nhân viên-chi nhánh
    """
    return jsonify(get_employees_by_branch_for_api(ma_chi_nhanh))
