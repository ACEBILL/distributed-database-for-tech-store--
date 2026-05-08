import json
import os
from urllib.error import URLError
from urllib.request import urlopen

from flask import Flask, jsonify


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


def _get_json(url):
    with urlopen(url, timeout=5) as response:
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
