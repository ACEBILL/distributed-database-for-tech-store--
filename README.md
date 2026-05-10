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
| Backend API trung tâm | http://localhost:5000 | Flask API trụ sở / middleware |
| Backend API CN01 | http://localhost:5001 | Flask API chi nhánh MySQL |
| Backend API CN02 | http://localhost:5002 | Flask API chi nhánh PostgreSQL |
| Service trụ sở | http://localhost:5010 | Service nội bộ điều phối đồng bộ |
| Service CN01 | http://localhost:5011 | Service nội bộ chi nhánh MySQL |
| Service CN02 | http://localhost:5012 | Service nội bộ chi nhánh PostgreSQL |
| Swagger UI trụ sở | http://localhost:5000/apidocs | Tài liệu API trụ sở / middleware |
| Swagger UI CN01 | http://localhost:5001/apidocs | Tài liệu API backend chi nhánh MySQL |
| Swagger UI CN02 | http://localhost:5002/apidocs | Tài liệu API backend chi nhánh PostgreSQL |
| SQL Server | localhost,1433 | `sa` / `MyPass@2025` mặc định |
| MySQL CN01 | localhost:3306 | `techstore` / `MyPass@2025`, DB `quan_ly_chi_nhanh` |
| PostgreSQL CN02 | localhost:5432 | `techstore` / `MyPass@2025`, DB `quan_ly_chi_nhanh` |
| Redis | localhost:6379 | Cache |

## API endpoints

Swagger UI:

```text
http://localhost:5000/apidocs
http://localhost:5001/apidocs
http://localhost:5002/apidocs
```

OpenAPI JSON:

```text
http://localhost:5000/apispec_1.json
http://localhost:5001/apispec_1.json
http://localhost:5002/apispec_1.json
```

Base URL thường dùng:

| Nhóm API | Base URL | Khi dùng |
|---|---|---|
| API trung tâm | `http://localhost:5000` | Frontend portal/trụ sở, middleware đọc dữ liệu chi nhánh |
| API CN01 | `http://localhost:5001` | Gọi trực tiếp backend MySQL CN01 khi test riêng chi nhánh |
| API CN02 | `http://localhost:5002` | Gọi trực tiếp backend PostgreSQL CN02 khi test riêng chi nhánh |
| Service trụ sở | `http://localhost:5010` | API nội bộ để dispatch event đồng bộ |
| Service CN01 | `http://localhost:5011` | API nội bộ nhận/apply event đồng bộ CN01 |
| Service CN02 | `http://localhost:5012` | API nội bộ nhận/apply event đồng bộ CN02 |

### Ghi chú triển khai hiện tại

- `POST /api/auth/login` trả JWT cho người dùng hợp lệ, mặc định dữ liệu mẫu dùng mật khẩu `pass123`.
- Swagger UI trong môi trường demo tự gắn JWT demo vào request, nên có thể bấm `Try it out` mà không cần dán token ở nút `Authorize`. Nếu gọi endpoint login trong Swagger, token trả về sẽ được lưu và dùng cho các request sau.
- `GET /api/nhan-vien` và `GET /api/nhan-vien/<ma_nhan_vien>` yêu cầu xác thực; các trường nhạy cảm được che với user không phải admin/giam_doc.
- `GET /api/san-pham` hỗ trợ query string: `keyword`, `ma_loai_sp`, `ma_ncc`, `trang_thai`, `gia_min`, `gia_max`, `page`, `limit`.
- `GET /api/nhan-vien` và `GET /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien` hỗ trợ query string: `keyword`, `chuc_vu`, `trang_thai`, `ma_phong_ban`, `page`, `limit`.
- `GET /api/san-pham/sync-events` hỗ trợ query string: `status`, `target_branch`, `ma_sp`, `event_type`.
- Các thao tác ghi trên sản phẩm, loại sản phẩm, nhà cung cấp, nhân viên, chi nhánh và phòng ban đã được giới hạn theo vai trò.
- Redis đang cache danh sách sản phẩm bằng key `cache:san_pham_list`.
- Nhánh dữ liệu thống kê theo chi nhánh hiện có hai mã mẫu là `CN01` và `CN02`.

