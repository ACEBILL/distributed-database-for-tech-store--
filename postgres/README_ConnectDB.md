# Kết nối PostgreSQL

Sau khi chạy:

```bash
docker compose up -d --build
```

kiểm tra container:

```bash
docker compose ps
```

## Kết nối bằng pgAdmin / DBeaver / TablePlus

```text
Host: localhost
Port: 5432
Database: quan_ly_chi_nhanh
User: techstore
Password: MyPass@2025
```

## Kết nối bằng terminal

```bash
docker compose exec postgres psql -U techstore -d quan_ly_chi_nhanh
```

Một vài lệnh `psql` thường dùng:

```text
\dt           -- liệt kê table
\dv           -- liệt kê view
\d nhan_vien  -- xem cấu trúc bảng nhan_vien
\q            -- thoát
```

## Ghi chú

- DB trung tâm hiện chỉ lưu mã và tên chi nhánh.
- Thông tin kết nối DB chi nhánh nằm trong `.env`, không lưu trực tiếp trong bảng database.
- Loại hệ CSDL của từng chi nhánh nằm trong `BRANCH_CNxx_DB_ENGINE`, ví dụ `postgresql`, `sqlserver`, `mysql`.
- Backend trong folder này chỉ có driver PostgreSQL (`psycopg`); muốn kết nối tới chi nhánh dùng engine khác cần thêm driver và code kết nối tương ứng.
- Backend API chạy ở `http://localhost:5000`.
- Swagger UI chạy ở `http://localhost:5000/apidocs`.
- Frontend chạy ở `http://localhost:3000`.
