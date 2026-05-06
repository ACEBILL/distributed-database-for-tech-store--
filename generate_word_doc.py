
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_heading_with_style(doc, text, level=1):
    """Add heading with proper formatting"""
    heading = doc.add_heading(text, level=level)
    return heading

def add_table_of_contents(doc):
    """Add table of contents"""
    heading = doc.add_heading("Table of Contents", level=1)
    
    # Manual TOC for readability
    sections = [
        "1. Test Environment Setup",
        "2. Authentication API Tests",
        "3. Product API Tests",
        "4. Employee API Tests",
        "5. Branch API Tests",
        "6. Department API Tests",
        "7. Category API Tests",
        "8. Supplier API Tests",
        "9. Statistics API Tests",
        "10. Known Issues",
        "11. Testing Recommendations",
    ]
    
    for section in sections:
        p = doc.add_paragraph(section, style='List Bullet')

def add_test_case(doc, tc_number, name, endpoint, method, expected, notes):
    """Add a test case to document"""
    # Test case heading
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    run = p.add_run(f"TC{tc_number:03d}: {name}")
    run.bold = True
    run.font.size = Pt(11)
    
    # Details table
    table = doc.add_table(rows=6, cols=2)
    table.style = 'Light Grid Accent 1'
    
    rows = table.rows
    rows[0].cells[0].text = "Endpoint"
    rows[0].cells[1].text = endpoint
    rows[1].cells[0].text = "Method"
    rows[1].cells[1].text = method
    rows[2].cells[0].text = "Expected Status"
    rows[2].cells[1].text = expected
    rows[3].cells[0].text = "Notes/Location"
    rows[3].cells[1].text = notes
    rows[4].cells[0].text = "Status"
    rows[4].cells[1].text = "Not Tested"
    rows[5].cells[0].text = "Issues Found"
    rows[5].cells[1].text = "None"
    
    doc.add_paragraph()  # Spacing

