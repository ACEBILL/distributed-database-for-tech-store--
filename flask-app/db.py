import os
import pyodbc
import redis


def get_db():
    """Kết nối SQL Server"""
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.getenv('DB_HOST', 'sqlserver')},{os.getenv('DB_PORT', '1433')};"
        f"DATABASE={os.getenv('DB_NAME', 'quan_ly_chi_nhanh')};"
        f"UID={os.getenv('DB_USER', 'sa')};"
        f"PWD={os.getenv('DB_PASSWORD', 'YourStr0ng!Pass')};"
        "TrustServerCertificate=yes;"
    )
    conn = pyodbc.connect(conn_str)
    return conn


def query_db(sql, params=None, fetchone=False):
    """Helper: chạy query và trả về dict"""
    conn = get_db()
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
    """Helper: chạy INSERT/UPDATE/DELETE"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or [])
        conn.commit()
    finally:
        conn.close()


def get_redis():
    """Kết nối Redis cache"""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True,
    )
