"""Trụ sở không lưu HOA_DON local. Service này đọc trực tiếp từ DB chi nhánh
(qua query_branch_db) rồi tổng hợp lại cho UI / API trụ sở.
"""

import logging
from decimal import Decimal

from db import (
    execute_branch_db,
    execute_db,
    get_branch_db_connection,
    get_branch_db_engine,
    has_branch_db_settings,
    query_branch_db,
)
from services.branch_replication_service import (
    backfill_invoice_replica,
    get_replica_invoice_detail,
    get_replica_invoices_from_branch,
    get_replica_revenue_for_branch,
    write_failover_invoice,
)
from services.branch_service import get_branch_by_id, get_branches


log = logging.getLogger(__name__)


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
            SELECT hd.ma_hd, hd.ngay_lap, hd.ma_nhan_vien,
                   COALESCE(hd.ten_nhan_vien, nv.ho_ten) AS ten_nhan_vien,
                   hd.ten_kh, hd.sdt_kh, hd.tong_tien, hd.ghi_chu
            FROM HOA_DON hd
            LEFT JOIN NHAN_VIEN nv ON hd.ma_nhan_vien = nv.ma_nhan_vien
            {where_sql}
            ORDER BY hd.ngay_lap DESC, hd.ma_hd
            """,
            tuple(params),
        )
    except Exception as exc:
        replica = get_replica_invoices_from_branch(ma_chi_nhanh, args)
        replica["branch_error"] = str(exc)
        return replica

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

    try:
        invoice = query_branch_db(
            ma_chi_nhanh,
            """
            SELECT hd.ma_hd, hd.ngay_lap, hd.ma_nhan_vien,
                   COALESCE(hd.ten_nhan_vien, nv.ho_ten) AS ten_nhan_vien,
                   hd.ten_kh, hd.sdt_kh, hd.tong_tien, hd.ghi_chu
            FROM HOA_DON hd
            LEFT JOIN NHAN_VIEN nv ON hd.ma_nhan_vien = nv.ma_nhan_vien
            WHERE hd.ma_hd = ?
            """,
            (ma_hd,),
            fetchone=True,
        )
    except Exception:
        return get_replica_invoice_detail(ma_chi_nhanh, ma_hd)
    if not invoice:
        return None
    invoice["tong_tien"] = _to_float(invoice.get("tong_tien"))
    invoice["ngay_lap"] = _iso(invoice.get("ngay_lap"))
    invoice["ma_chi_nhanh"] = ma_chi_nhanh

    try:
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
    except Exception:
        return get_replica_invoice_detail(ma_chi_nhanh, ma_hd)
    for item in items:
        item["don_gia"] = _to_float(item.get("don_gia"))
        item["thanh_tien"] = _to_float(item.get("thanh_tien"))
        if item.get("so_luong") is not None:
            item["so_luong"] = int(item["so_luong"])

    invoice["chi_tiet"] = items
    return invoice


def _validate_invoice_payload(data):
    required = ["ma_hd", "ma_nhan_vien"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        raise ValueError("Thiếu trường bắt buộc: " + ", ".join(missing))

    ma_hd = str(data.get("ma_hd") or "").strip()
    if not ma_hd.isdigit() or int(ma_hd) <= 0:
        raise ValueError("Mã hóa đơn phải là số nguyên dương")
    data["ma_hd"] = ma_hd

    items = data.get("items") or data.get("chi_tiet") or []
    if not isinstance(items, list) or not items:
        raise ValueError("Hóa đơn phải có ít nhất 1 chi tiết")

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


def _placeholder_sql(sql, engine):
    return sql.replace("?", "%s") if engine in {"mysql", "postgresql"} else sql


def _create_invoice_in_branch_db(ma_chi_nhanh, data, items):
    """Tao hoa don thang vao DB chi nhanh (transactional). Raises neu DB khong reachable
    hoac vi pham nghiep vu (employee/SP khong ton tai, ma_hd da co)."""
    tong_tien = round(sum(item["thanh_tien"] for item in items), 2)

    employee = query_branch_db(
        ma_chi_nhanh,
        "SELECT ma_nhan_vien, ho_ten FROM NHAN_VIEN WHERE ma_nhan_vien = ?",
        (data["ma_nhan_vien"],),
        fetchone=True,
    )
    if not employee:
        raise ValueError(f"Nhân viên {data['ma_nhan_vien']} không tồn tại ở chi nhánh {ma_chi_nhanh}")
    data["ten_nhan_vien"] = data.get("ten_nhan_vien") or employee["ho_ten"]

    existing = query_branch_db(
        ma_chi_nhanh,
        "SELECT ma_hd FROM HOA_DON WHERE ma_hd = ?",
        (data["ma_hd"],),
        fetchone=True,
    )
    if existing:
        raise ValueError(f"Mã hóa đơn {data['ma_hd']} đã tồn tại")

    ma_sps = [item["ma_sp"] for item in items]
    placeholders = ", ".join(["?"] * len(ma_sps))
    found = query_branch_db(
        ma_chi_nhanh,
        f"SELECT ma_sp FROM SAN_PHAM WHERE ma_sp IN ({placeholders})",
        tuple(ma_sps),
    )
    found_codes = {row["ma_sp"] for row in found}
    missing_codes = [code for code in ma_sps if code not in found_codes]
    if missing_codes:
        raise ValueError("Sản phẩm không tồn tại ở chi nhánh: " + ", ".join(missing_codes))

    engine = get_branch_db_engine(ma_chi_nhanh)
    conn = get_branch_db_connection(ma_chi_nhanh)
    try:
        cursor = conn.cursor()
        cursor.execute(
            _placeholder_sql(
                "INSERT INTO HOA_DON (ma_hd, ma_nhan_vien, ten_nhan_vien, ten_kh, sdt_kh, tong_tien, ghi_chu) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                engine,
            ),
            (
                data["ma_hd"],
                data["ma_nhan_vien"],
                data.get("ten_nhan_vien"),
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


def create_failover_invoice_for_branch(ma_chi_nhanh, data):
    """Tao hoa don khi backend chi nhanh chet:
       1. Validate payload.
       2. Neu DB chi nhanh reachable, ghi thang vao DB chi nhanh (HOA_DON + CT_HOA_DON)
          → HQ tu dong thay du lieu moi qua doc realtime.
       3. Neu DB chi nhanh cung khong reachable, fallback ghi vao replica + central_failover_events
          → replay khi backend chi nhanh song lai.
    """
    items = _validate_invoice_payload(data)

    try:
        _create_invoice_in_branch_db(ma_chi_nhanh, data, items)
    except ValueError:
        raise
    except Exception as exc:
        log.warning(
            "[failover-invoice] branch DB unreachable for %s, falling back to replica: %s",
            ma_chi_nhanh,
            exc,
        )
        payload = dict(data)
        payload["items"] = items
        result = write_failover_invoice(ma_chi_nhanh, "INVOICE_UPSERT", data.get("ma_hd"), payload)
        if result:
            result["branch_db_unreachable"] = True
        return result

    invoice = get_invoice_detail_from_branch(ma_chi_nhanh, data["ma_hd"])
    if invoice:
        try:
            backfill_invoice_replica(ma_chi_nhanh, invoice, invoice.get("chi_tiet"))
        except Exception as exc:
            log.warning("[failover-invoice] replica sync failed for %s: %s", data["ma_hd"], exc)
        invoice["source"] = "branch_database_via_hq"
    return invoice


def delete_failover_invoice_for_branch(ma_chi_nhanh, ma_hd):
    """Xoa hoa don khi backend chi nhanh chet, write-through neu DB chi nhanh con song."""
    try:
        execute_branch_db(ma_chi_nhanh, "DELETE FROM CT_HOA_DON WHERE ma_hd = ?", (ma_hd,))
        execute_branch_db(ma_chi_nhanh, "DELETE FROM HOA_DON WHERE ma_hd = ?", (ma_hd,))
    except Exception as exc:
        log.warning(
            "[failover-invoice] branch DB unreachable for %s delete, falling back to replica: %s",
            ma_chi_nhanh,
            exc,
        )
        return write_failover_invoice(ma_chi_nhanh, "INVOICE_DELETE", ma_hd, {"ma_hd": ma_hd})

    try:
        branch = ma_chi_nhanh.upper()
        execute_db(
            "DELETE FROM branch_ct_hoa_don_replica WHERE ma_chi_nhanh = ? AND ma_hd = ?",
            (branch, ma_hd),
        )
        execute_db(
            "DELETE FROM branch_hoa_don_replica WHERE ma_chi_nhanh = ? AND ma_hd = ?",
            (branch, ma_hd),
        )
    except Exception as exc:
        log.warning("[failover-invoice] replica delete failed for %s: %s", ma_hd, exc)
    return {"ma_hd": ma_hd, "source": "branch_database_via_hq"}


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
            "source": result.get("source", "branch_database"),
            "so_hoa_don": len(result["data"]),
            "error": result.get("error"),
            "branch_error": result.get("branch_error"),
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
        replica = get_replica_revenue_for_branch(ma_chi_nhanh)
        replica["branch_error"] = str(exc)
        return replica


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
            "source": data.get("source", "branch_database"),
            "so_hoa_don": data["so_hoa_don"],
            "tong_doanh_thu": data["tong_doanh_thu"],
            "error": data.get("error"),
            "branch_error": data.get("branch_error"),
        })

        if data["branch_status"] not in ("ok", "replica"):
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
