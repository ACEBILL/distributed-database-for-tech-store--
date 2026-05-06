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

## Known Issues and Errors (From Testing)

### Issue 1: JWT Token Verification Issues
- **File:** `middleware/auth.py`, `services/auth_service.py`
- **Description:** JWT token verification may fail during testing if token generation is not properly seeded or if expiration is misconfigured.
- **Affected Tests:** TC008, TC024, TC034 (and auth-dependent tests)
- **Workaround:** Use real login endpoint or implement proper mock token generation in tests.
- **Test File:** `backend/tests/test_auth_api.py`

### Issue 2: Branch Database Configuration Not Set Up
- **File:** `config.py`, `.env.example`
- **Description:** CN01 (MySQL) and CN02 (PostgreSQL) branch databases are not configured in default setup. Endpoints that query branch databases will fail.
- **Affected Tests:** TC005 (branch login), TC019 (branch products), TC034-TC035 (branch employees)
- **Workaround:** Configure branch database credentials in `.env` file:
  ```
  BRANCH_CN01_DB_HOST=
  BRANCH_CN01_DB_ENGINE=mysql
  BRANCH_CN01_DB_PORT=3306
  BRANCH_CN01_DB_NAME=
  BRANCH_CN01_DB_USER=
  BRANCH_CN01_DB_PASSWORD=
  ```
- **Test File:** `backend/tests/test_product_api.py`, `backend/tests/test_employee_api.py`

### Issue 3: Redis Cache Connection Issues
- **File:** `services/cache_service.py`
- **Description:** Redis cache service may fail if Redis is not running or connection is misconfigured.
- **Affected Tests:** TC022 (product caching)
- **Workaround:** Ensure `docker compose up -d` completes successfully and Redis container is running. Check Docker logs: `docker compose logs redis`
- **Test File:** `backend/tests/test_product_api.py`

### Issue 4: Role-Based Access Control Not Fully Tested
- **File:** `middleware/auth.py`, All API files (product_api.py, employee_api.py, etc.)
- **Description:** @require_role decorators need proper JWT token with correct role information to be tested properly. Default test tokens may not have correct roles.
- **Affected Tests:** TC013, TC029, TC040, TC052, TC057 (create/update/delete operations)
- **Workaround:** Create separate test tokens with different roles: admin, giam_doc, truong_phong, nhan_vien
- **Test File:** `backend/tests/conftest.py` (fixtures need enhancement)

### Issue 5: Pagination Edge Cases
- **File:** `services/employee_service.py`, `db.py`
- **Description:** Pagination may not properly handle invalid page numbers (0, negative, exceeding max) or invalid limits.
- **Affected Tests:** TC025 (employee pagination)
- **Workaround:** Test with edge cases: page=0, page=-1, limit=-10, limit=999999
- **Test File:** `backend/tests/test_employee_api.py`

### Issue 6: Multi-Database Support Incomplete
- **File:** `services/auth_service.py`, `db.py`
- **Description:** PostgreSQL driver for CN02 is not implemented. Only SQL Server (central) and MySQL (CN01) are partially supported.
- **Affected Tests:** Branch-related tests for CN02
- **Workaround:** Before testing CN02 endpoints, implement PostgreSQL connection handler in `db.py`
- **Test File:** Related branch tests in `backend/tests/`

### Issue 7: Sensitive Field Masking Inconsistencies
- **File:** `services/employee_service.py` (mask_employees_list, mask_sensitive_employee_fields)
- **Description:** Sensitive fields (salary, personal info) may not be consistently masked across all user types and endpoints.
- **Affected Tests:** TC028 (field masking), TC024 (employee list)
- **Workaround:** Verify masking logic works for each role type and verify with non-admin accounts
- **Test File:** `backend/tests/test_employee_api.py`

### Issue 8: Soft Delete Verification
- **File:** `services/employee_service.py`, `services/product_service.py`
- **Description:** Soft delete operations may not properly set deletion status or may not prevent deleted records from appearing in filtered lists.
- **Affected Tests:** TC016, TC032, TC042, TC049 (delete operations)
- **Workaround:** Query database directly to verify `trang_thai` field is properly updated
- **Test File:** `backend/tests/test_*.py`

### Issue 9: Error Handling for Missing Required Fields
- **File:** All API files (api/*.py)
- **Description:** Some endpoints may not properly validate or return appropriate error codes (400) for missing required fields in POST/PUT requests.
- **Affected Tests:** TC003, TC014, TC030 (missing field tests)
- **Workaround:** Add comprehensive request validation in each endpoint
- **Test File:** `backend/tests/test_*.py`

### Issue 10: Database Connection Pooling Under Load
- **File:** `db.py`, `config.py`
- **Description:** Connection pooling may have issues under concurrent test execution or may not properly recycle connections.
- **Affected Tests:** All database-related tests
- **Workaround:** Run tests sequentially with `pytest -n 0` or use reduced concurrency. Check connection pool settings in config.
- **Test File:** `backend/tests/`

## Testing Resources

- **Main Test Suite:** See `TEST_CASES.md` for detailed test cases (68 total)
- **Word Document:** See `TEST_CASES.docx` for formatted test case documentation
- **Test Scripts Location:** `backend/tests/`
  - `conftest.py` - Fixtures and setup
  - `test_auth_api.py` - Authentication tests
  - `test_product_api.py` - Product API tests
  - `test_employee_api.py` - Employee API tests
  - `test_other_api.py` - Branch, Department, Category, Supplier tests
  - `test_stats_api.py` - Statistics API tests

### Running Tests
```bash
cd backend
pip install pytest pytest-cov
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```
