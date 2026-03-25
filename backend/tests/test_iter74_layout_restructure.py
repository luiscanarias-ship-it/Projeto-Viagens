"""
Iteration 74 - Layout Restructure Backend Tests
Tests for existing endpoints that should still work after layout changes:
- GET /api/affiliate-links
- GET /api/plan/paris-acbc2d
- GET /api/og-image/paris-acbc2d
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestExistingEndpoints:
    """Verify existing endpoints still work after layout restructure"""
    
    def test_affiliate_links_endpoint(self):
        """GET /api/affiliate-links returns valid affiliate data"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify expected affiliate platforms exist
        expected_platforms = ['skyscanner', 'booking', 'getyourguide']
        for platform in expected_platforms:
            assert platform in data, f"Missing platform: {platform}"
            assert 'url' in data[platform], f"Missing url for {platform}"
            assert 'name' in data[platform], f"Missing name for {platform}"
        print(f"✓ Affiliate links endpoint working - {len(data)} platforms")
    
    def test_plan_endpoint(self):
        """GET /api/plan/paris-acbc2d returns valid plan data"""
        response = requests.get(f"{BASE_URL}/api/plan/paris-acbc2d")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify plan structure
        assert 'destination' in data, "Missing destination"
        assert 'plan' in data, "Missing plan object"
        assert data['destination'] == 'Paris', f"Expected Paris, got {data['destination']}"
        
        plan = data['plan']
        assert 'itinerary' in plan, "Missing itinerary in plan"
        assert 'summary' in plan, "Missing summary in plan"
        print(f"✓ Plan endpoint working - destination: {data['destination']}")
    
    def test_og_image_endpoint(self):
        """GET /api/og-image/paris-acbc2d returns PNG image"""
        response = requests.get(f"{BASE_URL}/api/og-image/paris-acbc2d")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content_type = response.headers.get('content-type', '')
        assert 'image/png' in content_type, f"Expected image/png, got {content_type}"
        
        # Verify image has content
        assert len(response.content) > 1000, "Image too small, might be broken"
        print(f"✓ OG image endpoint working - size: {len(response.content)} bytes")


class TestAuthEndpoints:
    """Test authentication for ambassador features"""
    
    def test_login_admin(self):
        """POST /api/auth/login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'token' in data, "Missing token in response"
        assert 'user' in data, "Missing user in response"
        
        user = data['user']
        # Admin has is_admin=True which grants ambassador privileges
        assert user.get('is_admin') == True or user.get('is_ambassador') == True, "Admin should have admin or ambassador status"
        print(f"✓ Admin login working - is_admin: {user.get('is_admin')}, is_ambassador: {user.get('is_ambassador')}")
        return data['token']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
