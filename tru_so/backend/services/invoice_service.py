"""Trụ sở không lưu HOA_DON local. Service này đọc trực tiếp từ DB chi nhánh
(qua query_branch_db) rồi tổng hợp lại cho UI / API trụ sở.
"""

from decimal import Decimal

from db import get_branch_db_engine, has_branch_db_settings, query_branch_db
from services.branch_service import get_branch_by_id, get_branches


def _to_float(value):
    if value is None:
        return 0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def _iso(value):
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else value


def _branch_ready(ma_chi_nhanh):
    if not get_branch_by_id(ma_chi_nhanh):
        return False
    return has_branch_db_settings(ma_chi_nhanh)


def get_invoices_from_branch(ma_chi_nhanh, args=None):
    """Đọc danh sách hóa đơn từ DB của 1 chi nhánh cụ thể."""
    args = args or {}
    if not _branch_ready(ma_chi_nhanh):
        return {"data": [], "branch_status": "not_configured"}

    where, params = [], []
    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        where.append("(hd.ma_hd LIKE ? OR hd.ten_kh LIKE ? OR hd.sdt_kh LIKE ?)")
        params.extend([like, like, like])

    tu_ngay = args.get("tu_ngay")
    if tu_ngay:
        where.append("hd.ngay_lap >= ?")
        params.append(tu_ngay)

    den_ngay = args.get("den_ngay")
    if den_ngay:
        where.append("hd.ngay_lap < ?")
        params.append(den_ngay)

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    try:
        rows = query_branch_db(
            ma_chi_nhanh,
            f"""
            SELECT hd.ma_hd, hd.ngay_lap, hd.ma_nhan_vien, nv.ho_ten AS ten_nhan_vien,
                   hd.ten_kh, hd.sdt_kh, hd.tong_tien, hd.ghi_chu
            FROM HOA_DON hd
            LEFT JOIN NHAN_VIEN nv ON hd.ma_nhan_vien = nv.ma_nhan_vien
            {where_sql}
            ORDER BY hd.ngay_lap DESC, hd.ma_hd
            """,
            tuple(params),
        )
    except Exception as exc:
        return {"data": [], "branch_status": "unreachable", "error": str(exc)}

    for row in rows:
        row["tong_tien"] = _to_float(row.get("tong_tien"))
        row["ngay_lap"] = _iso(row.get("ngay_lap"))
        row["ma_chi_nhanh"] = ma_chi_nhanh

    return {
        "data": rows,
        "branch_status": "ok",
        "ma_chi_nhanh": ma_chi_nhanh,
        "engine": get_branch_db_engine(ma_chi_nhanh),
    }


