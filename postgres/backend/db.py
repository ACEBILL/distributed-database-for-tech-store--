import math
import os

import psycopg
import redis
from flask import current_app


DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 200


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


def _normalize_sql(sql):
    return sql.replace("?", "%s")


def get_db_connection():
    return psycopg.connect(
        host=current_app.config["DB_HOST"],
        port=int(current_app.config["DB_PORT"]),
        user=current_app.config["DB_USER"],
        password=current_app.config["DB_PASSWORD"],
        dbname=current_app.config["DB_NAME"],
    )


def query_db(sql, params=None, fetchone=False):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(_normalize_sql(sql), params or [])
        columns = [col[0] for col in cursor.description] if cursor.description else []

        if fetchone:
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def execute_db(sql, params=None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(_normalize_sql(sql), params or [])
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def execute_db_fetchone(sql, params=None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(_normalize_sql(sql), params or [])
        columns = [col[0] for col in cursor.description] if cursor.description else []
        row = cursor.fetchone() if cursor.description else None
        conn.commit()
        return dict(zip(columns, row)) if row else None
    finally:
        conn.close()


def get_branch_db_settings(branch_code):
    normalized_code = branch_code.upper().replace("-", "_")
    prefix = f"BRANCH_{normalized_code}_DB_"

    settings = {
        "engine": get_branch_db_engine(branch_code),
        "host": os.getenv(f"{prefix}HOST"),
        "port": os.getenv(f"{prefix}PORT", "5432"),
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
    engine = os.getenv(f"BRANCH_{normalized_code}_DB_ENGINE", "postgresql")
    return engine.strip().lower()


def has_branch_db_settings(branch_code):
    try:
        get_branch_db_settings(branch_code)
        return True
    except ValueError:
        return False


def get_branch_db_connection(branch_code):
    settings = get_branch_db_settings(branch_code)
    if settings["engine"] != "postgresql":
        raise NotImplementedError(
            f"Branch database engine is not supported yet: {settings['engine']}"
        )

    return psycopg.connect(
        host=settings["host"],
        port=int(settings["port"]),
        user=settings["user"],
        password=settings["password"],
        dbname=settings["name"],
    )


def query_branch_db(branch_code, sql, params=None, fetchone=False):
    conn = get_branch_db_connection(branch_code)
    try:
        cursor = conn.cursor()
        cursor.execute(_normalize_sql(sql), params or [])
        columns = [col[0] for col in cursor.description] if cursor.description else []

        if fetchone:
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_redis_connection():
    return redis.Redis(
        host=current_app.config["REDIS_HOST"],
        port=current_app.config["REDIS_PORT"],
        decode_responses=True,
    )