### Hiện đã có

| Endpoint | Mô tả |
|---|---|
| `GET /api/ping` | Kiểm tra backend API còn sống |
| `POST /api/auth/login` | Đăng nhập bằng tài khoản ở DB hiện tại |
| `POST /api/auth/tru-so/login` | Alias đăng nhập rõ ràng cho trụ sở |
| `POST /api/auth/branches/<ma_chi_nhanh>/login` | Đăng nhập chi nhánh thông qua API trung tâm, ví dụ `CN01`, `CN02` |
| `GET /api/auth/me` | Lấy thông tin user từ JWT hiện tại |
| `GET /api/auth/tru-so/me` | Alias lấy thông tin user trụ sở |
| `GET /api/auth/branches/<ma_chi_nhanh>/me` | Alias lấy thông tin user chi nhánh |
| `GET /api/san-pham` | Danh sách sản phẩm đang bán, có cache Redis |
| `GET /api/san-pham?keyword=<tu_khoa>` | Tìm sản phẩm theo tên, mã hoặc mô tả |
| `GET /api/san-pham?ma_loai_sp=<ma_loai_sp>` | Lọc sản phẩm theo loại |
| `GET /api/san-pham?ma_ncc=<ma_ncc>` | Lọc sản phẩm theo nhà cung cấp |
| `GET /api/san-pham?trang_thai=1&gia_min=<min>&gia_max=<max>` | Lọc sản phẩm theo trạng thái và khoảng giá |
| `GET /api/san-pham?page=1&limit=10` | Phân trang danh sách sản phẩm |
| `GET /api/san-pham/<ma_sp>` | Chi tiết sản phẩm |
| `POST /api/san-pham` | Tạo sản phẩm |
| `PUT /api/san-pham/<ma_sp>` | Cập nhật sản phẩm |
| `DELETE /api/san-pham/<ma_sp>` | Ngưng bán sản phẩm |
| `GET /api/san-pham/sync-events` | Xem event đồng bộ sản phẩm đã tạo ở trụ sở |
| `GET /api/san-pham/sync-events?ma_sp=<ma_sp>&status=<status>` | Lọc event đồng bộ theo sản phẩm/trạng thái |
| `GET /api/san-pham-theo-chi-nhanh` | Sản phẩm theo chi nhánh |
| `GET /api/san-pham/chi-nhanh/<ma_chi_nhanh>` | Sản phẩm theo mã chi nhánh |
| `GET /api/san-pham/loai/<ma_loai_sp>` | Sản phẩm theo mã loại sản phẩm |
| `GET /api/san-pham/ncc/<ma_ncc>` | Sản phẩm theo mã nhà cung cấp |
| `GET /api/chi-nhanh/<ma_chi_nhanh>/san-pham` | Đọc sản phẩm trực tiếp từ DB chi nhánh qua middleware trung tâm |
| `GET /api/nhan-vien` | Danh sách nhân viên |
| `GET /api/nhan-vien?keyword=<tu_khoa>` | Tìm nhân viên theo tên, mã, CCCD hoặc SĐT |
| `GET /api/nhan-vien?chuc_vu=<chuc_vu>&trang_thai=1&ma_phong_ban=<ma_pb>` | Lọc nhân viên theo chức vụ, trạng thái, phòng ban |
| `GET /api/nhan-vien?page=1&limit=10` | Phân trang danh sách nhân viên |
| `GET /api/nhan-vien/<ma_nhan_vien>` | Chi tiết nhân viên |
| `POST /api/nhan-vien` | Tạo nhân viên |
| `PUT /api/nhan-vien/<ma_nhan_vien>` | Cập nhật nhân viên |
| `DELETE /api/nhan-vien/<ma_nhan_vien>` | Xóa mềm nhân viên |
| `GET /api/nhan-vien/phong-ban/<ma_pb>` | Nhân viên theo mã phòng ban |
| `GET /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien` | Đọc nhân viên trực tiếp từ DB chi nhánh qua middleware trung tâm |
| `GET /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien?page=1&limit=10` | Phân trang nhân viên đọc từ DB chi nhánh |
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
| `GET /api/chi-nhanh/<ma_chi_nhanh>/health` | Kiểm tra cấu hình/kết nối DB chi nhánh |
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
| `GET /api/thong-ke/san-pham-theo-chi-nhanh/<ma_chi_nhanh>` | Thống kê sản phẩm theo một chi nhánh |
| `GET /api/thong-ke/nhan-vien-theo-chi-nhanh/<ma_chi_nhanh>` | Thống kê/danh sách nhân viên theo một chi nhánh |

