# Chi nhánh MySQL

## Cách chạy
B1: python -m venv .venv
B2: Khởi động môi trường ảo (Chú ý nếu termial có sẵn (.venv) hoặc xài Pycharm thì không cần )
B3: pip install -r requirements.txt

# TechStore Chi Nhánh - API Documentation

Base URL: `http://localhost:8000`

---

## Nhân viên `/nhanvien`

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/nhanvien/` | Lấy danh sách tất cả nhân viên |
| GET | `/nhanvien/{ma_nhan_vien}` | Lấy nhân viên theo mã |
| POST | `/nhanvien/login` | Đăng nhập nhân viên |

---

## Khách hàng `/khachhang`

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/khachhang/` | Lấy danh sách tất cả khách hàng |
| GET | `/khachhang/{ma_kh}` | Lấy khách hàng theo mã |

---

## Sản phẩm `/sanpham`

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/sanpham/` | Lấy danh sách tất cả sản phẩm |
| GET | `/sanpham/{ma_sp}` | Lấy sản phẩm theo mã |

---

## Danh mục `/danhmuc`

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/danhmuc/` | Lấy danh sách tất cả danh mục |
| GET | `/danhmuc/{danh_muc_id}` | Lấy danh mục theo mã |

---

## Nhà cung cấp `/ncc`

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/ncc/` | Lấy danh sách tất cả nhà cung cấp |
| GET | `/ncc/{ma_ncc}` | Lấy nhà cung cấp theo mã |

---

## Đơn hàng `/donhang`

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/donhang/` | Lấy danh sách tất cả đơn hàng |
| GET | `/donhang/{ma_donhang}` | Lấy đơn hàng theo mã |
| POST | `/donhang/tao-don-hang` | Tạo đơn hàng mới (tự động tạo khách hàng nếu chưa có) |

### Body `POST /donhang/tao-don-hang`
```json
{
  "ma_donhang": "string",
  "trang_thai": "string",
  "thoi_gian_dat": "2026-01-01T00:00:00Z",
  "thoi_gian_hoan_thanh": "2026-01-01T00:00:00Z",
  "phuong_thuc_thanh_toan": "string",
  "ma_kh": "string",
  "ten_kh": "string",
  "sdt": "string",
  "ma_nhan_vien": "string"
}
```

---

## Chi tiết đơn hàng `/ctdonhang`

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/ctdonhang/` | Lấy danh sách tất cả chi tiết đơn hàng |
| GET | `/ctdonhang/{ma_donhang}/{ma_sp}` | Lấy chi tiết đơn hàng theo mã đơn và mã sản phẩm |
