import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    DB_HOST = os.getenv("DB_HOST", "sqlserver")
    DB_PORT = os.getenv("DB_PORT", "1433")
    DB_USER = os.getenv("DB_USER", "sa")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "MyPass@2025")
    DB_NAME = os.getenv("DB_NAME", "quan_ly_chi_nhanh")

    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
