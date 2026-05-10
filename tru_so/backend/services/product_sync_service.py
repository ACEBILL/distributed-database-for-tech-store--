import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from urllib.error import URLError
from urllib.request import Request, urlopen

from flask import current_app

from db import execute_db, query_db


SYNC_EVENT_STATUS_PENDING = "pending"
SYNC_EVENT_STATUS_SENT = "sent"
SYNC_EVENT_STATUS_FAILED = "failed"
SYNC_EVENT_STATUS_DEAD_LETTER = "dead_letter"

MAX_RETRY_COUNT = 5


def ensure_product_sync_events_table():
    execute_db(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'product_sync_events')
        CREATE TABLE product_sync_events (
            event_id NVARCHAR(100) PRIMARY KEY,
            ma_sp NVARCHAR(20) NOT NULL,
            event_type NVARCHAR(50) NOT NULL,
            target_branch NVARCHAR(20) NOT NULL,
            version INT NOT NULL,
            payload NVARCHAR(MAX) NOT NULL,
            status NVARCHAR(20) DEFAULT 'pending',
            message NVARCHAR(MAX) NULL,
            created_at DATETIME DEFAULT GETDATE(),
            dispatched_at DATETIME NULL
        )
        """
    )


def _json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _utc_now_text():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def _next_version():
    ensure_product_sync_events_table()
    row = query_db(
        "SELECT COALESCE(MAX(version), 0) + 1 AS next_version FROM product_sync_events",
        fetchone=True,
    )
    return int(row["next_version"] if row else 1)


def _service_api_url():
    return os.getenv("SERVICE_API_URL", "").rstrip("/")


def _service_token():
    return current_app.config.get("SERVICE_TOKEN")


def _post_json(url, payload):
    body = json.dumps(payload, ensure_ascii=False, default=_json_default).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Service-Token": _service_token() or "",
        },
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _event_payload(event_id, event_type, product, version):
    data = dict(product)
    if "gia" in data:
        data["don_gia"] = data["gia"]

    return {
        "event_id": event_id,
        "event_type": event_type,
        "source": "TRU_SO",
        "target_branch": product.get("ma_chi_nhanh"),
        "version": version,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


def update_product_sync_event_status(event_id, status, message=None):
    ensure_product_sync_events_table()
    execute_db(
        """
        UPDATE product_sync_events
        SET status = ?, message = ?, dispatched_at = GETDATE()
        WHERE event_id = ?
        """,
        (status, message, event_id),
    )


def create_product_sync_event(event_type, product):
    ensure_product_sync_events_table()
    target_branch = product.get("ma_chi_nhanh") if product else None
    if not target_branch:
        return None

    version = _next_version()
    event_id = f"evt_{_utc_now_text()}_{product['ma_sp']}"
    payload = _event_payload(event_id, event_type, product, version)
    payload_json = json.dumps(payload, ensure_ascii=False, default=_json_default)

    execute_db(
        """
        INSERT INTO product_sync_events (
            event_id, ma_sp, event_type, target_branch, version, payload, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            product["ma_sp"],
            event_type,
            target_branch,
            version,
            payload_json,
            SYNC_EVENT_STATUS_PENDING,
        ),
    )
    dispatch_product_sync_event(payload)
    return payload


def dispatch_product_sync_event(event):
    service_url = _service_api_url()
    if not service_url:
        update_product_sync_event_status(
            event["event_id"],
            SYNC_EVENT_STATUS_PENDING,
            "SERVICE_API_URL is not configured",
        )
        return None

    try:
        result = _post_json(f"{service_url}/api/service/products/dispatch-event", event)
    except (OSError, URLError, TimeoutError) as exc:
        update_product_sync_event_status(
            event["event_id"],
            SYNC_EVENT_STATUS_FAILED,
            str(exc),
        )
        return None

    success = bool(result.get("success"))
    update_product_sync_event_status(
        event["event_id"],
        SYNC_EVENT_STATUS_SENT if success else SYNC_EVENT_STATUS_FAILED,
        json.dumps(result, ensure_ascii=False, default=_json_default),
    )
    return result


