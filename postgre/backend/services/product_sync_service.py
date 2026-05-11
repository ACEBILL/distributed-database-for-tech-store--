import json
import os
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

from db import (
    build_pagination_meta,
    execute_db,
    get_db_engine,
    now_sql,
    pagination_clause,
    parse_pagination,
    query_db,
)


SUPPORTED_PRODUCT_EVENTS = {
    "PRODUCT_CREATED",
    "PRODUCT_UPDATED",
    "PRODUCT_DELETED",
}


def ensure_sync_log_table():
    engine = get_db_engine()
    id_column = "SERIAL PRIMARY KEY" if engine == "postgresql" else "INT AUTO_INCREMENT PRIMARY KEY"
    timestamp_type = "TIMESTAMP" if engine == "postgresql" else "DATETIME"
    execute_db(
        f"""
        CREATE TABLE IF NOT EXISTS sync_log (
            id {id_column},
            event_id VARCHAR(100) NOT NULL UNIQUE,
            event_type VARCHAR(50) NOT NULL,
            ma_sp VARCHAR(50),
            version INT NOT NULL,
            source VARCHAR(50),
            target_branch VARCHAR(50),
            status VARCHAR(20) NOT NULL,
            message TEXT,
            received_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
            applied_at {timestamp_type} NULL
        )
        """
    )


def _branch_code():
    from flask import current_app

    return (current_app.config.get("BRANCH_CODE") or "").upper()


def _normalize_product_data(data):
    normalized = dict(data or {})
    if "don_gia" in normalized and "gia" not in normalized:
        normalized["gia"] = normalized["don_gia"]
    if "ma_ncc" in normalized and "ma_NCC" not in normalized:
        normalized["ma_ncc"] = normalized["ma_ncc"]
    return normalized


def _event_already_logged(event_id):
    ensure_sync_log_table()
    return query_db(
        "SELECT event_id, status FROM sync_log WHERE event_id = ?",
        (event_id,),
        fetchone=True,
    )


def _record_sync_log(event, status, message):
    ensure_sync_log_table()
    execute_db(
        """
        INSERT INTO sync_log (
            event_id, event_type, ma_sp, version, source, target_branch,
            status, message, applied_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, {now})
        """.format(now=now_sql()),
        (
            event["event_id"],
            event.get("event_type"),
            (event.get("data") or {}).get("ma_sp"),
            event.get("version"),
            event.get("source"),
            event.get("target_branch"),
            status,
            message,
        ),
    )


def _product_exists(ma_sp):
    return bool(
        query_db(
            "SELECT ma_sp FROM SAN_PHAM WHERE ma_sp = ?",
            (ma_sp,),
            fetchone=True,
        )
    )


def _insert_product(data, trang_thai=None):
    required = ["ma_sp", "ten_sp", "gia", "ma_loai_sp", "ma_ncc"]
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        raise ValueError("Missing product fields for insert: " + ", ".join(missing))

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
            trang_thai if trang_thai is not None else data.get("trang_thai", 1),
        ),
    )


def _update_product(data, force_deleted=False):
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

    if force_deleted and "trang_thai" not in data:
        assignments.append("trang_thai = ?")
        params.append(0)

    assignments.append(f"cap_nhat_vao = {now_sql()}")
    params.append(data["ma_sp"])
    execute_db(
        f"UPDATE SAN_PHAM SET {', '.join(assignments)} WHERE ma_sp = ?",
        tuple(params),
    )


def _apply_product_event(event):
    event_type = event.get("event_type")
    if event_type not in SUPPORTED_PRODUCT_EVENTS:
        raise ValueError(f"Unsupported event_type: {event_type}")

    target_branch = (event.get("target_branch") or "").upper()
    if target_branch != _branch_code():
        raise ValueError(f"Event target_branch {target_branch} does not match this branch")

    data = _normalize_product_data(event.get("data"))
    if not data.get("ma_sp"):
        raise ValueError("Missing data.ma_sp")

    force_deleted = event_type == "PRODUCT_DELETED"
    exists = _product_exists(data["ma_sp"])
    if exists:
        _update_product(data, force_deleted)
    else:
        _insert_product(data, trang_thai=0 if force_deleted else None)


def apply_product_sync_event(event):
    required = ["event_id", "event_type", "target_branch", "version", "data"]
    missing = [field for field in required if event.get(field) in (None, "")]
    if missing:
        raise ValueError("Missing event fields: " + ", ".join(missing))

    existing_log = _event_already_logged(event["event_id"])
    if existing_log:
        return {
            "event_id": event["event_id"],
            "status": "ignored",
            "version": event.get("version"),
        }

    try:
        _apply_product_event(event)
    except Exception as exc:
        _record_sync_log(event, "failed", str(exc))
        raise

    _record_sync_log(event, "success", "Applied successfully")
    return {
        "event_id": event["event_id"],
        "ma_sp": event["data"].get("ma_sp"),
        "version": event.get("version"),
        "status": "applied",
    }


