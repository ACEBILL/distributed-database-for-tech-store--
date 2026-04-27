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
| Swagger UI | http://localhost:5000/apidocs | Tài liệu API |
| SQL Server | localhost,1433 | `sa` / `MyPass@2025` mặc định |
| Redis | localhost:6379 | Cache |

## API endpoints

Swagger UI:

```text
http://localhost:5000/apidocs
```

OpenAPI JSON:

```text
http://localhost:5000/apispec_1.json
```

### Hiện đã có

| Endpoint | Mô tả |
|---|---|
| `GET /api/san-pham` | Danh sách sản phẩm đang bán, có cache Redis |
| `GET /api/san-pham/<ma_sp>` | Chi tiết sản phẩm |
| `POST /api/san-pham` | Tạo sản phẩm |
| `PUT /api/san-pham/<ma_sp>` | Cập nhật sản phẩm |
| `DELETE /api/san-pham/<ma_sp>` | Ngưng bán sản phẩm |
| `GET /api/san-pham-theo-chi-nhanh` | Sản phẩm theo chi nhánh |
| `GET /api/san-pham/chi-nhanh/<ma_chi_nhanh>` | Sản phẩm theo mã chi nhánh |
| `GET /api/nhan-vien` | Danh sách nhân viên |
| `GET /api/nhan-vien/<ma_nhan_vien>` | Chi tiết nhân viên |
| `POST /api/nhan-vien` | Tạo nhân viên |
| `PUT /api/nhan-vien/<ma_nhan_vien>` | Cập nhật nhân viên |
| `DELETE /api/nhan-vien/<ma_nhan_vien>` | Xóa mềm nhân viên |
| `GET /api/nhan-vien/phong-ban/<ma_pb>` | Nhân viên theo mã phòng ban |
| `GET /api/phong-ban` | Danh sách phòng ban |
| `GET /api/phong-ban/<ma_pb>` | Chi tiết phòng ban |
| `POST /api/phong-ban` | Tạo phòng ban |
| `PUT /api/phong-ban/<ma_pb>` | Cập nhật phòng ban |
| `DELETE /api/phong-ban/<ma_pb>` | Xóa phòng ban |
| `GET /api/chi-nhanh` | Danh sách chi nhánh |
| `GET /api/chi-nhanh/<ma_chi_nhanh>` | Chi tiết chi nhánh |
| `POST /api/chi-nhanh` | Tạo chi nhánh |
| `PUT /api/chi-nhanh/<ma_chi_nhanh>` | Cập nhật chi nhánh |
| `DELETE /api/chi-nhanh/<ma_chi_nhanh>` | Xóa chi nhánh |
| `GET /api/loai-san-pham` | Danh sách loại sản phẩm |
| `GET /api/loai-san-pham/<ma_loai_sp>` | Chi tiết loại sản phẩm |
| `POST /api/loai-san-pham` | Tạo loại sản phẩm |
| `PUT /api/loai-san-pham/<ma_loai_sp>` | Cập nhật loại sản phẩm |
| `DELETE /api/loai-san-pham/<ma_loai_sp>` | Xóa loại sản phẩm |
| `GET /api/nha-cung-cap` | Danh sách nhà cung cấp |
| `GET /api/nha-cung-cap/<ma_ncc>` | Chi tiết nhà cung cấp |
| `POST /api/nha-cung-cap` | Tạo nhà cung cấp |
| `PUT /api/nha-cung-cap/<ma_ncc>` | Cập nhật nhà cung cấp |
| `DELETE /api/nha-cung-cap/<ma_ncc>` | Xóa nhà cung cấp |
| `GET /api/thong-ke` | Danh sách chi nhánh và trạng thái cấu hình DB chi nhánh |
| `GET /api/thong-ke/chi-nhanh` | Thống kê sản phẩm theo chi nhánh |
| `GET /api/thong-ke/luong-phong-ban` | Thống kê lương theo phòng ban |

### Route API nên có theo database

Các route dưới đây là roadmap dựa trên schema trong `init/mssql/01-schema-and-data.sql`. Những route có dấu `*` là route đã có.

