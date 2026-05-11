# TEST CASES — TÍNH NĂNG CƠ SỞ DỮ LIỆU PHÂN TÁN

**Swagger UI trụ sở:** http://localhost:5000/apidocs  
**Swagger UI CN01:** http://localhost:5001/apidocs  
**Swagger UI CN02:** http://localhost:5002/apidocs

---

## Hướng dẫn chung

1. Mở `http://localhost:5000/apidocs`
2. Chạy **TC01** trước để lấy JWT token → copy giá trị `token` trong response
3. Nhấn nút **Authorize** (góc trên phải Swagger) → dán token vào ô `Bearer`
4. Từ TC02 trở đi, Swagger tự động gắn token vào header `Authorization`
5. Với mỗi test case: nhấn **Try it out** → điền tham số → nhấn **Execute** → đối chiếu **Expected Response**

---

## NHÓM 1 — XÁC THỰC (Tiền điều kiện cho các test khác)

---

### TC01 — Đăng nhập trụ sở (SQL Server)

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Lấy JWT token scope `central` để gọi các API trụ sở |
| **Swagger** | `POST /api/auth/login` |
| **DBMS xử lý** | SQL Server |

**Request Body:**
```json
{
  "ma_nhan_vien": "NV001",
  "mat_khau": "pass123"
}
```

**Expected Response — 200 OK:**
```json
{
  "token": "<JWT string>",
  "scope": "central",
  "ma_nhan_vien": "NV001",
  "ho_ten": "...",
  "chuc_vu": "..."
}
```

**Tiêu chí Pass:**
- [x] HTTP status = 200
- [x] `token` không rỗng
- [x] `scope` = `"central"`

---

### TC02 — Đăng nhập chi nhánh CN01 qua gateway trụ sở

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác thực người dùng CN01 thông qua backend trụ sở → `query_branch_db` đọc MySQL |
| **Swagger** | `POST /api/auth/branches/{ma_chi_nhanh}/login` |
| **DBMS xử lý** | MySQL CN01 (thông qua `query_branch_db` tại trụ sở) |

**Path param:** `ma_chi_nhanh = CN01`

**Request Body:**
```json
{
  "ma_nhan_vien": "NV101",
  "mat_khau": "pass123"
}
```

**Expected Response — 200 OK:**
```json
{
  "token": "<JWT string>",
  "scope": "branch",
  "branch_code": "CN01",
  "source_engine": "mysql"
}
```

**Tiêu chí Pass:**
- [x] HTTP status = 200
- [x] `scope` = `"branch"`
- [x] `branch_code` = `"CN01"`
- [x] `source_engine` = `"mysql"`

---

### TC03 — Đăng nhập chi nhánh CN02 qua gateway trụ sở

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác thực người dùng CN02, DBMS là PostgreSQL |
| **Swagger** | `POST /api/auth/branches/{ma_chi_nhanh}/login` |
| **DBMS xử lý** | PostgreSQL CN02 |

**Path param:** `ma_chi_nhanh = CN02`

**Request Body:**
```json
{
  "ma_nhan_vien": "NV201",
  "mat_khau": "pass123"
}
```

**Expected Response — 200 OK:**
```json
{
  "scope": "branch",
  "branch_code": "CN02",
  "source_engine": "postgresql"
}
```

**Tiêu chí Pass:**
- [x] HTTP status = 200
- [x] `source_engine` = `"postgresql"`

---

## NHÓM 2 — GIÁM SÁT SỨC KHỎE HỆ THỐNG PHÂN TÁN

---

### TC04 — Kiểm tra sức khỏe toàn hệ thống

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận tất cả node DB và service đang hoạt động |
| **Swagger** | `GET /api/system/health` |
| **Token yêu cầu** | JWT scope `central` (từ TC01) |
| **File xử lý** | `central_api/api/system_api.py` |

**Request:** không có body, không có query param

