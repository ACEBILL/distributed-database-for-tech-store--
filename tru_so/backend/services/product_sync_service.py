import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.error import URLError
from urllib.request import Request, urlopen

from flask import current_app

from db import execute_db, query_db


SYNC_EVENT_STATUS_PENDING = "pending"
SYNC_EVENT_STATUS_SENT = "sent"
SYNC_EVENT_STATUS_FAILED = "failed"
SYNC_EVENT_STATUS_DEAD_LETTER = "dead_letter"

MAX_RETRY_COUNT = int(os.getenv("PRODUCT_SYNC_MAX_RETRY_COUNT", "5"))
BASE_RETRY_DELAY_SECONDS = int(os.getenv("PRODUCT_SYNC_BASE_RETRY_DELAY_SECONDS", "5"))
MAX_RETRY_DELAY_SECONDS = int(os.getenv("PRODUCT_SYNC_MAX_RETRY_DELAY_SECONDS", "300"))


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
    execute_db(
        """
        IF COL_LENGTH('product_sync_events', 'retry_count') IS NULL
        ALTER TABLE product_sync_events
        ADD retry_count INT NOT NULL
            CONSTRAINT DF_product_sync_events_retry_count DEFAULT 0
        """
    )
    execute_db(
        """
        IF COL_LENGTH('product_sync_events', 'last_error') IS NULL
        ALTER TABLE product_sync_events ADD last_error NVARCHAR(MAX) NULL
        """
    )
    execute_db(
        """
        IF COL_LENGTH('product_sync_events', 'next_retry_at') IS NULL
        ALTER TABLE product_sync_events ADD next_retry_at DATETIME NULL
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


def _retry_delay(retry_count):
    exponent = max(0, min(retry_count - 1, 8))
    seconds = min(MAX_RETRY_DELAY_SECONDS, BASE_RETRY_DELAY_SECONDS * (2**exponent))
    return timedelta(seconds=seconds)


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
    if status == SYNC_EVENT_STATUS_FAILED:
        row = query_db(
            "SELECT retry_count FROM product_sync_events WHERE event_id = ?",
            (event_id,),
            fetchone=True,
        )
        retry_count = int(row["retry_count"] if row else 0) + 1
        final_status = (
            SYNC_EVENT_STATUS_DEAD_LETTER
            if retry_count >= MAX_RETRY_COUNT
            else SYNC_EVENT_STATUS_FAILED
        )
        next_retry_at = None
        if final_status == SYNC_EVENT_STATUS_FAILED:
            next_retry_at = datetime.now(timezone.utc).replace(tzinfo=None) + _retry_delay(
                retry_count
            )

        execute_db(
            """
            UPDATE product_sync_events
            SET status = ?, message = ?, last_error = ?, retry_count = ?,
                next_retry_at = ?, dispatched_at = GETDATE()
            WHERE event_id = ?
            """,
            (final_status, message, message, retry_count, next_retry_at, event_id),
        )
        return

    if status == SYNC_EVENT_STATUS_SENT:
        execute_db(
            """
            UPDATE product_sync_events
            SET status = ?, message = ?, last_error = NULL,
                next_retry_at = NULL, dispatched_at = GETDATE()
            WHERE event_id = ?
            """,
            (status, message, event_id),
        )
        return

    execute_db(
        """
        UPDATE product_sync_events
        SET status = ?, message = ?, next_retry_at = NULL
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


def get_product_sync_event(event_id):
    ensure_product_sync_events_table()
    return query_db(
        """
        SELECT event_id, ma_sp, event_type, target_branch, version, payload, status,
               message, retry_count, last_error, created_at, dispatched_at,
               next_retry_at
        FROM product_sync_events
        WHERE event_id = ?
        """,
        (event_id,),
        fetchone=True,
    )


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


def retry_product_sync_event(event_id, force=False):
    row = get_product_sync_event(event_id)
    if not row:
        return None

    if not force and row["status"] == SYNC_EVENT_STATUS_SENT:
        raise ValueError("Event has already been sent")

    event = json.loads(row["payload"])
    update_product_sync_event_status(
        event_id,
        SYNC_EVENT_STATUS_PENDING,
        "Retry requested",
    )
    result = dispatch_product_sync_event(event)
    updated = get_product_sync_event(event_id)
    return {
        "event": _format_sync_event_row(updated),
        "dispatch_result": result,
    }


def retry_failed_product_sync_events(limit=20, due_only=False, include_dead_letter=False):
    ensure_product_sync_events_table()
    statuses = [SYNC_EVENT_STATUS_PENDING, SYNC_EVENT_STATUS_FAILED]
    if include_dead_letter:
        statuses.append(SYNC_EVENT_STATUS_DEAD_LETTER)

    placeholders = ", ".join("?" for _ in statuses)
    rows = query_db(
        f"""
        SELECT event_id, status, next_retry_at, version
        FROM product_sync_events
        WHERE status IN ({placeholders})
        ORDER BY
            CASE WHEN next_retry_at IS NULL THEN 0 ELSE 1 END,
            next_retry_at,
            version
        """,
        tuple(statuses),
    )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    selected = []
    for row in rows:
        if due_only and row.get("next_retry_at") and row["next_retry_at"] > now:
            continue
        selected.append(row)
        if len(selected) >= limit:
            break

    results = []
    success_count = 0
    failed_count = 0
    for row in selected:
        retry_result = retry_product_sync_event(
            row["event_id"],
            force=row["status"] == SYNC_EVENT_STATUS_DEAD_LETTER,
        )
        event_status = retry_result["event"]["status"]
        if event_status == SYNC_EVENT_STATUS_SENT:
            success_count += 1
        else:
            failed_count += 1
        results.append(retry_result)

    return {
        "total": len(selected),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results,
    }


def get_product_sync_event_summary_by_branch():
    ensure_product_sync_events_table()
    rows = query_db(
        """
        SELECT target_branch, status, COUNT(*) AS total
        FROM product_sync_events
        GROUP BY target_branch, status
        """
    )
    summary = {}
    for row in rows:
        branch = row["target_branch"]
        status = row["status"]
        summary.setdefault(
            branch,
            {
                "pending_events": 0,
                "failed_events": 0,
                "dead_letter_events": 0,
                "sent_events": 0,
            },
        )
        key = {
            SYNC_EVENT_STATUS_PENDING: "pending_events",
            SYNC_EVENT_STATUS_FAILED: "failed_events",
            SYNC_EVENT_STATUS_DEAD_LETTER: "dead_letter_events",
            SYNC_EVENT_STATUS_SENT: "sent_events",
        }.get(status)
        if key:
            summary[branch][key] = int(row["total"])
    return summary


def _format_sync_event_row(row):
    if not row:
        return None
    formatted = dict(row)
    for field in ["created_at", "dispatched_at", "next_retry_at"]:
        formatted[field] = (
            formatted[field].isoformat() if formatted.get(field) else None
        )
    return formatted


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
               message, retry_count, last_error, next_retry_at,
               created_at, dispatched_at
        FROM product_sync_events
        """
        + where_sql
        + " ORDER BY version DESC",
        tuple(params),
    )
    rows = [_format_sync_event_row(row) for row in rows]
    return {"data": rows}
