# README Tester - Kiểm Thử Hệ Thống Đồng Bộ

Tài liệu này dùng để tester chạy và kiểm tra các phần mới đã thêm:

- Trụ sở tạo event đồng bộ sản phẩm khi thêm/sửa/ngừng bán sản phẩm.
- Service trụ sở gửi event sang service chi nhánh.
- Service chi nhánh nhận event, gọi backend local để upsert/soft delete sản phẩm.
- Chi nhánh ghi lịch sử xử lý vào `sync_log`.
- Trụ sở lưu event phát sinh vào `product_sync_events`.

## 1. Phạm Vi Sync Hiện Tại

Đồng bộ hiện tại đang ở mức **event-based one-way sync cho sản phẩm từ trụ sở sang chi nhánh**.

Đã có:

- Trụ sở là nguồn dữ liệu gốc của `SAN_PHAM`.
- Khi sửa sản phẩm ở API trụ sở, hệ thống tạo event:
  - `PRODUCT_CREATED`
  - `PRODUCT_UPDATED`
  - `PRODUCT_DELETED`
- Event được lưu ở SQL Server trong bảng `product_sync_events`.
- Service trụ sở gửi event sang đúng service chi nhánh theo `target_branch`.
- Chi nhánh nhận event qua API nội bộ:
  - `POST /api/service/products/apply-change`
  - `POST /api/service/products/apply-batch`
  - `GET /api/service/products/local-version`
  - `GET /api/service/products/sync-log`
- Chi nhánh ghi kết quả vào bảng `sync_log`.
- Có `X-Service-Token` để chặn user/frontend gọi trực tiếp API nội bộ.

Chưa có:

- Chưa đồng bộ hai chiều từ chi nhánh về trụ sở.
- Chưa đồng bộ nhân viên, phòng ban, nhà cung cấp, loại sản phẩm.
- Chưa có retry tự động cho event lỗi.
- Chưa có màn hình frontend riêng để xem sync log.
- Chưa có xử lý xung đột khi chi nhánh sửa cùng một sản phẩm.
- `apply-batch` đã có ở service chi nhánh, nhưng trụ sở hiện mới gửi từng event bằng `apply-change`.
- Việc xác định sản phẩm thuộc chi nhánh hiện đang dựa vào `loai_sp.ma_chi_nhanh`.

Nói ngắn gọn: **sync hiện tại đủ để demo luồng trụ sở sửa sản phẩm và chi nhánh nhận thay đổi**, chưa phải hệ thống đồng bộ phân tán đầy đủ cho tất cả bảng.

## 2. Chạy Hệ Thống

Ở root project:

```powershell
docker compose up -d --build --remove-orphans
```

Sau khi build xong, kiểm tra nhanh các service nội bộ đã có route đồng bộ mới chưa:

```powershell
$svcHeaders = @{ "X-Service-Token" = "dev-service-token-change-in-production" }

Invoke-RestMethod `
  -Uri "http://localhost:5011/api/service/products/local-version" `
  -Headers $svcHeaders

Invoke-RestMethod `
  -Uri "http://localhost:5012/api/service/products/local-version" `
  -Headers $svcHeaders
```

Kết quả mong đợi:

- Cả hai lệnh đều trả về `success = true`.
- Nếu bị `404 Not Found`, nghĩa là container service vẫn đang chạy image cũ.

Khi gặp `404`, rebuild lại riêng các service:

```powershell
docker compose up -d --build tru-so-service mysql-service postgre-service
```

Nếu vẫn còn `404`, chạy mạnh hơn bằng cách recreate container:

```powershell
docker compose up -d --build --force-recreate tru-so-service mysql-service postgre-service
```

Giải thích ngắn: backend có mount source code vào container nên nhiều thay đổi được reload nhanh hơn, còn các service `tru_so/service`, `mysql/service`, `postgre/service` được copy vào image khi build. Vì vậy sau khi sửa service mà không rebuild, route mới như `/api/service/products/local-version` sẽ chưa tồn tại trong container.

Kiểm tra container:

```powershell
docker compose ps
```

Kiểm tra log cần thiết:

```powershell
docker compose logs --tail=80 tru-so-backend tru-so-service mysql-backend mysql-service postgre-backend postgre-service
```

## 3. Thông Tin Port

