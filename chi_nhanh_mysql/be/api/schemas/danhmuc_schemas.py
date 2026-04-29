from pydantic import BaseModel


class DanhMucCreate(BaseModel):
    danh_muc_id: str
    ten_danh_muc: str
    status: int


class DanhMucUpdate(BaseModel):
    ten_danh_muc: str | None = None
    status: int | None = None


class DanhMucResponse(BaseModel):
    danh_muc_id: str
    ten_danh_muc: str
    status: int

    class Config:
        from_attributes = True
