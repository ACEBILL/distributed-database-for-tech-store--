import json
import os
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

from flask import current_app

from db import execute_db, get_db_engine, query_db


STATUS_PENDING = "pending"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"


def _branch_code():
    return (current_app.config.get("BRANCH_CODE") or os.getenv("BRANCH_CODE") or "").upper()


def _service_api_url():
    return os.getenv("SERVICE_API_URL", "").rstrip("/")


def _service_token():
    return current_app.config.get("SERVICE_TOKEN") or os.getenv(
        "SERVICE_TOKEN",
        "dev-service-token-change-in-production",
    )


def _utc_now_text():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def ensure_branch_replication_events_table():
    engine = get_db_engine()
    id_col = "SERIAL PRIMARY KEY" if engine == "postgresql" else "INT AUTO_INCREMENT PRIMARY KEY"
    ts_type = "TIMESTAMP" if engine == "postgresql" else "DATETIME"
    execute_db(
        f"""
        CREATE TABLE IF NOT EXISTS branch_replication_events (
            id {id_col},
            event_id VARCHAR(150) NOT NULL UNIQUE,
            entity_type VARCHAR(40) NOT NULL,
            object_id VARCHAR(80) NOT NULL,
            event_type VARCHAR(60) NOT NULL,
            version INT NOT NULL,
            payload TEXT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            message TEXT,
            retry_count INT NOT NULL DEFAULT 0,
            created_at {ts_type} DEFAULT CURRENT_TIMESTAMP,
            dispatched_at {ts_type} NULL
        )
        """
    )


def _next_version():
    ensure_branch_replication_events_table()
    row = query_db(
        "SELECT COALESCE(MAX(version), 0) + 1 AS next_v FROM branch_replication_events",
        fetchone=True,
    )
    return int(row["next_v"] if row else 1)


def _post_json(url, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Service-Token": _service_token(),
        },
        method="POST",
    )
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _update_event_status(event_id, status, message=None):
    ensure_branch_replication_events_table()
    engine = get_db_engine()
    now_fn = "NOW()" if engine in {"mysql", "postgresql"} else "CURRENT_TIMESTAMP"
    execute_db(
        f"""
        UPDATE branch_replication_events
        SET status = ?, message = ?, dispatched_at = {now_fn}
        WHERE event_id = ?
        """,
        (status, message, event_id),
    )


def dispatch_replication_event(event):
    service_url = _service_api_url()
    if not service_url:
        _update_event_status(event["event_id"], STATUS_PENDING, "SERVICE_API_URL not configured")
        return None

    try:
        result = _post_json(
            f"{service_url}/api/service/branch-replication/dispatch-to-hq",
            event,
        )
    except (OSError, URLError, TimeoutError) as exc:
        _update_event_status(event["event_id"], STATUS_FAILED, str(exc))
        return None

    _update_event_status(
        event["event_id"],
        STATUS_SENT if result.get("success") else STATUS_FAILED,
        json.dumps(result, ensure_ascii=False),
    )
    return result


def create_replication_event(entity_type, event_type, object_id, data):
    ensure_branch_replication_events_table()
    branch = _branch_code()
    version = _next_version()
    event_id = f"rep_{branch}_{entity_type}_{_utc_now_text()}_{object_id}"
    event = {
        "event_id": event_id,
        "entity_type": entity_type,
        "event_type": event_type,
        "object_id": object_id,
        "source": branch,
        "source_branch": branch,
        "target": "TRU_SO",
        "version": version,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "data": dict(data or {}),
    }
    event["data"]["ma_chi_nhanh"] = event["data"].get("ma_chi_nhanh") or branch

    execute_db(
        """
        INSERT INTO branch_replication_events (
            event_id, entity_type, object_id, event_type, version, payload, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            entity_type,
            object_id,
            event_type,
            version,
            json.dumps(event, ensure_ascii=False),
            STATUS_PENDING,
        ),
    )
    dispatch_replication_event(event)
    return event


def safe_create_replication_event(entity_type, event_type, object_id, data):
    try:
        return create_replication_event(entity_type, event_type, object_id, data)
    except Exception:
        return None
