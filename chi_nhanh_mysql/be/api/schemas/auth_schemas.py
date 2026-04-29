from pydantic import BaseModel

class LoginRequest(BaseModel):
    nhanvien_id: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"