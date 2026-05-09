# Lộ trình phân tán - Đồ án CSDL phân tán Tech Store

Tài liệu này mô tả hướng phát triển hệ thống theo đúng tinh thần CSDL phân tán, đồng thời tránh các khẳng định quá mạnh so với mức triển khai hiện tại. Mục tiêu chính là có một demo thuyết phục: nhiều node DB độc lập, phân mảnh dữ liệu rõ ràng, đọc/ghi theo đúng node, đồng bộ bất đồng bộ và minh chứng eventual consistency.

## Kết luận thiết kế

Hệ thống hiện tại phù hợp để phát triển thành một demo CSDL phân tán theo mô hình:

```text
HQ SQL Server = node điều phối + master data
CN01 MySQL    = node chi nhánh 1
CN02 PostgreSQL = node chi nhánh 2

HQ backend/service
  -> đọc metadata trung tâm
  -> đọc xuyên sang DB chi nhánh khi cần
  -> phát event đồng bộ master data xuống chi nhánh

Branch backend/service
  -> phục vụ dữ liệu cục bộ của chi nhánh
  -> nhận event đồng bộ từ HQ
  -> ghi sync_log cục bộ
```

Điểm mạnh của hướng này:

- Có nhiều DBMS khác nhau: SQL Server, MySQL, PostgreSQL.
- Có node trụ sở và node chi nhánh tách riêng backend/service.
- Có phân mảnh ngang thật cho nhân viên theo node.
- Có nhân bản bất đồng bộ cho sản phẩm từ HQ xuống chi nhánh.
- Có location transparency ở mức API: frontend/trụ sở có thể gọi một endpoint và backend tự đọc DB chi nhánh phù hợp.

Điểm cần nói cẩn thận:

- `product_sync_events` hiện là **transactional outbox / event log**, chưa phải event sourcing đầy đủ.
- Ẩn `luong`, `cccd`, `sdt` theo quyền là **mô phỏng phân mảnh dọc ở tầng API**, chưa phải vertical fragmentation ở tầng database vật lý.
- Hệ thống thể hiện eventual consistency cho luồng HQ -> branch; chưa phải AP hoàn toàn cho mọi loại dữ liệu.
- Saga nếu làm nên trình bày là **outbox + retry + compensating status**, không nên nói là distributed transaction đầy đủ.

---

## Kiến trúc tổng quan

```text
                        +---------------------------------+
                        |         Frontend Portal          |
                        |  localhost:3000 / 3001 / 3002   |
                        +----------------+----------------+
                                         |
                        +----------------v----------------+
                        |    Backend Trụ sở / Gateway      |
                        |    Flask API - localhost:5000    |
                        |    DB: SQL Server                |
                        |    Cache: Redis                  |
                        +--------+----------------+--------+
                                 |                |
                         dispatch events   read-through query
                                 |                |
                        +--------v--------+       |
                        | Service trụ sở  |       |
                        | localhost:5010  |       |
                        +--------+--------+       |
                                 |                |
              +------------------+----------------+------------------+
              |                                                   |
      +-------v--------+                                  +-------v--------+
      | Service CN01   |                                  | Service CN02   |
      | localhost:5011 |                                  | localhost:5012 |
      +-------+--------+                                  +-------+--------+
              | apply event                                       | apply event
      +-------v--------+                                  +-------v--------+
      | Backend CN01   |                                  | Backend CN02   |
      | Flask :5001    |                                  | Flask :5002    |
      | DB: MySQL      |                                  | DB: PostgreSQL |
      +----------------+                                  +----------------+
```

## Trạng thái hiện tại

| Thành phần | Trạng thái | Ghi chú |
|---|---|---|
| 3 node DB dị hệ quản trị | Hoàn thành | SQL Server, MySQL, PostgreSQL |
| Backend Flask riêng cho mỗi node | Hoàn thành | Trụ sở, CN01, CN02 |
| Service layer riêng cho mỗi node | Hoàn thành | `tru-so-service`, `mysql-service`, `postgre-service` |
| JWT theo scope `central` / `branch` | Hoàn thành | Đã phân biệt trụ sở và chi nhánh |
| Swagger hiển thị API sản phẩm/nhân viên | Hoàn thành | Đã tự gắn token demo cho Swagger |
| Middleware read-through HQ -> branch DB | Hoàn thành | Sản phẩm, nhân viên, health chi nhánh |
| Product outbox/event log tại HQ | Hoàn thành mức demo | Bảng `product_sync_events` |
| Apply event sản phẩm tại branch | Hoàn thành mức demo | Bảng `sync_log` tại branch |
| Retry tự động khi branch offline | Chưa có | Cần bổ sung để demo eventual consistency mạnh |
| Sync `loai_sp`, `NCC` HQ -> branch | Chưa có | Nên làm nếu cần demo master data đầy đủ |
| Sync nhân viên Branch -> HQ | Chưa có | Điểm cộng, không bắt buộc |
| Health dashboard tổng hợp | Chưa có | Rất hữu ích khi báo cáo |