### API trụ sở rõ namespace

Các endpoint này là alias rõ nghĩa cho dữ liệu trụ sở trên `http://localhost:5000`. Endpoint cũ vẫn còn để tương thích frontend/script hiện tại.

| Endpoint | Mô tả |
|---|---|
| `GET /api/tru-so/ping` | Kiểm tra backend trụ sở còn sống |
| `GET /api/tru-so/san-pham` | Danh sách sản phẩm ở SQL Server trung tâm |
| `GET /api/tru-so/san-pham/<ma_sp>` | Chi tiết sản phẩm ở trụ sở |
| `POST /api/tru-so/san-pham` | Tạo sản phẩm ở trụ sở |
| `PUT /api/tru-so/san-pham/<ma_sp>` | Cập nhật sản phẩm ở trụ sở |
| `DELETE /api/tru-so/san-pham/<ma_sp>` | Ngưng bán sản phẩm ở trụ sở |
| `GET /api/tru-so/san-pham/sync-events` | Xem event đồng bộ sản phẩm phát sinh từ trụ sở |
| `GET /api/tru-so/nhan-vien` | Danh sách nhân viên trụ sở |
| `GET /api/tru-so/nhan-vien/<ma_nhan_vien>` | Chi tiết nhân viên trụ sở |
| `POST /api/tru-so/nhan-vien` | Tạo nhân viên trụ sở |
| `PUT /api/tru-so/nhan-vien/<ma_nhan_vien>` | Cập nhật nhân viên trụ sở |
| `DELETE /api/tru-so/nhan-vien/<ma_nhan_vien>` | Xóa mềm nhân viên trụ sở nếu quyền cho phép |
| `GET /api/tru-so/chi-nhanh` | Danh sách chi nhánh trong DB trung tâm |
| `GET /api/tru-so/chi-nhanh/<ma_chi_nhanh>` | Chi tiết chi nhánh trong DB trung tâm |
| `POST /api/tru-so/chi-nhanh` | Tạo chi nhánh trong DB trung tâm |
| `PUT /api/tru-so/chi-nhanh/<ma_chi_nhanh>` | Cập nhật chi nhánh trong DB trung tâm |
| `DELETE /api/tru-so/chi-nhanh/<ma_chi_nhanh>` | Xóa chi nhánh trong DB trung tâm |
| `GET /api/tru-so/loai-san-pham` | Danh sách loại sản phẩm ở DB trung tâm |
| `GET /api/tru-so/phong-ban` | Danh sách phòng ban ở DB trung tâm |
| `GET /api/tru-so/nha-cung-cap` | Danh sách nhà cung cấp ở DB trung tâm |
| `GET /api/tru-so/thong-ke` | Thống kê/metadata chi nhánh nhìn từ trụ sở |
| `GET /api/tru-so/thong-ke/chi-nhanh` | Thống kê chi nhánh từ view trung tâm |
| `GET /api/tru-so/thong-ke/luong-phong-ban` | Thống kê lương phòng ban từ view trung tâm |

### API backend chi nhánh trực tiếp

Các endpoint dưới đây có trên backend chi nhánh `CN01` (`http://localhost:5001`) và `CN02` (`http://localhost:5002`). Khi đi qua portal trung tâm, ưu tiên gọi các route middleware trên `http://localhost:5000`.

Các route `/api/internal/products/...` là API nội bộ cho service, cần header `X-Service-Token`.

