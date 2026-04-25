# Dự án CSDL Phân Tán - Quản lý Chi nhánh

## Yêu cầu

- **Docker Desktop** đã cài và đang chạy
- **Git** để clone repo
- **SQL Server Management Studio (SSMS)** để quản lý database — tải miễn phí tại [aka.ms/ssmsfullsetup](https://aka.ms/ssmsfullsetup)

---

## Setup (3 bước)

```bash
git clone <url-repo>
cp .env.example .env
docker compose up -d --build
```

Lần đầu mất ~2-3 phút (tải SQL Server image + build Flask). Các lần sau vài giây.

Kiểm tra tất cả container đang chạy:

```bash
docker compose ps
```

---

## Kết nối Database bằng SSMS

### Bước 1: Mở SSMS

Mở SQL Server Management Studio. Cửa sổ **Connect to Server** sẽ hiện ra tự động.

Nếu bạn đang kết nối sẵn một server khác rồi, nhấn **Connect > Database Engine...** ở góc trên trái Object Explorer để mở thêm kết nối mới.

### Bước 2: Điền thông tin kết nối

```
Server type:      Database Engine
Server name:      localhost,1433
Authentication:   SQL Server Authentication   ← KHÔNG chọn Windows Authentication
Login:            sa
Password:         MyPass@2025
```

> **Lưu ý quan trọng:**
> - Server name dùng dấu **phẩy** (localhost**,**1433), không phải dấu hai chấm
> - Authentication phải chọn **SQL Server Authentication**, không phải Windows Authentication

### Bước 3: Trust Server Certificate

Nếu gặp lỗi chứng chỉ, làm như sau:

1. Ở cửa sổ Connect to Server, tìm mục **Connection Security** (hoặc nhấn **Options >>** → tab **Connection Properties**)
2. Tick vào **Trust server certificate**
3. Nhấn **Connect**

### Bước 4: Mở database

Sau khi kết nối thành công, ở Object Explorer bên trái, mở theo đường dẫn:

```
Databases > quan_ly_chi_nhanh > Tables
```

### Bước 5: Thao tác với dữ liệu

**Xem dữ liệu:** Chuột phải vào bảng → Select Top 1000 Rows

**Sửa dữ liệu trực tiếp:** Chuột phải vào bảng → Edit Top 200 Rows

**Viết SQL thủ công:** Nhấn **New Query** trên toolbar, gõ SQL rồi nhấn **F5** để chạy:

```sql
USE quan_ly_chi_nhanh;

-- Xem tất cả sản phẩm theo chi nhánh
SELECT 
    cn.ten_chi_nhanh,
    lsp.ten_loai_sp,
    sp.ten_sp,
    FORMAT(sp.gia, 'N0') AS gia,
    sp.ti_le_giam_gia,
    CASE WHEN sp.trang_thai = 1 THEN N'Đang bán' ELSE N'Ngừng bán' END AS trang_thai
FROM SAN_PHAM sp
JOIN loai_sp lsp ON sp.ma_loai_sp = lsp.ma_loai_sp
JOIN chi_nhanh cn ON lsp.ma_chi_nhanh = cn.ma_chi_nhanh
ORDER BY cn.ten_chi_nhanh, sp.gia DESC;
```

---

## Kết nối qua terminal (cách thay thế)

Nếu không dùng SSMS, có thể vào SQL Server trực tiếp qua terminal:

```bash
docker compose exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "MyPass@2025" -C -d quan_ly_chi_nhanh
```

Gõ SQL xong nhấn `GO` rồi Enter để chạy. Gõ `exit` để thoát.

---

## Truy cập Flask Web

| Service        | URL / Host            | Ghi chú             |
|----------------|-----------------------|----------------------|
| **Flask Web**  | http://localhost:5000 | Giao diện chính      |
| SQL Server     | localhost,1433        | sa / MyPass@2025     |
| Redis          | localhost:6379        |                      |

### API endpoints

| Endpoint        | Mô tả                              |
|-----------------|-------------------------------------|
| `/api/san-pham` | JSON danh sách sản phẩm (có cache) |
| `/api/thong-ke` | JSON thống kê chi nhánh            |

---

## Cấu trúc project

```
├── docker-compose.yml
├── .env.example
├── init/mssql/
│   └── 01-schema-and-data.sql    ← Schema + dummy data (T-SQL)
└── flask-app/
    ├── Dockerfile                ← Có cài ODBC driver
    ├── requirements.txt          ← pyodbc
    ├── app.py                    ← Routes chính
    ├── db.py                     ← Kết nối SQL Server + Redis
    ├── templates/                ← Giao diện HTML
    └── static/css/style.css
```

---

## Dữ liệu dummy có sẵn

| Bảng         | Số bản ghi | Mô tả                      |
|--------------|-----------|------------------------------|
| chi_nhanh    | 5         | HN, HCM, ĐN, CT, HP        |
| loai_sp      | 10        | Laptop, Phone, Phụ kiện...  |
| NCC          | 8         | Apple, Samsung, Dell...     |
| SAN_PHAM     | 25        | Sản phẩm tech có giá VNĐ   |
| phong_ban    | 6         | BGĐ, KD, KT, Kho, NS, KT  |
| NHAN_VIEN    | 20        | Đủ chức vụ, 1 NV đã nghỉ   |

### Query mẫu để thử

```sql
USE quan_ly_chi_nhanh;

-- Thống kê sản phẩm theo chi nhánh
SELECT * FROM v_thong_ke_chi_nhanh;

-- Sản phẩm + giá bán thực tế
SELECT * FROM v_san_pham_theo_chi_nhanh;

-- Nhân viên theo phòng ban
SELECT * FROM v_nhan_vien_phong_ban;

-- Tổng lương theo phòng ban
SELECT * FROM v_luong_phong_ban;
```

---

## Lệnh Docker thường dùng

```bash
docker compose up -d --build      # Bật (build lại Flask nếu sửa Dockerfile)
docker compose up -d              # Bật nhanh
docker compose down               # Tắt (giữ data)
docker compose down -v            # Tắt + xóa data (reset hoàn toàn)
docker compose logs -f flask-app  # Xem log Flask
docker compose logs -f sqlserver  # Xem log SQL Server
docker compose ps                 # Xem trạng thái container
```

**Hot reload:** Flask bật debug mode + volume mount → sửa code Python tự restart, không cần chạy lệnh gì.

---

## Lưu ý

- SQL Server bắt buộc phải có password mạnh (chữ hoa + chữ thường + số + ký tự đặc biệt, ≥8 ký tự). Không thể bỏ password.
- Image SQL Server khá nặng (~1.5GB lần tải đầu), nhưng chỉ tải 1 lần.
- Dùng NVARCHAR thay VARCHAR để hỗ trợ tiếng Việt đầy đủ.
- Docker Desktop ăn RAM qua process **vmmem**. Nếu máy chậm, tạo file `C:\Users\<tên-user>\.wslconfig` để giới hạn:

```ini
[wsl2]
memory=3GB
processors=2
swap=1GB
```

Sau đó chạy `wsl --shutdown` trong PowerShell rồi mở lại Docker Desktop.

---

## Xử lý lỗi

**Port bị trùng:** Sửa `.env`, đổi port (ví dụ `MSSQL_PORT=1434`), chạy lại `docker compose up -d`. Kết nối SSMS bằng `localhost,1434`.

**Reset toàn bộ:** `docker compose down -v` rồi `docker compose up -d --build`

**Flask lỗi kết nối:** SQL Server cần ~30s để sẵn sàng. Chạy `docker compose restart flask-app`

**SSMS báo lỗi kết nối:**
- Kiểm tra Docker Desktop đang chạy: `docker compose ps`
- Kiểm tra đúng port: `localhost,1433` (dấu phẩy, không phải dấu hai chấm)
- Kiểm tra đúng Authentication: phải chọn **SQL Server Authentication**
- Tick **Trust server certificate**
