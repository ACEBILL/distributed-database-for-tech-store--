import math
import os

import pymysql
import pyodbc
import redis
from flask import current_app


DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 200
SUPPORTED_DB_ENGINES = {"sqlserver", "mysql", "postgresql"}


def normalize_db_engine(engine):
    engine = (engine or "sqlserver").strip().lower()
    if engine not in SUPPORTED_DB_ENGINES:
        raise NotImplementedError(f"Database engine is not supported yet: {engine}")
    return engine


def get_db_engine():
    return normalize_db_engine(current_app.config.get("DB_ENGINE", "sqlserver"))


def _normalize_sql(sql, engine):
    if engine == "mysql":
        return sql.replace("?", "%s")
    return sql


def pagination_clause(order_by, offset, limit, engine=None):
    engine = normalize_db_engine(engine or get_db_engine())
    if engine in {"mysql", "postgresql"}:
        return f" ORDER BY {order_by} LIMIT ? OFFSET ?", (limit, offset)
    return f" ORDER BY {order_by} OFFSET ? ROWS FETCH NEXT ? ROWS ONLY", (
        offset,
        limit,
    )


def now_sql(engine=None):
    engine = normalize_db_engine(engine or get_db_engine())
    return "NOW()" if engine in {"mysql", "postgresql"} else "GETDATE()"


def password_hash_sql(engine=None):
    engine = normalize_db_engine(engine or get_db_engine())
    if engine == "mysql":
        return "UPPER(SHA2(?, 256))"
    return "CONVERT(NVARCHAR(255), HASHBYTES('SHA2_256', CAST(? AS VARCHAR(255))), 2)"


def parse_pagination(args, default_limit=DEFAULT_PAGE_LIMIT, max_limit=MAX_PAGE_LIMIT):
    try:
        page = int(args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        limit = int(args.get("limit", default_limit))
    except (TypeError, ValueError):
        limit = default_limit

    page = max(1, page)
    limit = max(1, min(limit, max_limit))
    offset = (page - 1) * limit
    return page, limit, offset


def build_pagination_meta(page, limit, total):
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": math.ceil(total / limit) if limit else 0,
    }


def get_db_connection():
    engine = get_db_engine()
    if engine == "mysql":
        return pymysql.connect(
            host=current_app.config["DB_HOST"],
            port=int(current_app.config["DB_PORT"]),
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            charset="utf8mb4",
        )

    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={current_app.config['DB_HOST']},{current_app.config['DB_PORT']};"
        f"DATABASE={current_app.config['DB_NAME']};"
        f"UID={current_app.config['DB_USER']};"
        f"PWD={current_app.config['DB_PASSWORD']};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def query_db(sql, params=None, fetchone=False):
    engine = get_db_engine()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = _normalize_sql(sql, engine)
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description] if cursor.description else []

        if fetchone:
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def execute_db(sql, params=None):
    engine = get_db_engine()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = _normalize_sql(sql, engine)
        cursor.execute(sql, params or [])
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def execute_db_fetchone(sql, params=None):
    engine = get_db_engine()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = _normalize_sql(sql, engine)
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description] if cursor.description else []
        row = cursor.fetchone() if cursor.description else None
        conn.commit()
        if row:
            return dict(zip(columns, row))
        if engine == "mysql" and getattr(cursor, "lastrowid", None):
            return {"lastrowid": cursor.lastrowid}
        return None
    finally:
        conn.close()


def get_branch_db_settings(branch_code):
    normalized_code = branch_code.upper().replace("-", "_")
    prefix = f"BRANCH_{normalized_code}_DB_"
    engine = get_branch_db_engine(branch_code)
    default_port = {"mysql": "3306", "postgresql": "5432"}.get(engine, "1433")

    settings = {
        "engine": engine,
        "host": os.getenv(f"{prefix}HOST"),
        "port": os.getenv(f"{prefix}PORT", default_port),
        "name": os.getenv(f"{prefix}NAME"),
        "user": os.getenv(f"{prefix}USER"),
        "password": os.getenv(f"{prefix}PASSWORD"),
    }

    missing_keys = [
        f"{prefix}{key.upper()}"
        for key, value in settings.items()
        if key not in ["engine", "port"] and not value
    ]
    if missing_keys:
        raise ValueError(
            f"Missing database configuration for branch {branch_code}: "
            + ", ".join(missing_keys)
        )

    return settings


def get_branch_db_engine(branch_code):
    normalized_code = branch_code.upper().replace("-", "_")
    engine = os.getenv(f"BRANCH_{normalized_code}_DB_ENGINE", "sqlserver")
    return normalize_db_engine(engine)


def has_branch_db_settings(branch_code):
    try:
        get_branch_db_settings(branch_code)
        return True
    except ValueError:
        return False


def get_branch_db_connection(branch_code):
    settings = get_branch_db_settings(branch_code)
    if settings["engine"] == "mysql":
        return pymysql.connect(
            host=settings["host"],
            port=int(settings["port"]),
            user=settings["user"],
            password=settings["password"],
            database=settings["name"],
            charset="utf8mb4",
        )
    if settings["engine"] == "postgresql":
        raise NotImplementedError("PostgreSQL branch connection is not implemented yet")

    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={settings['host']},{settings['port']};"
        f"DATABASE={settings['name']};"
        f"UID={settings['user']};"
        f"PWD={settings['password']};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def query_branch_db(branch_code, sql, params=None, fetchone=False):
    engine = get_branch_db_engine(branch_code)
    conn = get_branch_db_connection(branch_code)
    try:
        cursor = conn.cursor()
        sql = _normalize_sql(sql, engine)
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description] if cursor.description else []

        if fetchone:
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def execute_branch_db(branch_code, sql, params=None):
    engine = get_branch_db_engine(branch_code)
    conn = get_branch_db_connection(branch_code)
    try:
        cursor = conn.cursor()
        sql = _normalize_sql(sql, engine)
        cursor.execute(sql, params or [])
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def get_redis_connection():
    return redis.Redis(
        host=current_app.config["REDIS_HOST"],
        port=current_app.config["REDIS_PORT"],
        decode_responses=True,
    )
