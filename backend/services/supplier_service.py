from db import execute_db, execute_db_fetchone, query_db


def get_all_suppliers_for_api():
    return query_db("""
        SELECT ma_NCC AS ma_ncc, ten_NCC AS ten_ncc
        FROM NCC
        ORDER BY ma_NCC
    """)


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
