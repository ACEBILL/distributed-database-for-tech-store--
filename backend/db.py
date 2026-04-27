import os

import pyodbc
import redis
from flask import current_app


def get_db_connection():
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
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or [])
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
        cursor.execute(sql, params or [])
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def execute_db_fetchone(sql, params=None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description] if cursor.description else []
        row = cursor.fetchone()
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
        "port": os.getenv(f"{prefix}PORT", "1433"),
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
    return engine.strip().lower()


def has_branch_db_settings(branch_code):
    try:
        get_branch_db_settings(branch_code)
        return True
    except ValueError:
        return False


def get_branch_db_connection(branch_code):
    settings = get_branch_db_settings(branch_code)
    if settings["engine"] != "sqlserver":
        raise NotImplementedError(
            f"Branch database engine is not supported yet: {settings['engine']}"
        )

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
    conn = get_branch_db_connection(branch_code)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or [])
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
