from db import build_pagination_meta, execute_db, parse_pagination, query_db


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

    categories = query_db(
        "SELECT ma_loai_sp, ten_loai_sp, ma_chi_nhanh FROM loai_sp"
        + where_sql
        + " ORDER BY ma_loai_sp OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
        tuple(where_params) + (offset, limit),
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
    return get_category_by_id_for_api(data["ma_loai_sp"])


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
    return get_category_by_id_for_api(ma_loai_sp)


def delete_category(ma_loai_sp):
    affected_rows = execute_db(
        "DELETE FROM loai_sp WHERE ma_loai_sp = ?",
        (ma_loai_sp,),
    )
    return affected_rows > 0
