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

Nguyên tắc nghiệp vụ quan trọng:

- Trụ sở là node điều phối và báo cáo toàn hệ thống. Trụ sở quản lý catalog sản phẩm, danh mục dùng chung, xem/tổng hợp thông tin nhân viên và doanh thu của các chi nhánh.
- CN01 và CN02 là hai cửa hàng độc lập. Dữ liệu vận hành của CN01 thuộc CN01; dữ liệu vận hành của CN02 thuộc CN02. Hai chi nhánh không ghi trực tiếp dữ liệu nghiệp vụ của nhau trong chế độ bình thường.
- Chi nhánh quản lý nhân viên, hóa đơn và nghiệp vụ bán hàng phát sinh tại chính chi nhánh đó. Dữ liệu cần cho báo cáo toàn hệ thống được trụ sở đọc/tổng hợp hoặc nhận qua cơ chế đồng bộ.
- Nếu bổ sung replica/failover giữa các chi nhánh, bản sao dữ liệu chi nhánh khác chỉ nên dùng cho đọc dự phòng hoặc chỉ được ghi khi có cơ chế chuyển quyền xử lý rõ ràng. Không coi CN01 và CN02 là một kho dữ liệu dùng chung.

## 2. Phân bố dữ liệu theo bảng

| Bảng / nhóm dữ liệu | Trụ sở SQL Server | CN01 MySQL | CN02 PostgreSQL | Kiểu phân tán |
| --- | --- | --- | --- | --- |
| `chi_nhanh` | Master | Seed/reference local | Seed/reference local | Dữ liệu tham chiếu |
| `loai_sp` | Master | Bản sao local | Bản sao local | Dữ liệu tham chiếu, có replicate |
| `NCC` | Master/seed | Seed local | Seed local | Dữ liệu tham chiếu, hiện chưa có sync tự động |
| `SAN_PHAM` | Master catalog | Replica catalog để bán hàng/đọc local | Replica catalog để bán hàng/đọc local | Replication một chiều từ trụ sở |
| `NHAN_VIEN` | Nhân viên trụ sở | Nhân viên CN01 | Nhân viên CN02 | Phân mảnh ngang |
| `phong_ban` | Phòng ban trụ sở | Phòng ban CN01 | Phòng ban CN02 | Phân mảnh ngang/reference local |
| `HOA_DON`, `CT_HOA_DON` | Không lưu local | Hóa đơn CN01 | Hóa đơn CN02 | Phân mảnh ngang theo chi nhánh |
| `product_sync_events` | Có | Không | Không | Outbox trụ sở -> chi nhánh |
| `sync_log` | Không | Có | Có | Idempotency/audit event nhận từ trụ sở |
| `branch_sync_events` | Không | Có thể có nếu mở rộng | Có thể có nếu mở rộng | Dự phòng cho luồng chi nhánh gửi dữ liệu/event lên trụ sở |
| `branch_received_events` | Có thể có nếu mở rộng | Không | Không | Audit/idempotency khi trụ sở nhận event từ chi nhánh |

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

### 3.2. Vai trò của chi nhánh với sản phẩm

Theo nghiệp vụ hiện tại, chi nhánh không phải nơi quản lý master sản phẩm. CN01/CN02 dùng bản sao `SAN_PHAM` local để tra cứu, lập hóa đơn và bán hàng khi vận hành tại cửa hàng.

Nếu chi nhánh cần đề xuất sản phẩm mới hoặc báo thông tin thay đổi, luồng đúng nên là gửi yêu cầu/event lên trụ sở để duyệt và cập nhật master catalog. Sau đó trụ sở mới phát event xuống các chi nhánh. Cách này giữ rõ quyền sở hữu dữ liệu: trụ sở sở hữu catalog, chi nhánh sở hữu nghiệp vụ bán hàng của mình.

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

Trong code hiện tại, trụ sở cũng có API ghi nhân viên vào chi nhánh qua `execute_branch_db()`:

- `create_employee_in_branch()`
- `update_employee_in_branch()`
- `soft_delete_employee_in_branch()`

Về nghiệp vụ, nên hiểu đây là quyền quản trị/gateway của trụ sở, không phải trụ sở sở hữu dữ liệu nhân viên chi nhánh. Chủ sở hữu vận hành của nhân viên CN01 là CN01, chủ sở hữu vận hành của nhân viên CN02 là CN02.

