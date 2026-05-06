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
| MySQL CN01 | localhost:3306 | `techstore` / `MyPass@2025`, DB `quan_ly_chi_nhanh` |
| PostgreSQL CN02 | localhost:5432 | `techstore` / `MyPass@2025`, DB `quan_ly_chi_nhanh` |
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

### Ghi chú triển khai hiện tại

- `POST /api/auth/login` trả JWT cho người dùng hợp lệ, mặc định dữ liệu mẫu dùng mật khẩu `pass123`.
- `GET /api/nhan-vien` và `GET /api/nhan-vien/<ma_nhan_vien>` yêu cầu xác thực; các trường nhạy cảm được che với user không phải admin/giam_doc.
- Các thao tác ghi trên sản phẩm, loại sản phẩm, nhà cung cấp, nhân viên, chi nhánh và phòng ban đã được giới hạn theo vai trò.
- Redis đang cache danh sách sản phẩm bằng key `cache:san_pham_list`.
- Nhánh dữ liệu thống kê theo chi nhánh hiện có hai mã mẫu là `CN01` và `CN02`.

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
| `GET` | `/api/thong-ke/san-pham-theo-chi-nhanh/<ma_chi_nhanh>` | `*` Lấy sản phẩm theo chi nhánh từ `v_san_pham_theo_chi_nhanh` |
| `GET` | `/api/thong-ke/nhan-vien-theo-chi-nhanh/<ma_chi_nhanh>` | `*` Lấy nhân viên theo chi nhánh (Lưu ý: Schema hiện không hỗ trợ liên kết trực tiếp nhân viên-chi nhánh) |


## Cấu trúc project

```text
├── docker-compose.yml
├── .env.example
├── init/
│   ├── mssql/
│   │   └── 01-schema-and-data.sql
│   ├── mysql/
│   │   ├── 01-schema-and-data.sql
│   │   └── 02-update-vietnamese-data.sql
│   └── postgres/
│       └── 01-schema-and-data.sql
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
BRANCH_CN01_DB_HOST=mysql
BRANCH_CN01_DB_ENGINE=mysql
BRANCH_CN01_DB_PORT=3306
BRANCH_CN01_DB_NAME=quan_ly_chi_nhanh
BRANCH_CN01_DB_USER=techstore
BRANCH_CN01_DB_PASSWORD=MyPass@2025

BRANCH_CN02_DB_HOST=postgres
BRANCH_CN02_DB_ENGINE=postgresql
BRANCH_CN02_DB_PORT=5432
BRANCH_CN02_DB_NAME=quan_ly_chi_nhanh
BRANCH_CN02_DB_USER=techstore
BRANCH_CN02_DB_PASSWORD=MyPass@2025
```

`BRANCH_CNxx_DB_ENGINE` dùng để frontend/API biết chi nhánh đó dùng hệ CSDL nào. Giá trị dự kiến:

```text
sqlserver
postgresql
mysql
```

Backend hiện đã hỗ trợ cả ba driver: `pyodbc` (SQL Server), `pymysql` (MySQL) và `psycopg` (PostgreSQL). Stack mặc định khi `docker compose up` đã bật cả ba DB.

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
docker compose logs -f mysql
docker compose logs -f postgres
```

Reset database hoàn toàn:

```bash
docker compose down -v
docker compose up -d --build
```

## Cap nhat bo sung cho ban demo hien tai

Luu y: muc nay la phan bo sung cho README goc, khong xoa va khong thay the noi dung cu. Khi can xem nhanh kien truc va cach chay ban demo hien tai, uu tien tham khao muc nay.

### Kien truc demo hien tai

```text
Frontend / Portal
   |
   v
Backend Flask API / Middleware
   |
   +-- DB chinh: SQL Server
   +-- CN01: MySQL
   `-- CN02: PostgreSQL
```

- SQL Server dang duoc dung lam DB trung tam.
- MySQL dang duoc dung lam DB chi nhanh `CN01`.
- PostgreSQL dang duoc dung lam DB chi nhanh `CN02`.
- Redis van dung cho cache.