---

## Bảng phân bố dữ liệu đề xuất

| Entity | Chiến lược dữ liệu | Node lưu trữ | Ghi chú chính xác |
|---|---|---|---|
| `chi_nhanh` | Metadata trung tâm, có thể replicate read-only | HQ là nguồn chính; branch có bản local tối thiểu | Không nên gọi là replicated nếu chỉ dựa vào HQ |
| `loai_sp` | Phân mảnh ngang theo `ma_chi_nhanh`, HQ giữ global catalog | HQ + branch subset | CN01 chỉ cần loại thuộc CN01, CN02 chỉ cần loại thuộc CN02 |
| `NCC` | Reference/master data replicated | HQ -> branch | HQ là source of truth |
| `SAN_PHAM` | Master ở HQ, replicated bất đồng bộ xuống branch | HQ + branch subset | Eventual consistency theo `loai_sp.ma_chi_nhanh` |
| `phong_ban` | Dữ liệu cục bộ theo node | Mỗi node tự quản lý | Không cần global nếu mỗi chi nhánh có cơ cấu riêng |
| `NHAN_VIEN` | Phân mảnh ngang theo node | HQ/CN01/CN02 | HQ giữ nhân viên trụ sở, branch giữ nhân viên chi nhánh |
| Trường nhạy cảm `NHAN_VIEN` | Mô phỏng phân mảnh dọc ở API | Tất cả node | Non-admin bị ẩn `luong`, `cccd`, `sdt` |
| `product_sync_events` | Outbox/event log trung tâm | HQ | Không gọi là event sourcing đầy đủ |
| `sync_log` | Audit log cục bộ | Mỗi branch | Ghi event đã apply, ignored, failed |

---

## Giai đoạn 1 - Làm rõ phân mảnh dữ liệu

**Mục tiêu:** chứng minh hệ thống không chỉ chạy nhiều DB, mà dữ liệu được phân bố có chủ đích.

**Lý thuyết áp dụng:** horizontal fragmentation, replicated reference data, API-level vertical fragmentation.

### 1.1 Phân mảnh ngang `NHAN_VIEN`

Đây là phần nên nhấn mạnh nhất vì rõ và đúng:

```text
NHAN_VIEN_HQ   = nhân viên trụ sở, lưu ở SQL Server
NHAN_VIEN_CN01 = nhân viên CN01, lưu ở MySQL
NHAN_VIEN_CN02 = nhân viên CN02, lưu ở PostgreSQL
```

API minh chứng:

```text
GET /api/tru-so/nhan-vien
GET /api/chi-nhanh/CN01/nhan-vien
GET /api/chi-nhanh/CN02/nhan-vien
```

Kết quả kỳ vọng:

- Trụ sở trả danh sách nhân viên trụ sở.
- CN01 trả nhân viên CN01.
- CN02 trả nhân viên CN02.
- Số lượng và dữ liệu giữa các node khác nhau.

### 1.2 Phân mảnh ngang `loai_sp`

Schema đã có `loai_sp.ma_chi_nhanh`. Cần bổ sung API rõ hơn:

```text
GET /api/chi-nhanh/{ma_chi_nhanh}/loai-san-pham
```

Ý nghĩa:

```sql
-- Fragment CN01
SELECT * FROM loai_sp WHERE ma_chi_nhanh = 'CN01';

-- Fragment CN02
SELECT * FROM loai_sp WHERE ma_chi_nhanh = 'CN02';

-- Global catalog tại HQ
SELECT * FROM loai_sp;
```

### 1.3 Mô phỏng phân mảnh dọc `NHAN_VIEN`