Đánh giá: cách này hợp lý cho nhân sự vì nhân viên gắn với nơi làm việc. Nhân viên CN01 và nhân viên CN02 là hai phân mảnh độc lập, không phải dữ liệu dùng chung giữa hai cửa hàng. Khi cần báo cáo toàn cục, trụ sở query phân tán và merge response.

## 6. Luồng dữ liệu hóa đơn và doanh thu

Hóa đơn là dữ liệu vận hành cục bộ của chi nhánh:

- `HOA_DON`, `CT_HOA_DON` nằm tại MySQL/PostgreSQL.
- Trụ sở không lưu hóa đơn local.
- `tru_so/backend/services/invoice_service.py` đọc trực tiếp từ từng DB chi nhánh để:
  - lấy danh sách hóa đơn theo chi nhánh,
  - lấy chi tiết hóa đơn,
  - tổng hợp doanh thu tất cả chi nhánh.

Đánh giá: đây là phân mảnh ngang đúng với nghiệp vụ bán lẻ, vì hóa đơn phát sinh tại chi nhánh. Tuy nhiên nếu số chi nhánh lớn, query tổng hợp trực tiếp tất cả DB sẽ chậm; nên có kho dữ liệu báo cáo hoặc job ETL riêng.

Điểm cần làm rõ: hóa đơn CN01 và hóa đơn CN02 độc lập nhau. CN01 không tạo/sửa hóa đơn CN02 trong chế độ bình thường và ngược lại. Trụ sở chỉ đọc/tổng hợp doanh thu để báo cáo, không biến dữ liệu hóa đơn của hai chi nhánh thành một bảng vận hành chung.

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
- `branch_sync_events`: outbox chi nhánh nếu mở rộng luồng gửi dữ liệu/event vận hành lên trụ sở.
- `branch_received_events`: log trụ sở đã nhận/applied event nào từ chi nhánh nếu dùng event chi nhánh -> trụ sở.

Có retry failed event và dead letter sau số lần retry tối đa. Cách này hợp lý hơn việc gọi trực tiếp DB chi nhánh trong cùng transaction vì giảm coupling và cho phép chi nhánh tạm thời mất kết nối.

## 9. Đánh giá tổng thể

### Điểm hợp lý

- Dùng mô hình dị hệ quản trị CSDL rõ ràng: SQL Server, MySQL, PostgreSQL.
- Phân mảnh ngang `NHAN_VIEN`, `HOA_DON` theo chi nhánh là đúng với nghiệp vụ.
- `SAN_PHAM` replicate xuống chi nhánh giúp đọc local nhanh và chi nhánh có thể bán hàng độc lập hơn, trong khi master catalog vẫn thuộc trụ sở.
- Outbox + `sync_log` tạo audit trail và idempotency, phù hợp với đồng bộ bất đồng bộ.
- API trụ sở che giấu vị trí vật lý của DB qua `query_branch_db`, tốt cho location transparency.
- Thống kê phân mảnh và distributed query là bằng chứng tốt cho đồ án CSDL phân tán.
- Sync `loai_sp` từ trụ sở xuống chi nhánh giúp giải quyết lỗi tham chiếu tiềm ẩn cho sản phẩm mới.

### Điểm chưa hợp lý / rủi ro

- `NCC` vẫn là reference data seed thủ công, chưa có sync tự động. Nếu thêm nhà cung cấp mới ở trụ sở, sản phẩm dùng `ma_ncc` mới có thể fail FK ở chi nhánh.
- `loai_sp` đã sync create/update/delete trực tiếp, nhưng chưa có outbox/retry riêng; hard delete category có thể gây lỗi FK nếu chi nhánh còn sản phẩm liên quan.
- Dispatch sản phẩm đang tạo event per branch và gọi service ngay trong request. Nếu branch chậm, request có thể bị ảnh hưởng; outbox nên tách worker nền đọc pending event.
- Distributed query nhân viên/doanh thu đang đọc tuần tự từng node. Khi số chi nhánh tăng, độ trễ tăng tuyến tính.
- Nếu sau này cho chi nhánh đề xuất/sửa sản phẩm rồi gửi lên trụ sở, cần có workflow duyệt hoặc conflict rule rõ ràng. Với nghiệp vụ hiện tại, cách đơn giản hơn là giữ sản phẩm một chiều: trụ sở sửa master, chi nhánh nhận bản sao.
- Nếu bật luồng chi nhánh gửi thay đổi sản phẩm lên trụ sở, cần ràng buộc lại quyền sở hữu dữ liệu để không phá vỡ nguyên tắc trụ sở là master catalog.
- Một số endpoint branch bắt lỗi sync bằng `except Exception: pass` khi tạo event lên trụ sở. Cách này giúp API không fail, nhưng có thể che giấu việc đồng bộ thất bại nếu không theo dõi `branch_sync_events`.

