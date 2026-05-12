"""Backfill toan bo du lieu nhan vien + hoa don tu CN01/CN02 len replica tru so.

Chay tay trong container tru-so-backend:
    docker compose exec tru-so-backend python scripts/backfill_branch_replicas.py
Hoac backfill 1 chi nhanh:
    docker compose exec tru-so-backend python scripts/backfill_branch_replicas.py CN01
"""

import sys
import traceback

from central_api.app import app
from db import has_branch_db_settings, query_branch_db
from services.branch_replication_service import (
    backfill_employee_replica,
    backfill_invoice_replica,
    ensure_branch_replica_tables,
)
from services.branch_service import get_branches


EMPLOYEE_SQL = """
    SELECT nv.ma_nhan_vien, nv.ho_ten, nv.cccd, nv.sdt, nv.luong, nv.trang_thai,
           nv.ma_phong_ban, nv.ma_ngay_lam, nv.chuc_vu,
           nv.ngay_bat_dau, nv.ngay_ket_thuc,
           pb.ten_pb
    FROM NHAN_VIEN nv
    LEFT JOIN phong_ban pb ON nv.ma_phong_ban = pb.ma_pb
"""

INVOICE_SQL = """
    SELECT hd.ma_hd, hd.ngay_lap, hd.ma_nhan_vien, nv.ho_ten AS ten_nhan_vien,
           hd.ten_kh, hd.sdt_kh, hd.tong_tien, hd.ghi_chu
    FROM HOA_DON hd
    LEFT JOIN NHAN_VIEN nv ON hd.ma_nhan_vien = nv.ma_nhan_vien
"""

INVOICE_DETAIL_SQL = """
    SELECT ct.id, ct.ma_sp, sp.ten_sp, ct.so_luong, ct.don_gia, ct.thanh_tien
    FROM CT_HOA_DON ct
    LEFT JOIN SAN_PHAM sp ON ct.ma_sp = sp.ma_sp
    WHERE ct.ma_hd = ?
    ORDER BY ct.id
"""


def _backfill_employees(branch_code):
    rows = query_branch_db(branch_code, EMPLOYEE_SQL)
    ok = 0
    fail = 0
    for row in rows:
        try:
            backfill_employee_replica(branch_code, row)
            ok += 1
        except Exception as exc:
            fail += 1
            print(f"  [employee] {row.get('ma_nhan_vien')} FAILED: {exc}")
    print(f"  Employees: {ok} ok, {fail} failed, total {len(rows)}")


def _backfill_invoices(branch_code):
    invoices = query_branch_db(branch_code, INVOICE_SQL)
    ok = 0
    fail = 0
    for invoice in invoices:
        try:
            details = query_branch_db(branch_code, INVOICE_DETAIL_SQL, (invoice["ma_hd"],))
            backfill_invoice_replica(branch_code, invoice, details)
            ok += 1
        except Exception as exc:
            fail += 1
            print(f"  [invoice] {invoice.get('ma_hd')} FAILED: {exc}")
            traceback.print_exc()
    print(f"  Invoices: {ok} ok, {fail} failed, total {len(invoices)}")


def backfill_branch(branch_code):
    branch_code = branch_code.upper()
    print(f"\n=== Backfill branch {branch_code} ===")
    if not has_branch_db_settings(branch_code):
        print(f"  SKIP: BRANCH_{branch_code}_DB_* env vars not configured")
        return
    try:
        _backfill_employees(branch_code)
        _backfill_invoices(branch_code)
    except Exception as exc:
        print(f"  ABORT branch {branch_code}: {exc}")
        traceback.print_exc()


def main(argv):
    targets = [code.upper() for code in argv[1:]]
    with app.app_context():
        ensure_branch_replica_tables()
        if not targets:
            targets = [b["ma_chi_nhanh"].upper() for b in get_branches()]
        print(f"Backfill targets: {targets}")
        for branch in targets:
            backfill_branch(branch)
    print("\nDone.")


if __name__ == "__main__":
    main(sys.argv)
