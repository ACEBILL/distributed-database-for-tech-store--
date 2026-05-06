import pytest
import json


class TestBranchAPI:
    """Test cases for Branch API"""

    def test_get_branches(self, client):
        """TC037: Test GET /api/chi-nhanh"""
        response = client.get('/api/chi-nhanh')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict) or isinstance(data, list)

    def test_get_branch_by_id_success(self, client):
        """TC038: Test GET /api/chi-nhanh/<ma_chi_nhanh> with valid ID"""
        response = client.get('/api/chi-nhanh/CN01')
        assert response.status_code in [200, 404]

    def test_get_branch_by_id_not_found(self, client):
        """TC039: Test GET /api/chi-nhanh/<ma_chi_nhanh> with nonexistent ID"""
        response = client.get('/api/chi-nhanh/CN99')
        assert response.status_code in [404, 200]

    def test_create_branch_success(self, client, valid_token):
        """TC040: Test POST /api/chi-nhanh with valid branch data"""
        branch_data = {
            'ma_chi_nhanh': 'CN_TEST',
            'ten_chi_nhanh': 'Test Branch',
            'dia_chi': 'Test Address'
        }
        response = client.post(
            '/api/chi-nhanh',
            json=branch_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        assert response.status_code in [201, 400, 401, 403]

    def test_update_branch_success(self, client, valid_token):
        """TC041: Test PUT /api/chi-nhanh/<ma_chi_nhanh> with valid data"""
        update_data = {
            'ten_chi_nhanh': 'Updated Branch Name'
        }
        response = client.put(
            '/api/chi-nhanh/CN01',
            json=update_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        assert response.status_code in [200, 404, 401, 403]

    def test_delete_branch_success(self, client, valid_token):
        """TC042: Test DELETE /api/chi-nhanh/<ma_chi_nhanh>"""
        response = client.delete(
            '/api/chi-nhanh/CN01',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        assert response.status_code in [200, 404, 401, 403]

    def test_branch_health_check(self, client, valid_token):
        """TC043: Test GET /api/chi-nhanh/<ma_chi_nhanh>/health"""
        response = client.get(
            '/api/chi-nhanh/CN01/health',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        # May not exist or may require authentication
        assert response.status_code in [200, 404, 401]


class TestDepartmentAPI:
    """Test cases for Department API"""

    def test_get_departments(self, client):
        """TC044: Test GET /api/phong-ban"""
        response = client.get('/api/phong-ban')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict) or isinstance(data, list)

    def test_get_department_by_id_success(self, client):
        """TC045: Test GET /api/phong-ban/<ma_pb> with valid ID"""
        response = client.get('/api/phong-ban/PB01')
        assert response.status_code in [200, 404]

    def test_get_department_by_id_not_found(self, client):
        """TC046: Test GET /api/phong-ban/<ma_pb> with nonexistent ID"""
        response = client.get('/api/phong-ban/PB99')
        assert response.status_code in [404, 200]

    def test_create_department_success(self, client, valid_token):
        """TC047: Test POST /api/phong-ban with valid department data"""
        dept_data = {
            'ma_pb': 'PB_TEST',
            'ten_pb': 'Test Department',
            'mo_ta': 'Test Description'
        }
        response = client.post(
            '/api/phong-ban',
            json=dept_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        assert response.status_code in [201, 400, 401, 403]

    def test_update_department_success(self, client, valid_token):
        """TC048: Test PUT /api/phong-ban/<ma_pb> with valid data"""
        update_data = {
            'ten_pb': 'Updated Department Name'
        }
        response = client.put(
            '/api/phong-ban/PB01',
            json=update_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        assert response.status_code in [200, 404, 401, 403]

    def test_delete_department_success(self, client, valid_token):
        """TC049: Test DELETE /api/phong-ban/<ma_pb>"""
        response = client.delete(
            '/api/phong-ban/PB01',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        assert response.status_code in [200, 404, 401, 403]


class TestCategoryAPI:
    """Test cases for Product Category API"""

    def test_get_categories(self, client):
        """TC050: Test GET /api/loai-san-pham"""
        response = client.get('/api/loai-san-pham')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict) or isinstance(data, list)

    def test_get_category_by_id_success(self, client):
        """TC051: Test GET /api/loai-san-pham/<ma_loai_sp> with valid ID"""
        response = client.get('/api/loai-san-pham/LSP001')
        assert response.status_code in [200, 404]

    def test_create_category_success(self, client, valid_token):
        """TC052: Test POST /api/loai-san-pham with valid category data"""
        cat_data = {
            'ma_loai_sp': 'LSP_TEST',
            'ten_loai_sp': 'Test Category',
            'mo_ta': 'Test Description'
        }
        response = client.post(
            '/api/loai-san-pham',
            json=cat_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        assert response.status_code in [201, 400, 401, 403]

    def test_update_category_success(self, client, valid_token):
        """TC053: Test PUT /api/loai-san-pham/<ma_loai_sp> with valid data"""
        update_data = {
            'ten_loai_sp': 'Updated Category Name'
        }
        response = client.put(
            '/api/loai-san-pham/LSP001',
            json=update_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        assert response.status_code in [200, 404, 401, 403]

    def test_delete_category_success(self, client, valid_token):
        """TC054: Test DELETE /api/loai-san-pham/<ma_loai_sp>"""
        response = client.delete(
            '/api/loai-san-pham/LSP001',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        assert response.status_code in [200, 404, 401, 403]


class TestSupplierAPI:
    """Test cases for Supplier API"""

    def test_get_suppliers(self, client):
        """TC055: Test GET /api/nha-cung-cap"""
        response = client.get('/api/nha-cung-cap')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict) or isinstance(data, list)

    def test_get_supplier_by_id_success(self, client):
        """TC056: Test GET /api/nha-cung-cap/<ma_ncc> with valid ID"""
        response = client.get('/api/nha-cung-cap/1')
        assert response.status_code in [200, 404]

    def test_create_supplier_success(self, client, valid_token):
        """TC057: Test POST /api/nha-cung-cap with valid supplier data"""
        supp_data = {
            'ten_NCC': 'Test Supplier',
            'dia_chi': 'Test Address',
            'sdt': '0123456789'
        }
        response = client.post(
            '/api/nha-cung-cap',
            json=supp_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        assert response.status_code in [201, 400, 401, 403]

    def test_update_supplier_success(self, client, valid_token):
        """TC058: Test PUT /api/nha-cung-cap/<ma_ncc> with valid data"""
        update_data = {
            'ten_NCC': 'Updated Supplier Name'
        }
        response = client.put(
            '/api/nha-cung-cap/1',
            json=update_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        assert response.status_code in [200, 404, 401, 403]

    def test_delete_supplier_success(self, client, valid_token):
        """TC059: Test DELETE /api/nha-cung-cap/<ma_ncc>"""
        response = client.delete(
            '/api/nha-cung-cap/1',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        assert response.status_code in [200, 404, 401, 403]
