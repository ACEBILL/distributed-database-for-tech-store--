from db import get_branch_db_engine, has_branch_db_settings, query_db


def get_branches():
    return query_db("""
        SELECT ma_chi_nhanh, ten_chi_nhanh
        FROM chi_nhanh
        ORDER BY ma_chi_nhanh
    """)


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
