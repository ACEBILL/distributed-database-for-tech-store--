from database import Base
from sqlalchemy import Column, String, DateTime, ForeignKey

class DonHang(Base):
    __tablename__ = "DON_HANG"
 
    ma_donhang = Column(String(255), primary_key=True, index=True)
    trang_thai = Column(String(255))
    thoi_gian_dat = Column(DateTime)
    thoi_gian_hoan_thanh = Column(DateTime)
    phuong_thuc_thanh_toan = Column(String(50))
    ma_kh = Column(String(255), ForeignKey("KHACH_HANG.ma_kh"))
    ma_nhan_vien = Column(String(255), ForeignKey("NHAN_VIEN.ma_nhan_vien"))
 