"""
Iteration 58 - Smart GetYourGuide Link System Tests
Tests for:
1. Backend: GET /api/affiliate-links returns GYG URL with affiliate_id WFPE9ME
2. Backend: POST /api/affiliate-click tracking for getyourguide platform
3. Frontend: GYG analytics script in head with data-gyg-partner-id=WFPE9ME
4. Frontend: TravelPlanner page loads without errors
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestGYGBackendAPI:
    """Backend API tests for GYG affiliate links"""
    
    def test_affiliate_links_returns_gyg_url(self):
        """GET /api/affiliate-links returns GYG URL https://www.getyourguide.com/s/ with affiliate_id WFPE9ME"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "getyourguide" in data, "getyourguide key missing from affiliate-links response"
        
        gyg = data["getyourguide"]
        assert gyg["url"] == "https://www.getyourguide.com/s/", f"GYG URL incorrect: {gyg['url']}"
        assert gyg["affiliate_id"] == "WFPE9ME", f"GYG affiliate_id incorrect: {gyg['affiliate_id']}"
        assert gyg["name"] == "GetYourGuide", f"GYG name incorrect: {gyg['name']}"
        print(f"✓ GYG affiliate link: url={gyg['url']}, affiliate_id={gyg['affiliate_id']}")
    
    def test_affiliate_click_tracking_getyourguide(self):
        """POST /api/affiliate-click tracking works for getyourguide platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "getyourguide"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "tracked", f"Expected status 'tracked', got {data}"
        print("✓ GYG click tracking works")
    
    def test_affiliate_click_invalid_platform(self):
        """POST /api/affiliate-click returns 400 for invalid platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "invalid_platform"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid platform returns 400")
    
    def test_affiliate_links_structure(self):
        """GET /api/affiliate-links returns all expected platforms"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        expected_platforms = ["skyscanner", "booking", "hotels", "getyourguide", "cars", "airalo", "holafly", "insurance", "googlemaps"]
        
        for platform in expected_platforms:
            assert platform in data, f"Platform {platform} missing from affiliate-links"
            assert "url" in data[platform], f"Platform {platform} missing 'url' field"
            assert "name" in data[platform], f"Platform {platform} missing 'name' field"
        
        print(f"✓ All {len(expected_platforms)} platforms present in affiliate-links")


class TestGYGFrontendIntegration:
    """Frontend integration tests for GYG smart links"""
    
    def test_index_html_gyg_script(self):
        """GYG analytics script loaded in head with data-gyg-partner-id=WFPE9ME"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        html = response.text
        # Check for GYG widget script with partner ID
        assert 'data-gyg-partner-id="WFPE9ME"' in html, "GYG partner ID not found in HTML"
        assert 'widget.getyourguide.com' in html, "GYG widget script not found in HTML"
        print("✓ GYG analytics script with partner_id=WFPE9ME found in index.html")
    
    def test_travel_planner_page_loads(self):
        """TravelPlanner page loads without errors"""
        response = requests.get(f"{BASE_URL}/travel-planner")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        html = response.text
        # Check for React app root
        assert 'id="root"' in html, "React root element not found"
        print("✓ TravelPlanner page loads successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