| Endpoint | Mô tả |
|---|---|
| `GET /api/ping` | Kiểm tra backend chi nhánh còn sống |
| `POST /api/auth/login` | Đăng nhập bằng tài khoản ở DB chi nhánh đang gọi |
| `GET /api/auth/me` | Lấy thông tin user từ JWT chi nhánh |
| `GET /api/chi-nhanh` | Thông tin chi nhánh hiện tại |
| `GET /api/chi-nhanh/<ma_chi_nhanh>` | Chi tiết chi nhánh hiện tại |
| `GET /api/chi-nhanh/<ma_chi_nhanh>/health` | Kiểm tra health của DB chi nhánh |
| `GET /api/internal/health` | Health nội bộ cho service gọi backend chi nhánh |
| `GET /api/san-pham` | Danh sách sản phẩm ở DB chi nhánh |
| `GET /api/chi-nhanh/<ma_chi_nhanh>/san-pham` | Danh sách sản phẩm theo mã chi nhánh |
| `GET /api/nhan-vien` | Danh sách nhân viên ở DB chi nhánh, hỗ trợ `page` và `limit` |
| `GET /api/nhan-vien/<ma_nhan_vien>` | Chi tiết nhân viên ở DB chi nhánh |
| `POST /api/nhan-vien` | Tạo nhân viên ở DB chi nhánh |
| `PUT /api/nhan-vien/<ma_nhan_vien>` | Cập nhật nhân viên ở DB chi nhánh |
| `DELETE /api/nhan-vien/<ma_nhan_vien>` | Xóa mềm/ngưng nhân viên ở DB chi nhánh |
| `GET /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien` | Danh sách nhân viên theo mã chi nhánh, hỗ trợ `page` và `limit` |
| `GET /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien/<ma_nhan_vien>` | Chi tiết nhân viên theo namespace chi nhánh |
| `POST /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien` | Tạo nhân viên theo namespace chi nhánh |
| `PUT /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien/<ma_nhan_vien>` | Cập nhật nhân viên theo namespace chi nhánh |
| `DELETE /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien/<ma_nhan_vien>` | Xóa mềm/ngưng nhân viên theo namespace chi nhánh |
| `GET /api/loai-san-pham` | Danh sách loại sản phẩm ở DB chi nhánh |
| `GET /api/loai-san-pham/<ma_loai_sp>` | Chi tiết loại sản phẩm |
| `POST /api/loai-san-pham` | Tạo loại sản phẩm |
| `PUT /api/loai-san-pham/<ma_loai_sp>` | Cập nhật loại sản phẩm |
| `DELETE /api/loai-san-pham/<ma_loai_sp>` | Xóa loại sản phẩm |
| `GET /api/phong-ban` | Danh sách phòng ban |
| `GET /api/phong-ban/<ma_pb>` | Chi tiết phòng ban |
| `POST /api/phong-ban` | Tạo phòng ban |
| `PUT /api/phong-ban/<ma_pb>` | Cập nhật phòng ban |
| `DELETE /api/phong-ban/<ma_pb>` | Xóa phòng ban |
| `GET /api/nha-cung-cap` | Danh sách nhà cung cấp |
| `GET /api/nha-cung-cap/<ma_ncc>` | Chi tiết nhà cung cấp |
| `POST /api/nha-cung-cap` | Tạo nhà cung cấp |
| `PUT /api/nha-cung-cap/<ma_ncc>` | Cập nhật nhà cung cấp |
| `DELETE /api/nha-cung-cap/<ma_ncc>` | Xóa nhà cung cấp |
| `GET /api/thong-ke` | Thống kê/metadata của chi nhánh |
| `GET /api/thong-ke/health` | Health thống kê của chi nhánh |
| `POST /api/internal/products/apply-change` | API nội bộ backend chi nhánh nhận một event sản phẩm từ service |
| `POST /api/internal/products/apply-batch` | API nội bộ backend chi nhánh nhận nhiều event sản phẩm từ service |
| `GET /api/internal/products/local-version` | API nội bộ xem version đồng bộ sản phẩm đã apply |
| `GET /api/internal/products/sync-log` | API nội bộ xem log đồng bộ sản phẩm |