**Expected Response — 200 OK:**
```json
{
  "overall": "ok",
  "hq": {
    "db": "ok",
    "db_engine": "sqlserver"
  },
  "branches": {
    "CN01": {
      "db": "ok",
      "db_engine": "mysql",
      "service": "ok",
      "pending_events": 0
    },
    "CN02": {
      "db": "ok",
      "db_engine": "postgresql",
      "service": "ok",
      "pending_events": 0
    }
  }
}
```

**Tiêu chí Pass:**
- [x] `overall` = `"ok"`
- [x] `hq.db` = `"ok"`
- [x] `branches.CN01.db` = `"ok"` và `branches.CN01.service` = `"ok"`
- [x] `branches.CN02.db` = `"ok"` và `branches.CN02.service` = `"ok"`

**Tiêu chí Fail (partial):**
- [ ] `overall` = `"degraded"` → một hoặc nhiều node không kết nối được

---

### TC05 — Kiểm tra sức khỏe chi nhánh CN01

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Kiểm tra kết nối DB riêng chi nhánh CN01 (MySQL) |
| **Swagger** | `GET /api/chi-nhanh/{ma_chi_nhanh}/health` |
| **Token yêu cầu** | JWT scope `central` |
| **File xử lý** | `services/branch_service.py` → `check_branch_health` |

**Path param:** `ma_chi_nhanh = CN01`

**Expected Response — 200 OK:**
```json
{
  "ma_chi_nhanh": "CN01",
  "ten_chi_nhanh": "Chi nhánh CN01",
  "he_quan_tri_csdl": "mysql",
  "status": "ok",
  "error": null
}
```

**Tiêu chí Pass:**
- [x] `status` = `"ok"`
- [x] `he_quan_tri_csdl` = `"mysql"`
- [x] `error` = `null`

---

### TC06 — Kiểm tra sức khỏe chi nhánh CN02

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Kiểm tra kết nối DB chi nhánh CN02 (PostgreSQL) |
| **Swagger** | `GET /api/chi-nhanh/{ma_chi_nhanh}/health` |
| **Token yêu cầu** | JWT scope `central` |

**Path param:** `ma_chi_nhanh = CN02`

**Expected Response — 200 OK:**
```json
{
  "ma_chi_nhanh": "CN02",
  "he_quan_tri_csdl": "postgresql",
  "status": "ok",
  "error": null
}
```

**Tiêu chí Pass:**
- [x] `status` = `"ok"`
- [x] `he_quan_tri_csdl` = `"postgresql"`

---

## NHÓM 3 — TRUY VẤN PHÂN TÁN (Distributed Query)

---

### TC07 — Truy vấn phân tán toàn bộ nhân viên

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận API tổng hợp nhân viên từ SQL Server + MySQL + PostgreSQL trong một request |
| **Swagger** | `GET /api/nhan-vien/tat-ca-chi-nhanh` |
| **Token yêu cầu** | JWT scope `central` |
| **File xử lý** | `services/employee_service.py` → `get_all_employees_distributed_for_api` |

**Request:** không có body, không có query param

**Expected Response — 200 OK:**
```json
{
  "query_type": "distributed_query",
  "total": 15,
  "nodes": {
    "tru_so": {
      "db_engine": "sqlserver",
      "count": 8,
      "data": [...]
    },
    "CN01": {
      "db_engine": "mysql",
      "count": 4,
      "data": [...]
    },
    "CN02": {
      "db_engine": "postgresql",
      "count": 3,
      "data": [...]
    }
  },
  "data": [
    {
      "ma_nhan_vien": "NV001",
      "source_node": "tru_so",
      "db_engine": "sqlserver",
      "ho_ten": "..."
    },
    {
      "ma_nhan_vien": "NV101",
      "source_node": "CN01",
      "db_engine": "mysql",
      "ho_ten": "..."
    }
  ]
}
```

