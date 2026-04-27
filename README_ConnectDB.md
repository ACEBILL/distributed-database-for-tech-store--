# Kết nối SQL Server

Sau khi chạy:

```bash
docker compose up -d --build
```

kiểm tra container:

```bash
docker compose ps
```

## Kết nối bằng SSMS / Azure Data Studio

```text
Server: localhost,1433
Authentication: SQL Server Authentication
Login: sa
Password: MyPass@2025
Database: quan_ly_chi_nhanh
```

Nếu gặp lỗi chứng chỉ, bật `Trust server certificate`.

## Kết nối bằng terminal

```bash
docker compose exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "MyPass@2025" -C -d quan_ly_chi_nhanh
```

## Ghi chú

- SQL Server cần password mạnh.
- DB trung tâm hiện chỉ lưu mã và tên chi nhánh.
- Thông tin kết nối DB chi nhánh nằm trong `.env`, không lưu trực tiếp trong bảng database.
- Loại hệ CSDL của từng chi nhánh nằm trong `BRANCH_CNxx_DB_ENGINE`, ví dụ `sqlserver`, `postgresql`, `mysql`.
- Backend hiện mới có driver kết nối SQL Server; PostgreSQL/MySQL cần thêm driver và code kết nối riêng.
- Backend API chạy ở `http://localhost:5000`.
- Swagger UI chạy ở `http://localhost:5000/apidocs`.
- Frontend chạy ở `http://localhost:3000`.
