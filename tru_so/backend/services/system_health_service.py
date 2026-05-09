import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from db import get_branch_db_engine, query_db
from services.branch_service import get_branches
from services.product_sync_service import get_product_sync_event_summary_by_branch


DEFAULT_BRANCH_BACKEND_URLS = {
    "CN01": "http://mysql-backend:5000",
    "CN02": "http://postgre-backend:5000",
}

DEFAULT_BRANCH_SERVICE_URLS = {
    "CN01": "http://mysql-service:5000",
    "CN02": "http://postgre-service:5000",
}


def _service_token():
    return os.getenv("SERVICE_TOKEN", "dev-service-token-change-in-production")


def _branch_backend_url(branch_code):
    return os.getenv(
        f"BRANCH_{branch_code}_API_URL", DEFAULT_BRANCH_BACKEND_URLS.get(branch_code, "")
    ).rstrip("/")


def _branch_service_url(branch_code):
    return os.getenv(
        f"BRANCH_{branch_code}_SERVICE_URL",
        DEFAULT_BRANCH_SERVICE_URLS.get(branch_code, ""),
    ).rstrip("/")


def _request_json(url, service_token=False):
    headers = {}
    if service_token:
        headers["X-Service-Token"] = _service_token()
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _safe_get(url, service_token=False):
    if not url:
        return {"status": "not_configured", "error": "URL is not configured"}
    try:
        return _request_json(url, service_token=service_token)
    except HTTPError as exc:
        return {"status": "error", "http_status": exc.code, "error": str(exc)}
    except (OSError, URLError, TimeoutError) as exc:
        return {"status": "down", "error": str(exc)}


def _status_from_payload(payload):
    if payload.get("status") in {"ok", "configured"}:
        return "ok"
    if payload.get("success") is True:
        return "ok"
    if payload.get("status") in {"down", "unreachable", "not_configured", "error"}:
        return payload["status"]
    if payload.get("error"):
        return "error"
    return payload.get("status", "unknown")


def _hq_db_status():
    try:
        query_db("SELECT 1 AS ok", fetchone=True)
        return "ok", None
    except Exception as exc:
        return "down", str(exc)


def _branch_last_sync_version(backend_url):
    payload = _safe_get(
        f"{backend_url}/api/internal/products/local-version", service_token=True
    )
    data = payload.get("data") or {}
    status = _status_from_payload(payload)
    return {
        "status": status,
        "last_sync_version": int(data.get("current_version") or 0),
        "last_event_id": data.get("last_event_id"),
        "last_sync_at": data.get("last_sync_at"),
        "error": None if status == "ok" else payload.get("error") or payload.get("message"),
    }


def get_system_health_for_api():
    hq_db_status, hq_db_error = _hq_db_status()
    event_summary = get_product_sync_event_summary_by_branch()

    nodes = {
        "tru_so": {
            "backend": "ok",
            "service": _status_from_payload(
                _safe_get(
                    os.getenv("SERVICE_API_URL", "http://tru-so-service:5000").rstrip("/")
                    + "/api/service/ping"
                )
            ),
            "db": hq_db_status,
            "db_engine": os.getenv("DB_ENGINE", "sqlserver"),
            "error": hq_db_error,
        }
    }

    for branch in get_branches():
        branch_code = branch["ma_chi_nhanh"].upper()
        backend_url = _branch_backend_url(branch_code)
        service_url = _branch_service_url(branch_code)

        backend_payload = _safe_get(f"{backend_url}/api/ping")
        service_payload = _safe_get(f"{service_url}/api/service/ping")
        db_payload = _safe_get(f"{backend_url}/api/internal/health", service_token=True)
        sync_payload = _branch_last_sync_version(backend_url)
        sync_summary = event_summary.get(branch_code, {})

        nodes[branch_code] = {
            "backend": _status_from_payload(backend_payload),
            "service": _status_from_payload(service_payload),
            "db": _status_from_payload(db_payload),
            "db_engine": get_branch_db_engine(branch_code),
            "pending_events": sync_summary.get("pending_events", 0),
            "failed_events": sync_summary.get("failed_events", 0),
            "dead_letter_events": sync_summary.get("dead_letter_events", 0),
            "sent_events": sync_summary.get("sent_events", 0),
            "last_sync_version": sync_payload["last_sync_version"],
            "last_event_id": sync_payload["last_event_id"],
            "last_sync_at": sync_payload["last_sync_at"],
            "errors": {
                "backend": backend_payload.get("error"),
                "service": service_payload.get("error"),
                "db": db_payload.get("error"),
                "sync_version": sync_payload.get("error"),
            },
        }

    unhealthy = []
    for node_name, node in nodes.items():
        for key in ["backend", "service", "db"]:
            if node.get(key) not in {"ok", "configured"}:
                unhealthy.append(f"{node_name}.{key}")
        if node.get("failed_events", 0) > 0:
            unhealthy.append(f"{node_name}.failed_events")
        if node.get("dead_letter_events", 0) > 0:
            unhealthy.append(f"{node_name}.dead_letter_events")

    return {
        "overall": "ok" if not unhealthy else "degraded",
        "unhealthy": unhealthy,
        "nodes": nodes,
    }
