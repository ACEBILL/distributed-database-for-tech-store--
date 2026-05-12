import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app

from db import (
    build_pagination_meta,
    execute_db,
    get_branch_db_engine,
    now_sql,
    pagination_clause,
    parse_pagination,
    query_branch_db,
    query_db,
)
from services.cache_service import delete_cache, get_cache, set_cache


def _hq_api_url():
    return os.getenv("HQ_API_URL", "http://tru-so-backend:5000").rstrip("/")


def _service_token():
    return current_app.config.get("SERVICE_TOKEN", "")


def _hq_get(path):
    req = Request(
        f"{_hq_api_url()}{path}",
        headers={"X-Service-Token": _service_token()},
        method="GET",
    )
    try:
        with urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HQ {exc.code}: {body}") from exc
    except (OSError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"HQ unreachable: {exc}") from exc


PRODUCT_CACHE_KEY = "cache:san_pham_list"


PRODUCT_BASE_SQL = """
    FROM SAN_PHAM sp
    JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
    JOIN NCC ncc ON sp.ma_ncc = ncc.ma_NCC
""" #1


def _build_product_filters(args):
    where = []
    params = []

    keyword = (args.get("keyword") or "").strip()
    if keyword:
        where.append("(sp.ten_sp LIKE ? OR sp.ma_sp LIKE ? OR sp.mo_ta LIKE ?)")
        like = f"%{keyword}%"
        params.extend([like, like, like])

    ma_loai_sp = args.get("ma_loai_sp")
    if ma_loai_sp:
        where.append("sp.ma_loai_sp = ?")
        params.append(ma_loai_sp)

    ma_ncc = args.get("ma_ncc")
    if ma_ncc:
        where.append("sp.ma_ncc = ?")
        params.append(ma_ncc)

    trang_thai = args.get("trang_thai")
    if trang_thai is not None and trang_thai != "":
        try:
            where.append("sp.trang_thai = ?")
            params.append(int(trang_thai))
        except (TypeError, ValueError):
            raise ValueError("trang_thai phải là số nguyên")
    else:
        where.append("sp.trang_thai = 1")

    gia_min = args.get("gia_min")
    if gia_min not in (None, ""):
        try:
            where.append("sp.gia >= ?")
            params.append(float(gia_min))
        except (TypeError, ValueError):
            raise ValueError("gia_min không hợp lệ")

    gia_max = args.get("gia_max")
    if gia_max not in (None, ""):
        try:
            where.append("sp.gia <= ?")
            params.append(float(gia_max))
        except (TypeError, ValueError):
            raise ValueError("gia_max không hợp lệ")

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    return where_sql, params


def get_active_products():
    return query_db(
        """
        SELECT sp.ma_sp, sp.ten_sp, sp.gia, sp.ti_le_giam_gia,
               lsp.ten_loai_sp, ncc.ten_NCC
        """
        + PRODUCT_BASE_SQL
        + " WHERE sp.trang_thai = 1"
    )


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

    assignments.append(f"cap_nhat_vao = {now_sql()}")
    params.append(ma_sp)
    affected_rows = execute_db(
        f"UPDATE SAN_PHAM SET {', '.join(assignments)} WHERE ma_sp = ?",
        tuple(params),
    )

    if affected_rows == 0:
        return None

    delete_cache(PRODUCT_CACHE_KEY)
    return get_product_by_id_for_api(ma_sp)


def list_hq_catalog_for_branch():
    """Trả về TOÀN BỘ catalog SP của trụ sở, mỗi dòng kèm flag `already_imported`.

    Phản ánh đúng quan hệ 1-N (1 SP HQ có thể được nhập về nhiều chi nhánh).
    UI bên branch sẽ hiện nút "Nhập" cho dòng chưa có, badge "Đã có" cho dòng đã có.
    """
    payload = _hq_get("/api/internal/products/list?only_active=1")
    hq_products = payload.get("data") or []

    local_codes = {
        row["ma_sp"]
        for row in query_db("SELECT ma_sp FROM SAN_PHAM")
    }
    for product in hq_products:
        product["already_imported"] = product.get("ma_sp") in local_codes
    return hq_products


