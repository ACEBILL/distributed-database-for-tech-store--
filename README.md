# Dự án CSDL phân tán - Backend API quản lý chi nhánh

Project dùng Flask API, SQL Server và Redis. Backend hiện chỉ trả JSON cho API client, không còn render HTML template.

## Yêu cầu

- Docker Desktop đang chạy
- Git

## Setup

Windows CMD:

```cmd
copy .env.example .env
docker compose up -d --build
```

PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

Linux/macOS/Git Bash:

```bash
cp .env.example .env
docker compose up -d --build
```

## Truy cập

| Service | URL / Host | Ghi chú |
|---|---|---|
| Frontend | http://localhost:3000 | Giao diện client |
| Backend API | http://localhost:5000 | Flask API |
| SQL Server | localhost,1433 | `sa` / `MyPass@2025` mặc định |
| Redis | localhost:6379 | Cache |

## API endpoints

| Endpoint | Mô tả |
|---|---|
| `GET /api/san-pham` | Danh sách sản phẩm đang bán, có cache Redis |
| `GET /api/nhan-vien` | Danh sách nhân viên |
| `GET /api/thong-ke` | Danh sách chi nhánh và trạng thái cấu hình DB chi nhánh |

## Cấu trúc project

```text
├── docker-compose.yml
├── .env.example
├── init/mssql/
│   └── 01-schema-and-data.sql
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py
    ├── config.py
    ├── db.py
    ├── api/
    │   ├── employee_api.py
    │   ├── product_api.py
    │   └── stats_api.py
    ├── services/
    │   ├── branch_service.py
    │   ├── cache_service.py
    │   ├── employee_service.py
    │   └── product_service.py
    └── middleware/
        └── error_handler.py
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── templates/
    │   └── index.html
    └── static/
        ├── css/style.css
        └── js/app.js
```

## Cấu hình DB chi nhánh

DB trung tâm chỉ lưu mã và tên chi nhánh. Thông tin kết nối DB chi nhánh để trong `.env`.

```env
BRANCH_CN01_DB_HOST=
BRANCH_CN01_DB_ENGINE=sqlserver
BRANCH_CN01_DB_PORT=1433
BRANCH_CN01_DB_NAME=
BRANCH_CN01_DB_USER=
BRANCH_CN01_DB_PASSWORD=

BRANCH_CN02_DB_HOST=
BRANCH_CN02_DB_ENGINE=sqlserver
BRANCH_CN02_DB_PORT=1433
BRANCH_CN02_DB_NAME=
BRANCH_CN02_DB_USER=
BRANCH_CN02_DB_PASSWORD=
```

`BRANCH_CNxx_DB_ENGINE` dùng để frontend/API biết chi nhánh đó dùng hệ CSDL nào. Giá trị dự kiến:

```text
sqlserver
postgresql
mysql
```

Hiện backend mới có driver kết nối SQL Server. Nếu một chi nhánh dùng PostgreSQL hoặc MySQL, cần cài thêm driver Python và viết thêm hàm kết nối tương ứng trước khi query dữ liệu thật.

Nếu chưa cấu hình DB chi nhánh, `/api/thong-ke` vẫn trả tên chi nhánh nhưng `trang_thai_ket_noi` là `not_configured`.

## Lệnh thường dùng

```bash
docker compose up -d --build
docker compose up -d
docker compose down
docker compose down -v
docker compose ps
docker compose logs -f frontend
docker compose logs -f backend
docker compose logs -f sqlserver
```

Reset database hoàn toàn:

```bash
docker compose down -v
docker compose up -d --build
```
