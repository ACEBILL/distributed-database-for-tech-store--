# Phân tán dữ liệu trong hệ thống

Ngày cập nhật: 2026-05-12

Tài liệu này mô tả cách repository hiện tại phân bố dữ liệu trên các node CSDL, luồng đồng bộ, truy vấn phân tán và đánh giá mức độ hợp lý của thiết kế.

## 1. Tổng quan kiến trúc phân tán

Hệ thống mô phỏng chuỗi cửa hàng công nghệ với 3 node CSDL chính:

| Node | DBMS | Vai trò | Container/API |
| --- | --- | --- | --- |
| Trụ sở | Microsoft SQL Server | Node điều phối, giữ master data và outbox chính | `tru-so-backend`, `tru-so-service` |
| CN01 | MySQL | Node chi nhánh Hà Nội, lưu dữ liệu vận hành cục bộ | `mysql-backend`, `mysql-service` |
| CN02 | PostgreSQL | Node chi nhánh TP.HCM, lưu dữ liệu vận hành cục bộ | `postgre-backend`, `postgre-service` |
| Redis | Redis | Cache danh sách sản phẩm | `redis-cache` |

Trụ sở không chỉ đọc SQL Server. Backend trụ sở có middleware đa DBMS trong `tru_so/backend/db.py`:

- `query_db()` / `execute_db()` đọc ghi DB hiện tại của service.
- `query_branch_db(ma_chi_nhanh, ...)` / `execute_branch_db(ma_chi_nhanh, ...)` tra cấu hình branch từ biến môi trường rồi kết nối đúng MySQL/PostgreSQL.
- Client gọi API trụ sở không cần biết dữ liệu đang nằm ở SQL Server, MySQL hay PostgreSQL. Đây là location transparency ở tầng API.

## 2. Phân bố dữ liệu theo bảng

| Bảng / nhóm dữ liệu | Trụ sở SQL Server | CN01 MySQL | CN02 PostgreSQL | Kiểu phân tán |
| --- | --- | --- | --- | --- |
| `chi_nhanh` | Master | Seed/reference local | Seed/reference local | Dữ liệu tham chiếu |
| `loai_sp` | Master | Bản sao local | Bản sao local | Dữ liệu tham chiếu, có replicate |
| `NCC` | Master/seed | Seed local | Seed local | Dữ liệu tham chiếu, hiện chưa có sync tự động |
| `SAN_PHAM` | Master catalog | Replica + có thể ghi cục bộ | Replica + có thể ghi cục bộ | Replication theo event |
| `NHAN_VIEN` | Nhân viên trụ sở | Nhân viên CN01 | Nhân viên CN02 | Phân mảnh ngang |
| `phong_ban` | Phòng ban trụ sở | Phòng ban CN01 | Phòng ban CN02 | Phân mảnh ngang/reference local |
| `HOA_DON`, `CT_HOA_DON` | Không lưu local | Hóa đơn CN01 | Hóa đơn CN02 | Phân mảnh ngang theo chi nhánh |
| `product_sync_events` | Có | Không | Không | Outbox trụ sở -> chi nhánh |
| `sync_log` | Không | Có | Có | Idempotency/audit event nhận từ trụ sở |
| `branch_sync_events` | Không | Có | Có | Outbox chi nhánh -> trụ sở |
| `branch_received_events` | Có | Không | Không | Idempotency/audit event nhận từ chi nhánh |

## 3. Luồng dữ liệu sản phẩm

### 3.1. Trụ sở tạo/sửa/xóa sản phẩm

1. API trụ sở ghi `SAN_PHAM` trong SQL Server qua `tru_so/backend/services/product_service.py`.
2. Service tạo event trong `product_sync_events` qua `create_product_sync_event()`.
3. Mỗi chi nhánh đang có trong bảng `chi_nhanh` nhận một event riêng, có `target_branch` và `version`.
4. `tru-so-service` dispatch event đến service của chi nhánh theo map:
   - `CN01 -> mysql-service`
   - `CN02 -> postgre-service`
5. Service chi nhánh gọi internal API `/api/internal/products/apply-change`.
6. Backend chi nhánh upsert vào `SAN_PHAM` local, ghi `sync_log`.
7. Nếu `event_id` đã tồn tại trong `sync_log`, event bị ignore để tránh apply trùng.
8. Trụ sở cập nhật trạng thái event: `pending`, `sent`, `failed`, `dead_letter`.

Kết quả: `SAN_PHAM` là bảng master ở trụ sở, nhưng được replicate xuống các chi nhánh để chi nhánh đọc nhanh và bán hàng ngay cả khi không cần join trực tiếp về SQL Server.

### 3.2. Chi nhánh tạo/sửa/xóa sản phẩm

1. API chi nhánh ghi `SAN_PHAM` local.
2. Backend chi nhánh tạo event trong `branch_sync_events`.
3. `mysql-service`/`postgre-service` forward event lên `tru-so-service`.
4. Trụ sở gọi internal API `/api/internal/products/apply-change`.
5. SQL Server apply thay đổi vào `SAN_PHAM`, ghi `branch_received_events`.
6. Sau khi apply thành công, trụ sở fan-out tiếp event sang các chi nhánh khác, loại trừ chi nhánh nguồn để tránh vòng lặp.

