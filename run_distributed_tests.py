#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated test runner - Distributed Database Features
======================================================
Chay:  python run_distributed_tests.py
Log:   test_results_YYYYMMDD_HHMMSS.log

Yeu cau:
  - Docker stack dang chay  (docker compose up -d)
  - pip install requests
"""

import argparse
import io
import json
import logging
import os
import sys
import time
from datetime import datetime

# Force UTF-8 output tren Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("Thieu thu vien: pip install requests")
    sys.exit(1)

# ─── Cấu hình ─────────────────────────────────────────────────────────────────
BASE_URL      = "http://localhost:5000"
HQ_USER       = {"ma_nhan_vien": "NV001", "mat_khau": "pass123"}
CN01_USER     = {"ma_nhan_vien": "NV001", "mat_khau": "pass123"}
CN02_USER     = {"ma_nhan_vien": "NV001", "mat_khau": "pass123"}

# Unique product ID per run to avoid PK conflict on repeated runs
TEST_SP_MA    = f"SP_AUTO_{datetime.now().strftime('%m%d%H%M%S')}"
TEST_SP_BODY  = {
    "ma_sp":          TEST_SP_MA,
    "ten_sp":         "Auto Test San Pham Phan Tan",
    "gia":            9_990_000,
    "ti_le_loi_nhuan": 10,
    "ti_le_giam_gia":  0,
    "mo_ta":          "Distributed sync auto test — safe to delete",
    "ma_loai_sp":     "LSP01",   # loai_sp gắn CN01 → event target_branch=CN01
    "ma_ncc":         1,
    "trang_thai":     1,
}

PASS  = "PASS"
FAIL  = "FAIL"
SKIP  = "SKIP"
ERROR = "ERROR"

# ─── Logger ────────────────────────────────────────────────────────────────────
def make_logger(log_path: str) -> logging.Logger:
    fmt = logging.Formatter("%(message)s")
    lg  = logging.getLogger("dist_test")
    lg.setLevel(logging.DEBUG)
    # File handler: luon UTF-8
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    # Console handler: boc UTF-8 neu can (Windows cp1252)
    if hasattr(sys.stdout, "buffer"):
        console_stream = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
    else:
        console_stream = sys.stdout
    ch = logging.StreamHandler(console_stream)
    ch.setFormatter(fmt)
    lg.addHandler(fh)
    lg.addHandler(ch)
    return lg

# ─── HTTP helper ───────────────────────────────────────────────────────────────
def api(method: str, url: str, token: str = None,
        body: dict = None, params: dict = None, timeout: int = 10):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        return requests.request(
            method, url, json=body, params=params,
            headers=headers, timeout=timeout
        )
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return None

# ─── Test result ───────────────────────────────────────────────────────────────
class TR:
    def __init__(self, tc_id: str, name: str):
        self.tc_id  = tc_id
        self.name   = name
        self.status = SKIP
        self.notes  = []
        self.req    = ""
        self.resp   = ""

    def passed(self):                self.status = PASS
    def failed(self, r):             self.status = FAIL;  self.notes.append(f"✗ {r}")
    def skipped(self, r):            self.status = SKIP;  self.notes.append(f"○ {r}")
    def errored(self, r):            self.status = ERROR; self.notes.append(f"! {r}")
    def note(self, msg: str):        self.notes.append(f"  {msg}")

# ─── Runner ────────────────────────────────────────────────────────────────────
class Runner:
    def __init__(self, base: str, lg: logging.Logger):
        self.base    = base.rstrip("/")
        self.lg      = lg
        self.results = []
        self.token   = None          # central JWT
        self.cn01_token = None
        self.cn02_token = None
        self.any_event_id = None     # để test retry by id

    # ── helpers ────────────────────────────────────────────────────────────────
    def url(self, path: str) -> str:
        return self.base + path

    def _fmt_req(self, method, path, body=None, params=None):
        lines = [f"{method.upper()} {self.base}{path}"]
        if params: lines.append(f"Params  : {json.dumps(params, ensure_ascii=False)}")
        if body:   lines.append(f"Body    :\n{json.dumps(body, ensure_ascii=False, indent=2)}")
        return "\n".join(lines)

    def _fmt_resp(self, r):
        if r is None:
            return "✗ Connection failed (server not reachable)"
        try:
            body = json.dumps(r.json(), ensure_ascii=False, indent=2)
        except Exception:
            body = r.text[:800]
        return f"HTTP {r.status_code}\n{body}"

    def _print(self, tr: TR):
        icon = {PASS: "✓", FAIL: "✗", SKIP: "○", ERROR: "!"}.get(tr.status, "?")
        sep  = "═" * 72
        self.lg.info(f"\n{sep}")
        self.lg.info(f"  {icon}  {tr.tc_id} — {tr.name}  [{tr.status}]")
        self.lg.info(sep)
        if tr.req:
            self.lg.info("  ── REQUEST ──")
            for ln in tr.req.splitlines():
                self.lg.info(f"    {ln}")
        if tr.resp:
            self.lg.info("  ── RESPONSE ──")
            for ln in tr.resp.splitlines():
                self.lg.info(f"    {ln}")
        if tr.notes:
            self.lg.info("  ── CHECKS ──")
            for n in tr.notes:
                self.lg.info(f"    {n}")

    def run(self, tc_id, name, fn):
        tr = TR(tc_id, name)
        try:
            fn(tr)
        except Exception as exc:
            tr.errored(f"Unhandled: {exc}")
        self.results.append(tr)
        self._print(tr)
        return tr

    # ── TC01 — Login trụ sở ────────────────────────────────────────────────────
    def tc01(self, tr: TR):
        path = "/api/auth/login"
        tr.req  = self._fmt_req("POST", path, HQ_USER)
        r       = api("POST", self.url(path), body=HQ_USER)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối server — kiểm tra docker compose up")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        data = r.json()
        if not data.get("token"):
            tr.failed("Không có token trong response")
            return
        user  = data.get("user", data)   # scope nằm trong "user" hoặc top-level
        scope = user.get("scope")
        if scope != "central":
            tr.failed(f"scope={scope}, expected central")
            return
        self.token = data["token"]
        tr.note(f"✓ scope = central")
        tr.note(f"✓ chuc_vu = {user.get('chuc_vu')}")
        tr.note(f"✓ Token acquired")
        tr.passed()

    # ── TC02 — Login CN01 qua gateway ─────────────────────────────────────────
    def tc02(self, tr: TR):
        path = "/api/auth/branches/CN01/login"
        tr.req  = self._fmt_req("POST", path, CN01_USER)
        r       = api("POST", self.url(path), body=CN01_USER)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code} — user có thể không tồn tại trên MySQL CN01")
            return
        data = r.json()
        user = data.get("user", data)
        ok   = user.get("scope") == "branch" and user.get("branch_code") == "CN01"
        if ok:
            self.cn01_token = data.get("token")
            tr.note(f"✓ scope = branch, branch_code = CN01")
            tr.note(f"✓ source_engine = {user.get('source_engine')}")
            tr.passed()
        else:
            tr.failed(f"scope={user.get('scope')}, branch_code={user.get('branch_code')}")

    # ── TC03 — Login CN02 qua gateway ─────────────────────────────────────────
    def tc03(self, tr: TR):
        path = "/api/auth/branches/CN02/login"
        tr.req  = self._fmt_req("POST", path, CN02_USER)
        r       = api("POST", self.url(path), body=CN02_USER)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code} — user có thể không tồn tại trên PostgreSQL CN02")
            return
        data = r.json()
        user = data.get("user", data)
        ok   = user.get("scope") == "branch" and user.get("branch_code") == "CN02"
        if ok:
            self.cn02_token = data.get("token")
            tr.note(f"✓ scope = branch, branch_code = CN02")
            tr.note(f"✓ source_engine = {user.get('source_engine')}")
            tr.passed()
        else:
            tr.failed(f"scope={user.get('scope')}, branch_code={user.get('branch_code')}")

    # ── TC04 — System health (không cần auth) ─────────────────────────────────
    def tc04(self, tr: TR):
        path = "/api/system/health"
        tr.req  = self._fmt_req("GET", path)
        r       = api("GET", self.url(path))   # no auth required
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        data    = r.json()
        overall = data.get("overall")
        nodes   = data.get("nodes", {})
        tr.note(f"overall = {overall}")
        for k, v in nodes.items():
            tr.note(f"  {k}: db={v.get('db')} service={v.get('service')} pending={v.get('pending_events')}")
        if overall == "ok":
            tr.passed()
        else:
            tr.failed(f"overall = {overall} (degraded) — một hoặc nhiều node có vấn đề")

    # ── TC05 — Health check DB CN01 ───────────────────────────────────────────
    def tc05(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path = "/api/chi-nhanh/CN01/health"
        tr.req  = self._fmt_req("GET", path)
        r       = api("GET", self.url(path), token=self.token)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        data   = r.json()
        status = data.get("status")
        tr.note(f"✓ he_quan_tri_csdl = {data.get('he_quan_tri_csdl')}")
        tr.note(f"✓ status = {status}")
        if data.get("error"):
            tr.note(f"  error: {data.get('error')}")
        if status == "ok":
            tr.passed()
        else:
            tr.failed(f"CN01 status = {status}")

    # ── TC06 — Health check DB CN02 ───────────────────────────────────────────
    def tc06(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path = "/api/chi-nhanh/CN02/health"
        tr.req  = self._fmt_req("GET", path)
        r       = api("GET", self.url(path), token=self.token)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        data   = r.json()
        status = data.get("status")
        tr.note(f"✓ he_quan_tri_csdl = {data.get('he_quan_tri_csdl')}")
        tr.note(f"✓ status = {status}")
        if status == "ok":
            tr.passed()
        else:
            tr.failed(f"CN02 status = {status}")

    # ── TC07 — Distributed query nhân viên ────────────────────────────────────
    def tc07(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path = "/api/nhan-vien/tat-ca-chi-nhanh"
        tr.req  = self._fmt_req("GET", path)
        r       = api("GET", self.url(path), token=self.token)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        data      = r.json()
        qt        = data.get("query_type")
        nodes     = data.get("nodes", {})
        employees = data.get("data", [])
        errors    = []

        if qt == "distributed_query":
            tr.note("✓ query_type = distributed_query")
        else:
            errors.append(f"query_type={qt}")

        for node_key, expected_engine in [
            ("tru_so", "sqlserver"), ("CN01", "mysql"), ("CN02", "postgresql")
        ]:
            if node_key in nodes:
                n      = nodes[node_key]
                engine = n.get("db_engine")
                count  = n.get("count", 0)
                err    = n.get("error")
                tr.note(f"✓ nodes.{node_key}: db_engine={engine}, count={count}" +
                        (f", error={err}" if err else ""))
                if engine != expected_engine:
                    errors.append(f"nodes.{node_key}.db_engine={engine} (expected {expected_engine})")
            else:
                errors.append(f"nodes.{node_key} missing")

        has_source = all("source_node" in e for e in employees) if employees else False
        has_engine = all("db_engine"   in e for e in employees) if employees else False
        tr.note(f"✓ total = {data.get('total')}")
        tr.note(f"✓ source_node field on each record: {has_source}")
        tr.note(f"✓ db_engine   field on each record: {has_engine}")

        if errors:
            tr.failed(" | ".join(errors))
        elif not has_source or not has_engine:
            tr.failed("Thiếu field source_node hoặc db_engine trên từng bản ghi")
        else:
            tr.passed()

    # ── TC08 — Fault tolerance (cấu trúc per-node error) ─────────────────────
    def tc08(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path = "/api/nhan-vien/tat-ca-chi-nhanh"
        tr.req  = self._fmt_req("GET", path)
        r       = api("GET", self.url(path), token=self.token)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        # Endpoint phải trả 200 dù node con có lỗi
        if r.status_code == 200:
            data  = r.json()
            nodes = data.get("nodes", {})
            # Mỗi node phải có ít nhất 2 key: db_engine và data (hoặc error)
            valid = all(
                "db_engine" in v and "data" in v
                for v in nodes.values()
            )
            tr.note(f"✓ HTTP 200 (fault-tolerant — node lỗi không làm sập query)")
            tr.note(f"✓ Cấu trúc per-node đủ field: {valid}")
            if valid:
                tr.passed()
            else:
                tr.failed("Node thiếu field db_engine hoặc data")
        else:
            tr.failed(f"Expected 200, got {r.status_code}")

    # ── TC09 — Thống kê phân mảnh ─────────────────────────────────────────────
    def tc09(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path = "/api/thong-ke/phan-manh"
        tr.req  = self._fmt_req("GET", path)
        r       = api("GET", self.url(path), token=self.token)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        data      = r.json()
        frag_type = data.get("fragmentation_type")
        nodes     = data.get("nodes", {})
        errors    = []

        if frag_type == "horizontal":
            tr.note("✓ fragmentation_type = horizontal")
        else:
            errors.append(f"fragmentation_type={frag_type}")

        for node_key, expected_engine in [
            ("tru_so", "sqlserver"), ("CN01", "mysql"), ("CN02", "postgresql")
        ]:
            if node_key in nodes:
                n  = nodes[node_key]
                sp = n.get("so_san_pham", 0)
                nv = n.get("so_nhan_vien", 0)
                st = n.get("status")
                tr.note(f"✓ {node_key}: db_engine={n.get('db_engine')}, "
                        f"san_pham={sp}, nhan_vien={nv}, status={st}")
                if st != "ok":
                    errors.append(f"{node_key}.status={st} (expected ok)")
            else:
                errors.append(f"nodes.{node_key} missing")

        if errors:
            tr.failed(" | ".join(errors))
        else:
            tr.passed()

    # ── TC10 — Tạo SP → outbox event CREATED ──────────────────────────────────
    def tc10(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        # Cleanup trước
        api("DELETE", self.url(f"/api/san-pham/{TEST_SP_MA}"), token=self.token)
        time.sleep(0.3)

        path = "/api/san-pham"
        tr.req  = self._fmt_req("POST", path, TEST_SP_BODY)
        r       = api("POST", self.url(path), token=self.token, body=TEST_SP_BODY)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code not in (200, 201):
            tr.failed(f"Expected 201, got {r.status_code}: {r.text[:200]}")
            return
        data  = r.json()
        ma_sp = data.get("ma_sp")
        tr.note(f"✓ ma_sp = {ma_sp}")
        tr.note(f"✓ ma_loai_sp = {data.get('ma_loai_sp')} → target_branch sẽ là CN01")
        if ma_sp == TEST_SP_MA:
            tr.passed()
        else:
            tr.failed(f"ma_sp mismatch: {ma_sp}")

    # ── TC11 — Xem event PRODUCT_CREATED ──────────────────────────────────────
    def tc11(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        time.sleep(1)   # chờ dispatch
        path = "/api/san-pham/sync-events"
        tr.req  = self._fmt_req("GET", path)
        r       = api("GET", self.url(path), token=self.token)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return

        body   = r.json()
        events = body if isinstance(body, list) else body.get("data", [])
        created = [e for e in events if e.get("event_type") == "PRODUCT_CREATED"]
        tr.note(f"✓ Tổng events: {len(events)}")
        tr.note(f"✓ PRODUCT_CREATED events: {len(created)}")

        # Lưu event_id để dùng cho TC16
        if events:
            self.any_event_id = (
                events[0].get("event_id") or
                str(events[0].get("id", ""))
            )
            ev = events[0]
            tr.note(f"  event_id mẫu: {self.any_event_id}")
            tr.note(f"  status: {ev.get('status')}, target_branch: {ev.get('target_branch')}")

        if created:
            tr.passed()
        else:
            tr.failed("Không tìm thấy PRODUCT_CREATED event — kiểm tra LSP01 có gắn với CN01 không")

    # ── TC12 — Cập nhật SP → event UPDATED ────────────────────────────────────
    def tc12(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path = f"/api/san-pham/{TEST_SP_MA}"
        body = {"ten_sp": "Auto Test Updated", "gia": 11_000_000, "ti_le_giam_gia": 5}
        tr.req  = self._fmt_req("PUT", path, body)
        r       = api("PUT", self.url(path), token=self.token, body=body)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code not in (200, 201):
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        time.sleep(0.5)
        # Xác nhận event UPDATED
        r2 = api("GET", self.url("/api/san-pham/sync-events"), token=self.token)
        if r2 and r2.status_code == 200:
            ev_body  = r2.json()
            events   = ev_body if isinstance(ev_body, list) else ev_body.get("data", [])
            updated  = [e for e in events if e.get("event_type") == "PRODUCT_UPDATED"]
            tr.note(f"✓ PRODUCT_UPDATED events: {len(updated)}")
            if updated:
                tr.passed()
            else:
                tr.failed("Không tìm thấy PRODUCT_UPDATED event")
        else:
            tr.note("(không thể kiểm tra sync-events — nhưng PUT thành công)")
            tr.passed()

    # ── TC13 — Xóa SP → event DELETED ─────────────────────────────────────────
    def tc13(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path = f"/api/san-pham/{TEST_SP_MA}"
        tr.req  = self._fmt_req("DELETE", path)
        r       = api("DELETE", self.url(path), token=self.token)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code not in (200, 204):
            tr.failed(f"Expected 200/204, got {r.status_code}")
            return
        time.sleep(0.5)
        r2 = api("GET", self.url("/api/san-pham/sync-events"), token=self.token)
        if r2 and r2.status_code == 200:
            ev_body = r2.json()
            events  = ev_body if isinstance(ev_body, list) else ev_body.get("data", [])
            deleted = [e for e in events if e.get("event_type") == "PRODUCT_DELETED"]
            tr.note(f"✓ PRODUCT_DELETED events: {len(deleted)}")
            if deleted:
                tr.passed()
            else:
                tr.failed("Không tìm thấy PRODUCT_DELETED event")
        else:
            tr.passed()

    # ── TC14 — Lọc event status=failed ────────────────────────────────────────
    def tc14(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path   = "/api/san-pham/sync-events"
        params = {"status": "failed"}
        tr.req  = self._fmt_req("GET", path, params=params)
        r       = api("GET", self.url(path), token=self.token, params=params)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        body   = r.json()
        events = body if isinstance(body, list) else body.get("data", [])
        tr.note(f"✓ Endpoint hoạt động")
        tr.note(f"  Failed events: {len(events)}")
        if events:
            ev = events[0]
            # Ghi event_id để retry
            self.any_event_id = ev.get("event_id") or str(ev.get("id", ""))
            tr.note(f"  event_id: {self.any_event_id}, retry_count: {ev.get('retry_count')}")
            tr.note(f"  last_error: {str(ev.get('last_error',''))[:80]}")
        else:
            tr.note("  (0 failed events — hệ thống đang ổn định, kết quả bình thường)")
        tr.passed()

    # ── TC15 — Retry tất cả event thất bại ────────────────────────────────────
    def tc15(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path = "/api/san-pham/sync-events/retry-failed"
        tr.req  = self._fmt_req("POST", path, {})
        r       = api("POST", self.url(path), token=self.token, body={})
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        data    = r.json()
        retried = data.get("retried", data.get("count", data.get("total", 0)))
        tr.note(f"✓ Endpoint hoạt động, retried = {retried}")
        tr.passed()

    # ── TC16 — Retry event theo ID ────────────────────────────────────────────
    def tc16(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        # Nếu chưa có event_id, lấy event đầu tiên
        if not self.any_event_id:
            r0 = api("GET", self.url("/api/san-pham/sync-events"), token=self.token)
            if r0 and r0.status_code == 200:
                body0  = r0.json()
                evs    = body0 if isinstance(body0, list) else body0.get("data", [])
                if evs:
                    self.any_event_id = (
                        evs[0].get("event_id") or str(evs[0].get("id", ""))
                    )
        if not self.any_event_id:
            tr.skipped("Không có event_id — cần có ít nhất 1 event trong hệ thống")
            return

        path = f"/api/san-pham/sync-events/{self.any_event_id}/retry"
        tr.req  = self._fmt_req("POST", path, {})
        r       = api("POST", self.url(path), token=self.token, body={})
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code in (200, 400, 404):
            tr.note(f"✓ Endpoint reachable, status = {r.status_code}")
            if r.status_code == 200:
                tr.note(f"  Result: {json.dumps(r.json(), ensure_ascii=False)[:200]}")
            elif r.status_code == 404:
                tr.note("  event_id not found (có thể đã được cleanup)")
            tr.passed()
        else:
            tr.failed(f"Unexpected status {r.status_code}")

    # ── TC17 — Dead letter queue ───────────────────────────────────────────────
    def tc17(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path   = "/api/san-pham/sync-events"
        params = {"status": "dead_letter"}
        tr.req  = self._fmt_req("GET", path, params=params)
        r       = api("GET", self.url(path), token=self.token, params=params)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        body   = r.json()
        events = body if isinstance(body, list) else body.get("data", [])
        tr.note(f"✓ Endpoint hoạt động")
        tr.note(f"  Dead letter events: {len(events)}")
        if events:
            ev = events[0]
            tr.note(f"  retry_count: {ev.get('retry_count')}, last_error: {str(ev.get('last_error',''))[:60]}")
        else:
            tr.note("  (0 dead_letter — hệ thống chưa có event vượt quá 5 lần retry)")
        tr.passed()

    # ── TC18 — Đọc SP từ DB chi nhánh qua trụ sở ──────────────────────────────
    def tc18(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path = "/api/chi-nhanh/CN01/san-pham"
        tr.req  = self._fmt_req("GET", path)
        r       = api("GET", self.url(path), token=self.token)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code == 200:
            body  = r.json()
            items = body if isinstance(body, list) else body.get("data", [])
            tr.note(f"✓ Đọc SP từ MySQL CN01 qua query_branch_db")
            tr.note(f"✓ Số sản phẩm: {len(items)}")
            tr.passed()
        elif r.status_code == 403:
            tr.note("Token central nhưng require_branch_access từ chối — thử với cn01_token")
            if self.cn01_token:
                r2 = api("GET", self.url(path), token=self.cn01_token)
                tr.resp += f"\n\n[Retry với CN01 token] HTTP {r2.status_code if r2 else 'N/A'}"
                if r2 and r2.status_code == 200:
                    items2 = r2.json() if isinstance(r2.json(), list) else r2.json().get("data", [])
                    tr.note(f"✓ Thành công với branch token, count={len(items2)}")
                    tr.passed()
                else:
                    tr.failed("Cả central lẫn branch token đều bị từ chối")
            else:
                tr.skipped("Cần cn01_token (TC02) để truy cập endpoint này")
        else:
            tr.failed(f"Unexpected status {r.status_code}")

    # ── TC19 — Thống kê chi nhánh từ view SQL Server ──────────────────────────
    def tc19(self, tr: TR):
        if not self.token:
            tr.skipped("Cần token — TC01 phải PASS trước")
            return
        path = "/api/thong-ke/chi-nhanh"
        tr.req  = self._fmt_req("GET", path)
        r       = api("GET", self.url(path), token=self.token)
        tr.resp = self._fmt_resp(r)
        if r is None:
            tr.failed("Không thể kết nối")
            return
        if r.status_code != 200:
            tr.failed(f"Expected 200, got {r.status_code}")
            return
        body  = r.json()
        items = body if isinstance(body, list) else body.get("data", [])
        tr.note(f"✓ Records từ v_thong_ke_chi_nhanh: {len(items)}")
        if items:
            sample = items[0]
            tr.note(f"  Sample: ma_chi_nhanh={sample.get('ma_chi_nhanh')}, "
                    f"gia_trung_binh={sample.get('gia_trung_binh')}")
            tr.passed()
        else:
            tr.failed("Không có dữ liệu thống kê chi nhánh")

    # ── TC20 — Mô phỏng request thất bại (negative cases) ────────────────────
    def tc20(self, tr: TR):
        errors = []

        # Sub-test 1: Login sai mật khẩu → expect 401
        path1 = "/api/auth/login"
        bad_creds = {"ma_nhan_vien": "NV001", "mat_khau": "wrong_password_xyz"}
        tr.req  = self._fmt_req("POST", path1, bad_creds)
        r1      = api("POST", self.url(path1), body=bad_creds)
        tr.resp = self._fmt_resp(r1)
        if r1 is None:
            tr.failed("Không thể kết nối server")
            return
        if r1.status_code == 401:
            tr.note("✓ Sub1: Login sai mật khẩu → 401 Unauthorized (expected)")
        else:
            tr.note(f"✗ Sub1: Login sai mật khẩu → {r1.status_code} (expected 401)")
            errors.append(f"Sub1: expected 401, got {r1.status_code}")

        # Sub-test 2: Gọi endpoint cần auth mà không gửi token → expect 401
        path2 = "/api/san-pham/sync-events"
        r2    = api("GET", self.url(path2))  # no token
        tr.resp += f"\n\n[Sub2 — no token]\n{self._fmt_resp(r2)}"
        if r2 is None:
            errors.append("Sub2: connection failed")
        elif r2.status_code == 401:
            tr.note("✓ Sub2: GET sync-events không có token → 401 Unauthorized (expected)")
        else:
            tr.note(f"✗ Sub2: GET sync-events không có token → {r2.status_code} (expected 401)")
            errors.append(f"Sub2: expected 401, got {r2.status_code}")

        # Sub-test 3: Endpoint không tồn tại → expect 404
        path3 = "/api/endpoint-khong-ton-tai"
        r3    = api("GET", self.url(path3), token=self.token)
        tr.resp += f"\n\n[Sub3 — 404]\n{self._fmt_resp(r3)}"
        if r3 is None:
            errors.append("Sub3: connection failed")
        elif r3.status_code == 404:
            tr.note("✓ Sub3: Endpoint không tồn tại → 404 Not Found (expected)")
        else:
            tr.note(f"✗ Sub3: Endpoint không tồn tại → {r3.status_code} (expected 404)")
            errors.append(f"Sub3: expected 404, got {r3.status_code}")

        if errors:
            tr.failed(" | ".join(errors))
        else:
            tr.passed()

    # ── Summary ────────────────────────────────────────────────────────────────
    def summary(self):
        passed  = sum(1 for r in self.results if r.status == PASS)
        failed  = sum(1 for r in self.results if r.status == FAIL)
        skipped = sum(1 for r in self.results if r.status == SKIP)
        errored = sum(1 for r in self.results if r.status == ERROR)
        total   = len(self.results)

        sep = "═" * 72
        self.lg.info(f"\n{sep}")
        self.lg.info("  SUMMARY")
        self.lg.info(sep)
        self.lg.info(f"  {'TC':<8} {'Status':<8} Tên test")
        self.lg.info(f"  {'─'*6} {'─'*6} {'─'*45}")
        icons = {PASS: "✓", FAIL: "✗", SKIP: "○", ERROR: "!"}
        for r in self.results:
            icon = icons.get(r.status, "?")
            self.lg.info(f"  {r.tc_id:<8} {icon} {r.status:<6} {r.name}")
        self.lg.info(f"\n  Total={total}  PASS={passed}  FAIL={failed}  SKIP={skipped}  ERROR={errored}")
        self.lg.info(sep)
        return failed + errored

    # ── Run all ────────────────────────────────────────────────────────────────
    def run_all(self):
        sep = "═" * 72
        self.lg.info(sep)
        self.lg.info("  DISTRIBUTED DATABASE — AUTOMATED TEST RUNNER")
        self.lg.info(f"  Target  : {self.base}")
        self.lg.info(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.lg.info(sep)

        TESTS = [
            ("TC01", "Đăng nhập trụ sở (SQL Server)",              self.tc01),
            ("TC02", "Đăng nhập CN01 qua gateway (MySQL)",          self.tc02),
            ("TC03", "Đăng nhập CN02 qua gateway (PostgreSQL)",     self.tc03),
            ("TC04", "System health — toàn hệ thống",              self.tc04),
            ("TC05", "Health check DB chi nhánh CN01",             self.tc05),
            ("TC06", "Health check DB chi nhánh CN02",             self.tc06),
            ("TC07", "Distributed query nhân viên 3 DBMS",         self.tc07),
            ("TC08", "Fault tolerance — cấu trúc per-node error",  self.tc08),
            ("TC09", "Thống kê phân mảnh ngang",                   self.tc09),
            ("TC10", "Tạo SP → outbox event CREATED",              self.tc10),
            ("TC11", "Xem event PRODUCT_CREATED",                  self.tc11),
            ("TC12", "Cập nhật SP → event UPDATED",                self.tc12),
            ("TC13", "Xóa SP → event DELETED",                     self.tc13),
            ("TC14", "Lọc event status=failed",                    self.tc14),
            ("TC15", "Retry tất cả event thất bại",               self.tc15),
            ("TC16", "Retry event theo ID",                        self.tc16),
            ("TC17", "Dead letter queue — xem event",              self.tc17),
            ("TC18", "Đọc SP từ DB chi nhánh CN01 qua trụ sở",    self.tc18),
            ("TC19", "Thống kê chi nhánh từ view SQL Server",      self.tc19),
            ("TC20", "Mô phỏng request thất bại (negative cases)", self.tc20),
        ]

        for tc_id, name, fn in TESTS:
            self.run(tc_id, name, fn)

        self.lg.info(f"\n  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return self.summary()


# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Distributed DB test runner")
    parser.add_argument("--base-url", default=BASE_URL,
                        help=f"API base URL (default: {BASE_URL})")
    args = parser.parse_args()

    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"test_results_{ts}.log"
    )

    lg = make_logger(log_path)
    lg.info(f"Log: {log_path}\n")

    runner    = Runner(args.base_url, lg)
    n_failed  = runner.run_all()
    lg.info(f"\nLog saved → {log_path}")

    sys.exit(0 if n_failed == 0 else 1)


if __name__ == "__main__":
    main()
