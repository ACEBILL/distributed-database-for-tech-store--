from db import execute_db, execute_db_fetchone, query_db


DEPARTMENT_SELECT_SQL = """
    SELECT
        ma_pb,
        ten_pb,
        ma_nv
    FROM phong_ban
"""


def get_all_departments_for_api():
    return query_db(DEPARTMENT_SELECT_SQL + " ORDER BY ma_pb")


def get_department_by_id_for_api(ma_pb):
    return query_db(
        DEPARTMENT_SELECT_SQL + " WHERE ma_pb = ?",
        (ma_pb,),
        fetchone=True,
    )


def create_department(data):
    if not data.get("ten_pb"):
        raise ValueError("Missing required field: ten_pb")

    row = execute_db_fetchone(
        """
        INSERT INTO phong_ban (ten_pb, ma_nv)
        OUTPUT INSERTED.ma_pb, INSERTED.ten_pb, INSERTED.ma_nv
        VALUES (?, ?)
        """,
        (data["ten_pb"], data.get("ma_nv")),
    )
    return row


def update_department(ma_pb, data):
    if not data:
        raise ValueError("Request body is required")

    assignments = []
    params = []

    if "ten_pb" in data:
        if not data["ten_pb"]:
            raise ValueError("ten_pb cannot be empty")
        assignments.append("ten_pb = ?")
        params.append(data["ten_pb"])

    if "ma_nv" in data:
        assignments.append("ma_nv = ?")
        params.append(data["ma_nv"])

    if not assignments:
        raise ValueError("No valid fields to update")

    params.append(ma_pb)
    affected_rows = execute_db(
        f"UPDATE phong_ban SET {', '.join(assignments)} WHERE ma_pb = ?",
        tuple(params),
    )

    if affected_rows == 0:
        return None

    return get_department_by_id_for_api(ma_pb)


def delete_department(ma_pb):
    affected_rows = execute_db(
        "DELETE FROM phong_ban WHERE ma_pb = ?",
        (ma_pb,),
    )
    return affected_rows > 0


def get_salary_stats_by_department_for_api():
    stats = query_db("SELECT * FROM v_luong_phong_ban ORDER BY ten_pb")
    for item in stats:
        for field in [
            "tong_luong",
            "luong_trung_binh",
            "luong_thap_nhat",
            "luong_cao_nhat",
        ]:
            item[field] = float(item[field]) if item[field] else 0
    return stats
