from flask import Blueprint, jsonify, request

from services.supplier_service import (
    create_supplier,
    delete_supplier,
    get_all_suppliers_for_api,
    get_supplier_by_id_for_api,
    update_supplier,
)


supplier_api_bp = Blueprint("supplier_api", __name__, url_prefix="/api")


@supplier_api_bp.route("/nha-cung-cap")
def api_nha_cung_cap_list():
    """Lấy danh sách nhà cung cấp
    ---
    tags:
      - Nhà cung cấp
    responses:
      200:
        description: Danh sách nhà cung cấp
    """
    return jsonify(get_all_suppliers_for_api())


@supplier_api_bp.route("/nha-cung-cap/<int:ma_ncc>")
def api_nha_cung_cap_detail(ma_ncc):
    """Lấy chi tiết nhà cung cấp
    ---
    tags:
      - Nhà cung cấp
    responses:
      200:
        description: Chi tiết nhà cung cấp
    """
    supplier = get_supplier_by_id_for_api(ma_ncc)
    if not supplier:
        return jsonify({"error": "Supplier not found"}), 404
    return jsonify(supplier)


@supplier_api_bp.route("/nha-cung-cap", methods=["POST"])
def api_create_nha_cung_cap():
    """Tạo nhà cung cấp
    ---
    tags:
      - Nhà cung cấp
    responses:
      201:
        description: Nhà cung cấp đã được tạo
    """
    supplier = create_supplier(request.get_json(silent=True) or {})
    return jsonify(supplier), 201


@supplier_api_bp.route("/nha-cung-cap/<int:ma_ncc>", methods=["PUT"])
def api_update_nha_cung_cap(ma_ncc):
    """Cập nhật nhà cung cấp
    ---
    tags:
      - Nhà cung cấp
    responses:
      200:
        description: Nhà cung cấp đã được cập nhật
    """
    supplier = update_supplier(ma_ncc, request.get_json(silent=True) or {})
    if not supplier:
        return jsonify({"error": "Supplier not found"}), 404
    return jsonify(supplier)


@supplier_api_bp.route("/nha-cung-cap/<int:ma_ncc>", methods=["DELETE"])
def api_delete_nha_cung_cap(ma_ncc):
    """Xóa nhà cung cấp
    ---
    tags:
      - Nhà cung cấp
    responses:
      200:
        description: Nhà cung cấp đã được xóa
    """
    deleted = delete_supplier(ma_ncc)
    if not deleted:
        return jsonify({"error": "Supplier not found"}), 404
    return jsonify({"message": "Supplier deleted", "ma_ncc": ma_ncc})
