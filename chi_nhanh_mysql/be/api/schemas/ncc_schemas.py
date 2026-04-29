# pydantic to valid va parse data  
from pydantic import BaseModel

class NCCCreate(BaseModel):
    ten_ncc: str

class NCCUpdate(BaseModel):
    ten_ncc: str | None = None

class NCCResponse(BaseModel):
    ma_ncc: int
    ten_ncc: str

    class Config: # Lấy attr từ obj
        from_attributes = True