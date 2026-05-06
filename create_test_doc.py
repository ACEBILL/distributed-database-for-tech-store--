from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from datetime import datetime

doc = Document()

# Title page
title = doc.add_heading('Test Case Document', 0)
title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

subtitle = doc.add_paragraph('Distributed Database for Tech Store')
subtitle.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
subtitle.runs[0].bold = True
subtitle.runs[0].font.size = Pt(14)

doc.add_paragraph()

info_para = doc.add_paragraph()
info_para.add_run(f"Date: {datetime.now().strftime('%B %d, %Y')}\n")
info_para.add_run('Project: Distributed Database System for Tech Store\n')
info_para.add_run('Scope: Backend API Testing (Flask + SQL Server/MySQL)\n')
info_para.add_run('Total Test Cases: 68\n')

doc.add_page_break()

# Table of Contents
doc.add_heading('Table of Contents', 1)
sections = [
    '1. Test Environment Setup',
    '2. Authentication API Tests (TC001-TC008)',
    '3. Product API Tests (TC009-TC022)',
    '4. Employee API Tests (TC023-TC036)',
    '5. Branch API Tests (TC037-TC043)',
    '6. Department API Tests (TC044-TC049)',
    '7. Category API Tests (TC050-TC054)',
    '8. Supplier API Tests (TC055-TC059)',
    '9. Statistics API Tests (TC060-TC068)',
    '10. Known Issues and Errors',
]
for section in sections:
    doc.add_paragraph(section, style='List Bullet')

doc.add_page_break()

# Test Environment Setup
doc.add_heading('1. Test Environment Setup', 1)
doc.add_paragraph('This section describes the setup required to run the test suite.')

doc.add_heading('Prerequisites', 2)
doc.add_paragraph('Docker Desktop running', style='List Bullet')
doc.add_paragraph('Python 3.8+', style='List Bullet')
doc.add_paragraph('pytest installed', style='List Bullet')

doc.add_heading('Installation', 2)
p = doc.add_paragraph('pip install pytest pytest-cov')
p.runs[0].font.name = 'Courier New'

doc.add_heading('Running Tests', 2)
commands = [
    'pytest backend/tests/ -v',
    'pytest backend/tests/ --cov=backend --cov-report=html',
]
for cmd in commands:
    p = doc.add_paragraph(cmd, style='List Bullet')
    p.runs[0].font.name = 'Courier New'

doc.add_page_break()

# Authentication API Tests
doc.add_heading('2. Authentication API Tests', 1)

auth_tests = [
    ('TC001', 'Successful login with valid credentials', 'POST /api/auth/login', '200', 'auth_api.py, auth_service.py'),
    ('TC002', 'Login with invalid credentials', 'POST /api/auth/login', '401', 'auth_api.py'),
    ('TC003', 'Login with missing required fields', 'POST /api/auth/login', '400/401', 'auth_api.py'),
    ('TC004', 'Login with nonexistent employee ID', 'POST /api/auth/login', '401', 'auth_service.py'),
    ('TC005', 'Branch login for CN01', 'POST /api/auth/branches/CN01/login', '200/400', 'auth_api.py'),
    ('TC006', 'Branch login for nonexistent branch', 'POST /api/auth/branches/CN99/login', '400/404', 'auth_api.py'),
    ('TC007', 'Get /me without authentication', 'GET /api/auth/me', '401', 'auth_api.py'),
    ('TC008', 'Get /me with valid token', 'GET /api/auth/me', '200', 'auth_api.py'),
]

for tc_id, name, endpoint, expected, notes in auth_tests:
    p = doc.add_paragraph()
    run = p.add_run(f'{tc_id}: {name}')
    run.bold = True
    run.font.size = Pt(11)
    
    table = doc.add_table(rows=3, cols=2)
    table.style = 'Light Grid Accent 1'
    
    table.rows[0].cells[0].text = 'Endpoint'
    table.rows[0].cells[1].text = endpoint
    table.rows[1].cells[0].text = 'Expected Status'
    table.rows[1].cells[1].text = expected
    table.rows[2].cells[0].text = 'Notes/Location'
    table.rows[2].cells[1].text = notes
    
    doc.add_paragraph()

doc.add_page_break()

# Product API Tests
doc.add_heading('3. Product API Tests', 1)

