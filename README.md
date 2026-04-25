# Dự án CSDL Phân Tán - Quản lý Chi nhánh

## Yêu cầu

- **Docker Desktop** đã cài và đang chạy
- **Git** để clone repo

---

## Setup (3 bước)

```bash
git clone <url-repo>
cp .env.example .env
docker compose up -d --build
```

Lần đầu mất ~2-3 phút (tải SQL Server image + build Flask). Các lần sau vài giây.

---

## Truy cập

| Service        | URL / Host           | Ghi chú                            |
|----------------|----------------------|------------------------------------|
| **Flask Web**  | http://localhost:5000| Giao diện chính                    |
| SQL Server     | localhost:1433       | user: sa / pass: YourStr0ng!Pass   |
| Redis          | localhost:6379       |                                    |

### API endpoints

| Endpoint        | Mô tả                              |
|-----------------|-------------------------------------|
| `/api/san-pham` | JSON danh sách sản phẩm (có cache) |
| `/api/thong-ke` | JSON thống kê chi nhánh            |

### Kết nối SQL Server bằng SSMS / Azure Data Studio

```
Server:   localhost,1433
Login:    sa
Password: YourStr0ng!Pass
Database: quan_ly_chi_nhanh
```

### Kết nối qua terminal

```bash
docker compose exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourStr0ng!Pass" -C -d quan_ly_chi_nhanh
```

---

## Cấu trúc project

```
├── docker-compose.yml
├── .env.example
├── init/mssql/
│   └── 01-schema-and-data.sql    ← Schema + dummy data (T-SQL)
└── flask-app/
    ├── Dockerfile                ← Có cài ODBC driver
    ├── requirements.txt          ← pyodbc thay pymysql
    ├── app.py                    ← Routes chính
    ├── db.py                     ← Kết nối SQL Server + Redis
    ├── templates/                ← Giao diện HTML
    └── static/css/style.css
```

---

## Dữ liệu dummy có sẵn

| Bảng         | Số bản ghi | Mô tả                      |
|--------------|-----------|------------------------------|
| chi_nhanh    | 5         | HN, HCM, ĐN, CT, HP        |
| loai_sp      | 10        | Laptop, Phone, Phụ kiện...  |
| NCC          | 8         | Apple, Samsung, Dell...     |
| SAN_PHAM     | 25        | Sản phẩm tech có giá VNĐ   |
| phong_ban    | 6         | BGĐ, KD, KT, Kho, NS, KT  |
| NHAN_VIEN    | 20        | Đủ chức vụ, 1 NV đã nghỉ   |

---

## Lệnh thường dùng

```bash
docker compose up -d --build      # Bật (build lại Flask nếu sửa Dockerfile)
docker compose up -d              # Bật nhanh
docker compose down               # Tắt (giữ data)
docker compose down -v            # Tắt + xóa data (reset hoàn toàn)
docker compose logs -f flask-app  # Xem log Flask
docker compose logs -f sqlserver  # Xem log SQL Server
```

**Hot reload:** Flask bật debug mode + volume mount → sửa code Python tự restart.

---

## Lưu ý SQL Server

- SQL Server bắt buộc phải có password mạnh (chữ hoa + chữ thường + số + ký tự đặc biệt, ≥8 ký tự). Không thể bỏ password như MySQL.
- Image SQL Server khá nặng (~1.5GB lần tải đầu), nhưng chỉ tải 1 lần.
- Dùng NVARCHAR thay VARCHAR để hỗ trợ tiếng Việt đầy đủ.

---

## Xử lý lỗi

**Port bị trùng:** Sửa `.env`, đổi port, chạy lại `docker compose up -d`

**Reset toàn bộ:** `docker compose down -v` rồi `docker compose up -d --build`

**Flask lỗi kết nối:** SQL Server cần ~30s để sẵn sàng. `docker compose restart flask-app`
