from flask import Blueprint, jsonify

from services.branch_service import get_branch_analysis_for_api, get_branch_stats_for_api
from services.department_service import get_salary_stats_by_department_for_api


stats_api_bp = Blueprint("stats_api", __name__, url_prefix="/api")


@stats_api_bp.route("/thong-ke")
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
    return jsonify(get_branch_stats_for_api())


@stats_api_bp.route("/thong-ke/chi-nhanh")
def api_thong_ke_chi_nhanh():
    """Lấy thống kê chi nhánh
    ---
    tags:
      - Thống kê
    responses:
      200:
        description: Dữ liệu từ view v_thong_ke_chi_nhanh
    """
    return jsonify(get_branch_analysis_for_api())


@stats_api_bp.route("/thong-ke/luong-phong-ban")
def api_thong_ke_luong_phong_ban():
    """Lấy thống kê lương theo phòng ban
    ---
    tags:
      - Thống kê
    responses:
      200:
        description: Dữ liệu từ view v_luong_phong_ban
    """
    return jsonify(get_salary_stats_by_department_for_api())
