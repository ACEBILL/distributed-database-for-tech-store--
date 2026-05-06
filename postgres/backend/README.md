# Backend — Tech Store Distributed Database API

Hướng dẫn cài đặt và chạy phần backend (Flask + Flasgger).

Yêu cầu:
- Python 3.10+ (hoặc tương thích)
- pip
- (Tùy chọn) Docker & Docker Compose

Cài đặt (chạy trên máy dev):

1. Tạo virtual environment và kích hoạt:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

2. Cài dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Biến môi trường chính (nếu muốn override, mặc định đã có trong `config.py`):
- SECRET_KEY — khóa bí mật Flask
- DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME — kết nối database
- REDIS_HOST, REDIS_PORT — cấu hình Redis
- FLASK_PORT — cổng (mặc định 5000)

Chạy ứng dụng (local):

```bash
# trong thư mục backend
python app.py
# API sẽ lắng nghe trên http://0.0.0.0:5000
```

Chạy bằng Docker (cách nhanh):

```bash
docker build -t techstore-backend ./backend
docker run -e DB_PASSWORD=MyPass@2025 -p 5000:5000 techstore-backend
```

Sử dụng docker-compose (khuyến nghị để chạy toàn bộ stack gồm SQL Server, Redis, backend, frontend):

```bash
# từ root của repo
docker compose up --build
```

Swagger UI (tài liệu API):
- Một khi backend chạy: truy cập `http://<host>:5000/apidocs/` để xem Swagger UI.

Ghi chú:
- Kết cấu proxy của frontend (nếu chạy bằng Docker Compose) đã cấu hình để forward `/api/` tới backend nội bộ.
- Thay đổi cấu hình database cho môi trường production cẩn thận (không dùng mật khẩu mặc định).
