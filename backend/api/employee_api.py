from flask import Blueprint, jsonify, request

from services.employee_service import (
    create_employee,
    get_all_employees_for_api,
    get_employee_by_id_for_api,
    get_employees_by_department_id_for_api,
    soft_delete_employee,
    update_employee,
)


employee_api_bp = Blueprint("employee_api", __name__, url_prefix="/api")


@employee_api_bp.route("/nhan-vien")
def api_nhan_vien():
    """
    Lấy danh sách nhân viên
    ---
    tags:
      - Nhân viên
    responses:
      200:
        description: Danh sách nhân viên
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  ma_nhan_vien:
                    type: string
                  ho_ten:
                    type: string
                  ten_pb:
                    type: string
                  chuc_vu:
                    type: string
                  luong:
                    type: number
                  trang_thai:
                    type: integer
    """
    return jsonify(get_all_employees_for_api())


@employee_api_bp.route("/nhan-vien/<ma_nhan_vien>")
def api_nhan_vien_detail(ma_nhan_vien):
    """
    Lấy chi tiết nhân viên
    ---
    tags:
      - Nhân viên
    parameters:
      - name: ma_nhan_vien
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Chi tiết nhân viên
      404:
        description: Không tìm thấy nhân viên
    """
    employee = get_employee_by_id_for_api(ma_nhan_vien)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(employee)


@employee_api_bp.route("/nhan-vien", methods=["POST"])
def api_create_nhan_vien():
    """
    Tạo nhân viên
    ---
    tags:
      - Nhân viên
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - ma_nhan_vien
              - ho_ten
              - mat_khau
              - ma_phong_ban
            properties:
              ma_nhan_vien:
                type: string
              ho_ten:
                type: string
              mat_khau:
                type: string
              ma_phong_ban:
                type: integer
              cccd:
                type: string
              sdt:
                type: string
              luong:
                type: number
              chuc_vu:
                type: string
    responses:
      201:
        description: Nhân viên đã được tạo
      400:
        description: Dữ liệu không hợp lệ
    """
    employee = create_employee(request.get_json(silent=True) or {})
    return jsonify(employee), 201


@employee_api_bp.route("/nhan-vien/<ma_nhan_vien>", methods=["PUT"])
def api_update_nhan_vien(ma_nhan_vien):
    """
    Cập nhật nhân viên
    ---
    tags:
      - Nhân viên
    parameters:
      - name: ma_nhan_vien
        in: path
        required: true
        schema:
          type: string
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              ho_ten:
                type: string
              cccd:
                type: string
              sdt:
                type: string
              luong:
                type: number
              mat_khau:
                type: string
              trang_thai:
                type: integer
              ma_phong_ban:
                type: integer
              ma_ngay_lam:
                type: integer
              chuc_vu:
                type: string
              ngay_bat_dau:
                type: string
              ngay_ket_thuc:
                type: string
    responses:
      200:
        description: Nhân viên đã được cập nhật
      404:
        description: Không tìm thấy nhân viên
    """
    employee = update_employee(ma_nhan_vien, request.get_json(silent=True) or {})
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(employee)


@employee_api_bp.route("/nhan-vien/<ma_nhan_vien>", methods=["DELETE"])
def api_delete_nhan_vien(ma_nhan_vien):
    """
    Xóa mềm nhân viên
    ---
    tags:
      - Nhân viên
    parameters:
      - name: ma_nhan_vien
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Nhân viên đã được chuyển sang trạng thái nghỉ
      404:
        description: Không tìm thấy nhân viên
    """
    deleted = soft_delete_employee(ma_nhan_vien)
    if not deleted:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify({"message": "Employee disabled", "ma_nhan_vien": ma_nhan_vien})


@employee_api_bp.route("/nhan-vien/phong-ban/<int:ma_pb>")
def api_nhan_vien_by_phong_ban(ma_pb):
    """
    Lấy nhân viên theo mã phòng ban
    ---
    tags:
      - Nhân viên
    parameters:
      - name: ma_pb
        in: path
        required: true
        schema:
          type: integer
        description: Mã phòng ban
    responses:
      200:
        description: Danh sách nhân viên thuộc phòng ban
    """
    return jsonify(get_employees_by_department_id_for_api(ma_pb))
