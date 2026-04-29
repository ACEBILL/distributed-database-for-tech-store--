from database import Base
from sqlalchemy import Column, String

class KhachHang(Base):
   __tablename__ = "KHACH_HANG"

   ma_kh = Column(String(255), primary_key=True, index=True)
   ten_kh = Column(String(255))
   sdt = Column(String(255))

