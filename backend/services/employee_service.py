from db import build_pagination_meta, execute_db, parse_pagination, query_db


EMPLOYEE_COLUMNS_SQL = """
    nv.ma_nhan_vien,
    nv.ho_ten,
    nv.cccd,
    nv.sdt,
    nv.luong,
    nv.trang_thai,
    nv.ma_phong_ban,
    nv.ma_ngay_lam,
    nv.chuc_vu,
    nv.ngay_bat_dau,
    nv.ngay_ket_thuc,
    pb.ten_pb
"""

EMPLOYEE_FROM_SQL = """
    FROM NHAN_VIEN nv
    LEFT JOIN phong_ban pb ON nv.ma_phong_ban = pb.ma_pb
"""

EMPLOYEE_SELECT_SQL = "SELECT " + EMPLOYEE_COLUMNS_SQL + EMPLOYEE_FROM_SQL


EMPLOYEE_MUTABLE_FIELDS = {
    "ho_ten": "ho_ten",
    "cccd": "cccd",
    "sdt": "sdt",
    "luong": "luong",
    "trang_thai": "trang_thai",
    "ma_phong_ban": "ma_phong_ban",
    "ma_ngay_lam": "ma_ngay_lam",
    "chuc_vu": "chuc_vu",
    "ngay_bat_dau": "ngay_bat_dau",
    "ngay_ket_thuc": "ngay_ket_thuc",
}


def format_employee(employee):
    if not employee:
        return None

    employee["luong"] = float(employee["luong"]) if employee["luong"] else 0
    employee["ngay_bat_dau"] = (
        employee["ngay_bat_dau"].isoformat() if employee["ngay_bat_dau"] else None
    )
    employee["ngay_ket_thuc"] = (
        employee["ngay_ket_thuc"].isoformat() if employee["ngay_ket_thuc"] else None
    )
    return employee


def _build_employee_filters(args):
    where = []
    params = []

    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        where.append(
            "(nv.ho_ten LIKE ? OR nv.ma_nhan_vien LIKE ? OR nv.cccd LIKE ? OR nv.sdt LIKE ?)"
        )
        params.extend([like, like, like, like])

    chuc_vu = args.get("chuc_vu")
    if chuc_vu:
        where.append("nv.chuc_vu = ?")
        params.append(chuc_vu)

    trang_thai = args.get("trang_thai")
    if trang_thai not in (None, ""):
        try:
            where.append("nv.trang_thai = ?")
            params.append(int(trang_thai))
        except (TypeError, ValueError):
            raise ValueError("trang_thai phải là số nguyên")

    ma_phong_ban = args.get("ma_phong_ban")
    if ma_phong_ban not in (None, ""):
        try:
            where.append("nv.ma_phong_ban = ?")
            params.append(int(ma_phong_ban))
        except (TypeError, ValueError):
            raise ValueError("ma_phong_ban phải là số nguyên")

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    return where_sql, params


def get_employee_by_id(ma_nhan_vien):
    return query_db(
        EMPLOYEE_SELECT_SQL + " WHERE nv.ma_nhan_vien = ?",
        (ma_nhan_vien,),
        fetchone=True,
    )


def get_employee_by_id_for_api(ma_nhan_vien):
    return format_employee(get_employee_by_id(ma_nhan_vien))


def get_all_employees_for_api(args=None):
    args = args or {}
    where_sql, where_params = _build_employee_filters(args)
    page, limit, offset = parse_pagination(args)

    total_row = query_db(
        "SELECT COUNT(*) AS total " + EMPLOYEE_FROM_SQL + where_sql,
        tuple(where_params),
        fetchone=True,
    )
    total = total_row["total"] if total_row else 0

    employees = query_db(
        EMPLOYEE_SELECT_SQL
        + where_sql
        + " ORDER BY nv.ma_nhan_vien OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
        tuple(where_params) + (offset, limit),
    )
    for employee in employees:
        format_employee(employee)

    return {
        "data": employees,
        "pagination": build_pagination_meta(page, limit, total),
    }


def get_employees_by_department_id_for_api(ma_pb):
    employees = query_db(
        EMPLOYEE_SELECT_SQL
        + """
        WHERE nv.ma_phong_ban = ?
        ORDER BY nv.chuc_vu DESC, nv.ma_nhan_vien
        """,
        (ma_pb,),
    )
    for employee in employees:
        format_employee(employee)
    return employees


