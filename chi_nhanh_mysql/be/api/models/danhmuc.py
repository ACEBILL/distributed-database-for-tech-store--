from database import Base
from sqlalchemy import Column, Integer, String
 
class DanhMuc(Base):
    __tablename__ = "DANH_MUC"
 
    danh_muc_id = Column(String(255), primary_key=True, index=True)
    ten_danh_muc = Column(String(255))
    status = Column(Integer)