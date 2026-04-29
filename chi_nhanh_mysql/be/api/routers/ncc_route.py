from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from api.schemas.ncc_schemas import NCCCreate, NCCUpdate, NCCResponse
from api.services.ncc_service import NCCService

router = APIRouter(
    prefix="/ncc",
    tags=["Nhà cung cấp"]
)

@router.get("/", response_model=list[NCCResponse])
def get_all_ncc(db: Session = Depends(get_db)):
    return NCCService.get_all(db)

@router.get("/{ma_ncc}", response_model=NCCResponse)
def get_ncc_by_id(ma_ncc: int, db: Session = Depends(get_db)):
    ncc = NCCService.get_by_id(db, ma_ncc)
    if not ncc:
        raise HTTPException(status_code=404, detail="Nhà cung cấp không tồn tại")
    return ncc