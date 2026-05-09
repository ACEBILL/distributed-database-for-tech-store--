from flask import Blueprint, jsonify, request

from middleware.auth import require_auth, require_role
from services.supplier_service import (
    create_supplier,
    delete_supplier,
    get_all_suppliers_for_api,
    get_supplier_by_id_for_api,
    update_supplier,
)


supplier_api_bp = Blueprint("supplier_api", __name__, url_prefix="/api")


@supplier_api_bp.route("/nha-cung-cap")
@supplier_api_bp.route("/tru-so/nha-cung-cap")
def api_nha_cung_cap_list():
    """Lấy danh sách nhà cung cấp
    ---
    tags:
      - Nhà cung cấp
    parameters:
      - name: keyword
        in: query
        schema: {type: string}
      - name: page
        in: query
        schema: {type: integer, default: 1}
      - name: limit
        in: query
        schema: {type: integer, default: 50, maximum: 200}
    responses:
      200:
        description: Danh sách nhà cung cấp + pagination
    """
    return jsonify(get_all_suppliers_for_api(request.args))


@supplier_api_bp.route("/nha-cung-cap/<int:ma_ncc>")
@supplier_api_bp.route("/tru-so/nha-cung-cap/<int:ma_ncc>")
def api_nha_cung_cap_detail(ma_ncc):
    """Lấy chi tiết nhà cung cấp
    ---
    tags:
      - Nhà cung cấp
    parameters:
      - name: ma_ncc
        in: path
        required: true
        schema: {type: integer}
    responses:
      200:
        description: Chi tiết nhà cung cấp
      404:
        description: Không tìm thấy
    """
    supplier = get_supplier_by_id_for_api(ma_ncc)
    if not supplier:
        return jsonify({"error": "Supplier not found"}), 404
    return jsonify(supplier)


@supplier_api_bp.route("/nha-cung-cap", methods=["POST"])
@supplier_api_bp.route("/tru-so/nha-cung-cap", methods=["POST"])
@require_role("admin", "giam_doc", "truong_phong")
def api_create_nha_cung_cap():
    """Tạo nhà cung cấp
    ---
    tags:
      - Nhà cung cấp
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - ten_ncc
            properties:
              ten_ncc: {type: string}
    responses:
      201:
        description: Nhà cung cấp đã được tạo
      400:
        description: Dữ liệu không hợp lệ
    """
    supplier = create_supplier(request.get_json(silent=True) or {})
    return jsonify(supplier), 201


@supplier_api_bp.route("/nha-cung-cap/<int:ma_ncc>", methods=["PUT"])
@supplier_api_bp.route("/tru-so/nha-cung-cap/<int:ma_ncc>", methods=["PUT"])
@require_role("admin", "giam_doc", "truong_phong")
def api_update_nha_cung_cap(ma_ncc):
    """Cập nhật nhà cung cấp
    ---
    tags:
      - Nhà cung cấp
    parameters:
      - name: ma_ncc
        in: path
        required: true
        schema: {type: integer}
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              ten_ncc: {type: string}
    responses:
      200:
        description: Nhà cung cấp đã được cập nhật
      404:
        description: Không tìm thấy
    """
    supplier = update_supplier(ma_ncc, request.get_json(silent=True) or {})
    if not supplier:
        return jsonify({"error": "Supplier not found"}), 404
    return jsonify(supplier)


@supplier_api_bp.route("/nha-cung-cap/<int:ma_ncc>", methods=["DELETE"])
@supplier_api_bp.route("/tru-so/nha-cung-cap/<int:ma_ncc>", methods=["DELETE"])
@require_role("admin", "giam_doc", "truong_phong")
def api_delete_nha_cung_cap(ma_ncc):
    """Xóa nhà cung cấp
    ---
    tags:
      - Nhà cung cấp
    parameters:
      - name: ma_ncc
        in: path
        required: true
        schema: {type: integer}
    responses:
      200:
        description: Nhà cung cấp đã được xóa
      404:
        description: Không tìm thấy
      409:
        description: Còn sản phẩm liên kết, không thể xóa
    """
    deleted = delete_supplier(ma_ncc)
    if not deleted:
        return jsonify({"error": "Supplier not found"}), 404
    return jsonify({"message": "Supplier deleted", "ma_ncc": ma_ncc})
