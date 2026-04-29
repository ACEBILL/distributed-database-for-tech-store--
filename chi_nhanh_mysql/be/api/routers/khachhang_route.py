from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from api.schemas.khachhang_schemas import KhachHangResponse
from api.services.khachhang_service import KhachHangService

router = APIRouter(
    prefix="/khachhang",
    tags=["Khách hàng"]
)

@router.get("/", response_model=list[KhachHangResponse])
def get_all_khachhang(db: Session = Depends(get_db)):
    return KhachHangService.get_all(db)

@router.get("/{ma_kh}", response_model=KhachHangResponse)
def get_khachhang_by_id(ma_kh: str, db: Session = Depends(get_db)):
    kh = KhachHangService.get_by_id(db, ma_kh)
    if not kh:
        raise HTTPException(status_code=404, detail="Khách hàng không tồn tại")
    return kh
