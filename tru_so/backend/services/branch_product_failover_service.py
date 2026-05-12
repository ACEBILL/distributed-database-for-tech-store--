"""Branch-compatible endpoints cho catalog san pham tu central API.

Khi frontend chi nhanh fallback ve tru so qua nginx (X-Branch-Failover),
cac endpoint /api/san-pham/from-hq + /api/san-pham/import-from-hq van phai
chay duoc — central API se goi cac ham trong file nay.

Hai mode:
- Branch DB van reachable: ghi truc tiep vao SAN_PHAM cua chi nhanh
  qua execute_branch_db.
- Branch DB khong reachable: queue event PRODUCT_IMPORT vao
  central_failover_events, will replay sang branch khi backend song lai.
"""

import json
from datetime import datetime, timezone

from db import execute_branch_db, execute_db, query_branch_db, query_db
from services.branch_replication_service import ensure_branch_replica_tables


def _event_suffix():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def _hq_catalog():
    rows = query_db(
        """
        SELECT sp.ma_sp, sp.ten_sp, sp.gia, sp.ti_le_loi_nhuan, sp.ti_le_giam_gia,
               sp.mo_ta, sp.ma_loai_sp, sp.ma_ncc, sp.trang_thai,
               lsp.ten_loai_sp, lsp.ma_chi_nhanh, ncc.ten_NCC
        FROM SAN_PHAM sp
        JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
        JOIN NCC ncc ON sp.ma_ncc = ncc.ma_NCC
        WHERE sp.trang_thai = 1
        ORDER BY sp.ma_sp
        """
    )
    for product in rows:
        for field in ("gia", "ti_le_loi_nhuan", "ti_le_giam_gia"):
            if product.get(field) is not None:
                product[field] = float(product[field])
    return rows


def _branch_existing_ma_sp(branch_code):
    """Tra ve set ma_sp da co o branch. Tra ve None neu branch DB khong reachable."""
    try:
        rows = query_branch_db(branch_code, "SELECT ma_sp FROM SAN_PHAM")
    except Exception:
        return None
    return {row["ma_sp"] for row in rows}


def _pending_imports_for_branch(branch_code):
    ensure_branch_replica_tables()
    rows = query_db(
        """
        SELECT object_id
        FROM central_failover_events
        WHERE target_branch = ?
          AND entity_type = 'product'
          AND event_type = 'PRODUCT_IMPORT'
          AND status = 'pending'
        """,
        (branch_code.upper(),),
    )
    return {row["object_id"] for row in rows}


def list_hq_catalog_for_branch_via_central(branch_code):
    """Tra ve HQ catalog + co already_imported / pending_import per row."""
    branch = branch_code.upper()
    products = _hq_catalog()
    existing = _branch_existing_ma_sp(branch)
    pending = _pending_imports_for_branch(branch)
    branch_db_reachable = existing is not None

    for product in products:
        ma_sp = product.get("ma_sp")
        if branch_db_reachable:
            product["already_imported"] = ma_sp in existing
        else:
            product["already_imported"] = False
        product["pending_import"] = ma_sp in pending
        product["branch_db_reachable"] = branch_db_reachable

    return {
        "branch_code": branch,
        "branch_db_reachable": branch_db_reachable,
        "data": products,
    }


def _get_hq_product(ma_sp):
    product = query_db(
        """
        SELECT sp.ma_sp, sp.ten_sp, sp.gia, sp.ti_le_loi_nhuan, sp.ti_le_giam_gia,
               sp.mo_ta, sp.ma_loai_sp, sp.ma_ncc, sp.trang_thai
        FROM SAN_PHAM sp
        WHERE sp.ma_sp = ?
        """,
        (ma_sp,),
        fetchone=True,
    )
    if not product:
        return None
    for field in ("gia", "ti_le_loi_nhuan", "ti_le_giam_gia"):
        if product.get(field) is not None:
            product[field] = float(product[field])
    return product


def _record_product_import_failover_event(branch_code, product):
    ensure_branch_replica_tables()
    branch = branch_code.upper()
    ma_sp = product["ma_sp"]
    payload = {
        "event_id": f"hq_failover_{branch}_product_{ma_sp}_{_event_suffix()}",
        "entity_type": "product",
        "event_type": "PRODUCT_IMPORT",
        "object_id": ma_sp,
        "source_branch": branch,
        "version": 0,
        "data": dict(product),
    }
    execute_db(
        """
        INSERT INTO central_failover_events (
            event_id, target_branch, entity_type, object_id, event_type, payload, status
        )
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """,
        (
            payload["event_id"],
            branch,
            "product",
            ma_sp,
            "PRODUCT_IMPORT",
            json.dumps(payload, ensure_ascii=False),
        ),
    )
    return payload


def import_product_to_branch_via_central(branch_code, ma_sp):
    """Co gang ghi truc tiep san pham vao branch DB. Failover neu khong duoc."""
    if not ma_sp:
        raise ValueError("ma_sp là bắt buộc")

    branch = branch_code.upper()
    product = _get_hq_product(ma_sp)
    if not product:
        raise LookupError(f"Sản phẩm {ma_sp} không tồn tại ở trụ sở")

    existing = _branch_existing_ma_sp(branch)
    if existing is None:
        pending = _pending_imports_for_branch(branch)
        if ma_sp in pending:
            return {
                "ma_sp": ma_sp,
                "branch_code": branch,
                "source": "hq_failover_pending",
                "message": "Đã ở hàng đợi failover; sẽ áp dụng khi backend chi nhánh sống lại",
                "product": product,
            }
        _record_product_import_failover_event(branch, product)
        return {
            "ma_sp": ma_sp,
            "branch_code": branch,
            "source": "hq_failover",
            "message": "Branch DB không truy cập được — đã ghi vào hàng đợi failover",
            "product": product,
        }

    if ma_sp in existing:
        raise ValueError(f"Sản phẩm {ma_sp} đã tồn tại ở chi nhánh {branch}")

    execute_branch_db(
        branch,
        """
        INSERT INTO SAN_PHAM (
            ma_sp, ten_sp, gia, ti_le_loi_nhuan, ti_le_giam_gia,
            mo_ta, ma_loai_sp, ma_ncc, trang_thai
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product["ma_sp"],
            product["ten_sp"],
            product.get("gia") or 0,
            product.get("ti_le_loi_nhuan") or 0,
            product.get("ti_le_giam_gia") or 0,
            product.get("mo_ta"),
            product["ma_loai_sp"],
            product["ma_ncc"],
            product.get("trang_thai", 1),
        ),
    )
    return {
        "ma_sp": ma_sp,
        "branch_code": branch,
        "source": "branch_database",
        "product": product,
    }