Hiện hệ thống đang ẩn field nhạy cảm theo role. Nên trình bày là **API-level vertical fragmentation / access-controlled projection**.

```text
Public projection:
  ma_nhan_vien, ho_ten, chuc_vu, trang_thai, ma_phong_ban

Private projection:
  luong, cccd, sdt, ngay_bat_dau, ngay_ket_thuc
```

Không nên nói đây là vertical fragmentation vật lý nếu các trường vẫn nằm trong cùng bảng DB.

### Checklist giai đoạn 1

- [ ] Bổ sung `GET /api/chi-nhanh/{ma_chi_nhanh}/loai-san-pham`.
- [ ] Viết bảng mapping entity -> node trong báo cáo.
- [ ] Test HQ vs CN01 vs CN02 cho `NHAN_VIEN`.
- [ ] Test HQ vs CN01 vs CN02 cho `loai_sp`.

---

## Giai đoạn 2 - Đồng bộ bất đồng bộ bằng Outbox Pattern

**Mục tiêu:** biến luồng sync sản phẩm thành demo eventual consistency rõ ràng, có retry.

**Lý thuyết áp dụng:** asynchronous replication, transactional outbox, idempotent consumer.

### 2.1 Chuẩn hóa luồng sync sản phẩm hiện tại

Luồng hiện tại nên được mô tả như sau:

```text
1. User tạo/sửa/ngưng bán sản phẩm tại HQ.
2. HQ ghi SAN_PHAM vào SQL Server.
3. HQ ghi event vào product_sync_events.
4. tru-so-service dispatch event sang service chi nhánh tương ứng.
5. branch-service gọi backend local để apply event.
6. Branch ghi sync_log.
```

Các điểm lý thuyết có thể trình bày:

- `product_sync_events` là outbox/event log.
- `event_id` giúp xử lý idempotent, gọi lại cùng event không apply trùng.
- `version` giúp biết branch đã đồng bộ tới mức nào.
- `sync_log` giúp audit và debug.

### 2.2 Retry khi branch offline

Không nên nói event bị mất. Code đã có event log ở HQ; vấn đề là **chưa có cơ chế retry tự động**.

Trạng thái đề xuất:

```text
pending -> sent -> applied
pending -> failed -> pending      retry
failed  -> dead_letter            quá số lần retry
```

Cột nên bổ sung cho `product_sync_events`:

```text
retry_count
last_error
next_retry_at
applied_at
```

Job đề xuất:

```text
Mỗi 30 giây:
  lấy event status IN ('pending', 'failed')
  nếu next_retry_at <= now
  dispatch lại sang branch service
  cập nhật retry_count/status/message
```

### 2.3 Mở rộng sync master data

Nếu còn thời gian, mở rộng pattern sản phẩm sang dữ liệu tham chiếu:

| Entity | Event types | Ghi chú |
|---|---|---|
| `loai_sp` | `CATEGORY_CREATED`, `CATEGORY_UPDATED`, `CATEGORY_DELETED` | Cần vì sản phẩm phụ thuộc loại |
| `NCC` | `SUPPLIER_CREATED`, `SUPPLIER_UPDATED`, `SUPPLIER_DELETED` | Cần vì sản phẩm phụ thuộc nhà cung cấp |

Ưu tiên thực tế: sync `loai_sp` trước `NCC`, vì `loai_sp.ma_chi_nhanh` quyết định sản phẩm thuộc branch nào.

### Checklist giai đoạn 2

- [ ] Thêm retry job ở `tru_so/service`.
- [ ] Thêm endpoint retry thủ công: `POST /api/tru-so/san-pham/sync-events/retry`.
- [ ] Bổ sung `retry_count`, `next_retry_at`, `last_error`.
- [ ] Test tắt `mysql-service`, sửa sản phẩm, bật lại và thấy event tự apply.
- [ ] Nếu còn thời gian: sync `loai_sp` HQ -> branch.

---

## Giai đoạn 3 - Demo eventual consistency

**Mục tiêu:** có kịch bản chạy được để chứng minh dữ liệu tạm thời không nhất quán rồi tự hội tụ.

**Lý thuyết áp dụng:** eventual consistency, availability under partial failure.

### Kịch bản demo đề xuất

