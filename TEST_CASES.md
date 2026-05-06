# Test Case Document - Distributed Database for Tech Store

## Overview
This document contains comprehensive test cases for the Distributed Database Tech Store project.

**Project:** Distributed Database for Tech Store  
**Date:** May 6, 2026  
**Scope:** Backend API Testing (Flask)  
**Database:** SQL Server (Central), MySQL (CN01), PostgreSQL (CN02 - Placeholder)  

---

## Table of Contents
1. [Test Environment Setup](#test-environment-setup)
2. [Authentication API Tests](#authentication-api-tests)
3. [Product API Tests](#product-api-tests)
4. [Employee API Tests](#employee-api-tests)
5. [Branch API Tests](#branch-api-tests)
6. [Department API Tests](#department-api-tests)
7. [Category API Tests](#category-api-tests)
8. [Supplier API Tests](#supplier-api-tests)
9. [Statistics API Tests](#statistics-api-tests)
10. [Known Issues](#known-issues)

---

## Test Environment Setup

### Prerequisites
- Docker Desktop running
- Python 3.8+
- pytest installed: `pip install pytest`
- test_requirements.txt:
  ```
  pytest==7.4.0
  pytest-cov==4.1.0
  ```

### Setup Steps
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest backend/tests/ -v

# Run tests with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Run specific test class
pytest backend/tests/test_auth_api.py::TestAuthAPI -v
```

---

## Authentication API Tests

### TC001: Test successful login with valid credentials
- **Endpoint:** `POST /api/auth/login`
- **Request Body:**
  ```json
  {
    "ma_nhan_vien": "NV001",
    "mat_khau": "pass123"
  }
  ```
- **Expected Response:** 200
- **Expected Data:** Contains JWT token and user info
- **Note Location:** auth_api.py, auth_service.py

### TC002: Test login with invalid credentials
- **Endpoint:** `POST /api/auth/login`
- **Request Body:**
  ```json
  {
    "ma_nhan_vien": "NV001",
    "mat_khau": "wrong_password"
  }
  ```
- **Expected Response:** 401
- **Expected Data:** Error message "Sai ma nhan vien hoac mat khau"
- **Note Location:** auth_api.py

### TC003: Test login with missing required fields
- **Endpoint:** `POST /api/auth/login`
- **Request Body:** `{"ma_nhan_vien": "NV001"}`
- **Expected Response:** 400 or 401
- **Note Location:** auth_api.py, auth_service.py

### TC004: Test login with nonexistent employee ID
- **Endpoint:** `POST /api/auth/login`
- **Request Body:**
  ```json
  {
    "ma_nhan_vien": "NV999",
    "mat_khau": "pass123"
  }
  ```
- **Expected Response:** 401
- **Note Location:** auth_service.py

### TC005: Test branch login for CN01 (MySQL)
- **Endpoint:** `POST /api/auth/branches/CN01/login`
- **Request Body:**
  ```json
  {
    "ma_nhan_vien": "NV001",
    "mat_khau": "pass123"
  }
  ```
- **Expected Response:** 200 or 400 (depends on CN01 configuration)
- **Note Location:** auth_api.py, auth_service.py

### TC006: Test branch login for nonexistent branch
- **Endpoint:** `POST /api/auth/branches/CN99/login`
- **Expected Response:** 400 or 404
- **Note Location:** auth_api.py

### TC007: Test /me endpoint without authentication
- **Endpoint:** `GET /api/auth/me`
- **Headers:** None
- **Expected Response:** 401
- **Note Location:** auth_api.py

### TC008: Test /me endpoint with valid token
- **Endpoint:** `GET /api/auth/me`
- **Headers:** `Authorization: Bearer <valid_token>`
- **Expected Response:** 200
- **Expected Data:** Current user info (ma_nhan_vien, ho_ten, chuc_vu, scope, etc.)
- **Note Location:** auth_api.py

---

## Product API Tests

### TC009: Test GET /api/san-pham without authentication
- **Expected Response:** 401
- **Note Location:** product_api.py, auth middleware

### TC010: Test GET /api/san-pham with valid token
- **Endpoint:** `GET /api/san-pham`
- **Expected Response:** 200
- **Expected Data:** List of products with pagination
- **Note Location:** product_api.py, product_service.py

### TC011: Test GET /api/san-pham/<ma_sp> with valid product ID
- **Endpoint:** `GET /api/san-pham/SP001`
- **Expected Response:** 200 or 404
- **Note Location:** product_api.py

### TC012: Test GET /api/san-pham/<ma_sp> with nonexistent product
- **Endpoint:** `GET /api/san-pham/SP999`
- **Expected Response:** 404
- **Note Location:** product_api.py

### TC013: Test POST /api/san-pham with valid product data
- **Endpoint:** `POST /api/san-pham`
- **Headers:** `Authorization: Bearer <admin_token>`
- **Request Body:**
  ```json
  {
    "ma_sp": "SP_TEST",
    "ten_sp": "Test Product",
    "gia": 100000,
    "ma_loai_sp": "LSP001",
    "ma_ncc": 1,
    "so_luong": 10
  }
  ```
- **Expected Response:** 201 (created)
- **Note Location:** product_api.py, product_service.py

### TC014: Test POST /api/san-pham with missing required fields
- **Expected Response:** 400 or 403
- **Note Location:** product_api.py, product_service.py

### TC015: Test PUT /api/san-pham/<ma_sp> with valid data
- **Endpoint:** `PUT /api/san-pham/SP001`
- **Expected Response:** 200 or 404
- **Note Location:** product_api.py

### TC016: Test DELETE /api/san-pham/<ma_sp> (soft delete)
- **Endpoint:** `DELETE /api/san-pham/SP001`
- **Expected Response:** 200 or 404
- **Note Location:** product_api.py

### TC017: Test GET /api/san-pham-theo-chi-nhanh
- **Expected Response:** 200
- **Note Location:** product_api.py

### TC018: Test GET /api/san-pham/chi-nhanh/<ma_chi_nhanh>
- **Endpoint:** `GET /api/san-pham/chi-nhanh/CN01`
- **Expected Response:** 200
- **Note Location:** product_api.py

### TC019: Test GET /api/chi-nhanh/<ma_chi_nhanh>/san-pham
- **Endpoint:** `GET /api/chi-nhanh/CN01/san-pham`
- **Expected Response:** 200 or 400
- **Note Location:** product_api.py

### TC020: Test GET /api/san-pham/loai/<ma_loai_sp>
- **Endpoint:** `GET /api/san-pham/loai/LSP001`
- **Expected Response:** 200
- **Note Location:** product_api.py

### TC021: Test GET /api/san-pham/ncc/<ma_ncc>
- **Endpoint:** `GET /api/san-pham/ncc/1`
- **Expected Response:** 200
- **Note Location:** product_api.py

### TC022: Test product caching with Redis
- **Test:** Verify that product list is cached after first request
- **Note Location:** cache_service.py, product_service.py

---

## Employee API Tests

### TC023: Test GET /api/nhan-vien without authentication
- **Expected Response:** 401
- **Note Location:** employee_api.py

### TC024: Test GET /api/nhan-vien with valid token
- **Endpoint:** `GET /api/nhan-vien`
- **Expected Response:** 200
- **Note Location:** employee_api.py

### TC025: Test GET /api/nhan-vien with pagination
- **Endpoint:** `GET /api/nhan-vien?page=1&limit=10`
- **Expected Response:** 200
- **Expected Data:** Data array with pagination metadata
- **Note Location:** employee_api.py

### TC026: Test GET /api/nhan-vien/<ma_nhan_vien> with valid ID
- **Endpoint:** `GET /api/nhan-vien/NV001`
- **Expected Response:** 200
- **Note Location:** employee_api.py

### TC027: Test GET /api/nhan-vien/<ma_nhan_vien> with nonexistent ID
- **Expected Response:** 404
- **Note Location:** employee_api.py

### TC028: Test that sensitive fields are masked for non-admin users
- **Expected:** Sensitive fields (salary, etc.) should be masked for non-admin
- **Note Location:** employee_api.py, employee_service.py

### TC029: Test POST /api/nhan-vien with valid employee data
- **Expected Response:** 201
- **Note Location:** employee_api.py

### TC030: Test POST /api/nhan-vien with missing required fields
- **Expected Response:** 400 or 403
- **Note Location:** employee_api.py

### TC031: Test PUT /api/nhan-vien/<ma_nhan_vien> with valid data
- **Expected Response:** 200 or 404
- **Note Location:** employee_api.py

### TC032: Test DELETE /api/nhan-vien/<ma_nhan_vien> (soft delete)
- **Expected Response:** 200 or 404
- **Note Location:** employee_api.py

### TC033: Test GET /api/nhan-vien/phong-ban/<ma_pb>
- **Endpoint:** `GET /api/nhan-vien/phong-ban/PB01`
- **Expected Response:** 200
- **Note Location:** employee_api.py

### TC034: Test GET /api/chi-nhanh/<ma_chi_nhanh>/nhan-vien
- **Endpoint:** `GET /api/chi-nhanh/CN01/nhan-vien`
- **Expected Response:** 200 or 400
- **Note Location:** employee_api.py

### TC035: Test creating employee in branch database
- **Expected Response:** 201 or error
- **Note Location:** employee_api.py, employee_service.py

### TC036: Test that non-admin users cannot manage employees
- **Expected Response:** 403
- **Note Location:** employee_api.py, auth middleware

---

## Branch API Tests

### TC037: Test GET /api/chi-nhanh
- **Expected Response:** 200
- **Expected Data:** List of branches
- **Note Location:** branch_api.py

### TC038: Test GET /api/chi-nhanh/<ma_chi_nhanh> with valid ID
- **Expected Response:** 200
- **Note Location:** branch_api.py

### TC039: Test GET /api/chi-nhanh/<ma_chi_nhanh> with nonexistent ID
- **Expected Response:** 404
- **Note Location:** branch_api.py

### TC040: Test POST /api/chi-nhanh with valid branch data
- **Expected Response:** 201
- **Note Location:** branch_api.py

### TC041: Test PUT /api/chi-nhanh/<ma_chi_nhanh> with valid data
- **Expected Response:** 200 or 404
- **Note Location:** branch_api.py

### TC042: Test DELETE /api/chi-nhanh/<ma_chi_nhanh>
- **Expected Response:** 200 or 404
- **Note Location:** branch_api.py

### TC043: Test GET /api/chi-nhanh/<ma_chi_nhanh>/health
- **Endpoint:** `GET /api/chi-nhanh/CN01/health`
- **Expected Response:** 200 or 404
- **Note Location:** branch_api.py

---

## Department API Tests

### TC044: Test GET /api/phong-ban
- **Expected Response:** 200
- **Note Location:** department_api.py

### TC045: Test GET /api/phong-ban/<ma_pb> with valid ID
- **Expected Response:** 200
- **Note Location:** department_api.py

### TC046: Test GET /api/phong-ban/<ma_pb> with nonexistent ID
- **Expected Response:** 404
- **Note Location:** department_api.py

### TC047: Test POST /api/phong-ban with valid department data
- **Expected Response:** 201
- **Note Location:** department_api.py

### TC048: Test PUT /api/phong-ban/<ma_pb> with valid data
- **Expected Response:** 200 or 404
- **Note Location:** department_api.py

### TC049: Test DELETE /api/phong-ban/<ma_pb>
- **Expected Response:** 200 or 404
- **Note Location:** department_api.py

---

## Category API Tests

### TC050: Test GET /api/loai-san-pham
- **Expected Response:** 200
- **Note Location:** category_api.py

### TC051: Test GET /api/loai-san-pham/<ma_loai_sp> with valid ID
- **Expected Response:** 200
- **Note Location:** category_api.py

### TC052: Test POST /api/loai-san-pham with valid category data
- **Expected Response:** 201
- **Note Location:** category_api.py

### TC053: Test PUT /api/loai-san-pham/<ma_loai_sp> with valid data
- **Expected Response:** 200 or 404
- **Note Location:** category_api.py

### TC054: Test DELETE /api/loai-san-pham/<ma_loai_sp>
- **Expected Response:** 200 or 404
- **Note Location:** category_api.py

---

## Supplier API Tests

### TC055: Test GET /api/nha-cung-cap
- **Expected Response:** 200
- **Note Location:** supplier_api.py

### TC056: Test GET /api/nha-cung-cap/<ma_ncc> with valid ID
- **Expected Response:** 200
- **Note Location:** supplier_api.py

### TC057: Test POST /api/nha-cung-cap with valid supplier data
- **Expected Response:** 201
- **Note Location:** supplier_api.py

### TC058: Test PUT /api/nha-cung-cap/<ma_ncc> with valid data
- **Expected Response:** 200 or 404
- **Note Location:** supplier_api.py

### TC059: Test DELETE /api/nha-cung-cap/<ma_ncc>
- **Expected Response:** 200 or 404
- **Note Location:** supplier_api.py

---

## Statistics API Tests

### TC060: Test GET /api/thong-ke (get stats overview)
- **Expected Response:** 200
- **Expected Data:** Branch statistics with connection status
- **Note Location:** stats_api.py

### TC061: Test GET /api/thong-ke/chi-nhanh (stats by branch)
- **Expected Response:** 200
- **Note Location:** stats_api.py

### TC062: Test GET /api/thong-ke/luong-phong-ban (salary by department)
- **Expected Response:** 200
- **Note Location:** stats_api.py

### TC063: Test GET /api/thong-ke/san-pham-theo-chi-nhanh/<ma_chi_nhanh>
- **Endpoint:** `GET /api/thong-ke/san-pham-theo-chi-nhanh/CN01`
- **Expected Response:** 200 or 404
- **Note Location:** stats_api.py

### TC064: Test GET /api/thong-ke/nhan-vien-theo-chi-nhanh/<ma_chi_nhanh>
- **Endpoint:** `GET /api/thong-ke/nhan-vien-theo-chi-nhanh/CN01`
- **Expected Response:** 200 or 404
- **Note Location:** stats_api.py

### TC065: Test branch connection status from stats
- **Verify:** Response includes `trang_thai_ket_noi` field
- **Note Location:** stats_api.py

### TC066: Test that stats API returns properly formatted data
- **Verify:** Data structure is consistent
- **Note Location:** stats_api.py

### TC067: Test stats with invalid branch ID
- **Endpoint:** `GET /api/thong-ke/san-pham-theo-chi-nhanh/INVALID`
- **Expected Response:** 404 or 200
- **Note Location:** stats_api.py

### TC068: Test stats aggregation
- **Verify:** Stats are properly aggregated
- **Note Location:** stats_api.py

---

## Known Issues

### Issue 1: Token Verification Issues
**Location:** middleware/auth.py, services/auth_service.py  
**Description:** JWT token verification may fail during testing if token generation is not properly seeded or if expiration is misconfigured.  
**Affected Tests:** TC008, TC024, TC034, TC060+  
**Workaround:** Use real login endpoint or mock token generation in tests.

### Issue 2: Branch Database Configuration Not Set Up
**Location:** config.py, .env.example  
**Description:** CN01 (MySQL) and CN02 (PostgreSQL) branch databases are not configured in default setup.  
**Affected Tests:** TC005, TC019, TC034-TC035  
**Workaround:** Configure branch database credentials in .env file before running tests.

### Issue 3: Redis Cache Connection Issues
**Location:** services/cache_service.py  
**Description:** Redis cache may fail if Redis service is not running in Docker.  
**Affected Tests:** TC022  
**Workaround:** Ensure `docker compose up -d` completes successfully and Redis container is running.

### Issue 4: Role-Based Access Control Not Fully Tested
**Location:** middleware/auth.py, API endpoints  
**Description:** @require_role decorators need proper token with role information to be tested properly.  
**Affected Tests:** TC013, TC029, TC040, TC052, TC057  
**Workaround:** Create separate test tokens with different roles (admin, giam_doc, truong_phong, nhan_vien).

### Issue 5: Pagination Implementation May Have Edge Cases
**Location:** services/employee_service.py, db.py  
**Description:** Pagination may not handle invalid page numbers or limits correctly.  
**Affected Tests:** TC025  
**Workaround:** Test with various page/limit combinations including edge cases (page=0, negative limits, etc.).

### Issue 6: Sensitive Field Masking Inconsistencies
**Location:** services/employee_service.py  
**Description:** Sensitive fields may not be consistently masked across all user types.  
**Affected Tests:** TC028, TC024  
**Workaround:** Verify masking logic for each role type separately.

### Issue 7: Soft Delete Verification
**Location:** services/employee_service.py, services/product_service.py  
**Description:** Soft delete may not properly mark records as deleted or may not prevent them from appearing in lists.  
**Affected Tests:** TC016, TC032, TC042, TC049  
**Workaround:** Query database directly to verify soft delete status.

### Issue 8: Error Handling for Missing Fields
**Location:** API endpoints, services  
**Description:** Some endpoints may not properly validate or return appropriate error codes for missing required fields.  
**Affected Tests:** TC003, TC014, TC030  
**Workaround:** Add comprehensive validation in request handlers.

### Issue 9: Database Connection Pooling Under Load
**Location:** db.py, config.py  
**Description:** Connection pooling may have issues under concurrent test execution.  
**Affected Tests:** All DB-related tests  
**Workaround:** Run tests sequentially or with reduced concurrency.

### Issue 10: Multi-Database Support Incomplete
**Location:** services/auth_service.py, db.py  
**Description:** PostgreSQL driver is not implemented; only SQL Server and MySQL are partially supported.  
**Affected Tests:** Branch-related tests for CN02  
**Workaround:** Implement PostgreSQL driver before testing CN02 endpoints.

---

## Testing Recommendations

1. **Run tests in this order:**
   - Authentication tests first (verify token generation)
   - Single endpoint tests (verify basic functionality)
   - Cross-endpoint tests (verify data consistency)
   - Authorization tests (verify access control)

2. **Use test database:**
   - Create separate test database from production
   - Seed test data before each test run
   - Clean up after tests complete

3. **Mock external dependencies:**
   - Mock Redis for cache tests
   - Mock email/notification services
   - Mock external API calls

4. **Performance testing:**
   - Test pagination with large datasets
   - Test caching effectiveness
   - Test concurrent requests

5. **Security testing:**
   - Test SQL injection prevention
   - Test XSS prevention in responses
   - Test authorization bypass attempts

---

## Test Execution Report

**Date:** May 6, 2026  
**Status:** Test cases created and documented  
**Next Steps:**
1. Fix identified issues
2. Run full test suite
3. Generate coverage report
4. Document results

---
