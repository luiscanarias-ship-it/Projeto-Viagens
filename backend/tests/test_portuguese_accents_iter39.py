"""
Tests for Portuguese text validation, AI Planner integration, and section ordering.
Iteration 39 - Focus on Portuguese accents and UX improvements.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test backend API endpoints first
class TestAffiliateEndpoints:
    """Test affiliate-links and affiliate-click endpoints"""
    
    def test_get_affiliate_links_returns_all_partners(self):
        """GET /api/affiliate-links should return all required partners"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        required_partners = ['booking', 'skyscanner', 'getyourguide', 'airalo', 'hotels', 'cars', 'holafly', 'insurance', 'googlemaps']
        
        for partner in required_partners:
            assert partner in data, f"Missing partner: {partner}"
            assert 'url' in data[partner], f"Partner {partner} missing 'url'"
            assert 'name' in data[partner], f"Partner {partner} missing 'name'"
        
        print(f"✓ All {len(required_partners)} affiliate partners present with URLs and names")
    
    def test_affiliate_click_tracks_booking(self):
        """POST /api/affiliate-click tracks clicks for booking platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "booking"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "tracked", f"Expected status=tracked, got {data}"
        print("✓ Affiliate click tracked for booking")
    
    def test_affiliate_click_tracks_skyscanner(self):
        """POST /api/affiliate-click tracks clicks for skyscanner platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "skyscanner"}
        )
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("✓ Affiliate click tracked for skyscanner")
    
    def test_affiliate_click_rejects_invalid_platform(self):
        """POST /api/affiliate-click rejects invalid platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "invalid_platform_xyz"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid platform rejected with 400")


class TestAITravelPlanEndpoint:
    """Test AI travel plan endpoint validation"""
    
    def test_travel_plan_rejects_missing_fields(self):
        """POST /api/ai/travel-plan rejects missing required fields"""
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan",
            json={"destination": "Lisboa"}  # Missing dates
        )
        # Should return 422 (validation error) or 400
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
        print("✓ Missing fields rejected correctly")
    
    def test_travel_plan_rejects_empty_destination(self):
        """POST /api/ai/travel-plan rejects empty destination"""
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan",
            json={
                "destination": "",
                "start_date": "2026-04-01",
                "end_date": "2026-04-05"
            }
        )
        # Should return 400 or 422
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
        print("✓ Empty destination rejected correctly")


class TestHealthEndpoint:
    """Basic health check"""
    
    def test_health_endpoint(self):
        """GET / or /api should return some response"""
        response = requests.get(f"{BASE_URL}/api/journeys")
        # Just checking the API is responsive
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print("✓ API is responsive")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
