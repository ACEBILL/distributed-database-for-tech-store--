# Roadmap final - CSDL phân tán Tech Store

Tài liệu này cô đọng hai bản roadmap trước thành một kế hoạch triển khai và báo cáo cuối cùng. Mục tiêu là trình bày hệ thống như một mô hình CSDL phân tán dị hệ quản trị, có phân bố dữ liệu rõ ràng, đồng bộ bất đồng bộ và demo eventual consistency.

## 1. Mô hình tổng thể

```text
Frontend Portal
  |
  v
Backend trụ sở / Gateway :5000
  |-- SQL Server HQ
  |-- Redis cache
  |-- read-through sang DB chi nhánh
  |
  v
Service trụ sở :5010
  |-- dispatch event sản phẩm
  |
  +--> Service CN01 :5011 -> Backend CN01 :5001 -> MySQL
  |
  `--> Service CN02 :5012 -> Backend CN02 :5002 -> PostgreSQL
```

Vai trò từng node:

| Node | DBMS | Vai trò |
|---|---|---|
| Trụ sở | SQL Server | Master data, gateway, outbox đồng bộ |
| CN01 | MySQL | Dữ liệu chi nhánh CN01, nhận event từ HQ |
| CN02 | PostgreSQL | Dữ liệu chi nhánh CN02, nhận event từ HQ |

## 2. Trạng thái hiện tại

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| 3 node DB khác hệ quản trị | Hoàn thành | SQL Server, MySQL, PostgreSQL |
| Backend riêng cho trụ sở/CN01/CN02 | Hoàn thành | Flask API |
| Service riêng cho trụ sở/CN01/CN02 | Hoàn thành | Integration boundary |
| JWT phân quyền `central` / `branch` | Hoàn thành | Đã phân biệt scope |
| Swagger cho sản phẩm/nhân viên | Hoàn thành | Có auto token demo |
| Read-through HQ -> branch DB | Hoàn thành | Sản phẩm, nhân viên, health |
| Đồng bộ sản phẩm HQ -> branch | Hoàn thành mức demo | `product_sync_events` + `sync_log` |
| Retry tự động khi branch offline | Hoàn thành mức demo | `tru-so-service` retry-due định kỳ, có API retry thủ công |
| Health endpoint tổng hợp | Hoàn thành | `GET /api/system/health` |
| Sync `loai_sp`, `NCC` | Chưa có | Điểm cộng |

## 3. Phân bố dữ liệu

| Entity | Chiến lược | Node lưu trữ | Ghi chú |
|---|---|---|---|
| `chi_nhanh` | Metadata trung tâm | HQ chính, branch có bản local tối thiểu | Không gọi là replicated nếu chỉ phụ thuộc HQ |
| `NHAN_VIEN` | Phân mảnh ngang theo node | HQ/CN01/CN02 | Mỗi node giữ nhân viên của mình |
| `phong_ban` | Dữ liệu cục bộ | Mỗi node | Phù hợp với tổ chức từng nơi |
| `loai_sp` | Phân mảnh ngang theo `ma_chi_nhanh` | HQ global catalog, branch subset | Cần API minh chứng theo branch |
| `NCC` | Reference data replicated | HQ -> branch | HQ là source of truth |
| `SAN_PHAM` | Master ở HQ, replicate bất đồng bộ | HQ + branch subset | Eventual consistency |
| `product_sync_events` | Transactional outbox / event log | HQ | Không gọi là event sourcing đầy đủ |
| `sync_log` | Audit log cục bộ | Branch | Chống apply trùng bằng `event_id` |

Ghi chú thuật ngữ:

- Ẩn `luong`, `cccd`, `sdt` theo role là **API-level vertical projection**, không phải vertical fragmentation vật lý.
- Luồng đồng bộ sản phẩm là **asynchronous replication bằng outbox pattern**, không phải event sourcing hoàn chỉnh.
- Hệ thống minh chứng **eventual consistency trong phạm vi HQ -> branch**, không nên nói toàn hệ thống là AP hoàn toàn.

## 4. Roadmap triển khai

### Giai đoạn 1 - Chốt phân mảnh dữ liệu

Mục tiêu: chứng minh dữ liệu được chia theo node, không chỉ là nhiều database chạy song song.

Việc cần làm:

- Bổ sung `GET /api/chi-nhanh/{ma_chi_nhanh}/loai-san-pham`. **Đã làm**.
- Test `GET /api/tru-so/nhan-vien`, `GET /api/chi-nhanh/CN01/nhan-vien`, `GET /api/chi-nhanh/CN02/nhan-vien`.
- Viết bảng mapping entity -> node trong báo cáo.
- Chụp kết quả HQ/CN01/CN02 khác nhau để minh chứng phân mảnh.

### Giai đoạn 2 - Hoàn thiện đồng bộ sản phẩm

Mục tiêu: biến product sync thành demo eventual consistency chạy được.

Việc cần làm:

- Thêm retry tự động cho `product_sync_events` khi branch service offline. **Đã làm mức demo qua worker trong `tru-so-service`**.
- Bổ sung cột/trạng thái nếu cần: `retry_count`, `last_error`, `next_retry_at`, `applied_at`, `dead_letter`. **Đã làm `retry_count`, `last_error`, `next_retry_at`, trạng thái `dead_letter`; không thêm `applied_at` ở HQ vì `sent` không đồng nghĩa `applied`**.
- Thêm retry thủ công:

```text
POST /api/tru-so/san-pham/sync-events/{event_id}/retry
POST /api/tru-so/san-pham/sync-events/retry-failed
```

Trạng thái đề xuất tại HQ (`product_sync_events`):

```text
pending -> sent
pending -> failed -> pending (retry)
failed  -> dead_letter
```

`sent` chỉ có nghĩa là HQ/service đã dispatch thành công sang branch, không đồng nghĩa trong bảng HQ có trạng thái `applied`.

Trạng thái tại branch (`sync_log`):

```text
received -> success/applied
received -> failed
duplicate -> ignored
```

Ghi chú: trong code hiện tại `sync_log.status` lưu thành công là `success`, còn response API trả về `status: "applied"`.

### Giai đoạn 3 - Demo eventual consistency

Kịch bản báo cáo:

1. Login trụ sở.
2. Tắt `mysql-service`.
3. Sửa sản phẩm thuộc CN01 tại HQ.
4. Kiểm tra event ở HQ có trạng thái `failed` hoặc `pending`.
5. Kiểm tra CN01 chưa nhận thay đổi.
6. Bật lại `mysql-service`.
7. Retry tự động hoặc retry thủ công.
8. Kiểm tra CN01 đã nhận thay đổi và `sync_log` có record.

Cách diễn đạt:

> Khi branch tạm thời không sẵn sàng, HQ vẫn ghi master data và lưu event vào outbox. Branch có thể trễ dữ liệu trong một khoảng thời gian, sau đó hội tụ nhờ retry. Đây là minh chứng cho eventual consistency dưới partial failure.

### Giai đoạn 4 - Health monitoring

Mục tiêu: quan sát được trạng thái toàn hệ thống phân tán.

Endpoint đề xuất:

```text
GET /api/system/health
```

Trạng thái: **đã làm**.

Payload mẫu:

```json
{
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

`last_sync_version` không tự có tại HQ. Khi tổng hợp health, HQ/service cần gọi branch endpoint hiện có:

```text
GET /api/internal/products/local-version
```

Nếu đi qua service chi nhánh thì dùng route service tương ứng:

```text
GET /api/service/products/local-version
```

### Giai đoạn 5 - Điểm cộng

Chỉ làm sau khi các phần bắt buộc đã chạy ổn:

- Sync `loai_sp` HQ -> branch.
- Sync `NCC` HQ -> branch.
- Dashboard health trên frontend trụ sở.
- Sync nhân viên Branch -> HQ dưới dạng log/report, không nhất thiết merge vào bảng nhân viên HQ.

## 5. Thứ tự ưu tiên cuối

```text
Bắt buộc:
  [1] Phân mảnh NHAN_VIEN và loai_sp rõ ràng.
  [2] Demo eventual consistency cho sản phẩm.
  [3] Tài liệu/diagram phân bố dữ liệu.

Nên có:
  [4] Retry tự động khi branch offline.
  [5] Health endpoint tổng hợp.
  [6] Retry thủ công/dead_letter cho event lỗi.

Điểm cộng:
  [7] Sync loai_sp hoặc NCC.
  [8] Dashboard health frontend.
  [9] Sync nhân viên Branch -> HQ dạng log/report.
```

## 6. Nội dung đưa vào báo cáo

Diagram nên có:

- Sơ đồ container/port/network.
- Sơ đồ phân bố dữ liệu theo bảng.
- Sequence diagram HQ ghi sản phẩm -> outbox -> service -> branch apply.
- Sequence diagram branch offline -> retry -> eventual consistency.
- Sequence diagram read-through từ HQ sang branch.

Từ khóa nên dùng:

- Heterogeneous distributed DBMS.
- Horizontal fragmentation.
- Replicated reference/master data.
- Transactional outbox.
- Asynchronous replication.
- Idempotent consumer.
- Eventual consistency.
- Location transparency.

Từ khóa nên tránh hoặc nói cẩn thận:

- Event sourcing hoàn chỉnh.
- Vertical fragmentation vật lý.
- AP toàn hệ thống.
- Distributed transaction đầy đủ.
- Saga đầy đủ nếu chưa có compensating action thật.

Known limitation nên nêu:

- `_next_version()` hiện lấy version theo kiểu `SELECT MAX(version) + 1`, chưa atomic. Nếu nhiều request tạo event đồng thời có thể sinh race condition hoặc trùng version; với demo tuần tự thì chấp nhận được, còn bản production nên dùng sequence/identity, transaction isolation phù hợp, unique constraint kèm retry, hoặc cơ chế lock.

## 7. Mapping lý thuyết vào code

| Lý thuyết | Minh chứng |
|---|---|
| Heterogeneous DBMS | SQL Server + MySQL + PostgreSQL |
| Horizontal fragmentation | `NHAN_VIEN` theo node, `loai_sp.ma_chi_nhanh` |
| Replication | `SAN_PHAM` HQ -> branch |
| Asynchronous replication | Service dispatch/apply event |
| Transactional outbox | `product_sync_events` tại HQ |
| Idempotent consumer | Branch bỏ qua `event_id` đã có trong `sync_log` |
| Eventual consistency | Demo branch offline rồi retry |
| Location transparency | HQ endpoint `/api/chi-nhanh/{ma}/...` |
| API-level projection | Ẩn `luong`, `cccd`, `sdt` theo role |
