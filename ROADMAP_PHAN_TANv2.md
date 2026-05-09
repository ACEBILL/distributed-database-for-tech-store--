# Lộ trình phân tán — Đồ án CSDL phân tán (Tech Store)

## Kiến trúc tổng quan

```text
                        ┌─────────────────────────────────┐
                        │         Frontend Portal          │
                        │  localhost:3000 / 3001 / 3002   │
                        └────────────┬────────────────────┘
                                     │
                        ┌────────────▼────────────────────┐
                        │    Backend Trụ sở (HQ)          │
                        │    Flask API  — localhost:5000   │
                        │    DB: SQL Server (localhost:1433)│
                        │    Cache: Redis (localhost:6379) │
                        └───┬─────────────┬───────────────┘
                            │             │
               ┌────────────▼──┐     ┌────▼───────────────┐
               │  Service HQ   │     │   (read-through)   │
               │  :5010        │     │   branch DB direct │
               └───┬───────────┘     └────────────────────┘
          dispatch │ events
         ┌─────────┴──────────┐
         │                    │
┌────────▼──────┐    ┌────────▼──────┐
│ Service CN01  │    │ Service CN02  │
│ :5011         │    │ :5012         │
└───────┬───────┘    └───────┬───────┘
        │ apply              │ apply
┌───────▼───────┐    ┌───────▼───────┐
│ Backend CN01  │    │ Backend CN02  │
│ Flask :5001   │    │ Flask :5002   │
│ DB: MySQL     │    │ DB: PostgreSQL│
│ :3306         │    │ :5432         │
└───────────────┘    └───────────────┘
```

---

## Trạng thái hiện tại

| Thành phần | Trạng thái |
|---|---|
| 3 node DB dị cấu trúc (SQL Server + MySQL + PostgreSQL) | ✅ Hoàn thành |
| Backend Flask riêng cho mỗi node | ✅ Hoàn thành |
| Event sourcing `product_sync_events` với version tracking | ✅ Hoàn thành |
| Service layer dispatch/apply events giữa các node | ✅ Hoàn thành |
| Redis cache tại trụ sở | ✅ Hoàn thành |
| JWT phân quyền theo scope (`central` / `branch`) | ✅ Hoàn thành |
| `loai_sp.ma_chi_nhanh` — mầm phân mảnh ngang | ✅ Có trong schema |
| Middleware read-through từ HQ đến branch DB | ✅ Hoàn thành |
| Retry sync khi branch offline | ❌ Chưa có |
| Sync nhân viên Branch → HQ | ❌ Chưa có |
| Sync `loai_sp`, `nha_cung_cap` HQ → Branch | ❌ Chưa có |
| Health dashboard tổng hợp toàn hệ thống | ❌ Chưa có |
| Demo kịch bản eventual consistency | ❌ Chưa có |

---

## Bảng phân mảnh dữ liệu

| Entity | Kiểu phân mảnh | Node lưu trữ | Ghi chú |
|---|---|---|---|
| `chi_nhanh` | Không phân mảnh (replicated) | HQ (SQL Server) | Metadata chi nhánh chỉ ở HQ |
| `loai_sp` | **Ngang** theo `ma_chi_nhanh` | HQ + mỗi branch lưu subset | CN01 thấy LSP01/02/05/06/09, CN02 thấy LSP03/04/07/08/10 |
| `NCC` | Nhân bản (replicated) | HQ → broadcast xuống branch | Dữ liệu master ở HQ |
| `SAN_PHAM` | Nhân bản có kiểm soát | HQ → branch qua sync events | Eventual consistency, HQ là source of truth |
| `phong_ban` | Không phân mảnh | Mỗi node tự quản lý cục bộ | Phòng ban của từng node riêng biệt |
| `NHAN_VIEN` | **Ngang** theo node | Mỗi node lưu nhân viên của mình | HQ = nhân viên trụ sở, CN01 = nhân viên chi nhánh HN |
| `NHAN_VIEN` (trường) | **Dọc** theo role | Trường `luong`, `cccd` ẩn với non-admin | Vertical fragmentation ở tầng API |
| `product_sync_events` | Không phân mảnh | HQ (SQL Server) | Event log trung tâm |
| `sync_log` | Không phân mảnh | Mỗi branch tự lưu | Audit log cục bộ tại branch |

