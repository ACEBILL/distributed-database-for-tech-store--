from pydantic import BaseModel
from datetime import datetime


class SanPhamCreate(BaseModel):
    ma_sp: str
    ten_sp: str
    sl_ton_kho: int
    gia: float
    ti_le_loi_nhuan: float
    ti_le_giam_gia: float
    mo_ta: str 
    danh_muc_id: str 
    ma_ncc: int 
    trang_thai: int 
    da_tao_vao: datetime 
    da_cap_nhat_vao: datetime 


class SanPhamUpdate(BaseModel):
    ten_sp: str | None = None
    sl_ton_kho: int | None = None
    gia: float | None = None
    ti_le_loi_nhuan: float | None = None
    ti_le_giam_gia: float | None = None
    mo_ta: str | None = None
    danh_muc_id: str | None = None
    ma_ncc: int | None = None
    trang_thai: int | None = None
    da_tao_vao: datetime | None = None
    da_cap_nhat_vao: datetime | None = None


class SanPhamResponse(BaseModel):
    ma_sp: str
    ten_sp: str
    sl_ton_kho: int
    gia: float
    ti_le_loi_nhuan: float
    ti_le_giam_gia: float
    mo_ta: str 
    danh_muc_id: str 
    ma_ncc: int 
    trang_thai: int 
    da_tao_vao: datetime 
    da_cap_nhat_vao: datetime 

    class Config:
        from_attributes = True