```powershell
# 1. Login trụ sở
$login = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:5000/api/auth/tru-so/login" `
  -ContentType "application/json" `
  -Body (@{ ma_nhan_vien="NV001"; mat_khau="pass123" } | ConvertTo-Json)

$headers = @{ Authorization = "Bearer $($login.token)" }

# 2. Tắt service nhận event của CN01
docker compose stop mysql-service

# 3. Sửa sản phẩm thuộc CN01 tại HQ
Invoke-RestMethod -Method Put `
  -Uri "http://localhost:5000/api/tru-so/san-pham/SP001" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body (@{ ti_le_giam_gia = 11 } | ConvertTo-Json)

# 4. Xem event tại HQ: pending/failed
Invoke-RestMethod `
  -Uri "http://localhost:5000/api/tru-so/san-pham/sync-events?ma_sp=SP001" `
  -Headers $headers

# 5. Kiểm tra CN01 chưa nhận thay đổi
Invoke-RestMethod `
  -Uri "http://localhost:5001/api/san-pham" `
  -Headers $headers

# 6. Bật lại service CN01
docker compose start mysql-service

# 7. Retry tự động hoặc retry thủ công
# 8. Kiểm tra CN01 đã nhận thay đổi
```

### Cách diễn đạt CAP cho đúng

Nên viết:

> Trong phạm vi đồng bộ sản phẩm HQ -> branch, hệ thống ưu tiên tiếp tục ghi tại HQ khi branch tạm thời không sẵn sàng. Dữ liệu branch có thể trễ trong một khoảng thời gian, sau đó hội tụ nhờ retry event. Đây là minh chứng cho eventual consistency dưới partial failure.

Không nên viết:

> Toàn bộ hệ thống chọn AP theo CAP.

Vì nếu HQ down thì luồng ghi master data tại HQ vẫn bị ảnh hưởng.

### Checklist giai đoạn 3

- [ ] Script demo PowerShell chạy được.
- [ ] Có log trước và sau retry.
- [ ] Có ảnh Swagger hoặc terminal cho `sync-events` và `sync-log`.
- [ ] Báo cáo giải thích rõ trạng thái temporary inconsistency.

---

## Giai đoạn 4 - Saga / Compensating Workflow ở mức demo

**Mục tiêu:** trình bày xử lý lỗi đa node mà không cần two-phase commit.

**Lý thuyết áp dụng:** saga-style workflow, compensating status, retry.

Nên gọi là **saga-style** hoặc **compensating workflow**, vì hiện hệ thống không rollback dữ liệu sản phẩm ở HQ khi branch fail.

### Luồng đề xuất cho tạo/sửa sản phẩm

```text
1. HQ validate dữ liệu.
2. HQ ghi SAN_PHAM.
3. HQ ghi product_sync_events.
4. HQ dispatch event sang branch.
5. Nếu branch apply thành công:
     event status = sent/applied
6. Nếu branch fail:
     event status = failed
     ghi last_error
     lên lịch retry
7. Nếu quá số lần retry:
     event status = dead_letter
     admin có thể retry thủ công
