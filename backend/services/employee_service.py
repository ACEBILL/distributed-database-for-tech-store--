from db import query_db


def get_all_employees():
    return query_db("""
        SELECT
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
        FROM NHAN_VIEN nv
        JOIN phong_ban pb ON nv.ma_phong_ban = pb.ma_pb
        ORDER BY pb.ma_pb, nv.chuc_vu DESC
    """)


def get_all_employees_for_api():
    employees = get_all_employees()
    for employee in employees:
        employee["luong"] = float(employee["luong"]) if employee["luong"] else 0
        employee["ngay_bat_dau"] = (
            employee["ngay_bat_dau"].isoformat()
            if employee["ngay_bat_dau"]
            else None
        )
        employee["ngay_ket_thuc"] = (
            employee["ngay_ket_thuc"].isoformat()
            if employee["ngay_ket_thuc"]
            else None
        )
    return employees
