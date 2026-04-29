from api import routers
from fastapi import FastAPI

app = FastAPI()

# Thêm router
app.include_router(routers.ncc_route.router)
app.include_router(routers.sanpham_route.router)
app.include_router(routers.donhang_route.router)
app.include_router(routers.khachhang_route.router)
app.include_router(routers.ctdonhang_route.router)
app.include_router(routers.danhmuc_route.router)
app.include_router(routers.nhanvien_route.router)