### Portal hien co

| Portal | URL | Pham vi |
|---|---|---|
| Cong portal | http://localhost:3000/ | Chon web trung tam hoac web chi nhanh |
| Web tru so | http://localhost:3000/sqlserver | Dang nhap bang tai khoan o SQL Server trung tam |
| Web chi nhanh CN01 | http://localhost:3000/mysql/cn01 | Dang nhap bang tai khoan o MySQL CN01 |
| Web chi nhanh CN02 | http://localhost:3000/postgresql/cn02 | Dang nhap bang tai khoan o PostgreSQL CN02 |

### Dich vu dang chay trong ban demo

| Service | URL / Host | Ghi chu |
|---|---|---|
| Frontend | http://localhost:3000 | Portal chon web, web tru so, web CN01 |
| Backend API | http://localhost:5000 | Flask API / middleware |
| Swagger UI | http://localhost:5000/apidocs | Tai lieu API |
| SQL Server trung tam | localhost,1433 | DB chinh |
| MySQL CN01 | localhost:3306 | DB chi nhanh |
| PostgreSQL CN02 | localhost:5432 | DB chi nhanh |
| Redis | localhost:6379 | Cache |

### Dang nhap va phan quyen hien tai

- Web tru so dung `POST /api/auth/login`.
- Web CN01 dung `POST /api/auth/branches/CN01/login`.
- Token trung tam co `scope=central`.
- Token chi nhanh co `scope=branch` va `branch_code=CN01`.

Tai khoan mau dang dung de test:

```text
NV001 / pass123
```

### Hanh vi nhan vien theo tung web

#### Web tru so (`/sqlserver`)

- Co submenu `Nhan vien tru so` va `Nhan vien chi nhanh`.
- `Nhan vien tru so`:
  - xem duoc
  - them duoc
  - sua duoc
- `Nhan vien chi nhanh`:
  - chi xem du lieu tu `CN01`
  - khong co form them/sua/xoa
- Token tru so khong duoc `DELETE /api/nhan-vien/<ma_nhan_vien>`.

#### Web chi nhanh CN01 (`/mysql/cn01`)

- Chi xem du lieu cua chinh chi nhanh `CN01`.
- Co the:
  - xem nhan vien
  - them nhan vien
  - sua nhan vien
  - ngung nhan vien (xoa mem)

### API branch / middleware dang dung

| Endpoint | Y nghia |
|---|---|
| `GET /api/chi-nhanh/CN01/health` | Kiem tra ket noi DB CN01 |
| `GET /api/chi-nhanh/CN01/san-pham` | Lay san pham tu MySQL CN01 |
| `GET /api/chi-nhanh/CN01/nhan-vien` | Lay nhan vien tu MySQL CN01 |

Ghi chu:

- `GET /api/nhan-vien` se tu doc theo portal dang dang nhap:
  - token trung tam -> SQL Server trung tam
  - token chi nhanh -> DB chi nhanh tuong ung
- `GET /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien` hien huu ich nhat cho portal tru so khi can xem du lieu chi nhanh.

### Phan trang nhan vien

- Ca web tru so va web chi nhanh deu da co phan trang cho danh sach nhan vien.
- Moi trang hien thi `10` nhan vien.
- Frontend co nut `Trang truoc` va `Trang sau`.
- Backend da ho tro query string:

```text
/api/nhan-vien?page=1&limit=10
/api/chi-nhanh/CN01/nhan-vien?page=1&limit=10
```

- Neu yeu cau trang lon hon so trang hien co, backend se tu dua ve trang hop le cuoi cung.

### Ghi chu ve du lieu

- Schema hien tai chua gan truc tiep nhan vien voi ma chi nhanh trong DB trung tam.
- Vi vay phan `Nhan vien chi nhanh` o portal tru so dang doc truc tiep tu DB chi nhanh qua middleware, thay vi suy luan tu schema SQL Server trung tam.
- Du lieu nhan vien trung tam va chi nhanh hien co the khac nhau ve so luong.