| Thành phần | URL |
|---|---|
| Frontend trụ sở | `http://localhost:3000` |
| Backend API trụ sở | `http://localhost:5000` |
| Service trụ sở | `http://localhost:5010` |
| Backend CN01 MySQL | `http://localhost:5001` |
| Service CN01 MySQL | `http://localhost:5011` |
| Backend CN02 PostgreSQL | `http://localhost:5002` |
| Service CN02 PostgreSQL | `http://localhost:5012` |

Service token mặc định:

```powershell
dev-service-token-change-in-production
```

## 4. Test Nhanh CN01

`SP001` thuộc `CN01` vì sản phẩm này có `ma_loai_sp = LSP01`, và `LSP01` đang gắn `ma_chi_nhanh = CN01`.

### 4.1. Đăng Nhập Trụ Sở

```powershell
$login = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:5000/api/auth/login" `
  -ContentType "application/json" `
  -Body (@{ ma_nhan_vien="NV001"; mat_khau="pass123" } | ConvertTo-Json)

$headers = @{ Authorization = "Bearer $($login.token)" }
```

### 4.2. Sửa Sản Phẩm Ở Trụ Sở

```powershell
Invoke-RestMethod -Method Put `
  -Uri "http://localhost:5000/api/san-pham/SP001" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body (@{ ti_le_giam_gia = 7 } | ConvertTo-Json)
```

Kết quả mong đợi:

- API trả về sản phẩm `SP001`.
- `ti_le_giam_gia` được cập nhật.
- Trụ sở tạo event `PRODUCT_UPDATED`.
- CN01 nhận event và ghi `sync_log`.

### 4.3. Xem Event Ở Trụ Sở

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:5000/api/san-pham/sync-events?ma_sp=SP001" `
  -Headers $headers
```

Kết quả mong đợi:

- Có item trong `data`.
- `event_type = PRODUCT_UPDATED`.
- `target_branch = CN01`.
- `status = sent` nếu gửi sang service chi nhánh thành công.

### 4.4. Xem Version Và Sync Log Ở CN01

```powershell
$svcHeaders = @{ "X-Service-Token" = "dev-service-token-change-in-production" }

Invoke-RestMethod `
  -Uri "http://localhost:5011/api/service/products/local-version" `
  -Headers $svcHeaders

Invoke-RestMethod `
  -Uri "http://localhost:5011/api/service/products/sync-log?ma_sp=SP001" `
  -Headers $svcHeaders
```

Kết quả mong đợi:

- `local-version` trả về `success = true`.
- `current_version` lớn hơn `0`.
- `sync-log` có item:
  - `event_type = PRODUCT_UPDATED`
  - `ma_sp = SP001`
  - `status = success`
  - `message = Applied successfully`

## 5. Test Nhanh CN02

Chọn sản phẩm thuộc loại của `CN02`. Ví dụ:

- `SP007`, `SP008`, `SP010`, `SP017`, `SP018`, `SP019`, `SP020`, `SP023`, `SP024`

Sửa một sản phẩm CN02:

```powershell
Invoke-RestMethod -Method Put `
  -Uri "http://localhost:5000/api/san-pham/SP007" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body (@{ ti_le_giam_gia = 4 } | ConvertTo-Json)
```

Kiểm tra service CN02:

```powershell
$svcHeaders = @{ "X-Service-Token" = "dev-service-token-change-in-production" }

Invoke-RestMethod `
  -Uri "http://localhost:5012/api/service/products/local-version" `
  -Headers $svcHeaders

Invoke-RestMethod `
  -Uri "http://localhost:5012/api/service/products/sync-log?ma_sp=SP007" `
  -Headers $svcHeaders
```

## 6. Test Apply-Change Trực Tiếp Vào Service Chi Nhánh

Đây là API nội bộ, chỉ dùng để test kỹ thuật. Frontend/user bình thường không gọi API này.

```powershell
$svcHeaders = @{
  "X-Service-Token" = "dev-service-token-change-in-production"
}

$event = @{
  event_id = "evt_manual_test_001"
  event_type = "PRODUCT_UPDATED"
  source = "TRU_SO"
  target_branch = "CN01"
  version = 999
  occurred_at = "2026-05-09T00:00:00Z"
  data = @{
    ma_sp = "SP001"
    ten_sp = "Laptop Dell XPS 15"
    gia = 32000000
    ti_le_loi_nhuan = 15
    ti_le_giam_gia = 8
    mo_ta = "Laptop cao cấp, màn 15.6 inch OLED"
    ma_loai_sp = "LSP01"
    ma_ncc = 3
    trang_thai = 1
  }
}

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:5011/api/service/products/apply-change" `
  -Headers $svcHeaders `
  -ContentType "application/json" `
  -Body ($event | ConvertTo-Json -Depth 5)