def generate_test_document():
    """Generate comprehensive test case Word document"""
    doc = Document()
    
    # Title page
    title = doc.add_heading("Test Case Document", 0)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    
    subtitle = doc.add_paragraph("Distributed Database for Tech Store")
    subtitle.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    subtitle_format = subtitle.runs[0]
    subtitle_format.bold = True
    subtitle_format.font.size = Pt(14)
    
    doc.add_paragraph()  # Spacing
    
    info_para = doc.add_paragraph()
    info_para.add_run(f"Date: {datetime.now().strftime('%B %d, %Y')}\n")
    info_para.add_run("Project: Distributed Database System for Tech Store\n")
    info_para.add_run("Scope: Backend API Testing (Flask + SQL Server/MySQL)\n")
    info_para.add_run("Total Test Cases: 68\n")
    
    doc.add_page_break()
    
    # Table of contents
    add_table_of_contents(doc)
    
    doc.add_page_break()
    
    # Test Environment Setup
    doc.add_heading("1. Test Environment Setup", 1)
    doc.add_paragraph(
        "This section describes the setup required to run the test suite."
    )
    
    doc.add_heading("Prerequisites", 2)
    doc.add_paragraph("Docker Desktop running", style='List Bullet')
    doc.add_paragraph("Python 3.8+", style='List Bullet')
    doc.add_paragraph("pytest installed", style='List Bullet')
    
    doc.add_heading("Installation", 2)
    p = doc.add_paragraph()
    p.add_run("pip install pytest pytest-cov").font.name = 'Courier New'
    
    doc.add_heading("Running Tests", 2)
    commands = [
        "pytest backend/tests/ -v",
        "pytest backend/tests/ --cov=backend --cov-report=html",
        "pytest backend/tests/test_auth_api.py -v"
    ]
    for cmd in commands:
        p = doc.add_paragraph(cmd, style='List Bullet')
        p.runs[0].font.name = 'Courier New'
    
    doc.add_page_break()
    
    # Authentication API Tests
    doc.add_heading("2. Authentication API Tests", 1)
    
    test_cases_auth = [
        (1, "Successful login with valid credentials", "POST /api/auth/login", 
         "POST", "200", "auth_api.py, auth_service.py"),
        (2, "Login with invalid credentials", "POST /api/auth/login", 
         "POST", "401", "auth_api.py"),
        (3, "Login with missing required fields", "POST /api/auth/login", 
         "POST", "400/401", "auth_api.py, auth_service.py"),
        (4, "Login with nonexistent employee ID", "POST /api/auth/login", 
         "POST", "401", "auth_service.py"),
        (5, "Branch login for CN01", "POST /api/auth/branches/CN01/login", 
         "POST", "200/400", "auth_api.py"),
        (6, "Branch login for nonexistent branch", "POST /api/auth/branches/CN99/login", 
         "POST", "400/404", "auth_api.py"),
        (7, "Get /me without authentication", "GET /api/auth/me", 
         "GET", "401", "auth_api.py"),
        (8, "Get /me with valid token", "GET /api/auth/me", 
         "GET", "200", "auth_api.py"),
    ]
    
    for tc_num, name, endpoint, method, expected, notes in test_cases_auth:
        add_test_case(doc, tc_num, name, endpoint, method, expected, notes)
    
    doc.add_page_break()
    
    # Product API Tests
    doc.add_heading("3. Product API Tests", 1)
    
    test_cases_product = [
        (9, "GET products without auth", "GET /api/san-pham", "GET", "401", "product_api.py"),
        (10, "GET products with auth", "GET /api/san-pham", "GET", "200", "product_api.py"),
        (11, "GET product by ID (valid)", "GET /api/san-pham/SP001", "GET", "200/404", "product_api.py"),
        (12, "GET product by ID (not found)", "GET /api/san-pham/SP999", "GET", "404", "product_api.py"),
        (13, "CREATE product", "POST /api/san-pham", "POST", "201", "product_api.py"),
        (14, "CREATE product (missing fields)", "POST /api/san-pham", "POST", "400", "product_api.py"),
        (15, "UPDATE product", "PUT /api/san-pham/SP001", "PUT", "200/404", "product_api.py"),
        (16, "DELETE product (soft delete)", "DELETE /api/san-pham/SP001", "DELETE", "200/404", "product_api.py"),
        (17, "GET products by branch", "GET /api/san-pham-theo-chi-nhanh", "GET", "200", "product_api.py"),
        (18, "GET products by branch ID", "GET /api/san-pham/chi-nhanh/CN01", "GET", "200", "product_api.py"),
        (19, "GET products from branch DB", "GET /api/chi-nhanh/CN01/san-pham", "GET", "200/400", "product_api.py"),
        (20, "GET products by category", "GET /api/san-pham/loai/LSP001", "GET", "200", "product_api.py"),
        (21, "GET products by supplier", "GET /api/san-pham/ncc/1", "GET", "200", "product_api.py"),
        (22, "Test product caching", "GET /api/san-pham", "GET", "200", "cache_service.py"),
    ]
    
    for tc_num, name, endpoint, method, expected, notes in test_cases_product:
        add_test_case(doc, tc_num, name, endpoint, method, expected, notes)
    
    doc.add_page_break()
    
    # Employee API Tests
    doc.add_heading("4. Employee API Tests", 1)
    
    test_cases_employee = [
        (23, "GET employees without auth", "GET /api/nhan-vien", "GET", "401", "employee_api.py"),
        (24, "GET employees with auth", "GET /api/nhan-vien", "GET", "200", "employee_api.py"),
        (25, "GET employees with pagination", "GET /api/nhan-vien?page=1&limit=10", "GET", "200", "employee_api.py"),
        (26, "GET employee by ID (valid)", "GET /api/nhan-vien/NV001", "GET", "200", "employee_api.py"),
        (27, "GET employee by ID (not found)", "GET /api/nhan-vien/NV999", "GET", "404", "employee_api.py"),
        (28, "Sensitive field masking", "GET /api/nhan-vien", "GET", "200", "employee_service.py"),
        (29, "CREATE employee", "POST /api/nhan-vien", "POST", "201", "employee_api.py"),
        (30, "CREATE employee (missing fields)", "POST /api/nhan-vien", "POST", "400", "employee_api.py"),
        (31, "UPDATE employee", "PUT /api/nhan-vien/NV001", "PUT", "200", "employee_api.py"),
        (32, "DELETE employee", "DELETE /api/nhan-vien/NV001", "DELETE", "200", "employee_api.py"),
        (33, "GET employees by department", "GET /api/nhan-vien/phong-ban/PB01", "GET", "200", "employee_api.py"),
        (34, "GET branch employees", "GET /api/chi-nhanh/CN01/nhan-vien", "GET", "200/400", "employee_api.py"),
    ]
    
    for tc_num, name, endpoint, method, expected, notes in test_cases_employee:
        add_test_case(doc, tc_num, name, endpoint, method, expected, notes)
    
    doc.add_page_break()
    
    # Branch API Tests
    doc.add_heading("5. Branch API Tests", 1)
    
    test_cases_branch = [
        (37, "GET branches", "GET /api/chi-nhanh", "GET", "200", "branch_api.py"),
        (38, "GET branch by ID (valid)", "GET /api/chi-nhanh/CN01", "GET", "200", "branch_api.py"),
        (39, "GET branch by ID (not found)", "GET /api/chi-nhanh/CN99", "GET", "404", "branch_api.py"),
        (40, "CREATE branch", "POST /api/chi-nhanh", "POST", "201", "branch_api.py"),
        (41, "UPDATE branch", "PUT /api/chi-nhanh/CN01", "PUT", "200", "branch_api.py"),
        (42, "DELETE branch", "DELETE /api/chi-nhanh/CN01", "DELETE", "200", "branch_api.py"),
    ]
    
    for tc_num, name, endpoint, method, expected, notes in test_cases_branch:
        add_test_case(doc, tc_num, name, endpoint, method, expected, notes)
    
    doc.add_page_break()
    
    # Known Issues
    doc.add_heading("10. Known Issues and Errors", 1)
    
    issues = [
        {
            "title": "Issue 1: Token Verification Issues",
            "location": "middleware/auth.py, services/auth_service.py",
            "description": "JWT token verification may fail during testing",
            "affected": "TC008, TC024, TC034",
            "workaround": "Use real login endpoint or mock token generation"
        },
        {
            "title": "Issue 2: Branch Database Configuration",
            "location": "config.py, .env.example",
            "description": "CN01 and CN02 branch DBs not configured by default",
            "affected": "TC005, TC019, TC034",
            "workaround": "Configure .env with branch database credentials"
        },
        {
            "title": "Issue 3: Redis Cache Connection",
            "location": "services/cache_service.py",
            "description": "Redis may fail if service not running",
            "affected": "TC022",
            "workaround": "Ensure docker compose completes and Redis is running"
        },
        {
            "title": "Issue 4: Role-Based Access Control",
            "location": "middleware/auth.py",
            "description": "@require_role decorators need proper role tokens",
            "affected": "TC013, TC029, TC040",
            "workaround": "Create test tokens with different roles"
        },
        {
            "title": "Issue 5: Pagination Edge Cases",
            "location": "services/employee_service.py, db.py",
            "description": "Pagination may not handle invalid page numbers",
            "affected": "TC025",
            "workaround": "Test with edge cases (page=0, negative limits)"
        },
    ]
    
    for issue in issues:
        p = doc.add_paragraph()
        run = p.add_run(issue["title"])
        run.bold = True
        
        doc.add_paragraph(f"Location: {issue['location']}", style='List Bullet')
        doc.add_paragraph(f"Description: {issue['description']}", style='List Bullet')
        doc.add_paragraph(f"Affected Tests: {issue['affected']}", style='List Bullet')
        doc.add_paragraph(f"Workaround: {issue['workaround']}", style='List Bullet')
        doc.add_paragraph()
    
    # Save document
    doc.save('TEST_CASES.docx')
    print("Word document created successfully: TEST_CASES.docx")

if __name__ == "__main__":
    generate_test_document()
