"""Replay central_failover_events ve DB chi nhanh sau khi backend chi nhanh song lai.

Khi trang thai chi nhanh chuyen tu down -> up, ham replay_pending_events_for_branch
duoc goi de day cac thay doi (nhan vien / hoa don / san pham nhap-from-HQ) phat sinh
trong giai doan failover xuong DB chi nhanh that, tranh chenh lech du lieu.
"""

import json
from datetime import datetime, timezone

from db import (
    execute_branch_db,
    execute_db,
    get_branch_db_engine,
    now_sql,
    password_hash_sql,
    query_branch_db,
    query_db,
)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _mark_replayed(event_id, status, message=None):
    execute_db(
        """
        UPDATE central_failover_events
        SET status = ?, replayed_at = SYSUTCDATETIME()
        WHERE event_id = ?
        """,
        (status, event_id),
    )


def _list_pending_for_branch(branch_code):
    return query_db(
        """
        SELECT event_id, target_branch, entity_type, object_id, event_type, payload
        FROM central_failover_events
        WHERE target_branch = ? AND status = 'pending'
        ORDER BY created_at, event_id
        """,
        (branch_code.upper(),),
    )


def _decode_payload(raw):
    if isinstance(raw, str):
        return json.loads(raw)
    if isinstance(raw, (bytes, bytearray)):
        return json.loads(raw.decode("utf-8"))
    return raw or {}


def _replay_employee(branch_code, event_type, payload):
    data = payload.get("data") or {}
    ma_nv = data.get("ma_nhan_vien") or payload.get("object_id")
    if not ma_nv:
        raise ValueError("Missing ma_nhan_vien in failover event")

    branch_engine = get_branch_db_engine(branch_code)
    now_fn = now_sql(branch_engine)

    if event_type == "EMPLOYEE_DELETE":
        execute_branch_db(
            branch_code,
            f"""
            UPDATE NHAN_VIEN
            SET trang_thai = 0,
                ngay_ket_thuc = COALESCE(ngay_ket_thuc, {now_fn})
            WHERE ma_nhan_vien = ?
            """,
            (ma_nv,),
        )
        return

    existing = query_branch_db(
        branch_code,
        "SELECT ma_nhan_vien FROM NHAN_VIEN WHERE ma_nhan_vien = ?",
        (ma_nv,),
        fetchone=True,
    )
    fields = {
        "ho_ten": data.get("ho_ten"),
        "cccd": data.get("cccd"),
        "sdt": data.get("sdt"),
        "luong": data.get("luong"),
        "trang_thai": data.get("trang_thai", 1),
        "ma_phong_ban": data.get("ma_phong_ban"),
        "ma_ngay_lam": data.get("ma_ngay_lam", 0),
        "chuc_vu": data.get("chuc_vu", "nhan_vien"),
        "ngay_bat_dau": data.get("ngay_bat_dau"),
        "ngay_ket_thuc": data.get("ngay_ket_thuc"),
    }

    if existing:
        assignments = ", ".join(f"{k} = ?" for k in fields.keys())
        params = list(fields.values()) + [ma_nv]
        execute_branch_db(
            branch_code,
            f"UPDATE NHAN_VIEN SET {assignments} WHERE ma_nhan_vien = ?",
            tuple(params),
        )
        return

    raw_password = data.get("mat_khau") or "FAILOVER_PLACEHOLDER"
    password_expr = password_hash_sql(branch_engine)
    columns = ["ma_nhan_vien"] + list(fields.keys()) + ["mat_khau"]
    value_placeholders = ", ".join(["?"] * (len(columns) - 1)) + ", " + password_expr
    execute_branch_db(
        branch_code,
        f"INSERT INTO NHAN_VIEN ({', '.join(columns)}) VALUES ({value_placeholders})",
        tuple([ma_nv] + list(fields.values()) + [raw_password]),
    )


def _replay_invoice_upsert(branch_code, payload):
    data = payload.get("data") or {}
    ma_hd = data.get("ma_hd") or payload.get("object_id")
    if not ma_hd:
        raise ValueError("Missing ma_hd in failover event")

    existing = query_branch_db(
        branch_code,
        "SELECT ma_hd FROM HOA_DON WHERE ma_hd = ?",
        (ma_hd,),
        fetchone=True,
    )
    if existing:
        execute_branch_db(
            branch_code,
            """
            UPDATE HOA_DON
            SET ngay_lap = ?, ma_nhan_vien = ?, ten_nhan_vien = ?, ten_kh = ?, sdt_kh = ?,
                tong_tien = ?, ghi_chu = ?
            WHERE ma_hd = ?
            """,
            (
                data.get("ngay_lap"),
                data.get("ma_nhan_vien"),
                data.get("ten_nhan_vien"),
                data.get("ten_kh"),
                data.get("sdt_kh"),
                data.get("tong_tien") or 0,
                data.get("ghi_chu"),
                ma_hd,
            ),
        )
        execute_branch_db(branch_code, "DELETE FROM CT_HOA_DON WHERE ma_hd = ?", (ma_hd,))
    else:
        execute_branch_db(
            branch_code,
            """
            INSERT INTO HOA_DON (
                ma_hd, ngay_lap, ma_nhan_vien, ten_nhan_vien, ten_kh, sdt_kh, tong_tien, ghi_chu
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ma_hd,
                data.get("ngay_lap"),
                data.get("ma_nhan_vien"),
                data.get("ten_nhan_vien"),
                data.get("ten_kh"),
                data.get("sdt_kh"),
                data.get("tong_tien") or 0,
                data.get("ghi_chu"),
            ),
        )

    for item in data.get("chi_tiet") or []:
        execute_branch_db(
            branch_code,
            """
            INSERT INTO CT_HOA_DON (ma_hd, ma_sp, so_luong, don_gia, thanh_tien)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ma_hd,
                item.get("ma_sp"),
                int(item.get("so_luong") or 0),
                item.get("don_gia") or 0,
                item.get("thanh_tien") or 0,
            ),
        )


