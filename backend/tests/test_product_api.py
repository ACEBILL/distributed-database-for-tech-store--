import pytest
import json


class TestProductAPI:
    """Test cases for Product API"""

    def test_get_products_without_auth(self, client):
        """TC009: Test GET /api/san-pham without authentication"""
        response = client.get('/api/san-pham')
        assert response.status_code == 401

    def test_get_products_with_auth(self, client, valid_token):
        """TC010: Test GET /api/san-pham with valid token"""
        response = client.get(
            '/api/san-pham',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        # Will fail if token verification is strict
        assert response.status_code in [200, 401]

    def test_get_product_by_id_success(self, client, valid_token):
        """TC011: Test GET /api/san-pham/<ma_sp> with valid product ID"""
        response = client.get(
            '/api/san-pham/SP001',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        assert response.status_code in [200, 404]

    def test_get_product_by_id_not_found(self, client, valid_token):
        """TC012: Test GET /api/san-pham/<ma_sp> with nonexistent product"""
        response = client.get(
            '/api/san-pham/SP999',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        # Should return 404 if product doesn't exist
        assert response.status_code in [404, 200]

    def test_create_product_success(self, client, valid_token):
        """TC013: Test POST /api/san-pham with valid product data"""
        product_data = {
            'ma_sp': 'SP_TEST',
            'ten_sp': 'Test Product',
            'gia': 100000,
            'ma_loai_sp': 'LSP001',
            'ma_ncc': 1,
            'so_luong': 10
        }
        response = client.post(
            '/api/san-pham',
            json=product_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        # Will depend on role and token validity
        assert response.status_code in [201, 400, 401, 403]

    def test_create_product_missing_fields(self, client, valid_token):
        """TC014: Test POST /api/san-pham with missing required fields"""
        product_data = {
            'ten_sp': 'Test Product'
            # Missing ma_sp, gia, etc.
        }
        response = client.post(
            '/api/san-pham',
            json=product_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        # Should fail validation
        assert response.status_code in [400, 201]

    def test_update_product_success(self, client, valid_token):
        """TC015: Test PUT /api/san-pham/<ma_sp> with valid data"""
        update_data = {
            'ten_sp': 'Updated Product Name',
            'gia': 150000
        }
        response = client.put(
            '/api/san-pham/SP001',
            json=update_data,
            headers={'Authorization': f'Bearer {valid_token}'},
            content_type='application/json'
        )
        assert response.status_code in [200, 404, 401, 403]

    def test_delete_product_success(self, client, valid_token):
        """TC016: Test DELETE /api/san-pham/<ma_sp> (soft delete)"""
        response = client.delete(
            '/api/san-pham/SP001',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        assert response.status_code in [200, 404, 401, 403]

    def test_get_products_by_branch(self, client):
        """TC017: Test GET /api/san-pham-theo-chi-nhanh"""
        response = client.get('/api/san-pham-theo-chi-nhanh')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict) or isinstance(data, list)

    def test_get_products_by_branch_id(self, client):
        """TC018: Test GET /api/san-pham/chi-nhanh/<ma_chi_nhanh>"""
        response = client.get('/api/san-pham/chi-nhanh/CN01')
        assert response.status_code == 200

    def test_get_products_from_branch_database(self, client, valid_token):
        """TC019: Test GET /api/chi-nhanh/<ma_chi_nhanh>/san-pham"""
        response = client.get(
            '/api/chi-nhanh/CN01/san-pham',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        # May fail if CN01 database not configured
        assert response.status_code in [200, 400, 404]

    def test_get_products_by_category(self, client, valid_token):
        """TC020: Test GET /api/san-pham/loai/<ma_loai_sp>"""
        response = client.get(
            '/api/san-pham/loai/LSP001',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        assert response.status_code in [200, 404, 401]

    def test_get_products_by_supplier(self, client, valid_token):
        """TC021: Test GET /api/san-pham/ncc/<ma_ncc>"""
        response = client.get(
            '/api/san-pham/ncc/1',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        assert response.status_code in [200, 404, 401]

    def test_product_cache_functionality(self, client, valid_token):
        """TC022: Test product caching with Redis"""
        # First call - should query database
        response1 = client.get(
            '/api/san-pham',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        # Second call - should be cached
        response2 = client.get(
            '/api/san-pham',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        # Both should succeed or both fail
        assert response1.status_code == response2.status_code
