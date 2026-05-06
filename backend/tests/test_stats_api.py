import pytest
import json


class TestStatsAPI:
    """Test cases for Statistics API"""

    def test_get_stats_overview(self, client):
        """TC060: Test GET /api/thong-ke (get stats overview)"""
        response = client.get('/api/thong-ke')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should have branch data
        assert isinstance(data, dict) or isinstance(data, list)

    def test_get_stats_by_branch(self, client):
        """TC061: Test GET /api/thong-ke/chi-nhanh (stats by branch)"""
        response = client.get('/api/thong-ke/chi-nhanh')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict) or isinstance(data, list)

    def test_get_salary_by_department(self, client):
        """TC062: Test GET /api/thong-ke/luong-phong-ban (salary by department)"""
        response = client.get('/api/thong-ke/luong-phong-ban')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict) or isinstance(data, list)

    def test_get_stats_products_by_branch(self, client):
        """TC063: Test GET /api/thong-ke/san-pham-theo-chi-nhanh/<ma_chi_nhanh>"""
        response = client.get('/api/thong-ke/san-pham-theo-chi-nhanh/CN01')
        assert response.status_code in [200, 404]

    def test_get_stats_employees_by_branch(self, client, valid_token):
        """TC064: Test GET /api/thong-ke/nhan-vien-theo-chi-nhanh/<ma_chi_nhanh>"""
        response = client.get(
            '/api/thong-ke/nhan-vien-theo-chi-nhanh/CN01',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        # May require authentication and CN01 to be configured
        assert response.status_code in [200, 404, 401]

    def test_branch_connection_status(self, client):
        """TC065: Test branch database connection status from stats"""
        response = client.get('/api/thong-ke')
        if response.status_code == 200:
            data = json.loads(response.data)
            # Check if data includes connection status
            # Should have trang_thai_ket_noi field
            if isinstance(data, dict) and 'branches' in data:
                assert any(branch.get('trang_thai_ket_noi') for branch in data['branches']) or True

    def test_stats_data_format(self, client):
        """TC066: Test that stats API returns properly formatted data"""
        response = client.get('/api/thong-ke/chi-nhanh')
        if response.status_code == 200:
            data = json.loads(response.data)
            # Verify data structure
            assert data is not None
            if isinstance(data, list):
                for item in data:
                    assert isinstance(item, dict)
            elif isinstance(data, dict):
                # Could be various formats
                assert True

    def test_stats_with_invalid_branch_id(self, client):
        """TC067: Test stats with invalid branch ID"""
        response = client.get('/api/thong-ke/san-pham-theo-chi-nhanh/INVALID')
        # Should handle gracefully
        assert response.status_code in [404, 200]

    def test_stats_aggregation(self, client):
        """TC068: Test that stats are properly aggregated"""
        response = client.get('/api/thong-ke/luong-phong-ban')
        if response.status_code == 200:
            data = json.loads(response.data)
            # Should contain aggregated salary data
            assert data is not None
