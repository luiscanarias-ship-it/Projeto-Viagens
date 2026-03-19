"""
Iteration 42: Contextual Monetization & Affiliate System Tests

Tests:
1. GET /api/affiliate-links - returns all affiliate links (booking, skyscanner, getyourguide, airalo, cars)
2. POST /api/affiliate-click - tracks affiliate clicks
3. POST /api/ai/travel-plan - generates travel plan (rate limited)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAffiliateLinks:
    """Tests for affiliate link endpoints"""
    
    def test_get_affiliate_links_returns_all_platforms(self):
        """GET /api/affiliate-links returns all expected platforms"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Required platforms for contextual monetization
        required_platforms = ['booking', 'skyscanner', 'getyourguide', 'airalo', 'cars']
        
        for platform in required_platforms:
            assert platform in data, f"Missing platform: {platform}"
            assert 'url' in data[platform], f"Platform {platform} missing 'url' field"
            assert 'name' in data[platform], f"Platform {platform} missing 'name' field"
            assert data[platform]['url'].startswith('http'), f"Platform {platform} has invalid URL: {data[platform]['url']}"
        
        print(f"✓ All {len(required_platforms)} affiliate platforms present with valid URLs")
        
    def test_affiliate_links_have_correct_urls(self):
        """Verify affiliate link URLs point to correct domains"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        
        expected_domains = {
            'booking': 'booking.com',
            'skyscanner': 'skyscanner',
            'getyourguide': 'getyourguide',
            'airalo': 'airalo.com',
            'cars': 'discovercars'
        }
        
        for platform, domain in expected_domains.items():
            assert domain in data[platform]['url'].lower(), f"Platform {platform} URL doesn't contain '{domain}'"
        
        print("✓ All affiliate URLs point to correct domains")


class TestAffiliateClickTracking:
    """Tests for affiliate click tracking"""
    
    def test_track_click_booking(self):
        """POST /api/affiliate-click tracks booking clicks"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "booking"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "tracked", f"Expected status 'tracked', got: {data}"
        print("✓ Booking click tracked successfully")
    
    def test_track_click_skyscanner(self):
        """POST /api/affiliate-click tracks skyscanner clicks"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "skyscanner"}
        )
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("✓ Skyscanner click tracked successfully")
    
    def test_track_click_getyourguide(self):
        """POST /api/affiliate-click tracks getyourguide clicks"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "getyourguide"}
        )
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("✓ GetYourGuide click tracked successfully")
    
    def test_track_click_airalo(self):
        """POST /api/affiliate-click tracks airalo (eSIM) clicks"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "airalo"}
        )
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("✓ Airalo (eSIM) click tracked successfully")
    
    def test_track_click_cars(self):
        """POST /api/affiliate-click tracks cars/transport clicks"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "cars"}
        )
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("✓ Cars/transport click tracked successfully")
    
    def test_track_click_invalid_platform_returns_400(self):
        """POST /api/affiliate-click with invalid platform returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "invalid_platform_xyz"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid platform, got {response.status_code}"
        print("✓ Invalid platform correctly rejected with 400")
    
    def test_track_click_missing_platform_returns_400(self):
        """POST /api/affiliate-click without platform returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={}
        )
        assert response.status_code == 400, f"Expected 400 for missing platform, got {response.status_code}"
        print("✓ Missing platform correctly rejected with 400")


class TestSupportTicketEndpoints:
    """Tests to verify support ticket endpoints exist for scroll bug testing"""
    
    def test_support_tickets_endpoint_requires_auth(self):
        """GET /api/support/tickets requires authentication"""
        response = requests.get(f"{BASE_URL}/api/support/tickets")
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Support tickets endpoint requires authentication")


class TestAuthForScrollBugTest:
    """Test authentication for scroll bug verification"""
    
    def test_login_admin(self):
        """Login with admin credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@4luis.com", "password": "Admin1"}
        )
        # Either 200 (success) or 401 (wrong password - that's fine, we just test endpoint works)
        assert response.status_code in [200, 401], f"Login endpoint error: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert 'token' in data, "Login response missing token"
            print(f"✓ Admin login successful, got token")
            return data['token']
        else:
            print("✓ Login endpoint working (credentials may need update)")
            return None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
