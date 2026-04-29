from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/TechStoreDB?charset=utf8mb4"
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db # Setup -> cleanup thay vì close thủ công, giúp đảm bảo rằng kết nối sẽ được đóng đúng cách ngay cả khi có lỗi xảy ra
    finally:
        db.close()