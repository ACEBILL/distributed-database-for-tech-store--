from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

from api.models.nhanvien import NhanVien

SECRET_KEY = "thanh_dzai_sieu_cap_vu_tru"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:

    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(passwword)
    
    @staticmethod
    def auth_nhanvien(db: Session, ma_nhan_vien, pwd):
        nhanvien = db.query(NhanVien).filter(NhanVien.ma_nhan_vien==ma_nhan_vien, NhanVien.mat_khau==pwd).first()
        return nhanvien

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()

        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})

        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
