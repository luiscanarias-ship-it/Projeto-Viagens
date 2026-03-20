"""
Iteration 48 - Fixed CTA Regression Tests
Tests for hybrid CTA system: always-visible fixed CTAs + AI-generated inline CTAs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAffiliateLinksEndpoint:
    """Test affiliate-links endpoint has all required platforms including insurance"""

    def test_affiliate_links_returns_all_platforms(self):
        """GET /api/affiliate-links should return all affiliate platforms"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        required_platforms = ['booking', 'skyscanner', 'getyourguide', 'airalo', 'insurance']
        
        for platform in required_platforms:
            assert platform in data, f"Missing platform: {platform}"
            assert 'url' in data[platform], f"Platform {platform} missing 'url' key"
            assert data[platform]['url'].startswith('http'), f"Platform {platform} URL invalid"
    
    def test_insurance_affiliate_is_iati(self):
        """Insurance affiliate should be IATI Seguros"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        assert 'insurance' in data
        assert 'iati' in data['insurance']['url'].lower()


class TestAffiliateClickTracking:
    """Test affiliate click tracking for all platforms"""

    def test_track_booking_click(self):
        """POST /api/affiliate-click tracks booking clicks"""
        response = requests.post(f"{BASE_URL}/api/affiliate-click", json={"platform": "booking"})
        assert response.status_code == 200

    def test_track_skyscanner_click(self):
        """POST /api/affiliate-click tracks skyscanner clicks"""
        response = requests.post(f"{BASE_URL}/api/affiliate-click", json={"platform": "skyscanner"})
        assert response.status_code == 200

    def test_track_getyourguide_click(self):
        """POST /api/affiliate-click tracks getyourguide clicks"""
        response = requests.post(f"{BASE_URL}/api/affiliate-click", json={"platform": "getyourguide"})
        assert response.status_code == 200

    def test_track_airalo_click(self):
        """POST /api/affiliate-click tracks airalo (eSIM) clicks"""
        response = requests.post(f"{BASE_URL}/api/affiliate-click", json={"platform": "airalo"})
        assert response.status_code == 200

    def test_track_insurance_click(self):
        """POST /api/affiliate-click tracks insurance clicks"""
        response = requests.post(f"{BASE_URL}/api/affiliate-click", json={"platform": "insurance"})
        assert response.status_code == 200


class TestTravelPlannerRoute:
    """Test travel planner route accessibility"""

    def test_travel_planner_page_accessible(self):
        """GET /travel-planner should return 200"""
        response = requests.get(f"{BASE_URL}/travel-planner", timeout=10)
        assert response.status_code == 200
    
    def test_travel_planner_with_destination_param(self):
        """GET /travel-planner?destination=Paris should return 200"""
        response = requests.get(f"{BASE_URL}/travel-planner?destination=Paris", timeout=10)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
