# Frontend — Tech Store Client

Hướng dẫn cài đặt và chạy phần frontend (static HTML/CSS/JS, phục vụ bằng Nginx).

Yêu cầu:
- (Tùy chọn) Trình duyệt hiện đại để mở `templates/index.html` trực tiếp
- (Tùy chọn) Docker & Docker Compose để phục vụ qua Nginx

Chạy nhanh (mở file trực tiếp):

1. Mở `frontend/templates/index.html` trong trình duyệt để xem giao diện (phù hợp demo cục bộ).
2. Lưu ý: khi mở file trực tiếp, các request tới `/api/` sẽ gọi tới cùng origin — cần chạy backend trên cùng host/cổng hoặc điều chỉnh URL trong `frontend/static/js/app.js`.

Chạy bằng Docker:

```bash
docker build -t techstore-frontend ./frontend
docker run -p 3000:80 --name frontend-client techstore-frontend
# truy cập http://localhost:3000
```

Sử dụng docker-compose (kết hợp với backend):

```bash
# từ root repository
docker compose up --build
# frontend mặc định được map tới port 3000 trên host
```

Cấu trúc và Cấu hình:
- Nginx proxy (frontend/nginx.conf) chuyển `/api/` tới `http://backend:5000/api/` khi chạy trong Docker Compose.
- API endpoints được gọi từ `frontend/static/js/app.js` bằng đường dẫn tương đối `/api/...`.

Ghi chú:
- Để chạy frontend độc lập nhưng gọi tới backend khác, chỉnh các URL trong `static/js/app.js` (ví dụ: `http://localhost:5000/api/...`).
- Nếu gặp lỗi CORS khi gọi trực tiếp tới backend, hãy chạy frontend và backend qua Docker Compose (proxy Nginx sẽ giải quyết).
