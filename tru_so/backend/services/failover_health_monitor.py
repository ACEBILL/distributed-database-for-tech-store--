"""Background poller: health-check branch backends va tu dong replay khi song lai.

Chay 1 daemon thread duy nhat trong tru-so-backend. Moi `POLL_INTERVAL_SEC` giay:
  1. Goi GET <branch_api_url>/api/ping cho moi chi nhanh.
  2. Neu trang thai chuyen tu DOWN -> UP, goi replay_pending_events_for_branch
     trong app context de day cac event failover ve DB chi nhanh that.

Bien moi truong:
  - BRANCH_<MA>_API_URL: URL backend chi nhanh (vd http://mysql-backend:5000).
  - FAILOVER_POLL_INTERVAL_SEC: chu ky poll (default 30s).
  - FAILOVER_AUTO_REPLAY: '1' de bat (default), '0' de tat.
"""

import json
import logging
import os
import threading
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


log = logging.getLogger(__name__)

POLL_INTERVAL_DEFAULT = 30
PING_TIMEOUT_SEC = 5
_thread_started = False
_thread_lock = threading.Lock()


def _branch_api_url(branch_code):
    normalized = branch_code.upper().replace("-", "_")
    return os.getenv(f"BRANCH_{normalized}_API_URL")


def _ping_branch(branch_code):
    url = _branch_api_url(branch_code)
    if not url:
        return False, "no_url"
    try:
        req = Request(f"{url.rstrip('/')}/api/ping", method="GET")
        with urlopen(req, timeout=PING_TIMEOUT_SEC) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body)
            return payload.get("status") == "ok", "ok"
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        return False, str(exc)


def _branch_codes_from_db(app):
    from db import query_db
    with app.app_context():
        rows = query_db("SELECT ma_chi_nhanh FROM chi_nhanh")
        return [row["ma_chi_nhanh"].upper() for row in rows]


def _do_replay(app, branch_code):
    from services.failover_replay_service import replay_pending_events_for_branch
    with app.app_context():
        summary = replay_pending_events_for_branch(branch_code)
        log.info(
            "[failover-replay] branch=%s replayed=%d failed=%d total=%d",
            branch_code,
            summary["replayed"],
            summary["failed"],
            summary["total"],
        )
        return summary


def _monitor_loop(app, interval_sec):
    state = {}
    log.info("[failover-monitor] started, interval=%ss", interval_sec)
    while True:
        try:
            branches = _branch_codes_from_db(app)
            for branch in branches:
                is_up, _reason = _ping_branch(branch)
                was_up = state.get(branch)
                state[branch] = is_up
                if is_up and was_up is False:
                    log.info("[failover-monitor] %s back online -> replay", branch)
                    try:
                        _do_replay(app, branch)
                    except Exception as exc:
                        log.exception("[failover-monitor] replay %s failed: %s", branch, exc)
        except Exception as exc:
            log.exception("[failover-monitor] loop error: %s", exc)
        time.sleep(interval_sec)


def start_failover_monitor(app):
    """Goi 1 lan khi app khoi dong. An toan voi multiple workers (only first starts)."""
    global _thread_started
    if os.getenv("FAILOVER_AUTO_REPLAY", "1") != "1":
        log.info("[failover-monitor] disabled via FAILOVER_AUTO_REPLAY=0")
        return
    with _thread_lock:
        if _thread_started:
            return
        _thread_started = True
        try:
            interval = int(os.getenv("FAILOVER_POLL_INTERVAL_SEC", POLL_INTERVAL_DEFAULT))
        except ValueError:
            interval = POLL_INTERVAL_DEFAULT
        thread = threading.Thread(
            target=_monitor_loop,
            args=(app, interval),
            name="failover-monitor",
            daemon=True,
        )
        thread.start()