def apply_product_sync_batch(payload):
    events = sorted(payload.get("events") or [], key=lambda item: item.get("version", 0))
    results = []
    success_count = 0
    failed_count = 0

    for event in events:
        event.setdefault("source", payload.get("source"))
        event.setdefault("target_branch", payload.get("target_branch"))
        try:
            result = apply_product_sync_event(event)
            success_count += 1
        except Exception as exc:
            result = {
                "event_id": event.get("event_id"),
                "version": event.get("version"),
                "status": "failed",
                "message": str(exc),
            }
            failed_count += 1
        results.append(result)

    return {
        "batch_id": payload.get("batch_id"),
        "total": len(events),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results,
    }


def get_local_product_sync_version():
    ensure_sync_log_table()
    row = query_db(
        """
        SELECT event_id, version, applied_at
        FROM sync_log
        WHERE status = 'success'
        ORDER BY version DESC
        """,
        fetchone=True,
    )
    return {
        "branch_code": _branch_code(),
        "current_version": int(row["version"]) if row else 0,
        "last_event_id": row["event_id"] if row else None,
        "last_sync_at": row["applied_at"].isoformat() if row and row["applied_at"] else None,
    }


# ─── Branch → Trụ sở outbox ──────────────────────────────────────────────────

BRANCH_SYNC_STATUS_PENDING    = "pending"
BRANCH_SYNC_STATUS_SENT       = "sent"
BRANCH_SYNC_STATUS_FAILED     = "failed"
BRANCH_SYNC_STATUS_DEAD_LETTER = "dead_letter"
BRANCH_MAX_RETRY = 5


def ensure_branch_sync_events_table():
    engine = get_db_engine()
    id_col  = "SERIAL PRIMARY KEY" if engine == "postgresql" else "INT AUTO_INCREMENT PRIMARY KEY"
    ts_type = "TIMESTAMP"          if engine == "postgresql" else "DATETIME"
    on_upd  = ""                   if engine == "postgresql" else " ON UPDATE CURRENT_TIMESTAMP"
    execute_db(
        f"""
        CREATE TABLE IF NOT EXISTS branch_sync_events (
            id           {id_col},
            event_id     VARCHAR(150) NOT NULL UNIQUE,
            ma_sp        VARCHAR(50),
            event_type   VARCHAR(50),
            version      INT,
            payload      TEXT,
            status       VARCHAR(20) NOT NULL DEFAULT 'pending',
            message      TEXT,
            retry_count  INT NOT NULL DEFAULT 0,
            last_error   TEXT,
            created_at   {ts_type} DEFAULT CURRENT_TIMESTAMP{on_upd},
            dispatched_at {ts_type} NULL
        )
        """
    )


def _branch_next_version():
    ensure_branch_sync_events_table()
    row = query_db(
        "SELECT COALESCE(MAX(version), 0) + 1 AS next_v FROM branch_sync_events",
        fetchone=True,
    )
    return int(row["next_v"] if row else 1)


def _utc_now_text():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def _service_api_url():
    return os.getenv("SERVICE_API_URL", "").rstrip("/")


def _service_token_val():
    return os.getenv("SERVICE_TOKEN", "dev-service-token-change-in-production")


def _post_to_service(url, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Service-Token": _service_token_val(),
        },
        method="POST",
    )
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _update_branch_event_status(event_id, status, message=None):
    ensure_branch_sync_events_table()
    engine = get_db_engine()
    now_fn = "NOW()" if engine in ("mysql", "postgresql") else "CURRENT_TIMESTAMP"
    execute_db(
        f"UPDATE branch_sync_events SET status = ?, message = ?, dispatched_at = {now_fn} WHERE event_id = ?",
        (status, message, event_id),
    )


def _branch_event_payload(event_id, event_type, product, version):
    branch = _branch_code()
    return {
        "event_id":      event_id,
        "event_type":    event_type,
        "source":        branch,
        "source_branch": branch,
        "target_branch": "TRU_SO",
        "version":       version,
        "occurred_at":   datetime.now(timezone.utc).isoformat(),
        "data":          dict(product),
    }