def _replay_invoice_delete(branch_code, payload):
    ma_hd = (payload.get("data") or {}).get("ma_hd") or payload.get("object_id")
    if not ma_hd:
        raise ValueError("Missing ma_hd in failover event")
    execute_branch_db(branch_code, "DELETE FROM CT_HOA_DON WHERE ma_hd = ?", (ma_hd,))
    execute_branch_db(branch_code, "DELETE FROM HOA_DON WHERE ma_hd = ?", (ma_hd,))


def _replay_product_import(branch_code, payload):
    data = payload.get("data") or {}
    ma_sp = data.get("ma_sp") or payload.get("object_id")
    if not ma_sp:
        raise ValueError("Missing ma_sp in failover event")

    existing = query_branch_db(
        branch_code,
        "SELECT ma_sp, trang_thai FROM SAN_PHAM WHERE ma_sp = ?",
        (ma_sp,),
        fetchone=True,
    )
    if existing:
        if int(existing.get("trang_thai") or 0):
            return
        execute_branch_db(
            branch_code,
            """
            UPDATE SAN_PHAM
            SET ten_sp = ?, gia = ?, ti_le_loi_nhuan = ?, ti_le_giam_gia = ?,
                mo_ta = ?, ma_loai_sp = ?, ma_ncc = ?, trang_thai = 1
            WHERE ma_sp = ?
            """,
            (
                data["ten_sp"],
                data.get("gia") or 0,
                data.get("ti_le_loi_nhuan") or 0,
                data.get("ti_le_giam_gia") or 0,
                data.get("mo_ta"),
                data["ma_loai_sp"],
                data["ma_ncc"],
                ma_sp,
            ),
        )
        return

    execute_branch_db(
        branch_code,
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
            data.get("gia") or 0,
            data.get("ti_le_loi_nhuan") or 0,
            data.get("ti_le_giam_gia") or 0,
            data.get("mo_ta"),
            data["ma_loai_sp"],
            data["ma_ncc"],
            data.get("trang_thai", 1),
        ),
    )


def _replay_product_remove(branch_code, payload):
    ma_sp = (payload.get("data") or {}).get("ma_sp") or payload.get("object_id")
    if not ma_sp:
        raise ValueError("Missing ma_sp in failover event")
    execute_branch_db(
        branch_code,
        "UPDATE SAN_PHAM SET trang_thai = 0 WHERE ma_sp = ?",
        (ma_sp,),
    )


def _replay_one_event(branch_code, event):
    payload = _decode_payload(event["payload"])
    entity = str(event["entity_type"]).lower()
    event_type = str(event["event_type"]).upper()

    if entity == "employee":
        _replay_employee(branch_code, event_type, payload)
    elif entity == "invoice":
        if event_type == "INVOICE_DELETE":
            _replay_invoice_delete(branch_code, payload)
        else:
            _replay_invoice_upsert(branch_code, payload)
    elif entity == "product":
        if event_type == "PRODUCT_IMPORT":
            _replay_product_import(branch_code, payload)
        elif event_type == "PRODUCT_REMOVE":
            _replay_product_remove(branch_code, payload)
        else:
            raise ValueError(f"Unsupported product event type: {event_type}")
    else:
        raise ValueError(f"Unsupported entity type: {entity}")


def replay_pending_events_for_branch(branch_code):
    """Replay tat ca event con pending cua branch. Tra ve summary."""
    branch = branch_code.upper()
    events = _list_pending_for_branch(branch)
    summary = {
        "branch_code": branch,
        "total": len(events),
        "replayed": 0,
        "failed": 0,
        "errors": [],
        "started_at": _now_iso(),
    }
    for event in events:
        try:
            _replay_one_event(branch, event)
            _mark_replayed(event["event_id"], "replayed")
            summary["replayed"] += 1
        except Exception as exc:
            _mark_replayed(event["event_id"], "failed")
            summary["failed"] += 1
            summary["errors"].append({"event_id": event["event_id"], "error": str(exc)})
    summary["finished_at"] = _now_iso()
    return summary
