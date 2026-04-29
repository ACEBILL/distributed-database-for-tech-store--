from sqlalchemy.orm import Session
from api.models.danhmuc import DanhMuc
from api.schemas.danhmuc_schemas import DanhMucCreate, DanhMucUpdate


class DanhMucService:

    @staticmethod
    def get_all(db: Session):
        return db.query(DanhMuc).all()

    @staticmethod
    def get_by_id(db: Session, danh_muc_id):
        return db.query(DanhMuc).filter(DanhMuc.danh_muc_id == danh_muc_id).first()
