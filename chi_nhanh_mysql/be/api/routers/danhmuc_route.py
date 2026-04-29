from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from api.schemas.danhmuc_schemas import DanhMucResponse
from api.services.danhmuc_service import DanhMucService

router = APIRouter(
    prefix="/danhmuc",
    tags=["Danh mục"]
)

@router.get("/", response_model=list[DanhMucResponse])
def get_all_danhmuc(db: Session = Depends(get_db)):
    return DanhMucService.get_all(db)

@router.get("/{danh_muc_id}", response_model=DanhMucResponse)
def get_danhmuc_by_id(danh_muc_id: str, db: Session = Depends(get_db)):
    dm = DanhMucService.get_by_id(db, danh_muc_id)
    if not dm:
        raise HTTPException(status_code=404, detail="Danh mục không tồn tại")
    return dm