**Tiêu chí Pass:**
- [x] `query_type` = `"distributed_query"`
- [x] `nodes` có đủ 3 key: `tru_so`, `CN01`, `CN02`
- [x] Mỗi node có `db_engine` đúng: `sqlserver` / `mysql` / `postgresql`
- [x] Mỗi bản ghi trong `data` có trường `source_node` và `db_engine`
- [x] `total` = tổng `count` của 3 node
- [x] Bản ghi từ `tru_so` có `db_engine = "sqlserver"`
- [x] Bản ghi từ `CN01` có `db_engine = "mysql"`

---

### TC08 — Truy vấn phân tán khi một chi nhánh không kết nối được

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận fault-tolerance: chi nhánh lỗi không làm sập toàn bộ query |
| **Swagger** | `GET /api/nhan-vien/tat-ca-chi-nhanh` |
| **Tiền điều kiện** | Dừng container mysql: `docker stop mysql` |
| **Token yêu cầu** | JWT scope `central` |

**Expected Response — 200 OK (vẫn thành công):**
```json
{
  "query_type": "distributed_query",
  "nodes": {
    "tru_so": { "db_engine": "sqlserver", "count": 8, "data": [...] },
    "CN01":   { "db_engine": "mysql", "count": 0, "data": [], "error": "..." },
    "CN02":   { "db_engine": "postgresql", "count": 3, "data": [...] }
  }
}
```

**Tiêu chí Pass:**
- [x] HTTP status = **200** (không bị 500)
- [x] `nodes.CN01` có trường `error` khác null
- [x] `nodes.CN01.count` = 0
- [x] `nodes.tru_so` và `nodes.CN02` vẫn trả đúng dữ liệu

**Khôi phục:** `docker start mysql`

---

## NHÓM 4 — THỐNG KÊ PHÂN MẢNH

---

### TC09 — Thống kê số bản ghi phân mảnh theo node

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận dữ liệu được phân bố vật lý trên 3 node khác nhau |
| **Swagger** | `GET /api/thong-ke/phan-manh` |
| **Token yêu cầu** | JWT scope `central` |
| **File xử lý** | `services/branch_service.py` → `get_fragmentation_stats_for_api` |

**Request:** không có body

**Expected Response — 200 OK:**
```json
{
  "fragmentation_type": "horizontal",
  "description": "Mỗi node lưu phân mảnh ngang riêng...",
  "nodes": {
    "tru_so": {
      "ten_node": "Trụ sở",
      "db_engine": "sqlserver",
      "so_san_pham": 20,
      "so_nhan_vien": 8,
      "status": "ok"
    },
    "CN01": {
      "ten_node": "Chi nhánh CN01",
      "db_engine": "mysql",
      "so_san_pham": 12,
      "so_nhan_vien": 4,
      "status": "ok"
    },
    "CN02": {
      "ten_node": "Chi nhánh CN02",
      "db_engine": "postgresql",
      "so_san_pham": 10,
      "so_nhan_vien": 3,
      "status": "ok"
    }
  }
}
```

**Tiêu chí Pass:**
- [x] `fragmentation_type` = `"horizontal"`
- [x] Mỗi node có `status` = `"ok"`
- [x] Mỗi node có `so_san_pham` > 0 và `so_nhan_vien` > 0
- [x] `db_engine` của từng node đúng: `sqlserver` / `mysql` / `postgresql`

---

## NHÓM 5 — ĐỒNG BỘ SẢN PHẨM (Transactional Outbox)

---

### TC10 — Tạo sản phẩm và kiểm tra event đồng bộ được tạo

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận khi tạo SP → outbox event được tạo trong `product_sync_events` |
| **Swagger** | `POST /api/san-pham` |
| **Token yêu cầu** | JWT scope `central` |
| **Bước tiếp theo** | Chạy TC11 để xem event |

**Request Body:**
```json
{
  "ma_sp": "SP_TEST_01",
  "ten_sp": "Sản phẩm test phân tán",
  "gia": 5000000,
  "ti_le_loi_nhuan": 10,
  "ti_le_giam_gia": 5,
  "mo_ta": "Test distributed sync",
  "ma_loai_sp": "LSP01",
  "ma_ncc": 1,
  "trang_thai": 1
}
```

