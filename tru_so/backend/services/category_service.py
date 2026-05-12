from db import (
    build_pagination_meta,
    execute_branch_db,
    execute_db,
    get_branch_db_engine,
    has_branch_db_settings,
    pagination_clause,
    parse_pagination,
    query_db,
)


def _build_category_filters(args):
    where = []
    params = []

    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        where.append("(ma_loai_sp LIKE ? OR ten_loai_sp LIKE ?)")
        params.extend([like, like])

    ma_chi_nhanh = args.get("ma_chi_nhanh")
    if ma_chi_nhanh:
        where.append("ma_chi_nhanh = ?")
        params.append(ma_chi_nhanh)

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    return where_sql, params


def get_all_categories_for_api(args=None):
    args = args or {}
    where_sql, where_params = _build_category_filters(args)
    page, limit, offset = parse_pagination(args)

    total_row = query_db(
        "SELECT COUNT(*) AS total FROM loai_sp" + where_sql,
        tuple(where_params),
        fetchone=True,
    )
    total = total_row["total"] if total_row else 0

    page_clause, page_params = pagination_clause("ma_loai_sp", offset, limit)
    categories = query_db(
        "SELECT ma_loai_sp, ten_loai_sp, ma_chi_nhanh FROM loai_sp"
        + where_sql
        + page_clause,
        tuple(where_params) + page_params,
    )

    return {
        "data": categories,
        "pagination": build_pagination_meta(page, limit, total),
    }


def get_category_by_id_for_api(ma_loai_sp):
    return query_db(
        """
        SELECT ma_loai_sp, ten_loai_sp, ma_chi_nhanh
        FROM loai_sp
        WHERE ma_loai_sp = ?
        """,
        (ma_loai_sp,),
        fetchone=True,
    )


def _list_configured_branch_codes():
    rows = query_db("SELECT ma_chi_nhanh FROM chi_nhanh ORDER BY ma_chi_nhanh")
    return [
        row["ma_chi_nhanh"]
        for row in rows
        if has_branch_db_settings(row["ma_chi_nhanh"])
    ]


def _category_upsert_sql(engine):
    if engine == "mysql":
        return """
        INSERT INTO loai_sp (ma_loai_sp, ten_loai_sp, ma_chi_nhanh)
        VALUES (?, ?, ?)
        ON DUPLICATE KEY UPDATE
            ten_loai_sp = VALUES(ten_loai_sp),
            ma_chi_nhanh = VALUES(ma_chi_nhanh)
        """

    if engine == "postgresql":
        return """
        INSERT INTO loai_sp (ma_loai_sp, ten_loai_sp, ma_chi_nhanh)
        VALUES (?, ?, ?)
        ON CONFLICT (ma_loai_sp) DO UPDATE SET
            ten_loai_sp = EXCLUDED.ten_loai_sp,
            ma_chi_nhanh = EXCLUDED.ma_chi_nhanh
        """

    return """
    MERGE loai_sp AS target
    USING (
        SELECT ? AS ma_loai_sp, ? AS ten_loai_sp, ? AS ma_chi_nhanh
    ) AS source
    ON target.ma_loai_sp = source.ma_loai_sp
    WHEN MATCHED THEN
        UPDATE SET
            ten_loai_sp = source.ten_loai_sp,
            ma_chi_nhanh = source.ma_chi_nhanh
    WHEN NOT MATCHED THEN
        INSERT (ma_loai_sp, ten_loai_sp, ma_chi_nhanh)
        VALUES (source.ma_loai_sp, source.ten_loai_sp, source.ma_chi_nhanh);
    """


def sync_category_to_branches(category):
    params = (
        category["ma_loai_sp"],
        category["ten_loai_sp"],
        category["ma_chi_nhanh"],
    )

    for branch_code in _list_configured_branch_codes():
        branch_engine = get_branch_db_engine(branch_code)
        execute_branch_db(
            branch_code,
            _category_upsert_sql(branch_engine),
            params,
        )


def delete_category_in_branches(ma_loai_sp):
    for branch_code in _list_configured_branch_codes():
        execute_branch_db(
            branch_code,
            "DELETE FROM loai_sp WHERE ma_loai_sp = ?",
            (ma_loai_sp,),
        )


def create_category(data):
    required_fields = ["ma_loai_sp", "ten_loai_sp", "ma_chi_nhanh"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError("Missing required fields: " + ", ".join(missing_fields))

    execute_db(
        """
        INSERT INTO loai_sp (ma_loai_sp, ten_loai_sp, ma_chi_nhanh)
        VALUES (?, ?, ?)
        """,
        (data["ma_loai_sp"], data["ten_loai_sp"], data["ma_chi_nhanh"]),
    )
    category = get_category_by_id_for_api(data["ma_loai_sp"])
    sync_category_to_branches(category)
    return category


def update_category(ma_loai_sp, data):
    if not data:
        raise ValueError("Request body is required")

    fields = []
    params = []
    for field in ["ten_loai_sp", "ma_chi_nhanh"]:
        if field in data:
            if not data[field]:
                raise ValueError(f"{field} cannot be empty")
            fields.append(f"{field} = ?")
            params.append(data[field])

    if not fields:
        raise ValueError("No valid fields to update")

    params.append(ma_loai_sp)
    affected_rows = execute_db(
        f"UPDATE loai_sp SET {', '.join(fields)} WHERE ma_loai_sp = ?",
        tuple(params),
    )
    if affected_rows == 0:
        return None
    category = get_category_by_id_for_api(ma_loai_sp)
    sync_category_to_branches(category)
    return category


def delete_category(ma_loai_sp):
    affected_rows = execute_db(
        "DELETE FROM loai_sp WHERE ma_loai_sp = ?",
        (ma_loai_sp,),
    )
    if affected_rows == 0:
        return False
    delete_category_in_branches(ma_loai_sp)
    return True
