from flask import Blueprint, jsonify, request

from middleware.auth import require_auth, require_role
from services.invoice_service import (
    create_invoice,
    delete_invoice,
    get_invoice_detail_for_api,
    get_invoices_for_api,
    get_revenue_stats,
)


invoice_api_bp = Blueprint("branch_invoice_api", __name__, url_prefix="/api")


@invoice_api_bp.route("/hoa-don")
@require_auth
def api_hoa_don_list():
    """Danh sách hóa đơn tại chi nhánh hiện tại
    ---
    tags:
      - Hóa đơn chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: keyword
        in: query
        schema: {type: string}
      - name: ma_nhan_vien
        in: query
        schema: {type: string}
      - name: tu_ngay
        in: query
        schema: {type: string, format: date}
      - name: den_ngay
        in: query
        schema: {type: string, format: date}
      - name: page
        in: query
        schema: {type: integer}
      - name: limit
        in: query
        schema: {type: integer}
    responses:
      200:
        description: Danh sách hóa đơn phân trang
    """
    return jsonify(get_invoices_for_api(request.args))


@invoice_api_bp.route("/hoa-don/<ma_hd>")
@require_auth
def api_hoa_don_detail(ma_hd):
    """Chi tiết hóa đơn (kèm các dòng CT_HOA_DON)
    ---
    tags:
      - Hóa đơn chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: ma_hd
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Hóa đơn + chi tiết
      404:
        description: Không tìm thấy hóa đơn
    """
    invoice = get_invoice_detail_for_api(ma_hd)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    return jsonify(invoice)


@invoice_api_bp.route("/hoa-don", methods=["POST"])
@require_role("admin", "giam_doc", "truong_phong", "pho_phong", "nhan_vien")
def api_hoa_don_create():
    """Lập hóa đơn mới tại chi nhánh
    ---
    tags:
      - Hóa đơn chi nhánh
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [ma_hd, ma_nhan_vien, items]
            properties:
              ma_hd: {type: string}
              ma_nhan_vien: {type: string}
              ten_kh: {type: string}
              sdt_kh: {type: string}
              ghi_chu: {type: string}
              items:
                type: array
                items:
                  type: object
                  required: [ma_sp, so_luong, don_gia]
                  properties:
                    ma_sp: {type: string}
                    so_luong: {type: integer}
                    don_gia: {type: number}
    responses:
      201:
        description: Hóa đơn vừa được tạo
      400:
        description: Payload không hợp lệ
    """
    try:
        invoice = create_invoice(request.get_json(silent=True) or {})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(invoice), 201


@invoice_api_bp.route("/hoa-don/<ma_hd>", methods=["DELETE"])
@require_role("admin", "giam_doc", "truong_phong")
def api_hoa_don_delete(ma_hd):
    """Xóa hóa đơn (cascade chi tiết)
    ---
    tags:
      - Hóa đơn chi nhánh
    security:
      - bearerAuth: []
    parameters:
      - name: ma_hd
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Đã xóa
      404:
        description: Không tìm thấy hóa đơn
    """
    if not delete_invoice(ma_hd):
        return jsonify({"error": "Invoice not found"}), 404
    return jsonify({"message": "Invoice deleted", "ma_hd": ma_hd})


@invoice_api_bp.route("/thong-ke/doanh-thu")
@require_auth
def api_thong_ke_doanh_thu():
    """Doanh thu chi nhánh (tổng, theo ngày, theo sản phẩm)
    ---
    tags:
      - Hóa đơn chi nhánh
    security:
      - bearerAuth: []
    responses:
      200:
        description: Thống kê doanh thu được tính trực tiếp từ HOA_DON / CT_HOA_DON
    """
    return jsonify(get_revenue_stats())
