from pydantic import BaseModel

class KhachHangCreate(BaseModel):
    ma_kh: str
    ten_kh: str
    sdt: str


class KhachHangUpdate(BaseModel):
    ten_kh: str | None = None
    sdt: str | None = None


class KhachHangResponse(BaseModel):
    ma_kh: str
    ten_kh: str
    sdt: str

    class Config:
        from_attributes = True