def import_product_from_hq(ma_sp):
    """Kéo 1 SP từ trụ sở về chi nhánh hiện tại.

    Không phát outbox event — trụ sở đã có bản gốc, không cần đẩy ngược.
    Lỗi nếu chi nhánh đã có ma_sp (caller nên kiểm tra trước).
    """
    if not ma_sp:
        raise ValueError("ma_sp là bắt buộc")

    existing = query_db("SELECT ma_sp FROM SAN_PHAM WHERE ma_sp = ?", (ma_sp,), fetchone=True)
    if existing:
        raise ValueError(f"Sản phẩm {ma_sp} đã tồn tại ở chi nhánh này")

    payload = _hq_get(f"/api/internal/products/{ma_sp}")
    if not payload.get("success") or not payload.get("data"):
        raise ValueError(f"Không tìm thấy {ma_sp} ở trụ sở")
    src = payload["data"]

    execute_db(
        """
        INSERT INTO SAN_PHAM (
            ma_sp, ten_sp, gia, ti_le_loi_nhuan, ti_le_giam_gia,
            mo_ta, ma_loai_sp, ma_ncc, trang_thai
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            src["ma_sp"],
            src["ten_sp"],
            src.get("gia") or 0,
            src.get("ti_le_loi_nhuan") or 0,
            src.get("ti_le_giam_gia") or 0,
            src.get("mo_ta"),
            src["ma_loai_sp"],
            src["ma_ncc"],
            src.get("trang_thai", 1),
        ),
    )
    delete_cache(PRODUCT_CACHE_KEY)
    return get_product_by_id_for_api(ma_sp)


def soft_delete_product(ma_sp):
    affected_rows = execute_db(
        """
        UPDATE SAN_PHAM
        SET trang_thai = 0, cap_nhat_vao = {now}
        WHERE ma_sp = ?
        """.format(now=now_sql()),
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


def get_products_from_branch_database_for_api(ma_chi_nhanh):
    branch = query_db(
        """
        SELECT ma_chi_nhanh, ten_chi_nhanh
        FROM chi_nhanh
        WHERE ma_chi_nhanh = ?
        """,
        (ma_chi_nhanh,),
        fetchone=True,
    )
    if not branch:
        return None

    # Hiển thị TOÀN BỘ SP đang active trên DB chi nhánh (đã replicate từ HQ).
    # Không filter theo loai_sp.ma_chi_nhanh — mỗi chi nhánh phục vụ đủ catalog.
    products = query_branch_db(
        ma_chi_nhanh,
        """
        SELECT
            sp.ma_sp,
            sp.ten_sp,
            sp.gia,
            sp.ti_le_loi_nhuan,
            sp.ti_le_giam_gia,
            ROUND(sp.gia * (1 + sp.ti_le_loi_nhuan / 100) * (1 - sp.ti_le_giam_gia / 100), 0) AS gia_ban_thuc_te,
            sp.trang_thai,
            lsp.ten_loai_sp,
            ncc.ten_NCC
        FROM SAN_PHAM sp
        JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
        JOIN NCC ncc ON sp.ma_ncc = ncc.ma_NCC
        WHERE sp.trang_thai = 1
        ORDER BY sp.ma_sp
        """,
    )
    # Gắn ma_chi_nhanh + ten_chi_nhanh vào từng dòng để frontend hiển thị thống nhất
    for product in products:
        product["ma_chi_nhanh"] = branch["ma_chi_nhanh"]
        product["ten_chi_nhanh"] = branch["ten_chi_nhanh"]
    for product in products:
        format_product(product)

    return {
        "branch": branch,
        "engine": get_branch_db_engine(ma_chi_nhanh),
        "source": "branch_database",
        "data": products,
        "pagination": build_pagination_meta(1, len(products) or 1, len(products)),
    }


def _is_default_request(args):
    relevant_keys = {
        "keyword",
        "ma_loai_sp",
        "ma_ncc",
        "trang_thai",
        "gia_min",
        "gia_max",
        "page",
        "limit",
    }
    return not any(args.get(key) not in (None, "") for key in relevant_keys)


def get_products_for_api(args=None):
    args = args or {}

    if _is_default_request(args):
        cached = get_cache(PRODUCT_CACHE_KEY)
        if cached:
            data = json.loads(cached)
            return {
                "source": "cache",
                "data": data,
                "pagination": build_pagination_meta(1, len(data) or 1, len(data)),
            }

        products = get_active_products()
        for product in products:
            format_product(product)

        set_cache(PRODUCT_CACHE_KEY, json.dumps(products, ensure_ascii=False), ttl=300)
        return {
            "source": "database",
            "data": products,
            "pagination": build_pagination_meta(1, len(products) or 1, len(products)),
        }

    where_sql, where_params = _build_product_filters(args)
    page, limit, offset = parse_pagination(args)

    total_row = query_db(
        "SELECT COUNT(*) AS total " + PRODUCT_BASE_SQL + where_sql,
        tuple(where_params),
        fetchone=True,
    )
    total = total_row["total"] if total_row else 0

    page_clause, page_params = pagination_clause("sp.ma_sp", offset, limit)
    products = query_db(
        """
        SELECT sp.ma_sp, sp.ten_sp, sp.gia, sp.ti_le_giam_gia,
               sp.trang_thai, sp.ma_loai_sp, sp.ma_ncc,
               lsp.ten_loai_sp, ncc.ten_NCC
        """
        + PRODUCT_BASE_SQL
        + where_sql
        + page_clause,
        tuple(where_params) + page_params,
    )
    for product in products:
        format_product(product)

    return {
        "source": "database",
        "data": products,
        "pagination": build_pagination_meta(page, limit, total),
    }
