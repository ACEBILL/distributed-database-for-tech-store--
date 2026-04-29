from database import Base
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey

class SanPham(Base):
   __tablename__ = "SAN_PHAM"

   ma_sp = Column(String(255), primary_key=True, index=True)
   ten_sp = Column(String(255))
   sl_ton_kho = Column(Integer)
   gia = Column(Numeric)
   ti_le_loi_nhuan = Column(Numeric)
   ti_le_giam_gia = Column(Numeric)
   mo_ta = Column(String(255))
   danh_muc_id = Column(String(255), ForeignKey("danh_muc.danh_muc_id"))
   ma_ncc = Column(Integer, ForeignKey("ncc.ma_ncc"))
   trang_thai = Column(Integer)
   da_tao_vao = Column(DateTime)
   da_cap_nhat_vao = Column(DateTime)