# Test Suite for Distributed Database Tech Store

This directory contains comprehensive test cases for the backend API.

## Overview

- **Total Test Cases:** 68
- **Coverage:** Authentication, Products, Employees, Branches, Departments, Categories, Suppliers, Statistics
- **Framework:** pytest
- **Documentation:** TEST_CASES.md, TEST_CASES.docx (in root directory)

## Files

- `conftest.py` - Test configuration, fixtures, and setup
- `test_auth_api.py` - Authentication API tests (TC001-TC008)
- `test_product_api.py` - Product API tests (TC009-TC022)
- `test_employee_api.py` - Employee API tests (TC023-TC036)
- `test_other_api.py` - Branch, Department, Category, Supplier tests (TC037-TC059)
- `test_stats_api.py` - Statistics API tests (TC060-TC068)

## Installation

```bash
cd backend
pip install -r test_requirements.txt
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_auth_api.py -v
pytest tests/test_product_api.py -v
```

### Run specific test class
```bash
pytest tests/test_auth_api.py::TestAuthAPI -v
```

### Run specific test case
```bash
pytest tests/test_auth_api.py::TestAuthAPI::test_login_success -v
```

### Run with coverage report
```bash
pytest tests/ --cov=.. --cov-report=html --cov-report=term
```

### Run in verbose mode with output capture disabled
```bash
pytest tests/ -vvs
```

## Test Results

Each test case includes:
- **Test ID:** TC### format
- **Description:** What is being tested
- **Endpoint:** API endpoint being called
- **Expected Status:** HTTP status code expected
- **Location:** Which files are affected

## Known Issues

Refer to [backend/README.md](../README.md#known-issues-and-errors-from-testing) for detailed list of issues found during testing:

1. JWT Token Verification Issues
2. Branch Database Configuration Not Set Up
3. Redis Cache Connection Issues
4. Role-Based Access Control
5. Pagination Edge Cases
6. Multi-Database Support Incomplete
7. Sensitive Field Masking
8. Soft Delete Verification
9. Missing Field Validation
10. Database Connection Pooling

## Test Case Mapping

### Authentication Tests (TC001-TC008)
- Login functionality
- Token generation
- User profile retrieval
- Branch authentication

### Product Tests (TC009-TC022)
- List products
- Create, read, update, delete products
- Filter by category/supplier
- Pagination
- Caching

### Employee Tests (TC023-TC036)
- List employees with pagination
- Create, read, update, delete employees
- Filter by department
- Branch employees
- Sensitive field masking

### Branch Tests (TC037-TC043)
- CRUD operations
- Health checks

### Department Tests (TC044-TC049)
- CRUD operations

### Category Tests (TC050-TC054)
- CRUD operations

### Supplier Tests (TC055-TC059)
- CRUD operations

### Statistics Tests (TC060-TC068)
- Branch statistics
- Salary statistics
- Product statistics
- Employee statistics

## Development Notes

- Tests use fixtures from `conftest.py` for app, client, and authentication
- Use valid tokens for authentication tests
- Mock external dependencies as needed
- Some tests may fail if database is not properly configured
- Run tests after `docker compose up -d` to ensure services are running

## CI/CD Integration

To integrate with CI/CD pipeline:

```bash
# Example GitHub Actions
pytest backend/tests/ --cov=backend --cov-report=xml
pytest backend/tests/ --junit-xml=test-results.xml
```

## Troubleshooting

### Tests fail with connection errors
- Ensure Docker containers are running: `docker compose ps`
- Check database credentials in `.env`

### JWT token tests fail
- Verify Redis is running: `docker compose logs redis`
- Check token expiration time in `services/auth_service.py`

### Import errors
- Ensure backend directory is in PYTHONPATH: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

### Permission denied
- On Linux/macOS: `chmod +x conftest.py`
