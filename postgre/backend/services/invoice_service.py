from decimal import Decimal

from db import (
    build_pagination_meta,
    execute_db,
    get_db_connection,
    get_db_engine,
    pagination_clause,
    parse_pagination,
    query_db,
)


def _placeholder_sql(sql, engine):
    return sql.replace("?", "%s") if engine in {"mysql", "postgresql"} else sql


def _format_money(value):
    if value is None:
        return 0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def _format_invoice_row(row):
    if not row:
        return None
    if "tong_tien" in row:
        row["tong_tien"] = _format_money(row["tong_tien"])
    if "ngay_lap" in row and row["ngay_lap"] is not None:
        row["ngay_lap"] = row["ngay_lap"].isoformat() if hasattr(row["ngay_lap"], "isoformat") else row["ngay_lap"]
    return row


def _format_item_row(row):
    if not row:
        return None
    for field in ("don_gia", "thanh_tien"):
        if field in row:
            row[field] = _format_money(row[field])
    if "so_luong" in row and row["so_luong"] is not None:
        row["so_luong"] = int(row["so_luong"])
    return row


def get_invoices_for_api(args=None):
    args = args or {}
    where, params = [], []

    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        where.append("(hd.ma_hd LIKE ? OR hd.ten_kh LIKE ? OR hd.sdt_kh LIKE ?)")
        params.extend([like, like, like])

    ma_nv = args.get("ma_nhan_vien")
    if ma_nv:
        where.append("hd.ma_nhan_vien = ?")
        params.append(ma_nv)

    tu_ngay = args.get("tu_ngay")
    if tu_ngay:
        where.append("hd.ngay_lap >= ?")
        params.append(tu_ngay)

    den_ngay = args.get("den_ngay")
    if den_ngay:
        where.append("hd.ngay_lap < ?")
        params.append(den_ngay)

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    page, limit, offset = parse_pagination(args)

    total_row = query_db(
        f"SELECT COUNT(*) AS total FROM HOA_DON hd{where_sql}",
        tuple(params),
        fetchone=True,
    )
    total = total_row["total"] if total_row else 0

    page_clause, page_params = pagination_clause("hd.ngay_lap DESC, hd.ma_hd", offset, limit)
    rows = query_db(
        f"""
        SELECT hd.ma_hd, hd.ngay_lap, hd.ma_nhan_vien, nv.ho_ten AS ten_nhan_vien,
               hd.ten_kh, hd.sdt_kh, hd.tong_tien, hd.ghi_chu
        FROM HOA_DON hd
        LEFT JOIN NHAN_VIEN nv ON hd.ma_nhan_vien = nv.ma_nhan_vien
        {where_sql}
        {page_clause}
        """,
        tuple(params) + page_params,
    )
    for row in rows:
        _format_invoice_row(row)

    return {
        "data": rows,
        "pagination": build_pagination_meta(page, limit, total),
    }


def get_invoice_detail_for_api(ma_hd):
    invoice = query_db(
        """
        SELECT hd.ma_hd, hd.ngay_lap, hd.ma_nhan_vien, nv.ho_ten AS ten_nhan_vien,
               hd.ten_kh, hd.sdt_kh, hd.tong_tien, hd.ghi_chu
        FROM HOA_DON hd
        LEFT JOIN NHAN_VIEN nv ON hd.ma_nhan_vien = nv.ma_nhan_vien
        WHERE hd.ma_hd = ?
        """,
        (ma_hd,),
        fetchone=True,
    )
    if not invoice:
        return None
    _format_invoice_row(invoice)

    items = query_db(
        """
        SELECT ct.id, ct.ma_sp, sp.ten_sp,
               ct.so_luong, ct.don_gia, ct.thanh_tien
        FROM CT_HOA_DON ct
        JOIN SAN_PHAM sp ON ct.ma_sp = sp.ma_sp
        WHERE ct.ma_hd = ?
        ORDER BY ct.id
        """,
        (ma_hd,),
    )
    for item in items:
        _format_item_row(item)

    invoice["chi_tiet"] = items
    return invoice


