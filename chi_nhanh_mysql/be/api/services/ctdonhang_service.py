from sqlalchemy.orm import Session
from api.models.ctdonhang import CtDonHang
from api.schemas.ctdonhang_schemas import CTDonHangCreate, CTDonHangUpdate


class CTDonHangService:

    @staticmethod
    def get_all(db: Session):
        return db.query(CtDonHang).all()

    @staticmethod
    def get_by_id(db: Session, ma_donhang, ma_sp):
        return db.query(CtDonHang).filter(CtDonHang.ma_donhang == ma_donhang, CtDonHang.ma_sp == ma_sp).first()
