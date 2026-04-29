from pydantic import BaseModel

class CTDonHangCreate(BaseModel):
	ma_donhang: str
	ma_sp: str
	so_luong: int
	don_gia: int

class CTDonHangUpdate(BaseModel):
	ma_sp: str | None = None
	so_luong: int | None = None
	don_gia: int | None = None

class CTDonHangResponse(BaseModel):
	ma_donhang: str
	ma_sp: str
	so_luong: int
	don_gia: int

	class Config:
		from_attributes = True