Kết quả: sản phẩm có khả năng đồng bộ hai chiều. Trụ sở vẫn là nơi hợp nhất, còn chi nhánh có quyền tạo/sửa/xóa sản phẩm local và đẩy lên trung tâm.

## 4. Luồng dữ liệu danh mục `loai_sp`

Trước đây `loai_sp` ở chi nhánh chỉ đến từ seed ban đầu. Nếu trụ sở tạo danh mục mới, sản phẩm dùng `ma_loai_sp` mới có thể sync xuống chi nhánh thất bại vì FK hoặc JOIN với `loai_sp` không có dòng tương ứng.

Hiện tại đã bổ sung luồng đơn giản trong `tru_so/backend/services/category_service.py`:

1. `create_category()` insert danh mục vào `loai_sp` SQL Server, đọc lại category vừa tạo, rồi `sync_category_to_branches()` upsert xuống tất cả chi nhánh có cấu hình DB.
2. `update_category()` update SQL Server, đọc lại category sau update, rồi upsert lại xuống chi nhánh.
3. `delete_category()` xóa SQL Server, nếu có dòng bị xóa thì gọi `delete_category_in_branches()` để xóa ở các chi nhánh.
4. Câu lệnh upsert phù hợp từng DBMS:
   - MySQL: `ON DUPLICATE KEY UPDATE`
   - PostgreSQL: `ON CONFLICT DO UPDATE`
   - SQL Server branch nếu có: `MERGE`

Đây là cách hợp lý cho danh mục vì danh mục ít thay đổi, không có luồng tạo danh mục từ chi nhánh, và cần đồng bộ trước khi replicate sản phẩm. Việc bổ sung update giúp tên danh mục không bị lệch giữa các node.

Giới hạn hiện tại:

- Nếu chi nhánh chưa có bản ghi `chi_nhanh` tương ứng, FK `loai_sp.ma_chi_nhanh` vẫn có thể fail. Hiện seed đang có `CN01`, `CN02`.
- Xóa danh mục là hard delete. Nếu chi nhánh còn sản phẩm tham chiếu category đó, FK trên chi nhánh có thể fail. Về nghiệp vụ, nên ưu tiên soft delete/trạng thái thay vì xóa vật lý.
- Đây là sync trực tiếp trong request, không có outbox riêng cho danh mục. Chấp nhận được cho demo và dữ liệu ít thay đổi, nhưng nếu một chi nhánh mất kết nối thì request category có thể lỗi và cần thao tác lại.

## 5. Luồng dữ liệu nhân viên

Nhân viên là phân mảnh ngang theo vị trí:

- SQL Server lưu nhân viên trụ sở.
- MySQL lưu nhân viên CN01.
- PostgreSQL lưu nhân viên CN02.

Trụ sở có thể đọc nhân viên chi nhánh bằng `query_branch_db()`:

- `GET /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien` đọc trực tiếp từ DB chi nhánh.
- `GET /api/nhan-vien/tat-ca-chi-nhanh` gom dữ liệu từ SQL Server + MySQL + PostgreSQL, gắn thêm `source_node` và `db_engine`.

Trụ sở cũng có API ghi nhân viên vào chi nhánh qua `execute_branch_db()`:

- `create_employee_in_branch()`
- `update_employee_in_branch()`
- `soft_delete_employee_in_branch()`

Đánh giá: cách này hợp lý cho nhân sự vì nhân viên gắn với nơi làm việc, ít cần replicate toàn bộ sang các node khác. Khi cần báo cáo toàn cục, trụ sở query phân tán và merge response.

## 6. Luồng dữ liệu hóa đơn và doanh thu

Hóa đơn là dữ liệu vận hành cục bộ của chi nhánh:

- `HOA_DON`, `CT_HOA_DON` nằm tại MySQL/PostgreSQL.
- Trụ sở không lưu hóa đơn local.
- `tru_so/backend/services/invoice_service.py` đọc trực tiếp từ từng DB chi nhánh để:
  - lấy danh sách hóa đơn theo chi nhánh,
  - lấy chi tiết hóa đơn,
  - tổng hợp doanh thu tất cả chi nhánh.

Đánh giá: đây là phân mảnh ngang đúng với nghiệp vụ bán lẻ, vì hóa đơn phát sinh tại chi nhánh. Tuy nhiên nếu số chi nhánh lớn, query tổng hợp trực tiếp tất cả DB sẽ chậm; nên có kho dữ liệu báo cáo hoặc job ETL riêng.

## 7. Truy vấn phân tán và thống kê phân mảnh

Hệ thống có 2 endpoint minh chứng phân tán rõ nhất:

| Endpoint | Chức năng |
| --- | --- |
| `GET /api/nhan-vien/tat-ca-chi-nhanh` | Distributed query nhân viên từ SQL Server + MySQL + PostgreSQL |
| `GET /api/thong-ke/phan-manh` | Đếm `SAN_PHAM` và `NHAN_VIEN` trên từng node |

