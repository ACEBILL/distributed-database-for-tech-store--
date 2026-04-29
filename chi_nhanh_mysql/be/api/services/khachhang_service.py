from sqlalchemy.orm import Session
from api.models.khachhang import KhachHang
from api.schemas.khachhang_schemas import KhachHangCreate, KhachHangUpdate


class KhachHangService:

    @staticmethod
    def get_all(db: Session):
        return db.query(KhachHang).all()

    @staticmethod
    def get_by_id(db: Session, ma_kh):
        return db.query(KhachHang).filter(KhachHang.ma_kh == ma_kh).first()