```

Gọi lại cùng `event_id` sẽ được bỏ qua để tránh xử lý trùng:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:5011/api/service/products/apply-change" `
  -Headers $svcHeaders `
  -ContentType "application/json" `
  -Body ($event | ConvertTo-Json -Depth 5)
```

Kết quả mong đợi lần thứ hai:

- `success = true`
- `status = ignored`

## 7. Test Apply-Batch

```powershell
$batch = @{
  source = "TRU_SO"
  target_branch = "CN01"
  batch_id = "batch_manual_test_001"
  events = @(
    @{
      event_id = "evt_batch_test_001"
      event_type = "PRODUCT_UPDATED"
      version = 1001
      data = @{
        ma_sp = "SP001"
        ti_le_giam_gia = 9
      }
    },
    @{
      event_id = "evt_batch_test_002"
      event_type = "PRODUCT_UPDATED"
      version = 1002
      data = @{
        ma_sp = "SP002"
        ti_le_giam_gia = 5
      }
    }
  )
}

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:5011/api/service/products/apply-batch" `
  -Headers $svcHeaders `
  -ContentType "application/json" `
  -Body ($batch | ConvertTo-Json -Depth 6)
```

Kiểm tra log:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:5011/api/service/products/sync-log?from_version=1001&to_version=1002" `
  -Headers $svcHeaders
```

## 8. Các Lỗi Thường Gặp

### 8.1. Lỗi 404 Khi Gọi `/api/service/products/local-version`

Nguyên nhân thường gặp: container service đang chạy image cũ.

Fix thường dùng:

```powershell
docker compose up -d --build tru-so-service mysql-service postgre-service
```

Nếu vẫn lỗi, ép recreate:

```powershell
docker compose up -d --build --force-recreate tru-so-service mysql-service postgre-service
```

Sau đó kiểm tra lại:

```powershell
$svcHeaders = @{ "X-Service-Token" = "dev-service-token-change-in-production" }

Invoke-RestMethod `
  -Uri "http://localhost:5011/api/service/products/local-version" `
  -Headers $svcHeaders
```

### 8.2. `sync-log` Rỗng

Có thể do:

- Chưa sửa sản phẩm sau khi rebuild service.
- Event cũ đã được gửi lúc service còn code cũ.
- Sản phẩm đang test không thuộc chi nhánh đó.

Fix nhanh: sửa lại sản phẩm một lần nữa rồi kiểm tra lại.

### 8.3. `product_sync_events.status = failed`

Kiểm tra log:

```powershell
docker compose logs --tail=100 tru-so-service mysql-service postgre-service
```

Kiểm tra service token và route:

```powershell
$svcHeaders = @{ "X-Service-Token" = "dev-service-token-change-in-production" }

Invoke-RestMethod `
  -Uri "http://localhost:5011/api/service/products/local-version" `
  -Headers $svcHeaders
```

### 8.4. Bảng Mới Không Có Sau Khi Đã Từng Chạy Docker Trước Đó

Docker volume cũ có thể không chạy lại file init SQL. Code hiện có đã có logic tự tạo bảng khi endpoint được gọi, nhưng nếu muốn reset sạch database demo:

```powershell
docker compose down -v
docker compose up -d --build --remove-orphans
```

Lệnh `down -v` sẽ xóa volume database, cần cẩn thận nếu đang có dữ liệu cần giữ.

## 9. Tóm Tắt Để Báo Cáo

Có thể giải thích ngắn gọn:

> Khi trụ sở sửa sản phẩm, backend trụ sở cập nhật SQL Server và tạo `product_sync_events`. Service trụ sở nhận event và gửi sang service chi nhánh theo `target_branch`. Service chi nhánh kiểm tra token, chống xử lý trùng bằng `event_id`, gọi backend local để upsert hoặc soft delete sản phẩm, sau đó ghi kết quả vào `sync_log`. API `local-version` cho biết chi nhánh đã đồng bộ tới version nào, còn `sync-log` dùng để debug lịch sử xử lý event.
