from pydantic import BaseModel


class NhanVienCreate(BaseModel):
    ma_nhan_vien: str
    ho_ten: str
    cccd: str
    sdt: str
    luong: float
    trang_thai: int
    mat_khau: str


class NhanVienUpdate(BaseModel):
    ho_ten: str | None = None
    cccd: str | None = None
    sdt: str | None = None
    luong: float | None = None
    trang_thai: int | None = None
    mat_khau: str | None = None


class NhanVienResponse(BaseModel):
    ma_nhan_vien: str
    ho_ten: str
    cccd: str
    sdt: str
    luong: float
    trang_thai: int
    mat_khau: str

    class Config:
        from_attributes = True