> **Lưu ý:** `ma_loai_sp = "LSP01"` là loại SP gắn với **CN01** → event sẽ có `target_branch = "CN01"`

**Expected Response — 201 Created:**
```json
{
  "ma_sp": "SP_TEST_01",
  "ten_sp": "Sản phẩm test phân tán",
  "ma_loai_sp": "LSP01"
}
```

**Tiêu chí Pass:**
- [x] HTTP status = 201
- [x] `ma_sp` = `"SP_TEST_01"` trong response

---

### TC11 — Xem danh sách event đồng bộ (sau TC10)

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận event `PRODUCT_CREATED` được ghi vào outbox và dispatch thành công |
| **Swagger** | `GET /api/san-pham/sync-events` |
| **Token yêu cầu** | JWT scope `central` |
| **Tiền điều kiện** | Đã chạy TC10 |

**Query params:** *(để trống để lấy tất cả)*

**Expected Response — 200 OK:**
```json
{
  "data": [
    {
      "event_id": "...",
      "event_type": "PRODUCT_CREATED",
      "target_branch": "CN01",
      "status": "sent",
      "retry_count": 0,
      "created_at": "..."
    }
  ]
}
```

**Tiêu chí Pass:**
- [x] Có ít nhất 1 event với `event_type = "PRODUCT_CREATED"`
- [x] `target_branch` = `"CN01"` (khớp với `ma_loai_sp = LSP01` ở TC10)
- [x] `status` = `"sent"` (dispatch thành công) hoặc `"pending"` (đang xử lý)
- [x] `retry_count` = 0 (chưa cần retry)

---

### TC12 — Cập nhật sản phẩm và kiểm tra event UPDATED

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận update SP tạo event `PRODUCT_UPDATED` |
| **Swagger** | `PUT /api/san-pham/{ma_sp}` |
| **Tiền điều kiện** | SP_TEST_01 đã tồn tại (sau TC10) |

**Path param:** `ma_sp = SP_TEST_01`

**Request Body:**
```json
{
  "ten_sp": "Sản phẩm test phân tán - đã cập nhật",
  "gia": 5500000,
  "ti_le_giam_gia": 10
}
```

**Expected Response — 200 OK:**
```json
{
  "ma_sp": "SP_TEST_01",
  "ten_sp": "Sản phẩm test phân tán - đã cập nhật",
  "gia": 5500000
}
```

**Kiểm tra tiếp** (chạy `GET /api/san-pham/sync-events`):
- [x] Có event mới `event_type = "PRODUCT_UPDATED"` với `target_branch = "CN01"`
- [x] Event có `status = "sent"`

---

### TC13 — Xoá sản phẩm và kiểm tra event DELETED

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận xoá SP tạo event `PRODUCT_DELETED` |
| **Swagger** | `DELETE /api/san-pham/{ma_sp}` |
| **Tiền điều kiện** | SP_TEST_01 đã tồn tại |

**Path param:** `ma_sp = SP_TEST_01`

**Expected Response — 200 OK hoặc 204 No Content**

**Kiểm tra tiếp** (chạy `GET /api/san-pham/sync-events`):
- [x] Có event `event_type = "PRODUCT_DELETED"` với `target_branch = "CN01"`

---

## NHÓM 6 — RETRY VÀ DEAD LETTER QUEUE

---

### TC14 — Xem danh sách event theo trạng thái

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Lọc event theo `status` để tìm event cần retry |
| **Swagger** | `GET /api/san-pham/sync-events` |
| **Token yêu cầu** | JWT scope `central` |

**Query params:**
```
status = failed
```

**Expected Response — 200 OK:**
```json
{
  "data": [
    {
      "event_id": "...",
      "event_type": "PRODUCT_CREATED",
      "target_branch": "CN01",
      "status": "failed",
      "retry_count": 2,
      "last_error": "Connection refused"
    }
  ]
}
```

