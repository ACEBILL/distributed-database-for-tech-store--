from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from api.schemas.sanpham_schemas import SanPhamResponse
from api.services.sanpham_service import SanPhamService

router = APIRouter(
    prefix="/sanpham",
    tags=["Sản phẩm"]
)

@router.get("/", response_model=list[SanPhamResponse])
def get_all_sanpham(db: Session = Depends(get_db)):
    return SanPhamService.get_all(db)

@router.get("/{ma_sp}", response_model=SanPhamResponse)
def get_sanpham_by_id(ma_sp: str, db: Session = Depends(get_db)):
    sp = SanPhamService.get_by_id(db, ma_sp)
    if not sp:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    return sp
