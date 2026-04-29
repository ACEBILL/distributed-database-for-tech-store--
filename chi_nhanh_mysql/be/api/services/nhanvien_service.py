from sqlalchemy.orm import Session
from api.models.nhanvien import NhanVien
from api.schemas.nhanvien_schemas import NhanVienCreate, NhanVienUpdate


class NhanVienService:

    @staticmethod
    def get_all(db: Session):
        return db.query(NhanVien).all()

    @staticmethod
    def get_by_id(db: Session, ma_nhan_vien):
        return db.query(NhanVien).filter(NhanVien.ma_nhan_vien == ma_nhan_vien).first()
