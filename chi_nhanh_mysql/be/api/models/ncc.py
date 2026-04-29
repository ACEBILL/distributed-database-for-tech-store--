from database import Base
from sqlalchemy import Column, Integer, String

class NCC(Base):
    __tablename__ = "NCC"

    ma_ncc = Column(Integer, primary_key=True, index=True)
    ten_ncc = Column(String(255))