def _ensure_retry_columns():
    execute_db(
        """
        IF NOT EXISTS (
            SELECT 1 FROM sys.columns
            WHERE object_id = OBJECT_ID('dbo.product_sync_events') AND name = 'retry_count'
        )
            ALTER TABLE product_sync_events ADD retry_count INT DEFAULT 0
        """
    )
    execute_db(
        """
        IF NOT EXISTS (
            SELECT 1 FROM sys.columns
            WHERE object_id = OBJECT_ID('dbo.product_sync_events') AND name = 'last_error'
        )
            ALTER TABLE product_sync_events ADD last_error NVARCHAR(MAX) NULL
        """
    )


def get_pending_event_counts_per_branch():
    ensure_product_sync_events_table()
    rows = query_db(
        """
        SELECT target_branch, COUNT(*) AS cnt
        FROM product_sync_events
        WHERE status IN ('pending', 'failed')
        GROUP BY target_branch
        """
    )
    return {row["target_branch"]: int(row["cnt"]) for row in rows}


def _do_retry(event_id, payload, current_retry_count):
    dispatch_product_sync_event(payload)
    new_retry_count = current_retry_count + 1

    status_row = query_db(
        "SELECT status, message FROM product_sync_events WHERE event_id = ?",
        (event_id,),
        fetchone=True,
    )
    new_status = (status_row or {}).get("status", SYNC_EVENT_STATUS_FAILED)
    last_error = (status_row or {}).get("message") if new_status == SYNC_EVENT_STATUS_FAILED else None

    if new_status == SYNC_EVENT_STATUS_FAILED and new_retry_count >= MAX_RETRY_COUNT:
        new_status = SYNC_EVENT_STATUS_DEAD_LETTER

    execute_db(
        "UPDATE product_sync_events SET retry_count = ?, status = ?, last_error = ? WHERE event_id = ?",
        (new_retry_count, new_status, last_error, event_id),
    )
    return {"event_id": event_id, "status": new_status, "retry_count": new_retry_count}


def retry_failed_events():
    ensure_product_sync_events_table()
    _ensure_retry_columns()

    rows = query_db(
        """
        SELECT event_id, payload, COALESCE(retry_count, 0) AS retry_count
        FROM product_sync_events
        WHERE status = 'failed' AND COALESCE(retry_count, 0) < ?
        ORDER BY version
        """,
        (MAX_RETRY_COUNT,),
    )

    results = []
    for row in rows:
        result = _do_retry(row["event_id"], json.loads(row["payload"]), int(row["retry_count"]))
        results.append(result)

    return {"retried": len(results), "results": results}


def retry_event_by_id(event_id):
    ensure_product_sync_events_table()
    _ensure_retry_columns()

    row = query_db(
        "SELECT event_id, payload, status, COALESCE(retry_count, 0) AS retry_count "
        "FROM product_sync_events WHERE event_id = ?",
        (event_id,),
        fetchone=True,
    )
    if not row:
        return None
    if row["status"] == SYNC_EVENT_STATUS_SENT:
        return {"event_id": event_id, "status": "skipped", "message": "Event already sent"}

    return _do_retry(event_id, json.loads(row["payload"]), int(row["retry_count"]))


def get_product_sync_events_for_api(args=None):
    ensure_product_sync_events_table()
    args = args or {}
    where = []
    params = []

    for field in ["status", "target_branch", "ma_sp", "event_type"]:
        value = args.get(field)
        if value:
            where.append(f"{field} = ?")
            params.append(value)

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    rows = query_db(
        """
        SELECT event_id, ma_sp, event_type, target_branch, version, status,
               message, created_at, dispatched_at
        FROM product_sync_events
        """
        + where_sql
        + " ORDER BY version DESC",
        tuple(params),
    )
    for row in rows:
        for field in ["created_at", "dispatched_at"]:
            row[field] = row[field].isoformat() if row.get(field) else None
    return {"data": rows}
