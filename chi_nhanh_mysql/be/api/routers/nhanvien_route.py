from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db

from api.schemas.nhanvien_schemas import NhanVienResponse
from api.schemas.auth_schemas import LoginRequest, LoginResponse

from api.services.nhanvien_service import NhanVienService
from api.services.auth_service import AuthService
router = APIRouter(
    prefix="/nhanvien",
    tags=["Nhân viên"]
)

@router.get("/", response_model=list[NhanVienResponse])
def get_all_nhanvien(db: Session = Depends(get_db)):
    return NhanVienService.get_all(db)

@router.get("/{ma_nhan_vien}", response_model=NhanVienResponse)
def get_nhanvien_by_id(ma_nhan_vien: str, db: Session = Depends(get_db)):
    nv = NhanVienService.get_by_id(db, ma_nhan_vien)
    if not nv:
        raise HTTPException(status_code=404, detail="Nhân viên không tồn tại")
    return nv

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db = Depends(get_db)):
    nhanvien = AuthService.auth_nhanvien(db, request.nhanvien_id, request.password)
    if not nhanvien:
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")
    
    access_token = AuthService.create_access_token(data={"sub": nhanvien.ma_nhan_vien})
    return LoginResponse(access_token=access_token)