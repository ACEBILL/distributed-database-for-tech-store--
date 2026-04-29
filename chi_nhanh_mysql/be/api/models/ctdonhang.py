from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey
 
class CtDonHang(Base):
    __tablename__ = "CT_DON_HANG"
 
    ma_donhang = Column(String(255), ForeignKey("don_hang.ma_donhang"), primary_key=True, index=True)
    ma_sp = Column(String(255), ForeignKey("san_pham.ma_sp"), primary_key=True, index=True)
    so_luong = Column(Integer)
    don_gia = Column(Integer)