### API service nội bộ

Nhóm này không dành cho frontend gọi trực tiếp. Các request ghi/đọc sync cần header:

```text
X-Service-Token: dev-service-token-change-in-production
```

| Base URL | Endpoint | Mô tả |
|---|---|---|
| `http://localhost:5010` | `GET /api/service/ping` | Kiểm tra service trụ sở còn sống |
| `http://localhost:5010` | `GET /api/service/registry` | Xem backend và peer service trụ sở đang cấu hình |
| `http://localhost:5010` | `GET /api/service/backend-health` | Trụ sở service kiểm tra backend trụ sở |
| `http://localhost:5010` | `GET /api/service/peers/health` | Trụ sở service kiểm tra service chi nhánh |
| `http://localhost:5010` | `POST /api/service/products/dispatch-event` | Dispatch một event sản phẩm từ trụ sở sang service chi nhánh |
| `http://localhost:5011` / `http://localhost:5012` | `GET /api/service/ping` | Kiểm tra service chi nhánh còn sống |
| `http://localhost:5011` / `http://localhost:5012` | `GET /api/service/registry` | Xem backend và peer service chi nhánh đang cấu hình |
| `http://localhost:5011` / `http://localhost:5012` | `GET /api/service/backend-health` | Service chi nhánh kiểm tra backend chi nhánh |
| `http://localhost:5011` / `http://localhost:5012` | `GET /api/service/peers/health` | Service chi nhánh kiểm tra peer service |
| `http://localhost:5011` / `http://localhost:5012` | `POST /api/service/products/apply-change` | Nhận và apply một event đồng bộ sản phẩm |
| `http://localhost:5011` / `http://localhost:5012` | `POST /api/service/products/apply-batch` | Nhận và apply nhiều event đồng bộ sản phẩm |
| `http://localhost:5011` / `http://localhost:5012` | `GET /api/service/products/local-version` | Xem version đồng bộ sản phẩm hiện tại ở chi nhánh |
| `http://localhost:5011` / `http://localhost:5012` | `GET /api/service/products/sync-log` | Xem log xử lý event đồng bộ sản phẩm |

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
| Frontend | http://localhost:3000 | Portal chon web, web tru so, web CN01, web CN02 |
| Backend API tru so | http://localhost:5000 | Flask API / middleware |
| Backend API CN01 | http://localhost:5001 | Flask API chi nhanh MySQL |
| Backend API CN02 | http://localhost:5002 | Flask API chi nhanh PostgreSQL |
| Service tru so | http://localhost:5010 | Service noi bo dispatch event sync |
| Service CN01 | http://localhost:5011 | Service noi bo nhan event sync CN01 |
| Service CN02 | http://localhost:5012 | Service noi bo nhan event sync CN02 |
| Swagger UI tru so | http://localhost:5000/apidocs | Tai lieu API tru so / middleware |
| Swagger UI CN01 | http://localhost:5001/apidocs | Tai lieu API backend chi nhanh MySQL |
| Swagger UI CN02 | http://localhost:5002/apidocs | Tai lieu API backend chi nhanh PostgreSQL |
| SQL Server trung tam | localhost,1433 | DB chinh |
| MySQL CN01 | localhost:3306 | DB chi nhanh |
| PostgreSQL CN02 | localhost:5432 | DB chi nhanh |
| Redis | localhost:6379 | Cache |

### Dang nhap va phan quyen hien tai

- Web tru so dung `POST /api/auth/login`.
- Web CN01 dung `POST /api/auth/branches/CN01/login`.
- Swagger UI tu gan JWT demo vao request trong ban demo, nen co the dung `Try it out` ma khong can dan token vao nut `Authorize`.
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
  - co the chuyen doi giua `CN01` (MySQL) va `CN02` (PostgreSQL) bang nut chon chi nhanh
  - chi xem du lieu, khong co form them/sua/xoa
- Token tru so khong duoc `DELETE /api/nhan-vien/<ma_nhan_vien>`.