`get_all_employees_distributed_for_api()` bắt lỗi theo từng node. Nếu một chi nhánh lỗi kết nối, response vẫn có thể trả dữ liệu node khác và gắn `error` cho node lỗi. Đây là điểm tốt cho fault tolerance ở mức API.

## 8. Nhất quán dữ liệu và retry

Sản phẩm được đồng bộ theo eventual consistency:

- Ghi business trước.
- Ghi event outbox.
- Service dispatch event.
- Consumer apply event và ghi log idempotency.

Các bảng hỗ trợ:

- `product_sync_events`: outbox trụ sở, có `status`, `message`, `retry_count`, `last_error`.
- `sync_log`: log chi nhánh đã nhận/applied event nào.
- `branch_sync_events`: outbox chi nhánh khi chi nhánh thay đổi sản phẩm.
- `branch_received_events`: log trụ sở đã nhận/applied event nào từ chi nhánh.

Có retry failed event và dead letter sau số lần retry tối đa. Cách này hợp lý hơn việc gọi trực tiếp DB chi nhánh trong cùng transaction vì giảm coupling và cho phép chi nhánh tạm thời mất kết nối.

## 9. Đánh giá tổng thể

### Điểm hợp lý

- Dùng mô hình dị hệ quản trị CSDL rõ ràng: SQL Server, MySQL, PostgreSQL.
- Phân mảnh ngang `NHAN_VIEN`, `HOA_DON` theo chi nhánh là đúng với nghiệp vụ.
- `SAN_PHAM` replicate xuống chi nhánh giúp đọc local nhanh và chi nhánh có thể vận hành độc lập hơn.
- Outbox + `sync_log` tạo audit trail và idempotency, phù hợp với đồng bộ bất đồng bộ.
- API trụ sở che giấu vị trí vật lý của DB qua `query_branch_db`, tốt cho location transparency.
- Thống kê phân mảnh và distributed query là bằng chứng tốt cho đồ án CSDL phân tán.
- Sync `loai_sp` từ trụ sở xuống chi nhánh giúp giải quyết lỗi tham chiếu tiềm ẩn cho sản phẩm mới.

### Điểm chưa hợp lý / rủi ro

- `NCC` vẫn là reference data seed thủ công, chưa có sync tự động. Nếu thêm nhà cung cấp mới ở trụ sở, sản phẩm dùng `ma_ncc` mới có thể fail FK ở chi nhánh.
- `loai_sp` đã sync create/update/delete trực tiếp, nhưng chưa có outbox/retry riêng; hard delete category có thể gây lỗi FK nếu chi nhánh còn sản phẩm liên quan.
- Dispatch sản phẩm đang tạo event per branch và gọi service ngay trong request. Nếu branch chậm, request có thể bị ảnh hưởng; outbox nên tách worker nền đọc pending event.
- Distributed query nhân viên/doanh thu đang đọc tuần tự từng node. Khi số chi nhánh tăng, độ trễ tăng tuyến tính.
- Chưa có conflict resolution rõ ràng nếu cùng một `ma_sp` bị sửa gần đồng thời ở trụ sở và chi nhánh. Hiện `version` mang tính thứ tự event, nhưng chưa có rule "last-write-wins" hoặc field-level merge chính thức.
- Hiện có replication sản phẩm hai chiều, trong khi danh mục/NCC lại chủ yếu một chiều/seed. Các bảng tham chiếu cần chính sách nhất quán hơn.
- Một số endpoint branch bắt lỗi sync bằng `except Exception: pass` khi tạo event lên trụ sở. Cách này giúp API không fail, nhưng có thể che giấu việc đồng bộ thất bại nếu không theo dõi `branch_sync_events`.

## 10. Kết luận

Thiết kế hiện tại là hợp lý cho một đồ án CSDL phân tán cấp chuỗi cửa hàng:

- `NHAN_VIEN` và `HOA_DON` nên phân mảnh ngang theo chi nhánh.
- `SAN_PHAM` nên replicate xuống chi nhánh để hỗ trợ đọc local và bán hàng.
- `loai_sp`, `NCC`, `chi_nhanh` là reference data nên cần có chiến lược sync từ trụ sở xuống chi nhánh.
- Trụ sở đóng vai trò aggregator và coordinator là phù hợp.

Mức độ hợp lý hiện tại: tốt cho demo và đồ án, đã thể hiện đủ các ý CSDL phân tán quan trọng như phân mảnh ngang, replication, outbox, idempotency, distributed query và location transparency.

Nếu nâng lên gần production, nên ưu tiên:

1. Sync thêm `NCC`.
2. Đổi xóa `loai_sp` sang soft delete hoặc thêm pre-check sản phẩm trên tất cả chi nhánh trước khi hard delete.
3. Tách worker nền xử lý `product_sync_events` và `branch_sync_events`.
4. Chạy distributed query song song thay vì tuần tự.
5. Thêm conflict resolution cho sửa sản phẩm hai chiều.
6. Thêm dashboard theo dõi pending/failed/dead-letter event.