**Tiêu chí Pass:**
- [x] Chỉ trả về event có `status = "failed"`
- [x] Trường `last_error` mô tả lý do thất bại

> Nếu không có event `failed`: tắt container `mysql-service` → chạy lại TC10 → bật lại → chạy TC14

---

### TC15 — Retry tất cả event thất bại

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận retry hoạt động — event `failed` được gửi lại |
| **Swagger** | `POST /api/san-pham/sync-events/retry-failed` |
| **Token yêu cầu** | JWT scope `central` |
| **File xử lý** | `services/product_sync_service.py` → `retry_failed_events` |

**Request Body:** `{}` *(body rỗng)*

**Expected Response — 200 OK:**
```json
{
  "retried": 2,
  "results": [
    { "event_id": "...", "status": "sent" },
    { "event_id": "...", "status": "sent" }
  ]
}
```

**Tiêu chí Pass:**
- [x] HTTP status = 200
- [x] `retried` >= 0
- [x] Sau khi retry: gọi lại `GET /api/san-pham/sync-events?status=failed` → số lượng giảm

---

### TC16 — Retry một event cụ thể theo ID

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Retry thủ công một event duy nhất theo `event_id` |
| **Swagger** | `POST /api/san-pham/sync-events/{event_id}/retry` |
| **Tiền điều kiện** | Có `event_id` từ TC14 |

**Path param:** `event_id = <lấy từ TC14>`

**Request Body:** `{}`

**Expected Response — 200 OK:**
```json
{
  "event_id": "...",
  "status": "sent",
  "retry_count": 3
}
```

**Tiêu chí Pass:**
- [x] HTTP status = 200
- [x] `status` = `"sent"` (nếu thành công) hoặc `"failed"` (nếu vẫn lỗi)
- [x] `retry_count` tăng thêm 1 so với trước

---

### TC17 — Xác nhận Dead Letter Queue (event retry > 5 lần)

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận event bị đánh `dead_letter` sau `MAX_RETRY_COUNT = 5` lần thất bại |
| **Swagger** | `GET /api/san-pham/sync-events` |
| **Tiền điều kiện** | Có event đã retry >= 5 lần (tắt mysql-service rồi retry nhiều lần) |

**Query params:**
```
status = dead_letter
```

**Expected Response — 200 OK:**
```json
{
  "data": [
    {
      "event_id": "...",
      "status": "dead_letter",
      "retry_count": 5,
      "last_error": "..."
    }
  ]
}
```

**Tiêu chí Pass:**
- [x] Event có `status = "dead_letter"`
- [x] `retry_count` = 5 (bằng `MAX_RETRY_COUNT`)
- [x] Event **vẫn còn trong DB** (không bị xóa)

---

## NHÓM 7 — ĐỌC DỮ LIỆU CHI NHÁNH TỪ TRỤ SỞ (Location Transparency)

---

### TC18 — Đọc sản phẩm từ DB chi nhánh CN01 qua trụ sở

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận trụ sở đọc được MySQL CN01 qua `query_branch_db` |
| **Swagger** | `GET /api/chi-nhanh/{ma_chi_nhanh}/san-pham` hoặc `GET /api/tru-so/san-pham` với source |
| **Token yêu cầu** | JWT scope `central` |

**Path param:** `ma_chi_nhanh = CN01`

**Expected Response — 200 OK:**
```json
[
  {
    "ma_sp": "SP001",
    "ten_sp": "...",
    "ma_chi_nhanh": "CN01",
    "gia": 5000000
  }
]
```

**Tiêu chí Pass:**
- [x] HTTP status = 200
- [x] Trả về sản phẩm (dữ liệu lấy từ MySQL, không phải SQL Server)

---

### TC19 — Thống kê chi nhánh từ view SQL Server

| Trường | Giá trị |
|--------|---------|
| **Mục tiêu** | Xác nhận view `v_thong_ke_chi_nhanh` tổng hợp dữ liệu đúng |
| **Swagger** | `GET /api/thong-ke/chi-nhanh` |
| **Token yêu cầu** | JWT scope `central` |

