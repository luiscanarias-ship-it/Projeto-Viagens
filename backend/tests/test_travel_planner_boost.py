"""
Test suite for AI Travel Planner Boost feature
Tests: travel-plan API, affiliate-links, affiliate-click tracking
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAffiliateLinks:
    """Test affiliate links endpoints - run first (no rate limiting)"""
    
    def test_get_affiliate_links(self):
        """GET /api/affiliate-links should return links for all affiliate partners"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify required affiliate partners exist
        required_partners = ['booking', 'skyscanner', 'getyourguide', 'airalo']
        for partner in required_partners:
            assert partner in data, f"Missing affiliate partner: {partner}"
            assert 'url' in data[partner], f"Missing URL for {partner}"
            assert 'name' in data[partner], f"Missing name for {partner}"
        
        print(f"Affiliate links returned: {list(data.keys())}")
        
    def test_track_affiliate_click_booking(self):
        """POST /api/affiliate-click for booking platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "booking"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "tracked", f"Expected status 'tracked', got {data}"
        print("Booking click tracked successfully")
        
    def test_track_affiliate_click_skyscanner(self):
        """POST /api/affiliate-click for skyscanner platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "skyscanner"}
        )
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("Skyscanner click tracked successfully")
        
    def test_track_affiliate_click_getyourguide(self):
        """POST /api/affiliate-click for getyourguide platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "getyourguide"}
        )
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("GetYourGuide click tracked successfully")
        
    def test_track_affiliate_click_airalo(self):
        """POST /api/affiliate-click for airalo platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "airalo"}
        )
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("Airalo click tracked successfully")
        
    def test_track_affiliate_click_invalid_platform(self):
        """POST /api/affiliate-click with invalid platform should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "invalid_platform"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid platform, got {response.status_code}"
        print("Invalid platform correctly rejected with 400")


class TestTravelPlanAPI:
    """Test AI travel plan generation endpoint"""
    
    def test_travel_plan_missing_fields(self):
        """POST /api/ai/travel-plan without required fields should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan",
            json={"destination": "Lisboa"}  # Missing dates
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("Missing fields correctly rejected with 400")
        
    def test_travel_plan_empty_destination(self):
        """POST /api/ai/travel-plan with empty destination should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan",
            json={
                "destination": "",
                "start_date": "2026-04-01",
                "end_date": "2026-04-05"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("Empty destination correctly rejected with 400")
        
    def test_travel_plan_generation(self):
        """POST /api/ai/travel-plan generates a complete plan (may be cached)"""
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan",
            json={
                "destination": "Lisboa",
                "start_date": "2026-04-01",
                "end_date": "2026-04-05",
                "trip_type": "cultural"
            },
            timeout=60  # Allow up to 60s for AI response
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plan" in data, "Response should contain 'plan' field"
        
        plan = data["plan"]
        # Verify plan structure
        assert "destination" in plan, "Plan should have destination"
        assert "dates" in plan, "Plan should have dates"
        assert "itinerary" in plan, "Plan should have itinerary"
        assert "weather" in plan, "Plan should have weather"
        assert "packing" in plan, "Plan should have packing"
        assert "local_tips" in plan, "Plan should have local_tips"
        
        # Verify itinerary structure
        assert isinstance(plan["itinerary"], list), "Itinerary should be a list"
        if len(plan["itinerary"]) > 0:
            day = plan["itinerary"][0]
            assert "day" in day, "Itinerary day should have 'day' number"
            assert "title" in day, "Itinerary day should have 'title'"
            assert "activities" in day, "Itinerary day should have 'activities'"
        
        # Verify packing structure
        assert "clothing" in plan["packing"], "Packing should have clothing"
        assert "essentials" in plan["packing"], "Packing should have essentials"
        
        print(f"Plan generated successfully for {plan['destination']}")
        print(f"Cached: {data.get('cached', False)}")
        print(f"Itinerary days: {len(plan['itinerary'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
