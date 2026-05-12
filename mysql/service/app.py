import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request


app = Flask(__name__)


def _system_name():
    return os.getenv("SYSTEM_NAME", "mysql")


def _backend_api_url():
    return os.getenv("BACKEND_API_URL", "http://mysql-backend:5000").rstrip("/")


def _peer_services():
    peers = {}
    raw_value = os.getenv("PEER_SERVICE_URLS", "")
    for item in raw_value.split(","):
        if not item.strip() or "=" not in item:
            continue
        name, url = item.split("=", 1)
        peers[name.strip()] = url.strip().rstrip("/")
    return peers


def _service_token():
    return os.getenv("SERVICE_TOKEN", "dev-service-token-change-in-production")


def _service_authorized():
    return request.headers.get("X-Service-Token") == _service_token()


def _get_json(url):
    with urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _backend_get(path):
    url = f"{_backend_api_url()}{path}"
    req = Request(url, headers={"X-Service-Token": _service_token()}, method="GET")
    with urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _backend_post(path, payload):
    url = f"{_backend_api_url()}{path}"
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


@app.get("/api/service/ping")
def ping():
    return jsonify({"service": _system_name(), "status": "ok"})


@app.get("/api/service/registry")
def registry():
    return jsonify(
        {
            "service": _system_name(),
            "backend_api_url": _backend_api_url(),
            "peers": _peer_services(),
        }
    )


@app.get("/api/service/backend-health")
def backend_health():
    try:
        return jsonify(_get_json(f"{_backend_api_url()}/api/ping"))
    except (OSError, URLError, TimeoutError) as exc:
        return jsonify({"status": "unreachable", "error": str(exc)}), 502


@app.get("/api/service/peers/health")
def peer_health():
    result = {}
    for name, url in _peer_services().items():
        try:
            result[name] = _get_json(f"{url}/api/service/ping")
        except (OSError, URLError, TimeoutError) as exc:
            result[name] = {"status": "unreachable", "error": str(exc)}
    return jsonify(result)


@app.post("/api/service/products/apply-change")
def apply_product_change():
    if not _service_authorized():
        return jsonify({"success": False, "message": "Invalid service token"}), 403
    try:
        return jsonify(
            _backend_post(
                "/api/internal/products/apply-change",
                request.get_json(silent=True) or {},
            )
        )
    except (OSError, URLError, TimeoutError) as exc:
        return jsonify({"success": False, "message": str(exc)}), 502


@app.post("/api/service/products/apply-batch")
def apply_product_batch():
    if not _service_authorized():
        return jsonify({"success": False, "message": "Invalid service token"}), 403
    try:
        return jsonify(
            _backend_post(
                "/api/internal/products/apply-batch",
                request.get_json(silent=True) or {},
            )
        )
    except (OSError, URLError, TimeoutError) as exc:
        return jsonify({"success": False, "message": str(exc)}), 502


@app.get("/api/service/products/local-version")
def product_local_version():
    if not _service_authorized():
        return jsonify({"success": False, "message": "Invalid service token"}), 403
    try:
        return jsonify(_backend_get("/api/internal/products/local-version"))
    except (OSError, URLError, TimeoutError) as exc:
        return jsonify({"success": False, "message": str(exc)}), 502


@app.get("/api/service/products/sync-log")
def product_sync_log():
    if not _service_authorized():
        return jsonify({"success": False, "message": "Invalid service token"}), 403
    query_string = request.query_string.decode("utf-8")
    path = "/api/internal/products/sync-log"
    if query_string:
        path += f"?{query_string}"
    try:
        return jsonify(_backend_get(path))
    except (OSError, URLError, TimeoutError) as exc:
        return jsonify({"success": False, "message": str(exc)}), 502


@app.post("/api/service/products/dispatch-to-hq")
def dispatch_product_to_hq():
    """Nhận event từ chi nhánh và forward lên tru-so-service."""
    if not _service_authorized():
        return jsonify({"success": False, "message": "Invalid service token"}), 403

    event = request.get_json(silent=True) or {}
    hq_url = _peer_services().get("tru_so")
    if not hq_url:
        return jsonify({"success": False, "message": "tru_so peer not configured"}), 400

    try:
        body = json.dumps(event, ensure_ascii=False).encode("utf-8")
        req = Request(
            f"{hq_url}/api/service/products/receive-from-branch",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Service-Token": _service_token(),
            },
            method="POST",
        )
        from urllib.request import urlopen as _urlopen
        with _urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError) as exc:
        return jsonify({"success": False, "message": str(exc)}), 502

    return jsonify(result)


@app.post("/api/service/branch-replication/dispatch-to-hq")
def dispatch_branch_replication_to_hq():
    """Nhận event vận hành từ chi nhánh và forward lên tru-so-service."""
    if not _service_authorized():
        return jsonify({"success": False, "message": "Invalid service token"}), 403

    event = request.get_json(silent=True) or {}
    hq_url = _peer_services().get("tru_so")
    if not hq_url:
        return jsonify({"success": False, "message": "tru_so peer not configured"}), 400

    try:
        body = json.dumps(event, ensure_ascii=False).encode("utf-8")
        req = Request(
            f"{hq_url}/api/service/branch-replication/receive-from-branch",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Service-Token": _service_token(),
            },
            method="POST",
        )
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError) as exc:
        return jsonify({"success": False, "message": str(exc)}), 502

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