---

## Giai đoạn 1 — Phân mảnh dữ liệu rõ ràng

**Lý thuyết áp dụng**: Horizontal Fragmentation, Vertical Fragmentation

**Thời gian ước tính**: 1–2 ngày

### 1.1 Phân mảnh ngang `loai_sp`

Schema đã có `loai_sp.ma_chi_nhanh`. Cần minh chứng bằng API:

- Thêm `GET /api/chi-nhanh/{ma_chi_nhanh}/loai-san-pham` tại branch backend — chỉ trả loại SP của chi nhánh đó.
- Tại HQ, `GET /api/loai-san-pham` trả toàn bộ (global view).
- Document rõ: truy vấn phân tán = union kết quả từ tất cả các node.

```sql
-- Fragment CN01 (MySQL): loai_sp WHERE ma_chi_nhanh IN ('CN01')
-- Fragment CN02 (PostgreSQL): loai_sp WHERE ma_chi_nhanh IN ('CN02')
-- Global view (SQL Server HQ): UNION của hai fragment trên
```

### 1.2 Phân mảnh dọc `NHAN_VIEN`

Đã có một phần trong middleware auth. Cần document rõ:

- **Fragment công khai**: `ma_nhan_vien`, `ho_ten`, `chuc_vu`, `trang_thai`, `ma_phong_ban`
- **Fragment nhạy cảm**: `luong`, `cccd`, `sdt` — chỉ `admin` / `giam_doc` thấy

```python
# Vertical fragmentation tại tầng API
PUBLIC_FIELDS  = ["ma_nhan_vien", "ho_ten", "chuc_vu", "trang_thai", "ma_phong_ban"]
PRIVATE_FIELDS = ["luong", "cccd", "sdt", "ngay_bat_dau"]
```

### 1.3 Checklist giai đoạn 1

- [ ] Endpoint `GET /api/chi-nhanh/{id}/loai-san-pham` tại branch backend
- [ ] Diagram bảng phân mảnh trong báo cáo
- [ ] Test: query HQ vs query branch trả khác nhau như thiết kế

---

## Giai đoạn 2 — Nhân bản & Đồng bộ

**Lý thuyết áp dụng**: Asynchronous Replication, Event Sourcing

**Thời gian ước tính**: 2–3 ngày

### 2.1 Mở rộng đối tượng sync (HQ → Branch)

Hiện chỉ có sản phẩm được sync. Cần thêm:

| Entity | Event types cần thêm | Bảng event |
|---|---|---|
| `loai_sp` | `CATEGORY_CREATED`, `CATEGORY_UPDATED`, `CATEGORY_DELETED` | `category_sync_events` tại HQ |
| `NCC` | `SUPPLIER_CREATED`, `SUPPLIER_UPDATED` | `supplier_sync_events` tại HQ |

Luồng giống hệt product sync hiện có — tái dùng pattern service dispatch.

### 2.2 Retry khi branch offline

Vấn đề hiện tại: nếu `mysql-service` down khi dispatch, event mất.

**Giải pháp**: polling retry đơn giản tại service HQ.

```python
# tru_so/service/app.py — thêm retry job
# Mỗi 30s: query product_sync_events WHERE status='pending' AND dispatched_at IS NULL
# Thử dispatch lại, cập nhật dispatched_at và status
```

Trạng thái event mở rộng:

```text
pending → dispatched → applied  (happy path)
pending → failed → pending       (retry)
pending → failed (max retries)   (dead letter)
```

### 2.3 Sync nhân viên Branch → HQ *(điểm cộng)*

Khi chi nhánh thêm nhân viên mới, thông báo về HQ để ghi nhận:

```text
Branch CN01 POST /api/nhan-vien
    → mysql-service dispatch EMPLOYEE_CREATED event
    → tru-so-service nhận
    → tru-so-backend ghi vào SQL Server (hoặc chỉ ghi log)
```