def get_invoice_detail_from_branch(ma_chi_nhanh, ma_hd):
    if not _branch_ready(ma_chi_nhanh):
        return None

    invoice = query_branch_db(
        ma_chi_nhanh,
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
    invoice["tong_tien"] = _to_float(invoice.get("tong_tien"))
    invoice["ngay_lap"] = _iso(invoice.get("ngay_lap"))
    invoice["ma_chi_nhanh"] = ma_chi_nhanh

    items = query_branch_db(
        ma_chi_nhanh,
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
        item["don_gia"] = _to_float(item.get("don_gia"))
        item["thanh_tien"] = _to_float(item.get("thanh_tien"))
        if item.get("so_luong") is not None:
            item["so_luong"] = int(item["so_luong"])

    invoice["chi_tiet"] = items
    return invoice


def get_all_invoices_aggregated(args=None):
    """Gom danh sách hóa đơn từ TẤT CẢ chi nhánh đang cấu hình."""
    branches = get_branches()
    aggregated = []
    branch_info = []

    for branch in branches:
        ma = branch["ma_chi_nhanh"]
        result = get_invoices_from_branch(ma, args)
        aggregated.extend(result["data"])
        branch_info.append({
            "ma_chi_nhanh": ma,
            "ten_chi_nhanh": branch["ten_chi_nhanh"],
            "engine": get_branch_db_engine(ma),
            "branch_status": result.get("branch_status", "unknown"),
            "so_hoa_don": len(result["data"]),
            "error": result.get("error"),
        })

    aggregated.sort(key=lambda r: (r.get("ngay_lap") or "", r.get("ma_hd") or ""), reverse=True)

    return {
        "data": aggregated,
        "branches": branch_info,
        "total": len(aggregated),
    }


def _revenue_for_branch(ma_chi_nhanh):
    if not _branch_ready(ma_chi_nhanh):
        return {
            "branch_status": "not_configured",
            "so_hoa_don": 0,
            "tong_doanh_thu": 0,
            "theo_ngay": [],
            "theo_san_pham": [],
        }

    try:
        summary = query_branch_db(
            ma_chi_nhanh,
            "SELECT COUNT(*) AS so_hoa_don, COALESCE(SUM(tong_tien), 0) AS tong_doanh_thu FROM HOA_DON",
            fetchone=True,
        ) or {}

        theo_ngay = query_branch_db(
            ma_chi_nhanh,
            "SELECT ngay, so_hoa_don, tong_doanh_thu FROM v_doanh_thu_theo_ngay ORDER BY ngay DESC",
        )
        for row in theo_ngay:
            row["so_hoa_don"] = int(row["so_hoa_don"] or 0)
            row["tong_doanh_thu"] = _to_float(row["tong_doanh_thu"])
            row["ngay"] = _iso(row.get("ngay"))

        theo_sp = query_branch_db(
            ma_chi_nhanh,
            "SELECT ma_sp, ten_sp, tong_so_luong, tong_doanh_thu FROM v_doanh_thu_theo_san_pham ORDER BY tong_doanh_thu DESC",
        )
        for row in theo_sp:
            row["tong_so_luong"] = int(row["tong_so_luong"] or 0)
            row["tong_doanh_thu"] = _to_float(row["tong_doanh_thu"])

        return {
            "branch_status": "ok",
            "so_hoa_don": int(summary.get("so_hoa_don") or 0),
            "tong_doanh_thu": _to_float(summary.get("tong_doanh_thu")),
            "theo_ngay": theo_ngay,
            "theo_san_pham": theo_sp,
        }
    except Exception as exc:
        return {
            "branch_status": "unreachable",
            "error": str(exc),
            "so_hoa_don": 0,
            "tong_doanh_thu": 0,
            "theo_ngay": [],
            "theo_san_pham": [],
        }


def get_revenue_for_branch(ma_chi_nhanh):
    branch = get_branch_by_id(ma_chi_nhanh)
    if not branch:
        return None
    payload = _revenue_for_branch(ma_chi_nhanh)
    payload["ma_chi_nhanh"] = ma_chi_nhanh
    payload["ten_chi_nhanh"] = branch["ten_chi_nhanh"]
    payload["engine"] = get_branch_db_engine(ma_chi_nhanh)
    return payload


def get_revenue_aggregated():
    """Tổng hợp doanh thu mọi chi nhánh; trụ sở không lưu local."""
    branches = get_branches()
    per_branch = []
    tong_hd = 0
    tong_doanh_thu = 0.0
    theo_ngay_map = {}
    theo_sp_map = {}

    for branch in branches:
        ma = branch["ma_chi_nhanh"]
        data = _revenue_for_branch(ma)
        per_branch.append({
            "ma_chi_nhanh": ma,
            "ten_chi_nhanh": branch["ten_chi_nhanh"],
            "engine": get_branch_db_engine(ma),
            "branch_status": data["branch_status"],
            "so_hoa_don": data["so_hoa_don"],
            "tong_doanh_thu": data["tong_doanh_thu"],
            "error": data.get("error"),
        })

        if data["branch_status"] != "ok":
            continue

        tong_hd += data["so_hoa_don"]
        tong_doanh_thu += data["tong_doanh_thu"]

        for row in data["theo_ngay"]:
            key = row["ngay"]
            entry = theo_ngay_map.setdefault(
                key, {"ngay": key, "so_hoa_don": 0, "tong_doanh_thu": 0.0}
            )
            entry["so_hoa_don"] += row["so_hoa_don"]
            entry["tong_doanh_thu"] += row["tong_doanh_thu"]

        for row in data["theo_san_pham"]:
            key = row["ma_sp"]
            entry = theo_sp_map.setdefault(
                key,
                {
                    "ma_sp": row["ma_sp"],
                    "ten_sp": row["ten_sp"],
                    "tong_so_luong": 0,
                    "tong_doanh_thu": 0.0,
                },
            )
            entry["tong_so_luong"] += row["tong_so_luong"]
            entry["tong_doanh_thu"] += row["tong_doanh_thu"]

    theo_ngay = sorted(theo_ngay_map.values(), key=lambda r: r["ngay"] or "", reverse=True)
    theo_san_pham = sorted(theo_sp_map.values(), key=lambda r: r["tong_doanh_thu"], reverse=True)

    return {
        "summary": {
            "so_hoa_don": tong_hd,
            "tong_doanh_thu": round(tong_doanh_thu, 2),
        },
        "theo_ngay": theo_ngay,
        "theo_san_pham": theo_san_pham,
        "theo_chi_nhanh": per_branch,
    }
