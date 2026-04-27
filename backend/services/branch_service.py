from db import execute_db, get_branch_db_engine, has_branch_db_settings, query_db


def get_branches():
    return query_db("""
        SELECT ma_chi_nhanh, ten_chi_nhanh
        FROM chi_nhanh
        ORDER BY ma_chi_nhanh
    """)


def get_branch_by_id(ma_chi_nhanh):
    return query_db(
        """
        SELECT ma_chi_nhanh, ten_chi_nhanh
        FROM chi_nhanh
        WHERE ma_chi_nhanh = ?
        """,
        (ma_chi_nhanh,),
        fetchone=True,
    )


def create_branch(data):
    required_fields = ["ma_chi_nhanh", "ten_chi_nhanh"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError("Missing required fields: " + ", ".join(missing_fields))

    execute_db(
        "INSERT INTO chi_nhanh (ma_chi_nhanh, ten_chi_nhanh) VALUES (?, ?)",
        (data["ma_chi_nhanh"], data["ten_chi_nhanh"]),
    )
    return get_branch_by_id(data["ma_chi_nhanh"])


def update_branch(ma_chi_nhanh, data):
    if not data:
        raise ValueError("Request body is required")
    if "ten_chi_nhanh" not in data:
        raise ValueError("No valid fields to update")
    if not data["ten_chi_nhanh"]:
        raise ValueError("ten_chi_nhanh cannot be empty")

    affected_rows = execute_db(
        "UPDATE chi_nhanh SET ten_chi_nhanh = ? WHERE ma_chi_nhanh = ?",
        (data["ten_chi_nhanh"], ma_chi_nhanh),
    )
    if affected_rows == 0:
        return None
    return get_branch_by_id(ma_chi_nhanh)


def delete_branch(ma_chi_nhanh):
    affected_rows = execute_db(
        "DELETE FROM chi_nhanh WHERE ma_chi_nhanh = ?",
        (ma_chi_nhanh,),
    )
    return affected_rows > 0


def get_branch_stats_for_api():
    branches = get_branches()
    return [
        {
            "ma_chi_nhanh": branch["ma_chi_nhanh"],
            "ten_chi_nhanh": branch["ten_chi_nhanh"],
            "he_quan_tri_csdl": get_branch_db_engine(branch["ma_chi_nhanh"]),
            "trang_thai_ket_noi": (
                "configured"
                if has_branch_db_settings(branch["ma_chi_nhanh"])
                else "not_configured"
            ),
            "data": None,
        }
        for branch in branches
    ]


def get_branch_analysis_for_api():
    stats = query_db("SELECT * FROM v_thong_ke_chi_nhanh ORDER BY ma_chi_nhanh")
    for item in stats:
        item["gia_trung_binh"] = (
            float(item["gia_trung_binh"]) if item["gia_trung_binh"] else 0
        )
    return stats
