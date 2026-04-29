from pydantic import BaseModel
from datetime import datetime


class DonHangCreate(BaseModel):
    ma_donhang: str
    trang_thai: str 
    thoi_gian_dat: datetime 
    thoi_gian_hoan_thanh: datetime 
    phuong_thuc_thanh_toan: str 
    ma_kh: str 
    ma_nhan_vien: str 


class DonHangUpdate(BaseModel):
    trang_thai: str | None = None
    thoi_gian_dat: datetime | None = None
    thoi_gian_hoan_thanh: datetime | None = None
    phuong_thuc_thanh_toan: str | None = None
    ma_kh: str | None = None
    ma_nhan_vien: str | None = None


class DonHangResponse(BaseModel):
    ma_donhang: str
    trang_thai: str
    thoi_gian_dat: datetime | None = None
    thoi_gian_hoan_thanh: datetime | None = None
    phuong_thuc_thanh_toan: str
    ma_kh: str
    ma_nhan_vien: str

    class Config:
        from_attributes = True

class TaoDonHangRequest(BaseModel):
    ma_donhang: str
    trang_thai: str 
    thoi_gian_dat: datetime 
    thoi_gian_hoan_thanh: datetime 
    phuong_thuc_thanh_toan: str 
    ma_khachhang: str
    ten_khachhang: str
    sdt_khachhang: str
    ma_nhan_vien: str

class TaoDonHangResponse(BaseModel):
    ma_donhang: str
    trang_thai: str
    thoi_gian_dat: datetime | None = None
    thoi_gian_hoan_thanh: datetime | None = None
    phuong_thuc_thanh_toan: str
    trang_thai: str