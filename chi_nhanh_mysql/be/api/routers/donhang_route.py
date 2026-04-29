from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from api.schemas.donhang_schemas import DonHangResponse, TaoDonHangRequest, TaoDonHangResponse
from api.services.donhang_service import DonHangService

router = APIRouter(
    prefix="/donhang",
    tags=["Đơn hàng"]
)

@router.get("/", response_model=list[DonHangResponse])
def get_all_donhang(db: Session = Depends(get_db)):
    return DonHangService.get_all(db)

@router.get("/{ma_donhang}", response_model=DonHangResponse)
def get_donhang_by_id(ma_donhang: str, db: Session = Depends(get_db)):
    dh = DonHangService.get_by_id(db, ma_donhang)
    if not dh:
        raise HTTPException(status_code=404, detail="Đơn hàng không tồn tại")
    return dh

@router.post("/tao-don-hang", response_model=TaoDonHangResponse)
def post_donhang(request: TaoDonHangRequest, db: Session = Depends(get_db)):
    donhang = DonHangService.create_donhang(db, request)
    if not donhang:
        raise HTTPException(status_code=400, detail="Tạo đơn hàng thất bại")
    return donhang