## 10. Phương án chịu lỗi khi server chi nhánh sập

Nếu mục tiêu là: trụ sở vẫn hoạt động, một chi nhánh bị sập nhưng người dùng của chi nhánh đó vẫn có thể làm việc gần như bình thường, phương án đơn giản và phù hợp nhất với kiến trúc hiện tại là **replica dữ liệu vận hành của chi nhánh lên trụ sở**.

### 10.1. Nguyên tắc

- Chế độ bình thường: CN01/CN02 vẫn là owner dữ liệu vận hành của chính mình.
- Trụ sở giữ bản sao gần thời gian thực của dữ liệu chi nhánh để báo cáo và dự phòng.
- Khi một chi nhánh sập, trụ sở được chuyển sang vai trò `acting-owner` tạm thời cho chi nhánh đó.
- Khi chi nhánh sống lại, các thay đổi phát sinh tại trụ sở trong thời gian failover được đẩy ngược về DB chi nhánh.

Mô hình này dễ hơn việc để CN01 và CN02 replicate chéo toàn bộ dữ liệu cho nhau, vì chỉ cần một điểm dự phòng trung tâm và tránh biến các chi nhánh độc lập thành một cụm active-active phức tạp.

### 10.2. Dữ liệu cần replicate lên trụ sở

Các bảng nên replicate từ chi nhánh lên SQL Server trụ sở:

| Dữ liệu | Owner bình thường | Replica tại trụ sở | Mục đích |
| --- | --- | --- | --- |
| `NHAN_VIEN` | Chi nhánh | Có | Quản trị, xem nhân sự, failover |
| `phong_ban` | Chi nhánh | Có | Tham chiếu nhân viên |
| `HOA_DON` | Chi nhánh | Có | Báo cáo doanh thu, failover bán hàng |
| `CT_HOA_DON` | Chi nhánh | Có | Chi tiết hóa đơn, doanh thu theo sản phẩm |
| `SAN_PHAM` | Trụ sở | Master sẵn có | Catalog bán hàng |

Trên SQL Server có thể tạo các bảng replica riêng, ví dụ:

- `branch_nhan_vien_replica`
- `branch_phong_ban_replica`
- `branch_hoa_don_replica`
- `branch_ct_hoa_don_replica`
- `branch_replication_inbox`
- `central_failover_events`

Mỗi bảng replica cần có `ma_chi_nhanh`, `source_branch`, `updated_at`, `version` hoặc `event_id` để biết dữ liệu thuộc chi nhánh nào và chống apply trùng.

### 10.3. Luồng bình thường

1. CN01 tạo/sửa nhân viên hoặc hóa đơn trong MySQL local.
2. CN01 ghi thêm event vào outbox local, ví dụ `branch_sync_events`.
3. `mysql-service` gửi event lên `tru-so-service`.
4. Trụ sở kiểm tra `event_id` trong `branch_replication_inbox`.
5. Nếu chưa nhận, trụ sở upsert dữ liệu vào bảng replica SQL Server.
6. Trụ sở dùng replica này cho báo cáo nhanh, thay vì lúc nào cũng query trực tiếp DB chi nhánh.

CN02 làm tương tự với PostgreSQL.

### 10.4. Luồng khi chi nhánh sập

Ví dụ CN01 sập nhưng trụ sở còn hoạt động:

