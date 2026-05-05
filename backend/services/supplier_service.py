from db import (
    build_pagination_meta,
    execute_db,
    execute_db_fetchone,
    get_db_engine,
    pagination_clause,
    parse_pagination,
    query_db,
)


def _build_supplier_filters(args):
    where = []
    params = []

    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        where.append("ten_NCC LIKE ?")
        params.append(like)

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    return where_sql, params


def get_all_suppliers_for_api(args=None):
    args = args or {}
    where_sql, where_params = _build_supplier_filters(args)
    page, limit, offset = parse_pagination(args)

    total_row = query_db(
        "SELECT COUNT(*) AS total FROM NCC" + where_sql,
        tuple(where_params),
        fetchone=True,
    )
    total = total_row["total"] if total_row else 0

    page_clause, page_params = pagination_clause("ma_NCC", offset, limit)
    suppliers = query_db(
        "SELECT ma_NCC AS ma_ncc, ten_NCC AS ten_ncc FROM NCC"
        + where_sql
        + page_clause,
        tuple(where_params) + page_params,
    )

    return {
        "data": suppliers,
        "pagination": build_pagination_meta(page, limit, total),
    }


def get_supplier_by_id_for_api(ma_ncc):
    return query_db(
        """
        SELECT ma_NCC AS ma_ncc, ten_NCC AS ten_ncc
        FROM NCC
        WHERE ma_NCC = ?
        """,
        (ma_ncc,),
        fetchone=True,
    )


def create_supplier(data):
    if not data.get("ten_ncc"):
        raise ValueError("Missing required field: ten_ncc")

    if get_db_engine() == "mysql":
        row = execute_db_fetchone(
            "INSERT INTO NCC (ten_NCC) VALUES (?)",
            (data["ten_ncc"],),
        )
        return get_supplier_by_id_for_api(row["lastrowid"])

    return execute_db_fetchone(
        """
        INSERT INTO NCC (ten_NCC)
        OUTPUT INSERTED.ma_NCC AS ma_ncc, INSERTED.ten_NCC AS ten_ncc
        VALUES (?)
        """,
        (data["ten_ncc"],),
    )


def update_supplier(ma_ncc, data):
    if not data:
        raise ValueError("Request body is required")
    if "ten_ncc" not in data:
        raise ValueError("No valid fields to update")
    if not data["ten_ncc"]:
        raise ValueError("ten_ncc cannot be empty")

    affected_rows = execute_db(
        "UPDATE NCC SET ten_NCC = ? WHERE ma_NCC = ?",
        (data["ten_ncc"], ma_ncc),
    )
    if affected_rows == 0:
        return None
    return get_supplier_by_id_for_api(ma_ncc)


def delete_supplier(ma_ncc):
    affected_rows = execute_db(
        "DELETE FROM NCC WHERE ma_NCC = ?",
        (ma_ncc,),
    )
    return affected_rows > 0