def _validate_payload(data):
    required = ["ma_hd", "ma_nhan_vien", "items"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        raise ValueError("Thiếu trường bắt buộc: " + ", ".join(missing))

    items = data.get("items") or []
    if not isinstance(items, list) or not items:
        raise ValueError("Hóa đơn phải có ít nhất 1 chi tiết (items)")

    cleaned = []
    for idx, raw in enumerate(items):
        if not isinstance(raw, dict):
            raise ValueError(f"items[{idx}] không hợp lệ")
        ma_sp = raw.get("ma_sp")
        if not ma_sp:
            raise ValueError(f"items[{idx}].ma_sp là bắt buộc")
        try:
            so_luong = int(raw.get("so_luong", 0))
            don_gia = float(raw.get("don_gia", 0))
        except (TypeError, ValueError):
            raise ValueError(f"items[{idx}] số lượng/đơn giá không hợp lệ")
        if so_luong <= 0 or don_gia < 0:
            raise ValueError(f"items[{idx}] số lượng phải > 0 và đơn giá >= 0")
        cleaned.append({
            "ma_sp": ma_sp,
            "so_luong": so_luong,
            "don_gia": don_gia,
            "thanh_tien": round(so_luong * don_gia, 2),
        })
    return cleaned


def create_invoice(data):
    items = _validate_payload(data)
    tong_tien = round(sum(item["thanh_tien"] for item in items), 2)

    employee = query_db(
        "SELECT ma_nhan_vien FROM NHAN_VIEN WHERE ma_nhan_vien = ?",
        (data["ma_nhan_vien"],),
        fetchone=True,
    )
    if not employee:
        raise ValueError(f"Nhân viên {data['ma_nhan_vien']} không tồn tại")

    existing = query_db("SELECT 1 AS ok FROM HOA_DON WHERE ma_hd = ?", (data["ma_hd"],), fetchone=True)
    if existing:
        raise ValueError(f"Mã hóa đơn {data['ma_hd']} đã tồn tại")

    ma_sps = [item["ma_sp"] for item in items]
    placeholders = ", ".join(["?"] * len(ma_sps))
    found = query_db(
        f"SELECT ma_sp FROM SAN_PHAM WHERE ma_sp IN ({placeholders})",
        tuple(ma_sps),
    )
    found_codes = {row["ma_sp"] for row in found}
    missing_codes = [code for code in ma_sps if code not in found_codes]
    if missing_codes:
        raise ValueError("Sản phẩm không tồn tại: " + ", ".join(missing_codes))

    engine = get_db_engine()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            _placeholder_sql(
                "INSERT INTO HOA_DON (ma_hd, ma_nhan_vien, ten_kh, sdt_kh, tong_tien, ghi_chu) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                engine,
            ),
            (
                data["ma_hd"],
                data["ma_nhan_vien"],
                data.get("ten_kh"),
                data.get("sdt_kh"),
                tong_tien,
                data.get("ghi_chu"),
            ),
        )

        for item in items:
            cursor.execute(
                _placeholder_sql(
                    "INSERT INTO CT_HOA_DON (ma_hd, ma_sp, so_luong, don_gia, thanh_tien) "
                    "VALUES (?, ?, ?, ?, ?)",
                    engine,
                ),
                (data["ma_hd"], item["ma_sp"], item["so_luong"], item["don_gia"], item["thanh_tien"]),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return get_invoice_detail_for_api(data["ma_hd"])


def delete_invoice(ma_hd):
    affected = execute_db("DELETE FROM HOA_DON WHERE ma_hd = ?", (ma_hd,))
    return affected > 0


def get_revenue_stats():
    summary_row = query_db(
        "SELECT COUNT(*) AS so_hoa_don, COALESCE(SUM(tong_tien), 0) AS tong_doanh_thu FROM HOA_DON",
        fetchone=True,
    )
    summary = {
        "so_hoa_don": int(summary_row["so_hoa_don"]) if summary_row else 0,
        "tong_doanh_thu": _format_money(summary_row["tong_doanh_thu"]) if summary_row else 0,
    }

    by_day = query_db(
        """
        SELECT ngay, so_hoa_don, tong_doanh_thu
        FROM v_doanh_thu_theo_ngay
        ORDER BY ngay DESC
        """
    )
    for row in by_day:
        row["so_hoa_don"] = int(row["so_hoa_don"])
        row["tong_doanh_thu"] = _format_money(row["tong_doanh_thu"])
        if hasattr(row["ngay"], "isoformat"):
            row["ngay"] = row["ngay"].isoformat()

    by_product = query_db(
        """
        SELECT ma_sp, ten_sp, tong_so_luong, tong_doanh_thu
        FROM v_doanh_thu_theo_san_pham
        ORDER BY tong_doanh_thu DESC
        """
    )
    for row in by_product:
        row["tong_so_luong"] = int(row["tong_so_luong"] or 0)
        row["tong_doanh_thu"] = _format_money(row["tong_doanh_thu"])

    return {
        "summary": summary,
        "theo_ngay": by_day,
        "theo_san_pham": by_product,
    }
