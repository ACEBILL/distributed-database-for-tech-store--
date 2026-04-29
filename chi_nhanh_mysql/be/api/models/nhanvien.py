from database import Base
from sqlalchemy import Column, Integer, String, Numeric
class NhanVien(Base):
    __tablename__ = "NHAN_VIEN"
 
    ma_nhan_vien = Column(String(255), primary_key=True, index=True)
    ho_ten = Column(String(255))
    cccd = Column(String(255))
    sdt = Column(String(255))
    luong = Column(Numeric)
    trang_thai = Column(Integer)
    mat_khau = Column(String(255))
 