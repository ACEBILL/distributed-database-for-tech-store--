import json

from db import query_db
from services.cache_service import get_cache, set_cache


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


def get_products_for_api():
    cached = get_cache(PRODUCT_CACHE_KEY)
    if cached:
        return {"source": "cache", "data": json.loads(cached)}

    products = get_active_products()
    for product in products:
        product["gia"] = float(product["gia"]) if product["gia"] else 0
        product["ti_le_giam_gia"] = (
            float(product["ti_le_giam_gia"]) if product["ti_le_giam_gia"] else 0
        )

    set_cache(PRODUCT_CACHE_KEY, json.dumps(products, ensure_ascii=False), ttl=300)
    return {"source": "database", "data": products}