**Expected Response — 200 OK:**
```json
[
  {
    "ma_chi_nhanh": "CN01",
    "ten_chi_nhanh": "Chi nhánh CN01",
    "tong_san_pham": 12,
    "gia_trung_binh": 8500000.0
  },
  {
    "ma_chi_nhanh": "CN02",
    "ten_chi_nhanh": "Chi nhánh CN02",
    "tong_san_pham": 10,
    "gia_trung_binh": 7200000.0
  }
]
```

**Tiêu chí Pass:**
- [x] HTTP status = 200
- [x] Có dữ liệu cho cả CN01 và CN02
- [x] `gia_trung_binh` là số thực (float)

---

## BẢNG TỔNG HỢP TEST CASES

| ID | Tên test | Swagger Endpoint | Nhóm tính năng phân tán |
|----|----------|-----------------|--------------------------|
| TC01 | Đăng nhập trụ sở | `POST /api/auth/login` | Xác thực |
| TC02 | Đăng nhập CN01 qua gateway | `POST /api/auth/branches/CN01/login` | Location transparency |
| TC03 | Đăng nhập CN02 qua gateway | `POST /api/auth/branches/CN02/login` | Location transparency |
| TC04 | System health toàn hệ thống | `GET /api/system/health` | Distributed monitoring |
| TC05 | Health check CN01 | `GET /api/chi-nhanh/CN01/health` | Distributed monitoring |
| TC06 | Health check CN02 | `GET /api/chi-nhanh/CN02/health` | Distributed monitoring |
| TC07 | Truy vấn phân tán nhân viên | `GET /api/nhan-vien/tat-ca-chi-nhanh` | Distributed query |
| TC08 | Fault tolerance khi CN01 down | `GET /api/nhan-vien/tat-ca-chi-nhanh` | Fault tolerance |
| TC09 | Thống kê phân mảnh | `GET /api/thong-ke/phan-manh` | Horizontal fragmentation |
| TC10 | Tạo SP → tạo event outbox | `POST /api/san-pham` | Transactional outbox |
| TC11 | Xem event PRODUCT_CREATED | `GET /api/san-pham/sync-events` | Outbox audit |
| TC12 | Cập nhật SP → event UPDATED | `PUT /api/san-pham/{ma_sp}` | Outbox + replication |
| TC13 | Xoá SP → event DELETED | `DELETE /api/san-pham/{ma_sp}` | Outbox + replication |
| TC14 | Lọc event theo status=failed | `GET /api/san-pham/sync-events?status=failed` | Event management |
| TC15 | Retry tất cả event thất bại | `POST /api/san-pham/sync-events/retry-failed` | Retry mechanism |
| TC16 | Retry event theo ID | `POST /api/san-pham/sync-events/{id}/retry` | Retry mechanism |
| TC17 | Dead Letter Queue | `GET /api/san-pham/sync-events?status=dead_letter` | DLQ pattern |
| TC18 | Đọc SP từ CN01 qua trụ sở | `GET /api/chi-nhanh/CN01/san-pham` | Location transparency |
| TC19 | Thống kê chi nhánh (view) | `GET /api/thong-ke/chi-nhanh` | Distributed aggregation |

---

## THỨ TỰ CHẠY KHUYẾN NGHỊ

```
TC01 (lấy token)
  ↓
TC04 → TC05 → TC06    (kiểm tra hệ thống trước)
  ↓
TC07 → TC08           (truy vấn phân tán)
  ↓
TC09                  (thống kê phân mảnh)
  ↓
TC02 → TC03           (login chi nhánh)
  ↓
TC10 → TC11 → TC12 → TC13   (vòng đời sản phẩm + sync)
  ↓
TC14 → TC15 → TC16 → TC17   (retry + DLQ)
  ↓
TC18 → TC19           (đọc dữ liệu xuyên node)
```
