import json

from db import execute_db, query_db
from services.cache_service import delete_cache, get_cache, set_cache


PRODUCT_CACHE_KEY = "cache:san_pham_list"


def get_active_products():
    return query_db("""
        SELECT sp.ma_sp, sp.ten_sp, sp.gia, sp.ti_le_giam_gia,
               lsp.ten_loai_sp, ncc.ten_NCC
        FROM SAN_PHAM sp
        JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
        JOIN NCC ncc ON sp.ma_ncc = ncc.ma_NCC
        WHERE sp.trang_thai = 1
    """)


def format_product(product):
    if not product:
        return None

    for field in ["gia", "ti_le_loi_nhuan", "ti_le_giam_gia", "gia_ban_thuc_te"]:
        if field in product:
            product[field] = float(product[field]) if product[field] else 0

    for field in ["tao_vao", "cap_nhat_vao"]:
        if field in product:
            product[field] = product[field].isoformat() if product[field] else None

    return product


def get_product_by_id_for_api(ma_sp):
    product = query_db(
        """
        SELECT sp.*, lsp.ten_loai_sp, ncc.ten_NCC
        FROM SAN_PHAM sp
        JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
        JOIN NCC ncc ON sp.ma_ncc = ncc.ma_NCC
        WHERE sp.ma_sp = ?
        """,
        (ma_sp,),
        fetchone=True,
    )
    return format_product(product)


def create_product(data):
    required_fields = ["ma_sp", "ten_sp", "gia", "ma_loai_sp", "ma_ncc"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError("Missing required fields: " + ", ".join(missing_fields))

    execute_db(
        """
        INSERT INTO SAN_PHAM (
            ma_sp, ten_sp, gia, ti_le_loi_nhuan, ti_le_giam_gia,
            mo_ta, ma_loai_sp, ma_ncc, trang_thai
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["ma_sp"],
            data["ten_sp"],
            data["gia"],
            data.get("ti_le_loi_nhuan", 0),
            data.get("ti_le_giam_gia", 0),
            data.get("mo_ta"),
            data["ma_loai_sp"],
            data["ma_ncc"],
            data.get("trang_thai", 1),
        ),
    )
    delete_cache(PRODUCT_CACHE_KEY)
    return get_product_by_id_for_api(data["ma_sp"])


def update_product(ma_sp, data):
    if not data:
        raise ValueError("Request body is required")

    allowed_fields = [
        "ten_sp",
        "gia",
        "ti_le_loi_nhuan",
        "ti_le_giam_gia",
        "mo_ta",
        "ma_loai_sp",
        "ma_ncc",
        "trang_thai",
    ]
    assignments = []
    params = []

    for field in allowed_fields:
        if field in data:
            assignments.append(f"{field} = ?")
            params.append(data[field])

    if not assignments:
        raise ValueError("No valid fields to update")

    assignments.append("cap_nhat_vao = GETDATE()")
    params.append(ma_sp)
    affected_rows = execute_db(
        f"UPDATE SAN_PHAM SET {', '.join(assignments)} WHERE ma_sp = ?",
        tuple(params),
    )

    if affected_rows == 0:
        return None

    delete_cache(PRODUCT_CACHE_KEY)
    return get_product_by_id_for_api(ma_sp)


def soft_delete_product(ma_sp):
    affected_rows = execute_db(
        """
        UPDATE SAN_PHAM
        SET trang_thai = 0, cap_nhat_vao = GETDATE()
        WHERE ma_sp = ?
        """,
        (ma_sp,),
    )
    if affected_rows:
        delete_cache(PRODUCT_CACHE_KEY)
    return affected_rows > 0


def get_products_by_branch_for_api(ma_chi_nhanh=None):
    sql = "SELECT * FROM v_san_pham_theo_chi_nhanh"
    params = None
    if ma_chi_nhanh:
        sql += " WHERE ma_chi_nhanh = ?"
        params = (ma_chi_nhanh,)
    sql += " ORDER BY ma_chi_nhanh, ma_sp"

    products = query_db(sql, params)
    for product in products:
        format_product(product)
    return products


def get_products_for_api():
    cached = get_cache(PRODUCT_CACHE_KEY)
    if cached:
        return {"source": "cache", "data": json.loads(cached)}

    products = get_active_products()
    for product in products:
        format_product(product)

    set_cache(PRODUCT_CACHE_KEY, json.dumps(products, ensure_ascii=False), ttl=300)
    return {"source": "database", "data": products}