def create_branch_sync_event(event_type, product):
    """Tạo outbox event gửi lên trụ sở khi chi nhánh thay đổi sản phẩm."""
    ensure_branch_sync_events_table()
    if not product or not product.get("ma_sp"):
        return None

    version  = _branch_next_version()
    event_id = f"br_evt_{_branch_code()}_{_utc_now_text()}_{product['ma_sp']}"
    payload  = _branch_event_payload(event_id, event_type, product, version)
    payload_json = json.dumps(payload, ensure_ascii=False)

    execute_db(
        """
        INSERT INTO branch_sync_events (event_id, ma_sp, event_type, version, payload, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (event_id, product["ma_sp"], event_type, version, payload_json, BRANCH_SYNC_STATUS_PENDING),
    )
    dispatch_branch_sync_event(payload)
    return payload


def dispatch_branch_sync_event(event):
    service_url = _service_api_url()
    if not service_url:
        _update_branch_event_status(
            event["event_id"], BRANCH_SYNC_STATUS_PENDING, "SERVICE_API_URL not configured"
        )
        return None

    try:
        result = _post_to_service(f"{service_url}/api/service/products/dispatch-to-hq", event)
    except (OSError, URLError, TimeoutError) as exc:
        _update_branch_event_status(event["event_id"], BRANCH_SYNC_STATUS_FAILED, str(exc))
        return None

    success = bool(result.get("success"))
    _update_branch_event_status(
        event["event_id"],
        BRANCH_SYNC_STATUS_SENT if success else BRANCH_SYNC_STATUS_FAILED,
        json.dumps(result, ensure_ascii=False),
    )
    return result


def get_branch_sync_events_for_api(args=None):
    ensure_branch_sync_events_table()
    args = args or {}
    where, params = [], []
    for field in ["status", "ma_sp", "event_type"]:
        if args.get(field):
            where.append(f"{field} = ?")
            params.append(args[field])
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    rows = query_db(
        "SELECT event_id, ma_sp, event_type, version, status, message, created_at, dispatched_at"
        f" FROM branch_sync_events{where_sql} ORDER BY version DESC LIMIT 100",
        tuple(params),
    )
    for row in rows:
        for field in ["created_at", "dispatched_at"]:
            row[field] = row[field].isoformat() if row.get(field) else None
    return {"branch_code": _branch_code(), "data": rows}


def _branch_do_retry(event_id, payload, current_retry_count):
    dispatch_branch_sync_event(payload)
    new_count = current_retry_count + 1
    status_row = query_db(
        "SELECT status FROM branch_sync_events WHERE event_id = ?", (event_id,), fetchone=True
    )
    new_status = (status_row or {}).get("status", BRANCH_SYNC_STATUS_FAILED)
    if new_status == BRANCH_SYNC_STATUS_FAILED and new_count >= BRANCH_MAX_RETRY:
        new_status = BRANCH_SYNC_STATUS_DEAD_LETTER
    execute_db(
        "UPDATE branch_sync_events SET retry_count = ?, status = ? WHERE event_id = ?",
        (new_count, new_status, event_id),
    )
    return {"event_id": event_id, "status": new_status, "retry_count": new_count}


def retry_branch_failed_events():
    ensure_branch_sync_events_table()
    rows = query_db(
        "SELECT event_id, payload, retry_count FROM branch_sync_events"
        " WHERE status = 'failed' AND retry_count < ? ORDER BY version",
        (BRANCH_MAX_RETRY,),
    )
    results = [
        _branch_do_retry(row["event_id"], json.loads(row["payload"]), int(row["retry_count"]))
        for row in rows
    ]
    return {"retried": len(results), "results": results}


def retry_branch_event_by_id(event_id):
    ensure_branch_sync_events_table()
    row = query_db(
        "SELECT event_id, payload, status, retry_count FROM branch_sync_events WHERE event_id = ?",
        (event_id,),
        fetchone=True,
    )
    if not row:
        return None
    if row["status"] == BRANCH_SYNC_STATUS_SENT:
        return {"event_id": event_id, "status": "skipped", "message": "Event already sent"}
    return _branch_do_retry(event_id, json.loads(row["payload"]), int(row["retry_count"]))


def get_product_sync_log_for_api(args=None):
    ensure_sync_log_table()
    args = args or {}
    where = []
    params = []

    for field in ["status", "ma_sp"]:
        value = args.get(field)
        if value:
            where.append(f"{field} = ?")
            params.append(value)

    for key, op in [("from_version", ">="), ("to_version", "<=")]:
        value = args.get(key)
        if value not in (None, ""):
            where.append(f"version {op} ?")
            params.append(int(value))

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    page, limit, offset = parse_pagination(args)
    total_row = query_db(
        "SELECT COUNT(*) AS total FROM sync_log" + where_sql,
        tuple(params),
        fetchone=True,
    )
    total = total_row["total"] if total_row else 0
    page_clause, page_params = pagination_clause("version DESC, id DESC", offset, limit)
    rows = query_db(
        """
        SELECT event_id, event_type, ma_sp, version, status, message,
               received_at, applied_at
        FROM sync_log
        """
        + where_sql
        + page_clause,
        tuple(params) + page_params,
    )
    for row in rows:
        for field in ["received_at", "applied_at"]:
            row[field] = row[field].isoformat() if row.get(field) else None

    return {
        "branch_code": _branch_code(),
        "items": rows,
        "pagination": build_pagination_meta(page, limit, total),
    }
