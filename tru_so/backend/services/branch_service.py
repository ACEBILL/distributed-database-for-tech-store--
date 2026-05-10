from db import (
    build_pagination_meta,
    execute_db,
    get_branch_db_engine,
    has_branch_db_settings,
    pagination_clause,
    parse_pagination,
    query_branch_db,
    query_db,
)


def get_branches():
    return query_db("""
        SELECT ma_chi_nhanh, ten_chi_nhanh
        FROM chi_nhanh
        ORDER BY ma_chi_nhanh
    """)


def _build_branch_filters(args):
    where = []
    params = []

    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        where.append("(ma_chi_nhanh LIKE ? OR ten_chi_nhanh LIKE ?)")
        params.extend([like, like])

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    return where_sql, params


def get_branches_for_api(args=None):
    args = args or {}
    where_sql, where_params = _build_branch_filters(args)
    page, limit, offset = parse_pagination(args)

    total_row = query_db(
        "SELECT COUNT(*) AS total FROM chi_nhanh" + where_sql,
        tuple(where_params),
        fetchone=True,
    )
    total = total_row["total"] if total_row else 0

    page_clause, page_params = pagination_clause("ma_chi_nhanh", offset, limit)
    branches = query_db(
        "SELECT ma_chi_nhanh, ten_chi_nhanh FROM chi_nhanh"
        + where_sql
        + page_clause,
        tuple(where_params) + page_params,
    )

    return {
        "data": branches,
        "pagination": build_pagination_meta(page, limit, total),
    }


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


def get_products_by_branch_for_api(ma_chi_nhanh):
    branch = get_branch_by_id(ma_chi_nhanh)
    if not branch:
        return []

    products = query_db(
        """
        SELECT *
        FROM v_san_pham_theo_chi_nhanh
        WHERE ma_chi_nhanh = ?
        ORDER BY ma_sp
        """,
        (ma_chi_nhanh,),
    )

    for product in products:
        for field in ["gia", "ti_le_loi_nhuan", "ti_le_giam_gia", "gia_ban_thuc_te"]:
            if field in product:
                product[field] = float(product[field]) if product[field] else 0

    return products


def get_fragmentation_stats_for_api():
    """Thống kê phân mảnh ngang: số bản ghi NHAN_VIEN và san_pham trên từng node."""
    nodes = {}

    try:
        sp_row = query_db("SELECT COUNT(*) AS cnt FROM san_pham", fetchone=True)
        nv_row = query_db("SELECT COUNT(*) AS cnt FROM NHAN_VIEN", fetchone=True)
        nodes["tru_so"] = {
            "ten_node": "Trụ sở",
            "db_engine": "sqlserver",
            "so_san_pham": int(sp_row["cnt"]) if sp_row else 0,
            "so_nhan_vien": int(nv_row["cnt"]) if nv_row else 0,
            "status": "ok",
        }
    except Exception as exc:
        nodes["tru_so"] = {
            "ten_node": "Trụ sở",
            "db_engine": "sqlserver",
            "so_san_pham": 0,
            "so_nhan_vien": 0,
            "status": "unreachable",
            "error": str(exc),
        }

    for branch in get_branches():
        ma = branch["ma_chi_nhanh"]
        engine = get_branch_db_engine(ma)
        node = {"ten_node": branch["ten_chi_nhanh"], "db_engine": engine}
        if not has_branch_db_settings(ma):
            node.update({"so_san_pham": 0, "so_nhan_vien": 0, "status": "not_configured"})
            nodes[ma] = node
            continue
        try:
            sp_row = query_branch_db(ma, "SELECT COUNT(*) AS cnt FROM san_pham", fetchone=True)
            nv_row = query_branch_db(ma, "SELECT COUNT(*) AS cnt FROM NHAN_VIEN", fetchone=True)
            node.update({
                "so_san_pham": int(sp_row["cnt"]) if sp_row else 0,
                "so_nhan_vien": int(nv_row["cnt"]) if nv_row else 0,
                "status": "ok",
            })
        except Exception as exc:
            node.update({"so_san_pham": 0, "so_nhan_vien": 0, "status": "unreachable", "error": str(exc)})
        nodes[ma] = node

    return {
        "fragmentation_type": "horizontal",
        "description": (
            "Mỗi node lưu phân mảnh ngang riêng của NHAN_VIEN và san_pham. "
            "Trụ sở dùng SQL Server, chi nhánh dùng MySQL/PostgreSQL."
        ),
        "nodes": nodes,
    }


def check_branch_health(ma_chi_nhanh):
    branch = get_branch_by_id(ma_chi_nhanh)
    if not branch:
        return None

    engine = get_branch_db_engine(ma_chi_nhanh)
    result = {
        "ma_chi_nhanh": branch["ma_chi_nhanh"],
        "ten_chi_nhanh": branch["ten_chi_nhanh"],
        "he_quan_tri_csdl": engine,
        "status": "unknown",
        "error": None,
    }

    if not has_branch_db_settings(ma_chi_nhanh):
        result["status"] = "not_configured"
        return result

    try:
        query_branch_db(ma_chi_nhanh, "SELECT 1 AS ok", fetchone=True)
        result["status"] = "ok"
    except Exception as exc:
        result["status"] = "unreachable"
        result["error"] = str(exc)

    return result
