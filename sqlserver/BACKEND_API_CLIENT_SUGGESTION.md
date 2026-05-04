# Goi y cau truc backend Flask API-only

Backend hien tai di theo huong API-only: client goi endpoint va nhan JSON, khong render HTML trong backend.

## Cau truc thu muc hien tai

```text
project-root/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── db.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── employee_api.py
│   │   ├── product_api.py
│   │   └── stats_api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── branch_service.py
│   │   ├── cache_service.py
│   │   ├── employee_service.py
│   │   └── product_service.py
│   └── middleware/
│       ├── __init__.py
│       └── error_handler.py
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── templates/
    │   └── index.html
    └── static/
        ├── css/style.css
        └── js/app.js
```

## Vai tro tung phan

### `backend/api/`

Khai bao route API va tra JSON.

```text
GET /api/san-pham
GET /api/nhan-vien
GET /api/thong-ke
```

### `backend/services/`

Xu ly logic chinh:

- Query SQL Server qua `backend/db.py`.
- Xu ly Redis cache.
- Chuyen doi du lieu truoc khi tra JSON.
- Doc `BRANCH_CNxx_DB_ENGINE` de biet chi nhanh dung `sqlserver`, `postgresql` hay `mysql`.

### `backend/middleware/`

Xu ly request/response dung chung:

- Error handler.
- Logging sau nay.
- Auth middleware sau nay.
- Chuan hoa response loi.

## Khong can `controllers/`

Neu backend chi phuc vu API client va chi tra JSON thi khong can `controllers/`.

Trong project nay:

- `api/` nhan request va tra JSON.
- `services/` xu ly logic.
- `middleware/` xu ly loi/auth/logging.

Chi nen them `controllers/` neu sau nay backend can xu ly mot lop route rieng phuc tap hon.

## Khong can `schemas/` luc nay

Hien tai API chi co GET, chua co POST/PUT nen chua can validate input bang `schemas/`.

Khi nao them endpoint tao/sua du lieu, co the them lai:

```text
backend/schemas/
├── __init__.py
└── product_schema.py
```