1. Healthcheck phát hiện `mysql-backend` hoặc MySQL CN01 không truy cập được.
2. Trụ sở đánh dấu trạng thái `CN01 = failover_to_hq`.
3. Người dùng CN01 đăng nhập vào portal/API dự phòng tại trụ sở.
4. Các thao tác của CN01 trong thời gian sự cố được ghi vào bảng replica tại trụ sở với `ma_chi_nhanh = 'CN01'`.
5. Đồng thời trụ sở ghi event vào `central_failover_events`.
6. Khi CN01 hoạt động lại, trụ sở replay `central_failover_events` về MySQL CN01.
7. Sau khi CN01 bắt kịp dữ liệu, trạng thái chuyển lại `CN01 = normal`.

Điểm quan trọng: trong thời gian failover, chỉ trụ sở được phép ghi thay CN01. Điều này tránh lỗi split-brain, tức là CN01 thật và trụ sở cùng ghi dữ liệu CN01 rồi xung đột khi kết nối lại.

### 10.5. Điều kiện để chi nhánh "hoạt động bình thường"

Chỉ replicate dữ liệu là chưa đủ. Khi server chi nhánh sập, người dùng cần có đường truy cập thay thế:

- frontend/API dự phòng tại trụ sở cho từng chi nhánh,
- routing hoặc link dự phòng, ví dụ `/failover/cn01`,
- xác thực người dùng chi nhánh bằng dữ liệu replica tại trụ sở,
- quyền ghi tạm thời theo trạng thái failover.

Với điều kiện trụ sở không sập, cách này đáp ứng tốt tiêu chí: một server chi nhánh bị sập nhưng chi nhánh đó vẫn có thể tiếp tục bán hàng/quản lý hóa đơn/nhân viên qua trụ sở, sau đó đồng bộ ngược khi server chi nhánh phục hồi.

### 10.6. Phần đã triển khai trong repository

- Backend chi nhánh có `services/branch_replication_service.py` để tạo outbox `branch_replication_events`.
- Khi chi nhánh tạo/cập nhật/ngưng nhân viên hoặc tạo/xóa hóa đơn, backend chi nhánh phát event replication lên `mysql-service` / `postgre-service`.
- `tru-so-service` nhận event tại `/api/service/branch-replication/receive-from-branch` và forward vào backend trụ sở.
- Backend trụ sở apply event vào các bảng replica SQL Server: `branch_employee_replica`, `branch_hoa_don_replica`, `branch_ct_hoa_don_replica`; bảng `branch_replication_inbox` chống nhận trùng event.
- Khi API trụ sở đọc nhân viên/hóa đơn/doanh thu của chi nhánh mà DB chi nhánh không truy cập được, hệ thống fallback sang replica tại trụ sở và trả `source = hq_replica`.
- Trụ sở có endpoint failover hóa đơn: `POST /api/chi-nhanh/<ma_chi_nhanh>/hoa-don/failover` và `DELETE /api/chi-nhanh/<ma_chi_nhanh>/hoa-don/<ma_hd>/failover`. Các API nhân viên theo chi nhánh cũng fallback ghi vào replica nếu DB chi nhánh lỗi.

## 11. Kết luận

Thiết kế hiện tại là hợp lý cho một đồ án CSDL phân tán cấp chuỗi cửa hàng:

- `NHAN_VIEN` và `HOA_DON` nên phân mảnh ngang theo chi nhánh.
- `SAN_PHAM` nên replicate một chiều từ trụ sở xuống chi nhánh để hỗ trợ đọc local và bán hàng.
- `loai_sp`, `NCC`, `chi_nhanh` là reference data nên cần có chiến lược sync từ trụ sở xuống chi nhánh.
- Trụ sở đóng vai trò aggregator và coordinator là phù hợp.

Mức độ hợp lý hiện tại: tốt cho demo và đồ án, đã thể hiện đủ các ý CSDL phân tán quan trọng như phân mảnh ngang, replication, outbox, idempotency, distributed query và location transparency.

Nếu nâng lên gần production, nên ưu tiên:

1. Sync thêm `NCC`.
2. Đổi xóa `loai_sp` sang soft delete hoặc thêm pre-check sản phẩm trên tất cả chi nhánh trước khi hard delete.
3. Tách worker nền xử lý `product_sync_events` và `branch_sync_events`.
4. Chạy distributed query song song thay vì tuần tự.
5. Nếu mở rộng luồng chi nhánh đề xuất/sửa sản phẩm, thêm workflow duyệt hoặc conflict rule trước khi ghi vào master catalog.
6. Thêm dashboard theo dõi pending/failed/dead-letter event.