Cần thêm:
- Bảng `employee_sync_events` tại MySQL/PostgreSQL branch
- Route `POST /api/service/employees/dispatch-event` tại branch service
- Route `POST /api/service/employees/apply-change` tại HQ service

### 2.4 Checklist giai đoạn 2

- [ ] `category_sync_events` schema + dispatch + apply
- [ ] Retry polling job tại service HQ
- [ ] Test: tắt branch service → event giữ trạng thái `pending` → bật lại → tự apply
- [ ] *(Optional)* Employee sync Branch → HQ

---

## Giai đoạn 3 — Minh chứng Nhất quán Cuối

**Lý thuyết áp dụng**: Eventual Consistency, CAP Theorem (hệ thống chọn AP)

**Thời gian ước tính**: 1 ngày

### Kịch bản demo (chạy được trong báo cáo)

```bash
# Bước 1: Tạo sản phẩm mới tại HQ
curl -X POST http://localhost:5000/api/san-pham \
  -H "Authorization: Bearer <token>" \
  -d '{"ma_sp":"SP999","ten_sp":"Test SP","gia":1000000,...}'

# Bước 2: Kiểm tra event đang pending
curl http://localhost:5000/api/san-pham/sync-events?ma_sp=SP999
# → status: "pending"

# Bước 3: Stop mysql-service (simulate branch offline)
docker compose stop mysql-service

# Bước 4: Đọc từ CN01 — SP chưa có (inconsistent)
curl http://localhost:5001/api/san-pham/SP999
# → 404 Not Found

# Bước 5: Start lại mysql-service
docker compose start mysql-service
# → retry job tự dispatch lại

# Bước 6: Đọc lại CN01 — SP đã có (eventually consistent)
curl http://localhost:5001/api/san-pham/SP999
# → 200 OK
```

### Điểm cần nhấn mạnh trong báo cáo

- Hệ thống **vẫn chấp nhận write** tại HQ khi branch offline → ưu tiên **Availability**
- Tính **nhất quán đạt được sau** khi branch online trở lại → **Eventual Consistency**
- Đây là đánh đổi có chủ đích theo mô hình AP trong CAP Theorem

---

## Giai đoạn 4 — Giao dịch Phân tán (Saga Pattern)

**Lý thuyết áp dụng**: Distributed Transactions, Compensating Transactions

**Thời gian ước tính**: 1–2 ngày

### Luồng Saga cho "Tạo sản phẩm"

```text
Bước 1: INSERT SAN_PHAM tại HQ          → thành công → tiếp tục
Bước 2: INSERT product_sync_events HQ   → thành công → tiếp tục
Bước 3: Dispatch event đến CN01         → thành công → tiếp tục
Bước 4: Dispatch event đến CN02         → THẤT BẠI   → compensate

Compensating transaction:
  - Đánh dấu event CN02 status='failed'
  - Ghi log lý do
  - Giữ SP tại HQ (không rollback — data vẫn valid tại HQ)
  - Retry CN02 sau
```

### Endpoint retry thủ công

```text
POST /api/san-pham/{ma_sp}/retry-sync
POST /api/san-pham/retry-sync/all-failed
```

### Checklist giai đoạn 4

- [ ] Saga logic tại `POST /api/san-pham`: wrap dispatch trong try/catch, ghi status
- [ ] Endpoint `retry-sync` thủ công
- [ ] Test: dispatch 1 branch thành công, 1 branch thất bại → trạng thái độc lập

---

## Giai đoạn 5 — Xử lý lỗi & Health Monitoring

**Lý thuyết áp dụng**: Fault Tolerance, Location Transparency

**Thời gian ước tính**: 1 ngày

### Endpoint health tổng hợp

```text
GET /api/system/health   (tại HQ :5000)
```

Trả JSON tổng hợp:

```json
{
  "timestamp": "2026-05-09T10:00:00",
  "nodes": {
    "tru_so": {
      "backend": "ok",
      "service": "ok",
      "db": "ok",
      "db_engine": "sqlserver"
    },
    "CN01": {
      "backend": "ok",
      "service": "degraded",
      "db": "ok",
      "db_engine": "mysql",
      "pending_events": 3
    },
    "CN02": {
      "backend": "ok",
      "service": "ok",
      "db": "ok",
      "db_engine": "postgresql",
      "pending_events": 0
    }
  },
  "overall": "degraded"
}
```

### Dashboard sync status (frontend)

Thêm tab "Trạng thái hệ thống" tại portal trụ sở:

- Bảng hiển thị: node | DB engine | backend | service | pending events | last sync
- Tự refresh mỗi 10s
- Màu xanh/vàng/đỏ theo trạng thái

### Checklist giai đoạn 5

- [ ] `GET /api/system/health` tổng hợp ping tất cả 6 service
- [ ] Hiển thị `pending_events` count per branch
- [ ] Tab "System Health" tại frontend trụ sở

---

## Giai đoạn 6 — Tài liệu & Demo cho báo cáo

**Thời gian ước tính**: 1 ngày

### Diagram cần có

1. **Sơ đồ kiến trúc vật lý**: các container, port, network `db-cluster`
2. **Sơ đồ phân mảnh dữ liệu**: entity nào → fragment nào → node nào
3. **Sequence diagram sync**: HQ insert → event → dispatch → branch apply → ack
4. **Sequence diagram saga**: các bước + compensating transaction

### Bảng so sánh CSDL tập trung vs phân tán

| Tiêu chí | Tập trung | Phân tán (đồ án này) |
|---|---|---|
| Tính sẵn sàng | Một điểm lỗi | Branch hoạt động độc lập khi HQ down |
| Khả năng mở rộng | Giới hạn tại 1 server | Thêm node = thêm capacity |
| Độ trễ đọc | Cao nếu xa server | Đọc tại node gần nhất |
| Nhất quán | Strong consistency | Eventual consistency |
| Độ phức tạp vận hành | Thấp | Cao (cần quản lý sync, conflict) |
| Phù hợp với | Hệ thống nhỏ, tập trung | Chuỗi cửa hàng nhiều chi nhánh |

### Checklist giai đoạn 6

- [ ] Sơ đồ kiến trúc (draw.io hoặc ASCII rõ ràng)
- [ ] Bảng phân mảnh hoàn chỉnh
- [ ] Script curl demo kịch bản eventual consistency
- [ ] Bảng so sánh tập trung vs phân tán
- [ ] README cập nhật hướng dẫn chạy demo

---

## Thứ tự ưu tiên

```
Bắt buộc (phải có để đủ điểm):
  [1] Giai đoạn 1 — Phân mảnh rõ ràng, có API và bảng ánh xạ
  [2] Giai đoạn 3 — Demo kịch bản eventual consistency chạy được
  [6] Giai đoạn 6 — Tài liệu và diagram đầy đủ

Nên có (tăng điểm):
  [3] Giai đoạn 2 — Retry sync khi branch offline
  [4] Giai đoạn 4 — Saga pattern / compensating transaction

Điểm cộng (nếu còn thời gian):
  [5] Giai đoạn 5 — Health dashboard tổng hợp
  [2b] Sync nhân viên Branch → HQ
```

---

## Tham chiếu kỹ thuật

| Khái niệm lý thuyết | Nơi minh chứng trong code |
|---|---|
| Horizontal Fragmentation | `loai_sp.ma_chi_nhanh`, `NHAN_VIEN` theo node |
| Vertical Fragmentation | Middleware ẩn trường `luong`/`cccd` theo role |
| Asynchronous Replication | `product_sync_events` + service dispatch |
| Eventual Consistency | Kịch bản demo giai đoạn 3 |
| Event Sourcing | `product_sync_events` append-only log + version |
| Saga Pattern | Wrap dispatch trong try/catch + compensating |
| Location Transparency | Frontend gọi HQ, HQ proxy đến branch tự động |
| Heterogeneous DBMS | SQL Server + MySQL + PostgreSQL cùng một hệ thống |