#### Chi nhánh

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/chi-nhanh` | `*` Lấy danh sách chi nhánh |
| `GET` | `/api/chi-nhanh/<ma_chi_nhanh>` | `*` Lấy chi tiết một chi nhánh |
| `POST` | `/api/chi-nhanh` | `*` Tạo chi nhánh mới |
| `PUT` | `/api/chi-nhanh/<ma_chi_nhanh>` | `*` Cập nhật tên chi nhánh |
| `DELETE` | `/api/chi-nhanh/<ma_chi_nhanh>` | `*` Xóa chi nhánh |
| `GET` | `/api/thong-ke` | `*` Lấy chi nhánh kèm engine DB và trạng thái cấu hình |

#### Loại sản phẩm

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/loai-san-pham` | `*` Lấy danh sách loại sản phẩm |
| `GET` | `/api/loai-san-pham/<ma_loai_sp>` | `*` Lấy chi tiết loại sản phẩm |
| `POST` | `/api/loai-san-pham` | `*` Tạo loại sản phẩm |
| `PUT` | `/api/loai-san-pham/<ma_loai_sp>` | `*` Cập nhật loại sản phẩm |
| `DELETE` | `/api/loai-san-pham/<ma_loai_sp>` | `*` Xóa loại sản phẩm |

#### Nhà cung cấp

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/nha-cung-cap` | `*` Lấy danh sách nhà cung cấp |
| `GET` | `/api/nha-cung-cap/<ma_ncc>` | `*` Lấy chi tiết nhà cung cấp |
| `POST` | `/api/nha-cung-cap` | `*` Tạo nhà cung cấp |
| `PUT` | `/api/nha-cung-cap/<ma_ncc>` | `*` Cập nhật nhà cung cấp |
| `DELETE` | `/api/nha-cung-cap/<ma_ncc>` | `*` Xóa nhà cung cấp |

#### Sản phẩm

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/san-pham` | `*` Lấy danh sách sản phẩm đang bán |
| `GET` | `/api/san-pham/<ma_sp>` | `*` Lấy chi tiết sản phẩm |
| `POST` | `/api/san-pham` | `*` Tạo sản phẩm |
| `PUT` | `/api/san-pham/<ma_sp>` | `*` Cập nhật sản phẩm |
| `DELETE` | `/api/san-pham/<ma_sp>` | `*` Xóa hoặc ngưng bán sản phẩm |
| `GET` | `/api/san-pham-theo-chi-nhanh` | `*` Lấy dữ liệu từ view `v_san_pham_theo_chi_nhanh` |
| `GET` | `/api/san-pham/chi-nhanh/<ma_chi_nhanh>` | `*` Lấy sản phẩm theo mã chi nhánh |

#### Phòng ban

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/phong-ban` | `*` Lấy danh sách phòng ban |
| `GET` | `/api/phong-ban/<ma_pb>` | `*` Lấy chi tiết phòng ban |
| `POST` | `/api/phong-ban` | `*` Tạo phòng ban |
| `PUT` | `/api/phong-ban/<ma_pb>` | `*` Cập nhật phòng ban |
| `DELETE` | `/api/phong-ban/<ma_pb>` | `*` Xóa phòng ban |

#### Nhân viên

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/nhan-vien` | `*` Lấy danh sách nhân viên |
| `GET` | `/api/nhan-vien/<ma_nhan_vien>` | `*` Lấy chi tiết nhân viên |
| `POST` | `/api/nhan-vien` | `*` Tạo nhân viên |
| `PUT` | `/api/nhan-vien/<ma_nhan_vien>` | `*` Cập nhật nhân viên |
| `DELETE` | `/api/nhan-vien/<ma_nhan_vien>` | `*` Xóa hoặc cho nhân viên nghỉ |
| `GET` | `/api/nhan-vien/phong-ban/<ma_pb>` | `*` Lấy nhân viên theo mã phòng ban |

#### Thống kê

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/thong-ke/chi-nhanh` | `*` Lấy dữ liệu từ view `v_thong_ke_chi_nhanh` |
| `GET` | `/api/thong-ke/luong-phong-ban` | `*` Lấy dữ liệu từ view `v_luong_phong_ban` |

## Cấu trúc project

```text
├── docker-compose.yml
├── .env.example
├── init/mssql/
│   └── 01-schema-and-data.sql
├── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py
    ├── config.py
    ├── db.py
    ├── api/
    │   ├── branch_api.py
    │   ├── category_api.py
    │   ├── department_api.py
    │   ├── employee_api.py
    │   ├── product_api.py
    │   ├── stats_api.py
    │   └── supplier_api.py
    ├── services/
    │   ├── branch_service.py
    │   ├── cache_service.py
    │   ├── category_service.py
    │   ├── department_service.py
    │   ├── employee_service.py
    │   ├── product_service.py
    │   └── supplier_service.py
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
