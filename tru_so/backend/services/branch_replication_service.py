import json
from datetime import datetime, timezone
from decimal import Decimal

from db import build_pagination_meta, execute_db, parse_pagination, query_db


def ensure_branch_replica_tables():
    execute_db(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'branch_replication_inbox')
        CREATE TABLE branch_replication_inbox (
            event_id NVARCHAR(150) PRIMARY KEY,
            source_branch NVARCHAR(20) NOT NULL,
            entity_type NVARCHAR(40) NOT NULL,
            object_id NVARCHAR(80) NOT NULL,
            event_type NVARCHAR(60) NOT NULL,
            version INT NOT NULL,
            payload NVARCHAR(MAX) NOT NULL,
            status NVARCHAR(20) NOT NULL,
            message NVARCHAR(MAX) NULL,
            received_at DATETIME2 DEFAULT SYSUTCDATETIME()
        )
        """
    )
    execute_db(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'central_failover_events')
        CREATE TABLE central_failover_events (
            event_id NVARCHAR(150) PRIMARY KEY,
            target_branch NVARCHAR(20) NOT NULL,
            entity_type NVARCHAR(40) NOT NULL,
            object_id NVARCHAR(80) NOT NULL,
            event_type NVARCHAR(60) NOT NULL,
            payload NVARCHAR(MAX) NOT NULL,
            status NVARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
            replayed_at DATETIME2 NULL
        )
        """
    )
    execute_db(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'branch_employee_replica')
        CREATE TABLE branch_employee_replica (
            ma_chi_nhanh NVARCHAR(20) NOT NULL,
            ma_nhan_vien NVARCHAR(20) NOT NULL,
            ho_ten NVARCHAR(100) NULL,
            cccd NVARCHAR(20) NULL,
            sdt NVARCHAR(20) NULL,
            luong DECIMAL(18, 2) NULL,
            trang_thai INT NULL,
            ma_phong_ban INT NULL,
            ma_ngay_lam INT NULL,
            chuc_vu NVARCHAR(50) NULL,
            ngay_bat_dau DATE NULL,
            ngay_ket_thuc DATE NULL,
            ten_pb NVARCHAR(100) NULL,
            source_branch NVARCHAR(20) NOT NULL,
            source_version INT NOT NULL,
            updated_at DATETIME2 DEFAULT SYSUTCDATETIME(),
            PRIMARY KEY (ma_chi_nhanh, ma_nhan_vien)
        )
        """
    )
    execute_db(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'branch_hoa_don_replica')
        CREATE TABLE branch_hoa_don_replica (
            ma_chi_nhanh NVARCHAR(20) NOT NULL,
            ma_hd NVARCHAR(20) NOT NULL,
            ngay_lap DATETIME2 NULL,
            ma_nhan_vien NVARCHAR(20) NULL,
            ten_nhan_vien NVARCHAR(100) NULL,
            ten_kh NVARCHAR(100) NULL,
            sdt_kh NVARCHAR(20) NULL,
            tong_tien DECIMAL(18, 2) NULL,
            ghi_chu NVARCHAR(MAX) NULL,
            source_branch NVARCHAR(20) NOT NULL,
            source_version INT NOT NULL,
            updated_at DATETIME2 DEFAULT SYSUTCDATETIME(),
            PRIMARY KEY (ma_chi_nhanh, ma_hd)
        )
        """
    )
    execute_db(
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'branch_ct_hoa_don_replica')
        CREATE TABLE branch_ct_hoa_don_replica (
            ma_chi_nhanh NVARCHAR(20) NOT NULL,
            ma_hd NVARCHAR(20) NOT NULL,
            line_no INT NOT NULL,
            ma_sp NVARCHAR(20) NULL,
            ten_sp NVARCHAR(255) NULL,
            so_luong INT NULL,
            don_gia DECIMAL(18, 2) NULL,
            thanh_tien DECIMAL(18, 2) NULL,
            source_branch NVARCHAR(20) NOT NULL,
            source_version INT NOT NULL,
            updated_at DATETIME2 DEFAULT SYSUTCDATETIME(),
            PRIMARY KEY (ma_chi_nhanh, ma_hd, line_no)
        )
        """
    )


def _money(value):
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _int_or_none(value):
    if value is None or value == "":
        return None
    return int(value)


def _record_inbox(event, status, message):
    execute_db(
        """
        INSERT INTO branch_replication_inbox (
            event_id, source_branch, entity_type, object_id, event_type,
            version, payload, status, message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["event_id"],
            event["source_branch"],
            event["entity_type"],
            event["object_id"],
            event["event_type"],
            event["version"],
            json.dumps(event, ensure_ascii=False),
            status,
            message,
        ),
    )


