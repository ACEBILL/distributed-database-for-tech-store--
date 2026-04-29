from sqlalchemy.orm import Session
from api.models.sanpham import SanPham
from api.schemas.sanpham_schemas import SanPhamCreate, SanPhamUpdate


class SanPhamService:

    @staticmethod
    def get_all(db: Session):
        return db.query(SanPham).all()

    @staticmethod
    def get_by_id(db: Session, ma_sp):
        return db.query(SanPham).filter(SanPham.ma_sp == ma_sp).first()
