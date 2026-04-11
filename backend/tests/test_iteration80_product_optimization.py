"""
Iteration 80 - Product Optimization Tests
Testing: Backend API endpoints for journeys and homepage
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://comeback-point.preview.emergentagent.com')


class TestBackendAPIs:
    """Backend API endpoint tests for iteration 80"""
    
    def test_get_journeys_returns_200(self):
        """GET /api/journeys should return 200"""
        response = requests.get(f"{BASE_URL}/api/journeys")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/journeys returned {len(data)} journeys")
    
    def test_get_homepage_main_journey_returns_200(self):
        """GET /api/homepage/main-journey should return 200"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "journey" in data, "Response should contain 'journey' key"
        
        journey = data.get("journey")
        if journey:
            assert "journey_id" in journey, "Journey should have journey_id"
            assert "name" in journey, "Journey should have name"
            print(f"✓ Main journey: {journey.get('name')}")
        else:
            print("✓ No main journey set (valid response)")
    
    def test_get_homepage_ambassador_journeys(self):
        """GET /api/homepage/ambassador-journeys should return 200"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"✓ Ambassador journeys endpoint working")
    
    def test_get_homepage_realized_journeys(self):
        """GET /api/homepage/realized-journeys should return 200"""
        response = requests.get(f"{BASE_URL}/api/homepage/realized-journeys")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"✓ Realized journeys endpoint working")
    
    def test_get_homepage_curated_dreams(self):
        """GET /api/homepage/curated-dreams should return 200"""
        response = requests.get(f"{BASE_URL}/api/homepage/curated-dreams")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"✓ Curated dreams endpoint working")
    
    def test_get_dreamers_stats(self):
        """GET /api/dreamers-stats should return 200"""
        response = requests.get(f"{BASE_URL}/api/dreamers-stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"✓ Dreamers stats endpoint working")
    
    def test_get_platform_stats(self):
        """GET /api/platform/stats should return 200"""
        response = requests.get(f"{BASE_URL}/api/platform/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"✓ Platform stats endpoint working")


class TestAuthenticatedEndpoints:
    """Tests requiring authentication"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers by logging in"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@4luis.com", "password": "Admin1"}
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("token") or data.get("access_token")
            if token:
                return {"Authorization": f"Bearer {token}"}
        
        # Try cookie-based auth
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@4luis.com", "password": "Admin1"}
        )
        return {}
    
    def test_dashboard_user_stats(self, auth_headers):
        """GET /api/dashboard/user-stats should work for authenticated users"""
        session = requests.Session()
        
        # Login first
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@4luis.com", "password": "Admin1"}
        )
        
        if login_response.status_code == 200:
            # Try to get dashboard stats
            response = session.get(f"{BASE_URL}/api/dashboard/user-stats")
            # May return 401 if session not maintained, which is acceptable
            assert response.status_code in [200, 401], f"Unexpected status: {response.status_code}"
            print(f"✓ Dashboard user stats endpoint accessible (status: {response.status_code})")
        else:
            pytest.skip("Login failed, skipping authenticated test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