product_tests = [
    ('TC009', 'GET products without auth', 'GET /api/san-pham', '401', 'product_api.py'),
    ('TC010', 'GET products with auth', 'GET /api/san-pham', '200', 'product_api.py'),
    ('TC011', 'GET product by ID (valid)', 'GET /api/san-pham/SP001', '200/404', 'product_api.py'),
    ('TC012', 'GET product by ID (not found)', 'GET /api/san-pham/SP999', '404', 'product_api.py'),
    ('TC013', 'CREATE product', 'POST /api/san-pham', '201', 'product_api.py'),
    ('TC014', 'CREATE product (missing fields)', 'POST /api/san-pham', '400', 'product_api.py'),
    ('TC015', 'UPDATE product', 'PUT /api/san-pham/SP001', '200/404', 'product_api.py'),
    ('TC016', 'DELETE product (soft delete)', 'DELETE /api/san-pham/SP001', '200/404', 'product_api.py'),
]

for tc_id, name, endpoint, expected, notes in product_tests:
    p = doc.add_paragraph()
    run = p.add_run(f'{tc_id}: {name}')
    run.bold = True
    run.font.size = Pt(11)
    
    table = doc.add_table(rows=3, cols=2)
    table.style = 'Light Grid Accent 1'
    
    table.rows[0].cells[0].text = 'Endpoint'
    table.rows[0].cells[1].text = endpoint
    table.rows[1].cells[0].text = 'Expected Status'
    table.rows[1].cells[1].text = expected
    table.rows[2].cells[0].text = 'Notes/Location'
    table.rows[2].cells[1].text = notes
    
    doc.add_paragraph()

doc.add_page_break()

# Known Issues
doc.add_heading('10. Known Issues and Errors', 1)

issues = [
    {
        'title': 'Issue 1: Token Verification Issues',
        'location': 'middleware/auth.py, services/auth_service.py',
        'description': 'JWT token verification may fail during testing if token generation is not properly seeded',
        'affected': 'TC008, TC024, TC034',
        'workaround': 'Use real login endpoint or mock token generation in tests'
    },
    {
        'title': 'Issue 2: Branch Database Configuration Not Set Up',
        'location': 'config.py, .env.example',
        'description': 'CN01 (MySQL) and CN02 (PostgreSQL) branch databases are not configured in default setup',
        'affected': 'TC005, TC019, TC034, TC035',
        'workaround': 'Configure branch database credentials in .env file before running tests'
    },
    {
        'title': 'Issue 3: Redis Cache Connection Issues',
        'location': 'services/cache_service.py',
        'description': 'Redis cache may fail if Redis service is not running in Docker',
        'affected': 'TC022',
        'workaround': 'Ensure docker compose up -d completes successfully and Redis container is running'
    },
    {
        'title': 'Issue 4: Role-Based Access Control Not Fully Tested',
        'location': 'middleware/auth.py, API endpoints',
        'description': '@require_role decorators need proper token with role information to be tested properly',
        'affected': 'TC013, TC029, TC040, TC052, TC057',
        'workaround': 'Create separate test tokens with different roles (admin, giam_doc, truong_phong, nhan_vien)'
    },
    {
        'title': 'Issue 5: Pagination Implementation May Have Edge Cases',
        'location': 'services/employee_service.py, db.py',
        'description': 'Pagination may not handle invalid page numbers or limits correctly',
        'affected': 'TC025',
        'workaround': 'Test with various page/limit combinations including edge cases'
    },
    {
        'title': 'Issue 6: Multi-Database Support Incomplete',
        'location': 'services/auth_service.py, db.py',
        'description': 'PostgreSQL driver is not implemented; only SQL Server and MySQL are partially supported',
        'affected': 'Branch-related tests for CN02',
        'workaround': 'Implement PostgreSQL driver before testing CN02 endpoints'
    },
]

for issue in issues:
    p = doc.add_paragraph()
    run = p.add_run(issue['title'])
    run.bold = True
    
    doc.add_paragraph(f"Location: {issue['location']}", style='List Bullet')
    doc.add_paragraph(f"Description: {issue['description']}", style='List Bullet')
    doc.add_paragraph(f"Affected Tests: {issue['affected']}", style='List Bullet')
    doc.add_paragraph(f"Workaround: {issue['workaround']}", style='List Bullet')
    doc.add_paragraph()

# Save document
doc.save('TEST_CASES.docx')
print('Word document created successfully: TEST_CASES.docx')
