from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from api.schemas.ctdonhang_schemas import CTDonHangResponse
from api.services.ctdonhang_service import CTDonHangService

router = APIRouter(
    prefix="/ctdonhang",
    tags=["Chi tiết đơn hàng"]
)

@router.get("/", response_model=list[CTDonHangResponse])
def get_all_ctdonhang(db: Session = Depends(get_db)):
    return CTDonHangService.get_all(db)

@router.get("/{ma_donhang}/{ma_sp}", response_model=CTDonHangResponse)
def get_ctdonhang_by_id(ma_donhang: str, ma_sp: str, db: Session = Depends(get_db)):
    rec = CTDonHangService.get_by_id(db, ma_donhang, ma_sp)
    if not rec:
        raise HTTPException(status_code=404, detail="Chi tiết đơn hàng không tồn tại")
    return rec