def _record_failover_event(event):
    execute_db(
        """
        INSERT INTO central_failover_events (
            event_id, target_branch, entity_type, object_id, event_type, payload, status
        )
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """,
        (
            event["event_id"],
            event["source_branch"],
            event["entity_type"],
            event["object_id"],
            event["event_type"],
            json.dumps(event, ensure_ascii=False),
        ),
    )


def _upsert_employee(event):
    data = event.get("data") or {}
    ma_chi_nhanh = (data.get("ma_chi_nhanh") or event["source_branch"]).upper()
    ma_nhan_vien = data.get("ma_nhan_vien") or event.get("object_id")
    if not ma_nhan_vien:
        raise ValueError("Missing ma_nhan_vien")

    execute_db(
        """
        MERGE branch_employee_replica AS target
        USING (SELECT ? AS ma_chi_nhanh, ? AS ma_nhan_vien) AS src
        ON target.ma_chi_nhanh = src.ma_chi_nhanh
           AND target.ma_nhan_vien = src.ma_nhan_vien
        WHEN MATCHED THEN UPDATE SET
            ho_ten = ?, cccd = ?, sdt = ?, luong = ?, trang_thai = ?,
            ma_phong_ban = ?, ma_ngay_lam = ?, chuc_vu = ?,
            ngay_bat_dau = ?, ngay_ket_thuc = ?, ten_pb = ?,
            source_branch = ?, source_version = ?, updated_at = SYSUTCDATETIME()
        WHEN NOT MATCHED THEN INSERT (
            ma_chi_nhanh, ma_nhan_vien, ho_ten, cccd, sdt, luong,
            trang_thai, ma_phong_ban, ma_ngay_lam, chuc_vu,
            ngay_bat_dau, ngay_ket_thuc, ten_pb, source_branch, source_version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            ma_chi_nhanh,
            ma_nhan_vien,
            data.get("ho_ten"),
            data.get("cccd"),
            data.get("sdt"),
            _money(data.get("luong")),
            _int_or_none(data.get("trang_thai")),
            _int_or_none(data.get("ma_phong_ban")),
            _int_or_none(data.get("ma_ngay_lam")),
            data.get("chuc_vu"),
            data.get("ngay_bat_dau"),
            data.get("ngay_ket_thuc"),
            data.get("ten_pb"),
            event["source_branch"],
            int(event["version"]),
            ma_chi_nhanh,
            ma_nhan_vien,
            data.get("ho_ten"),
            data.get("cccd"),
            data.get("sdt"),
            _money(data.get("luong")),
            _int_or_none(data.get("trang_thai")),
            _int_or_none(data.get("ma_phong_ban")),
            _int_or_none(data.get("ma_ngay_lam")),
            data.get("chuc_vu"),
            data.get("ngay_bat_dau"),
            data.get("ngay_ket_thuc"),
            data.get("ten_pb"),
            event["source_branch"],
            int(event["version"]),
        ),
    )


def _delete_invoice(event):
    data = event.get("data") or {}
    ma_chi_nhanh = (data.get("ma_chi_nhanh") or event["source_branch"]).upper()
    ma_hd = data.get("ma_hd") or event.get("object_id")
    if not ma_hd:
        raise ValueError("Missing ma_hd")
    execute_db(
        "DELETE FROM branch_ct_hoa_don_replica WHERE ma_chi_nhanh = ? AND ma_hd = ?",
        (ma_chi_nhanh, ma_hd),
    )
    execute_db(
        "DELETE FROM branch_hoa_don_replica WHERE ma_chi_nhanh = ? AND ma_hd = ?",
        (ma_chi_nhanh, ma_hd),
    )


def _upsert_invoice(event):
    data = event.get("data") or {}
    ma_chi_nhanh = (data.get("ma_chi_nhanh") or event["source_branch"]).upper()
    ma_hd = data.get("ma_hd") or event.get("object_id")
    if not ma_hd:
        raise ValueError("Missing ma_hd")

    execute_db(
        """
        MERGE branch_hoa_don_replica AS target
        USING (SELECT ? AS ma_chi_nhanh, ? AS ma_hd) AS src
        ON target.ma_chi_nhanh = src.ma_chi_nhanh AND target.ma_hd = src.ma_hd
        WHEN MATCHED THEN UPDATE SET
            ngay_lap = ?, ma_nhan_vien = ?, ten_nhan_vien = ?, ten_kh = ?,
            sdt_kh = ?, tong_tien = ?, ghi_chu = ?, source_branch = ?,
            source_version = ?, updated_at = SYSUTCDATETIME()
        WHEN NOT MATCHED THEN INSERT (
            ma_chi_nhanh, ma_hd, ngay_lap, ma_nhan_vien, ten_nhan_vien,
            ten_kh, sdt_kh, tong_tien, ghi_chu, source_branch, source_version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            ma_chi_nhanh,
            ma_hd,
            data.get("ngay_lap"),
            data.get("ma_nhan_vien"),
            data.get("ten_nhan_vien"),
            data.get("ten_kh"),
            data.get("sdt_kh"),
            _money(data.get("tong_tien")),
            data.get("ghi_chu"),
            event["source_branch"],
            int(event["version"]),
            ma_chi_nhanh,
            ma_hd,
            data.get("ngay_lap"),
            data.get("ma_nhan_vien"),
            data.get("ten_nhan_vien"),
            data.get("ten_kh"),
            data.get("sdt_kh"),
            _money(data.get("tong_tien")),
            data.get("ghi_chu"),
            event["source_branch"],
            int(event["version"]),
        ),
    )

    execute_db(
        "DELETE FROM branch_ct_hoa_don_replica WHERE ma_chi_nhanh = ? AND ma_hd = ?",
        (ma_chi_nhanh, ma_hd),
    )
    for index, item in enumerate(data.get("chi_tiet") or [], start=1):
        line_no = _int_or_none(item.get("id")) or index
        execute_db(
            """
            INSERT INTO branch_ct_hoa_don_replica (
                ma_chi_nhanh, ma_hd, line_no, ma_sp, ten_sp, so_luong,
                don_gia, thanh_tien, source_branch, source_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ma_chi_nhanh,
                ma_hd,
                line_no,
                item.get("ma_sp"),
                item.get("ten_sp"),
                _int_or_none(item.get("so_luong")),
                _money(item.get("don_gia")),
                _money(item.get("thanh_tien")),
                event["source_branch"],
                int(event["version"]),
            ),
        )


def apply_branch_replication_event(event):
    ensure_branch_replica_tables()
    required = ["event_id", "entity_type", "event_type", "object_id", "source_branch", "version"]
    missing = [field for field in required if event.get(field) in (None, "")]
    if missing:
        raise ValueError("Missing event fields: " + ", ".join(missing))

    existing = query_db(
        "SELECT event_id, status FROM branch_replication_inbox WHERE event_id = ?",
        (event["event_id"],),
        fetchone=True,
    )
    if existing:
        return {"success": True, "status": "ignored", "event_id": event["event_id"]}

    try:
        entity_type = str(event["entity_type"]).lower()
        event_type = str(event["event_type"]).upper()
        if entity_type == "employee":
            _upsert_employee(event)
        elif entity_type == "invoice" and event_type == "INVOICE_DELETE":
            _delete_invoice(event)
        elif entity_type == "invoice":
            _upsert_invoice(event)
        else:
            raise ValueError(f"Unsupported replication entity: {entity_type}")
    except Exception as exc:
        _record_inbox(event, "failed", str(exc))
        raise

    _record_inbox(event, "success", "Applied successfully")
    return {"success": True, "status": "applied", "event_id": event["event_id"]}


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") and value is not None else value


def _event_suffix():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def _format_employee(row):
    if not row:
        return None
    if row.get("luong") is not None:
        row["luong"] = float(row["luong"])
    row["ngay_bat_dau"] = _iso(row.get("ngay_bat_dau"))
    row["ngay_ket_thuc"] = _iso(row.get("ngay_ket_thuc"))
    row["source_node"] = row.get("ma_chi_nhanh")
    row["db_engine"] = "sqlserver_replica"
    return row


def get_replica_employee_by_id(ma_chi_nhanh, ma_nhan_vien):
    ensure_branch_replica_tables()
    row = query_db(
        """
        SELECT ma_nhan_vien, ho_ten, cccd, sdt, luong, trang_thai,
               ma_phong_ban, ma_ngay_lam, chuc_vu, ngay_bat_dau,
               ngay_ket_thuc, ten_pb, ma_chi_nhanh
        FROM branch_employee_replica
        WHERE ma_chi_nhanh = ? AND ma_nhan_vien = ?
        """,
        (ma_chi_nhanh.upper(), ma_nhan_vien),
        fetchone=True,
    )
    return _format_employee(row)


def get_replica_employees_for_api(ma_chi_nhanh, args=None):
    ensure_branch_replica_tables()
    args = args or {}
    where = ["ma_chi_nhanh = ?"]
    params = [ma_chi_nhanh.upper()]

    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        where.append("(ho_ten LIKE ? OR ma_nhan_vien LIKE ? OR cccd LIKE ? OR sdt LIKE ?)")
        params.extend([like, like, like, like])
    if args.get("chuc_vu"):
        where.append("chuc_vu = ?")
        params.append(args["chuc_vu"])
    if args.get("ma_phong_ban"):
        where.append("ma_phong_ban = ?")
        params.append(args["ma_phong_ban"])
    if args.get("trang_thai") not in (None, ""):
        where.append("trang_thai = ?")
        params.append(int(args["trang_thai"]))

    where_sql = " WHERE " + " AND ".join(where)
    page, limit, offset = parse_pagination(args)
    total_row = query_db(
        "SELECT COUNT(*) AS total FROM branch_employee_replica" + where_sql,
        tuple(params),
        fetchone=True,
    )
    total = int(total_row["total"] if total_row else 0)
    if total > 0:
        page = min(page, ((total - 1) // limit) + 1)
    else:
        page = 1
    offset = (page - 1) * limit

    rows = query_db(
        """
        SELECT ma_nhan_vien, ho_ten, cccd, sdt, luong, trang_thai,
               ma_phong_ban, ma_ngay_lam, chuc_vu, ngay_bat_dau,
               ngay_ket_thuc, ten_pb, ma_chi_nhanh
        FROM branch_employee_replica
        """
        + where_sql
        + " ORDER BY ma_nhan_vien OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
        tuple(params) + (offset, limit),
    )
    for row in rows:
        _format_employee(row)

    return {
        "branch_code": ma_chi_nhanh.upper(),
        "data": rows,
        "pagination": build_pagination_meta(page, limit, total),
        "source": "hq_replica",
        "branch_status": "replica",
    }


def _format_invoice(row):
    if not row:
        return None
    row["ngay_lap"] = _iso(row.get("ngay_lap"))
    if row.get("tong_tien") is not None:
        row["tong_tien"] = float(row["tong_tien"])
    return row


def _format_invoice_item(row):
    if not row:
        return None
    row["id"] = row.pop("line_no", row.get("id"))
    if row.get("so_luong") is not None:
        row["so_luong"] = int(row["so_luong"])
    for field in ("don_gia", "thanh_tien"):
        if row.get(field) is not None:
            row[field] = float(row[field])
    return row


def get_replica_invoices_from_branch(ma_chi_nhanh, args=None):
    ensure_branch_replica_tables()
    args = args or {}
    where = ["ma_chi_nhanh = ?"]
    params = [ma_chi_nhanh.upper()]

    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        where.append("(ma_hd LIKE ? OR ten_kh LIKE ? OR sdt_kh LIKE ?)")
        params.extend([like, like, like])
    if args.get("tu_ngay"):
        where.append("ngay_lap >= ?")
        params.append(args["tu_ngay"])
    if args.get("den_ngay"):
        where.append("ngay_lap < ?")
        params.append(args["den_ngay"])

    where_sql = " WHERE " + " AND ".join(where)
    rows = query_db(
        """
        SELECT ma_hd, ngay_lap, ma_nhan_vien, ten_nhan_vien,
               ten_kh, sdt_kh, tong_tien, ghi_chu, ma_chi_nhanh
        FROM branch_hoa_don_replica
        """
        + where_sql
        + " ORDER BY ngay_lap DESC, ma_hd",
        tuple(params),
    )
    for row in rows:
        _format_invoice(row)
    return {"data": rows, "branch_status": "replica", "source": "hq_replica"}


def get_replica_invoice_detail(ma_chi_nhanh, ma_hd):
    ensure_branch_replica_tables()
    invoice = query_db(
        """
        SELECT ma_hd, ngay_lap, ma_nhan_vien, ten_nhan_vien,
               ten_kh, sdt_kh, tong_tien, ghi_chu, ma_chi_nhanh
        FROM branch_hoa_don_replica
        WHERE ma_chi_nhanh = ? AND ma_hd = ?
        """,
        (ma_chi_nhanh.upper(), ma_hd),
        fetchone=True,
    )
    if not invoice:
        return None
    _format_invoice(invoice)
    items = query_db(
        """
        SELECT line_no, ma_sp, ten_sp, so_luong, don_gia, thanh_tien
        FROM branch_ct_hoa_don_replica
        WHERE ma_chi_nhanh = ? AND ma_hd = ?
        ORDER BY line_no
        """,
        (ma_chi_nhanh.upper(), ma_hd),
    )
    for item in items:
        _format_invoice_item(item)
    invoice["chi_tiet"] = items
    invoice["source"] = "hq_replica"
    return invoice


def get_replica_revenue_for_branch(ma_chi_nhanh):
    ensure_branch_replica_tables()
    branch = ma_chi_nhanh.upper()
    summary = query_db(
        """
        SELECT COUNT(*) AS so_hoa_don, COALESCE(SUM(tong_tien), 0) AS tong_doanh_thu
        FROM branch_hoa_don_replica
        WHERE ma_chi_nhanh = ?
        """,
        (branch,),
        fetchone=True,
    ) or {}
    theo_ngay = query_db(
        """
        SELECT CAST(ngay_lap AS date) AS ngay,
               COUNT(*) AS so_hoa_don,
               COALESCE(SUM(tong_tien), 0) AS tong_doanh_thu
        FROM branch_hoa_don_replica
        WHERE ma_chi_nhanh = ?
        GROUP BY CAST(ngay_lap AS date)
        ORDER BY ngay DESC
        """,
        (branch,),
    )
    for row in theo_ngay:
        row["ngay"] = _iso(row.get("ngay"))
        row["so_hoa_don"] = int(row["so_hoa_don"] or 0)
        row["tong_doanh_thu"] = float(row["tong_doanh_thu"] or 0)

    theo_sp = query_db(
        """
        SELECT ma_sp, MAX(ten_sp) AS ten_sp,
               COALESCE(SUM(so_luong), 0) AS tong_so_luong,
               COALESCE(SUM(thanh_tien), 0) AS tong_doanh_thu
        FROM branch_ct_hoa_don_replica
        WHERE ma_chi_nhanh = ?
        GROUP BY ma_sp
        ORDER BY tong_doanh_thu DESC
        """,
        (branch,),
    )
    for row in theo_sp:
        row["tong_so_luong"] = int(row["tong_so_luong"] or 0)
        row["tong_doanh_thu"] = float(row["tong_doanh_thu"] or 0)

    return {
        "branch_status": "replica",
        "source": "hq_replica",
        "so_hoa_don": int(summary.get("so_hoa_don") or 0),
        "tong_doanh_thu": float(summary.get("tong_doanh_thu") or 0),
        "theo_ngay": theo_ngay,
        "theo_san_pham": theo_sp,
    }


def backfill_employee_replica(ma_chi_nhanh, employee_row):
    ensure_branch_replica_tables()
    branch = ma_chi_nhanh.upper()
    data = dict(employee_row or {})
    data["ma_chi_nhanh"] = branch
    event = {
        "event_id": f"backfill_{branch}_employee_{data.get('ma_nhan_vien')}",
        "entity_type": "employee",
        "event_type": "EMPLOYEE_BACKFILL",
        "object_id": data.get("ma_nhan_vien"),
        "source_branch": branch,
        "version": 0,
        "data": data,
    }
    _upsert_employee(event)


def backfill_invoice_replica(ma_chi_nhanh, invoice_row, chi_tiet=None):
    ensure_branch_replica_tables()
    branch = ma_chi_nhanh.upper()
    data = dict(invoice_row or {})
    data["ma_chi_nhanh"] = branch
    data["chi_tiet"] = list(chi_tiet or [])
    event = {
        "event_id": f"backfill_{branch}_invoice_{data.get('ma_hd')}",
        "entity_type": "invoice",
        "event_type": "INVOICE_BACKFILL",
        "object_id": data.get("ma_hd"),
        "source_branch": branch,
        "version": 0,
        "data": data,
    }
    _upsert_invoice(event)


def write_failover_employee(ma_chi_nhanh, event_type, object_id, data):
    ensure_branch_replica_tables()
    branch = ma_chi_nhanh.upper()
    payload = dict(data or {})
    payload["ma_chi_nhanh"] = branch
    payload["ma_nhan_vien"] = payload.get("ma_nhan_vien") or object_id
    event = {
        "event_id": f"hq_failover_{branch}_employee_{payload['ma_nhan_vien']}_{event_type}",
        "entity_type": "employee",
        "event_type": event_type,
        "object_id": payload["ma_nhan_vien"],
        "source_branch": branch,
        "version": 0,
        "data": payload,
    }
    if event_type == "EMPLOYEE_DELETE":
        payload["trang_thai"] = 0
    _upsert_employee(event)
    event["event_id"] = f"hq_failover_{branch}_employee_{payload['ma_nhan_vien']}_{_event_suffix()}_{event_type}"
    _record_failover_event(event)
    employee = get_replica_employee_by_id(branch, payload["ma_nhan_vien"])
    if employee:
        employee["source"] = "hq_failover"
    return employee


def write_failover_invoice(ma_chi_nhanh, event_type, object_id, data=None):
    ensure_branch_replica_tables()
    branch = ma_chi_nhanh.upper()
    payload = dict(data or {})
    payload["ma_chi_nhanh"] = branch
    payload["ma_hd"] = payload.get("ma_hd") or object_id
    if "items" in payload and "chi_tiet" not in payload:
        payload["chi_tiet"] = payload.pop("items")
    if event_type != "INVOICE_DELETE":
        details = []
        total = 0.0
        for idx, item in enumerate(payload.get("chi_tiet") or [], start=1):
            row = dict(item)
            row["id"] = row.get("id") or idx
            row["so_luong"] = int(row.get("so_luong") or 0)
            row["don_gia"] = _money(row.get("don_gia")) or 0
            row["thanh_tien"] = _money(row.get("thanh_tien"))
            if row["thanh_tien"] is None:
                row["thanh_tien"] = round(row["so_luong"] * row["don_gia"], 2)
            total += row["thanh_tien"]
            details.append(row)
        payload["chi_tiet"] = details
        payload["tong_tien"] = _money(payload.get("tong_tien")) or round(total, 2)

    event = {
        "event_id": f"hq_failover_{branch}_invoice_{payload['ma_hd']}_{event_type}",
        "entity_type": "invoice",
        "event_type": event_type,
        "object_id": payload["ma_hd"],
        "source_branch": branch,
        "version": 0,
        "data": payload,
    }
    if event_type == "INVOICE_DELETE":
        _delete_invoice(event)
    else:
        _upsert_invoice(event)
    event["event_id"] = f"hq_failover_{branch}_invoice_{payload['ma_hd']}_{_event_suffix()}_{event_type}"
    _record_failover_event(event)
    if event_type == "INVOICE_DELETE":
        return {"ma_hd": payload["ma_hd"], "source": "hq_failover"}
    invoice = get_replica_invoice_detail(branch, payload["ma_hd"])
    if invoice:
        invoice["source"] = "hq_failover"
    return invoice
