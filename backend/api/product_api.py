from flask import Blueprint, jsonify, request

from middleware.auth import require_auth, require_role
from services.product_service import (
    create_product,
    get_product_by_id_for_api,
    get_products_by_branch_for_api,
    get_products_for_api,
    soft_delete_product,
    update_product,
)


product_api_bp = Blueprint("product_api", __name__, url_prefix="/api")


@product_api_bp.route("/san-pham")
def api_san_pham():
    """
    Lấy danh sách sản phẩm
    ---
    tags:
      - Sản phẩm
    parameters:
      - name: keyword
        in: query
        schema: {type: string}
        description: Tìm theo ma_sp / ten_sp / mo_ta
      - name: ma_loai_sp
        in: query
        schema: {type: string}
      - name: ma_ncc
        in: query
        schema: {type: integer}
      - name: trang_thai
        in: query
        schema: {type: integer}
        description: 1 = đang bán, 0 = ngưng bán. Bỏ trống mặc định 1
      - name: gia_min
        in: query
        schema: {type: number}
      - name: gia_max
        in: query
        schema: {type: number}
      - name: page
        in: query
        schema: {type: integer, default: 1}
      - name: limit
        in: query
        schema: {type: integer, default: 50, maximum: 200}
    responses:
      200:
        description: Danh sách sản phẩm + pagination. Khi không truyền filter sẽ dùng cache Redis
    """
    return jsonify(get_products_for_api(request.args))


@product_api_bp.route("/san-pham/<ma_sp>")
def api_san_pham_detail(ma_sp):
    """Lấy chi tiết sản phẩm
    ---
    tags:
      - Sản phẩm
    parameters:
      - name: ma_sp
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Chi tiết sản phẩm
      404:
        description: Không tìm thấy sản phẩm
    """
    product = get_product_by_id_for_api(ma_sp)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@product_api_bp.route("/san-pham", methods=["POST"])
@require_role("admin", "giam_doc", "truong_phong")
def api_create_san_pham():
    """Tạo sản phẩm
    ---
    tags:
      - Sản phẩm
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - ma_sp
              - ten_sp
              - gia
              - ma_loai_sp
              - ma_ncc
            properties:
              ma_sp: {type: string}
              ten_sp: {type: string}
              gia: {type: number}
              ti_le_loi_nhuan: {type: number}
              ti_le_giam_gia: {type: number}
              mo_ta: {type: string}
              ma_loai_sp: {type: string}
              ma_ncc: {type: integer}
              trang_thai: {type: integer}
    responses:
      201:
        description: Sản phẩm đã được tạo
      400:
        description: Dữ liệu không hợp lệ
      409:
        description: Trùng mã sản phẩm hoặc vi phạm khóa ngoại
    """
    product = create_product(request.get_json(silent=True) or {})
    return jsonify(product), 201


@product_api_bp.route("/san-pham/<ma_sp>", methods=["PUT"])
@require_role("admin", "giam_doc", "truong_phong")
def api_update_san_pham(ma_sp):
    """Cập nhật sản phẩm
    ---
    tags:
      - Sản phẩm
    parameters:
      - name: ma_sp
        in: path
        required: true
        schema: {type: string}
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              ten_sp: {type: string}
              gia: {type: number}
              ti_le_loi_nhuan: {type: number}
              ti_le_giam_gia: {type: number}
              mo_ta: {type: string}
              ma_loai_sp: {type: string}
              ma_ncc: {type: integer}
              trang_thai: {type: integer}
    responses:
      200:
        description: Sản phẩm đã được cập nhật
      404:
        description: Không tìm thấy sản phẩm
    """
    product = update_product(ma_sp, request.get_json(silent=True) or {})
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@product_api_bp.route("/san-pham/<ma_sp>", methods=["DELETE"])
@require_role("admin", "giam_doc", "truong_phong")
def api_delete_san_pham(ma_sp):
    """Ngưng bán sản phẩm
    ---
    tags:
      - Sản phẩm
    parameters:
      - name: ma_sp
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Sản phẩm đã được ngưng bán
      404:
        description: Không tìm thấy sản phẩm
    """
    deleted = soft_delete_product(ma_sp)
    if not deleted:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product disabled", "ma_sp": ma_sp})


@product_api_bp.route("/san-pham-theo-chi-nhanh")
def api_san_pham_theo_chi_nhanh():
    """Lấy sản phẩm theo chi nhánh
    ---
    tags:
      - Sản phẩm
    responses:
      200:
        description: Dữ liệu từ view v_san_pham_theo_chi_nhanh
    """
    return jsonify(get_products_by_branch_for_api())


@product_api_bp.route("/san-pham/chi-nhanh/<ma_chi_nhanh>")
def api_san_pham_by_chi_nhanh(ma_chi_nhanh):
    """Lấy sản phẩm theo mã chi nhánh
    ---
    tags:
      - Sản phẩm
    parameters:
      - name: ma_chi_nhanh
        in: path
        required: true
        schema: {type: string}
    responses:
      200:
        description: Dữ liệu sản phẩm thuộc một chi nhánh
    """
    return jsonify(get_products_by_branch_for_api(ma_chi_nhanh))


@product_api_bp.route("/san-pham/loai/<ma_loai_sp>")
def api_san_pham_by_loai(ma_loai_sp):
    """Lấy sản phẩm theo mã loại sản phẩm
    ---
    tags:
      - Sản phẩm
    parameters:
      - name: ma_loai_sp
        in: path
        required: true
        schema: {type: string}
      - name: page
        in: query
        schema: {type: integer, default: 1}
      - name: limit
        in: query
        schema: {type: integer, default: 50, maximum: 200}
    responses:
      200:
        description: Sản phẩm thuộc loại đã chọn
    """
    args = request.args.to_dict()
    args["ma_loai_sp"] = ma_loai_sp
    return jsonify(get_products_for_api(args))


@product_api_bp.route("/san-pham/ncc/<int:ma_ncc>")
def api_san_pham_by_ncc(ma_ncc):
    """Lấy sản phẩm theo mã nhà cung cấp
    ---
    tags:
      - Sản phẩm
    parameters:
      - name: ma_ncc
        in: path
        required: true
        schema: {type: integer}
      - name: page
        in: query
        schema: {type: integer, default: 1}
      - name: limit
        in: query
        schema: {type: integer, default: 50, maximum: 200}
    responses:
      200:
        description: Sản phẩm thuộc nhà cung cấp đã chọn
    """
    args = request.args.to_dict()
    args["ma_ncc"] = str(ma_ncc)
    return jsonify(get_products_for_api(args))