def create_employee(data):
    required_fields = ["ma_nhan_vien", "ho_ten", "mat_khau", "ma_phong_ban"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError("Missing required fields: " + ", ".join(missing_fields))

    execute_db(
        """
        INSERT INTO NHAN_VIEN (
            ma_nhan_vien, ho_ten, cccd, sdt, luong, mat_khau, trang_thai,
            ma_phong_ban, ma_ngay_lam, chuc_vu, ngay_bat_dau, ngay_ket_thuc
        )
        VALUES (
            ?, ?, ?, ?, ?,
            CONVERT(NVARCHAR(255), HASHBYTES('SHA2_256', ?), 2),
            ?, ?, ?, ?, ?, ?
        )
        """,
        (
            data["ma_nhan_vien"],
            data["ho_ten"],
            data.get("cccd"),
            data.get("sdt"),
            data.get("luong", 0),
            data["mat_khau"],
            data.get("trang_thai", 1),
            data["ma_phong_ban"],
            data.get("ma_ngay_lam", 0),
            data.get("chuc_vu", "nhan_vien"),
            data.get("ngay_bat_dau"),
            data.get("ngay_ket_thuc"),
        ),
    )

    return get_employee_by_id_for_api(data["ma_nhan_vien"])


def update_employee(ma_nhan_vien, data):
    if not data:
        raise ValueError("Request body is required")

    assignments = []
    params = []

    for field, column in EMPLOYEE_MUTABLE_FIELDS.items():
        if field in data:
            assignments.append(f"{column} = ?")
            params.append(data[field])

    if "mat_khau" in data:
        assignments.append("mat_khau = CONVERT(NVARCHAR(255), HASHBYTES('SHA2_256', ?), 2)")
        params.append(data["mat_khau"])

    if not assignments:
        raise ValueError("No valid fields to update")

    params.append(ma_nhan_vien)
    affected_rows = execute_db(
        f"UPDATE NHAN_VIEN SET {', '.join(assignments)} WHERE ma_nhan_vien = ?",
        tuple(params),
    )

    if affected_rows == 0:
        return None

    return get_employee_by_id_for_api(ma_nhan_vien)


def soft_delete_employee(ma_nhan_vien):
    affected_rows = execute_db(
        """
        UPDATE NHAN_VIEN
        SET trang_thai = 0, ngay_ket_thuc = COALESCE(ngay_ket_thuc, GETDATE())
        WHERE ma_nhan_vien = ?
        """,
        (ma_nhan_vien,),
    )
    return affected_rows > 0


def get_employees_by_branch_for_api(ma_chi_nhanh):
    """
    Lấy danh sách nhân viên theo chi nhánh.
    
    Lưu ý: Schema hiện tại không có kết nối trực tiếp giữa nhân viên và chi nhánh.
    Nhân viên được liên kết với phòng ban, nhưng phòng ban cũng không có chi nhánh.
    Hàm này trả về tất cả nhân viên của hệ thống.
    Để thực hiện thực sự theo chi nhánh, cần cập nhật schema.
    """
    # Kiểm tra chi nhánh tồn tại
    from services.branch_service import get_branch_by_id
    branch = get_branch_by_id(ma_chi_nhanh)
    if not branch:
        return []

    # Hiện tại trả về tất cả nhân viên (không thể lọc theo chi nhánh)
    employees = query_db(
        EMPLOYEE_SELECT_SQL + " ORDER BY nv.ma_nhan_vien"
    )
    for employee in employees:
        format_employee(employee)
    
    return employees


def mask_sensitive_employee_fields(employee, is_admin=False):
    """
    Ẩn các trường nhạy cảm (cccd, sdt, luong) nếu người dùng không phải admin/giam_doc.
    
    Sensitive fields: cccd, sdt, luong
    """
    if not employee or is_admin:
        return employee
    
    # Tạo bản sao để không thay đổi dữ liệu gốc
    masked = dict(employee)
    masked["cccd"] = None
    masked["sdt"] = None
    masked["luong"] = None
    
    return masked


def mask_employees_list(employees, is_admin=False):
    """Ẩn thông tin nhạy cảm cho danh sách nhân viên"""
    return [mask_sensitive_employee_fields(emp, is_admin) for emp in employees]