```

Đây là compensating status chứ không phải rollback sản phẩm tại HQ.

### Endpoint đề xuất

```text
POST /api/tru-so/san-pham/sync-events/{event_id}/retry
POST /api/tru-so/san-pham/sync-events/retry-failed
GET  /api/tru-so/san-pham/sync-events?status=dead_letter
```

### Checklist giai đoạn 4

- [ ] Có retry thủ công theo `event_id`.
- [ ] Có retry hàng loạt event failed.
- [ ] Có trạng thái `dead_letter`.
- [ ] Báo cáo giải thích vì sao không dùng 2PC.

---

## Giai đoạn 5 - Health monitoring và location transparency

**Mục tiêu:** thể hiện hệ thống phân tán có quan sát được trạng thái từng node.

**Lý thuyết áp dụng:** fault tolerance, monitoring, location transparency.

### Endpoint tổng hợp

```text
GET /api/system/health
```

Payload đề xuất:

```json
{
  "timestamp": "2026-05-09T10:00:00",
  "overall": "degraded",
  "nodes": {
    "tru_so": {
      "backend": "ok",
      "service": "ok",
      "db": "ok",
      "db_engine": "sqlserver"
    },
    "CN01": {
      "backend": "ok",
      "service": "down",
      "db": "ok",
      "db_engine": "mysql",
      "pending_events": 3,
      "last_sync_version": 12
    },
    "CN02": {
      "backend": "ok",
      "service": "ok",
      "db": "ok",
      "db_engine": "postgresql",
      "pending_events": 0,
      "last_sync_version": 15
    }
  }
}
```

### Dashboard frontend

Thêm tab ở portal trụ sở:

```text
Node | DB engine | Backend | Service | DB | Pending events | Last sync version
```

### Checklist giai đoạn 5

- [ ] `GET /api/system/health`.
- [ ] Đếm pending/failed events theo branch.
- [ ] Hiển thị trạng thái service CN01/CN02.
- [ ] Frontend auto refresh mỗi 10 giây.

---

## Giai đoạn 6 - Báo cáo và demo

**Mục tiêu:** biến implementation thành câu chuyện phân tán rõ ràng.

### Diagram nên có

1. Sơ đồ vật lý container/port/network.
2. Sơ đồ phân bố dữ liệu theo bảng.
3. Sequence diagram sync sản phẩm HQ -> branch.
4. Sequence diagram retry khi branch offline.
5. Sequence diagram read-through từ HQ sang branch.

### Bảng so sánh tập trung và phân tán

| Tiêu chí | CSDL tập trung | Hệ thống Tech Store phân tán |
|---|---|---|
| Lưu trữ | Một DB chính | Nhiều DB theo node |
| DBMS | Một hệ quản trị | SQL Server + MySQL + PostgreSQL |
| Đọc dữ liệu chi nhánh | Qua DB trung tâm | Đọc trực tiếp DB chi nhánh hoặc qua gateway |
| Ghi master data sản phẩm | Một nơi | HQ ghi, branch nhận sync |
| Nhất quán | Mạnh trong một DB | Eventual consistency cho dữ liệu replicated |
| Khi branch service down | Không áp dụng | HQ vẫn ghi, branch nhận sau retry |
| Độ phức tạp | Thấp | Cao hơn do sync, retry, health check |

### Câu chữ nên dùng trong báo cáo

Nên dùng:

- "Hệ thống mô phỏng CSDL phân tán dị hệ quản trị."
- "Dữ liệu nhân viên được phân mảnh ngang theo node."
- "Sản phẩm được nhân bản bất đồng bộ từ HQ xuống branch bằng outbox/event log."
- "Hệ thống thể hiện eventual consistency trong luồng đồng bộ sản phẩm."
- "Trụ sở đóng vai trò gateway để che giấu vị trí dữ liệu chi nhánh."

Tránh dùng quá mạnh:

- "Event sourcing hoàn chỉnh."
- "Vertical fragmentation vật lý" nếu chỉ ẩn field bằng API.
- "Hệ thống AP toàn phần."
- "Distributed transaction/Saga đầy đủ" nếu chưa có rollback/compensating action thật.

---

## Thứ tự ưu tiên đề xuất

```text
Bắt buộc để báo cáo vững:
  [1] Làm rõ phân mảnh NHAN_VIEN và loai_sp.
  [2] Demo eventual consistency cho sản phẩm.
  [3] Tài liệu/diagram phân bố dữ liệu.

Nên làm để tăng điểm:
  [4] Retry tự động khi branch service offline.
  [5] Health endpoint tổng hợp.
  [6] Retry thủ công và dead_letter cho event lỗi.

Điểm cộng:
  [7] Sync loai_sp hoặc NCC từ HQ xuống branch.
  [8] Dashboard health trên frontend.
  [9] Sync nhân viên Branch -> HQ dạng log/report, không nhất thiết merge vào bảng chính.
```

---

## Mapping lý thuyết vào code

| Khái niệm | Minh chứng nên dùng |
|---|---|
| Horizontal fragmentation | `NHAN_VIEN` theo node; `loai_sp.ma_chi_nhanh` |
| Replication | `SAN_PHAM` HQ -> branch, `NCC`/`loai_sp` nếu mở rộng |
| Asynchronous replication | Service dispatch/apply event |
| Transactional outbox | `product_sync_events` tại HQ |
| Idempotent consumer | Branch bỏ qua event đã có `event_id` trong `sync_log` |
| Eventual consistency | Demo branch offline rồi retry |
| Location transparency | API HQ `/api/chi-nhanh/{ma}/...` đọc đúng DB branch |
| Heterogeneous DBMS | SQL Server + MySQL + PostgreSQL |
| Access-controlled projection | Ẩn `luong`, `cccd`, `sdt` theo role |

