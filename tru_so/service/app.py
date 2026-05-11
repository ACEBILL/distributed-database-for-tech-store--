import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request


app = Flask(__name__)


def _system_name():
    return os.getenv("SYSTEM_NAME", "tru_so")


def _backend_api_url():
    return os.getenv("BACKEND_API_URL", "http://tru-so-backend:5000").rstrip("/")


def _peer_services():
    peers = {}
    raw_value = os.getenv("PEER_SERVICE_URLS", "")
    for item in raw_value.split(","):
        if not item.strip() or "=" not in item:
            continue
        name, url = item.split("=", 1)
        peers[name.strip()] = url.strip().rstrip("/")
    return peers


def _branch_service_map():
    mapping = {}
    raw_value = os.getenv("BRANCH_SERVICE_MAP", "CN01=mysql,CN02=postgre")
    for item in raw_value.split(","):
        if not item.strip() or "=" not in item:
            continue
        branch_code, peer_name = item.split("=", 1)
        mapping[branch_code.strip().upper()] = peer_name.strip()
    return mapping


def _service_token():
    return os.getenv("SERVICE_TOKEN", "dev-service-token-change-in-production")


def _service_authorized():
    return request.headers.get("X-Service-Token") == _service_token()


def _get_json(url):
    with urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json_with_token(url):
    req = Request(url, headers={"X-Service-Token": _service_token()}, method="GET")
    with urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


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


@app.post("/api/service/products/dispatch-event")
def dispatch_product_event():
    if not _service_authorized():
        return jsonify({"success": False, "message": "Invalid service token"}), 403

    event = request.get_json(silent=True) or {}
    target_branch = (event.get("target_branch") or "").upper()
    peer_name = _branch_service_map().get(target_branch)
    peer_url = _peer_services().get(peer_name)
    if not peer_url:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"No peer service configured for branch {target_branch}",
                }
            ),
            400,
        )

    try:
        local_version = _get_json_with_token(
            f"{peer_url}/api/service/products/local-version"
        )
        applied = _post_json(f"{peer_url}/api/service/products/apply-change", event)
    except (OSError, URLError, TimeoutError) as exc:
        return jsonify({"success": False, "message": str(exc)}), 502

    return jsonify(
        {
            "success": bool(applied.get("success")),
            "message": "Product sync event dispatched",
            "data": {
                "target_branch": target_branch,
                "peer": peer_name,
                "local_version": local_version.get("data"),
                "apply_result": applied,
            },
        }
    )


@app.post("/api/service/products/receive-from-branch")
def receive_product_from_branch():
    """Nhận event từ chi nhánh, áp dụng vào trụ sở (MSSQL)."""
    if not _service_authorized():
        return jsonify({"success": False, "message": "Invalid service token"}), 403

    event = request.get_json(silent=True) or {}
    try:
        result = _post_json(
            f"{_backend_api_url()}/api/internal/products/apply-change",
            event,
        )
    except (OSError, URLError, TimeoutError) as exc:
        return jsonify({"success": False, "message": str(exc)}), 502

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
