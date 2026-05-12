from flask import Blueprint, g, jsonify, request

from middleware.auth import require_auth, require_branch_access
from services.invoice_service import (
    create_failover_invoice_for_branch,
    delete_failover_invoice_for_branch,
    get_all_invoices_aggregated,
    get_invoice_detail_from_branch,
    get_invoices_from_branch,
    get_revenue_aggregated,
    get_revenue_for_branch,
)


invoice_api_bp = Blueprint("central_invoice_api", __name__, url_prefix="/api")


@invoice_api_bp.route("/hoa-don")
@invoice_api_bp.route("/tru-so/hoa-don")
@require_auth
def api_hoa_don_aggregated():
    """Tổng hợp danh sách hóa đơn từ TẤT CẢ chi nhánh.
    Trụ sở không lưu HOA_DON local — dữ liệu lấy realtime từ DB chi nhánh.
    ---
    tags:
      - Hóa đơn trụ sở
    security:
      - bearerAuth: []
    parameters:
      - name: keyword
        in: query
        schema: {type: string}
      - name: tu_ngay
        in: query
        schema: {type: string, format: date}
      - name: den_ngay
        in: query
        schema: {type: string, format: date}
    responses:
      200:
        description: Danh sách hóa đơn gộp các chi nhánh
    """
    if g.current_user.get("scope") == "branch":
        branch_code = (g.current_user.get("branch_code") or "").upper()
        return jsonify(get_invoices_from_branch(branch_code, request.args))
    return jsonify(get_all_invoices_aggregated(request.args))


@invoice_api_bp.route("/hoa-don", methods=["POST"])
@require_auth
def api_hoa_don_failover_create_for_branch_portal():
    branch_code = (g.current_user.get("branch_code") or "").upper()
    if g.current_user.get("scope") != "branch" or not branch_code:
        return jsonify({"error": "Branch token required for failover invoice create"}), 403
    try:
        invoice = create_failover_invoice_for_branch(
            branch_code,
            request.get_json(silent=True) or {},
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(invoice), 201


@invoice_api_bp.route("/hoa-don/<ma_hd>", methods=["DELETE"])
@require_auth
def api_hoa_don_failover_delete_for_branch_portal(ma_hd):
    branch_code = (g.current_user.get("branch_code") or "").upper()
    if g.current_user.get("scope") != "branch" or not branch_code:
        return jsonify({"error": "Branch token required for failover invoice delete"}), 403
    result = delete_failover_invoice_for_branch(branch_code, ma_hd)
    return jsonify({"message": "Invoice deleted in HQ failover replica", **result})


@invoice_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/hoa-don")
@invoice_api_bp.route("/tru-so/chi-nhanh/<ma_chi_nhanh>/hoa-don")
@require_branch_access
def api_hoa_don_by_branch(ma_chi_nhanh):
    """Danh sách hóa đơn của 1 chi nhánh cụ thể.
    ---
    tags:
      - Hóa đơn trụ sở
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Danh sách hóa đơn của chi nhánh
    """
    return jsonify(get_invoices_from_branch(ma_chi_nhanh, request.args))


@invoice_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/hoa-don/<ma_hd>")
@invoice_api_bp.route("/tru-so/chi-nhanh/<ma_chi_nhanh>/hoa-don/<ma_hd>")
@require_branch_access
def api_hoa_don_detail(ma_chi_nhanh, ma_hd):
    """Chi tiết hóa đơn của 1 chi nhánh.
    ---
    tags:
      - Hóa đơn trụ sở
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
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
    invoice = get_invoice_detail_from_branch(ma_chi_nhanh, ma_hd)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    return jsonify(invoice)


@invoice_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/hoa-don/failover", methods=["POST"])
@invoice_api_bp.route("/tru-so/chi-nhanh/<ma_chi_nhanh>/hoa-don/failover", methods=["POST"])
@require_branch_access
def api_create_failover_hoa_don(ma_chi_nhanh):
    try:
        invoice = create_failover_invoice_for_branch(
            ma_chi_nhanh,
            request.get_json(silent=True) or {},
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(invoice), 201


@invoice_api_bp.route("/chi-nhanh/<ma_chi_nhanh>/hoa-don/<ma_hd>/failover", methods=["DELETE"])
@invoice_api_bp.route("/tru-so/chi-nhanh/<ma_chi_nhanh>/hoa-don/<ma_hd>/failover", methods=["DELETE"])
@require_branch_access
def api_delete_failover_hoa_don(ma_chi_nhanh, ma_hd):
    result = delete_failover_invoice_for_branch(ma_chi_nhanh, ma_hd)
    return jsonify({"message": "Invoice deleted in HQ failover replica", **result})


@invoice_api_bp.route("/thong-ke/doanh-thu")
@invoice_api_bp.route("/tru-so/thong-ke/doanh-thu")
@require_auth
def api_doanh_thu_aggregated():
    """Doanh thu tổng hợp toàn hệ thống (gộp từ tất cả chi nhánh).
    ---
    tags:
      - Hóa đơn trụ sở
    security:
      - bearerAuth: []
    responses:
      200:
        description: Tổng doanh thu + breakdown theo ngày/sản phẩm/chi nhánh
    """
    if g.current_user.get("scope") == "branch":
        branch_code = (g.current_user.get("branch_code") or "").upper()
        payload = get_revenue_for_branch(branch_code)
        if payload is None:
            return jsonify({"error": "Branch not found"}), 404
        return jsonify(payload)
    return jsonify(get_revenue_aggregated())


@invoice_api_bp.route("/thong-ke/doanh-thu/<ma_chi_nhanh>")
@invoice_api_bp.route("/tru-so/thong-ke/doanh-thu/<ma_chi_nhanh>")
@require_branch_access
def api_doanh_thu_chi_nhanh(ma_chi_nhanh):
    """Doanh thu của 1 chi nhánh (đọc trực tiếp từ DB chi nhánh).
    ---
    tags:
      - Hóa đơn trụ sở
    security:
      - bearerAuth: []
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Doanh thu của chi nhánh
      404:
        description: Không tìm thấy chi nhánh
    """
    payload = get_revenue_for_branch(ma_chi_nhanh)
    if payload is None:
        return jsonify({"error": "Branch not found"}), 404
    return jsonify(payload)