#### Web chi nhanh CN01 (`/mysql/cn01`) va CN02 (`/postgresql/cn02`)

- Chi xem du lieu cua chinh chi nhanh `CN01` hoac `CN02`.
- Co the:
  - xem nhan vien
  - them nhan vien
  - sua nhan vien
  - ngung nhan vien (xoa mem)

### API branch / middleware dang dung

| Endpoint | Y nghia |
|---|---|
| `GET /api/chi-nhanh/<ma_chi_nhanh>/health` | Kiem tra ket noi DB chi nhanh (CN01 / CN02) |
| `GET /api/chi-nhanh/<ma_chi_nhanh>/san-pham` | Lay san pham tu DB chi nhanh |
| `GET /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien` | Lay nhan vien tu DB chi nhanh |

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

## Cap nhat - Khanh update (2026-05-10)

Ba tinh nang bo sung tai tru so (`tru_so/backend`), khong anh huong den code chi nhanh.

### 1. Retry dong bo san pham that bai

Bo sung hai endpoint cho phep thu lai cac event dong bo dang o trang thai `failed`:

| Endpoint | Mo ta |
|---|---|
| `POST /api/san-pham/sync-events/retry-failed` | Retry tat ca event `failed` chua qua gioi han 5 lan |
| `POST /api/tru-so/san-pham/sync-events/retry-failed` | Alias namespace tru so |
| `POST /api/san-pham/sync-events/<event_id>/retry` | Retry mot event cu the theo event_id |
| `POST /api/tru-so/san-pham/sync-events/<event_id>/retry` | Alias namespace tru so |

Chi retry event co `status='failed'`, khong retry `pending` de tranh dispatch trung khi event dang duoc xu ly. Yeu cau quyen: `admin` hoac `giam_doc`.

### 2. Mo rong schema product_sync_events

Them hai cot moi vao bang `product_sync_events` tai SQL Server (tu dong tao neu chua co):

- `retry_count INT DEFAULT 0` - dem so lan da thu lai
- `last_error NVARCHAR(MAX)` - luu loi cuoi cung

Trang thai event duoc mo rong:

```text
pending     -> sent         (dispatch thanh cong)
pending     -> failed       (dispatch that bai)
failed      -> sent         (retry thanh cong)
failed      -> failed       (retry that bai, retry_count tang)
failed      -> dead_letter  (retry_count >= 5, khong con retry)
dead_letter -> (ket thuc)
```

Cot `last_error` duoc ghi tu cot `message` sau moi lan retry that bai, giup truy vet nguyen nhan.

### 3. Health endpoint tong hop toan he thong

Endpoint moi tra trang thai tat ca node trong he thong phan tan:

```text
GET /api/system/health
```

Ket qua mau:

```json
{
  "overall": "degraded",
  "nodes": {
    "tru_so": {
      "db_engine": "sqlserver",
      "db": "ok",
      "service": "ok",
      "pending_events": 0
    },
    "CN01": {
      "db_engine": "mysql",
      "db": "ok",
      "service": "unreachable",
      "pending_events": 3
    },
    "CN02": {
      "db_engine": "postgresql",
      "db": "ok",
      "service": "ok",
      "pending_events": 0
    }
  }
}
```

`overall` la `ok` khi tat ca db va service deu `ok`, nguoc lai la `degraded`.

### File da thay doi

| File | Thay doi |
|---|---|
| `tru_so/backend/services/product_sync_service.py` | Them hang so `MAX_RETRY_COUNT`, cot `retry_count`/`last_error`, ham `retry_failed_events`, `retry_event_by_id`, `get_pending_event_counts_per_branch`; sua logic retry chi lay `status='failed'` (tranh double-dispatch); ghi `last_error` tu cot `message` sau moi lan retry that bai |
| `tru_so/backend/central_api/api/product_api.py` | Them 4 endpoint retry, cap nhat enum status trong doc |
| `tru_so/backend/central_api/api/system_api.py` | File moi - blueprint `system_api_bp` voi `GET /api/system/health` |
| `tru_so/backend/central_api/app.py` | Dang ky `system_api_bp` |
