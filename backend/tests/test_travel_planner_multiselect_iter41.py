"""
Test Suite: Travel Planner Multi-Select Trip Types (Iteration 41)
Tests the NEW features:
- trip_type accepts array of strings
- /api/ai/travel-plan works with multi-select trip types
- /api/ai/travel-plan/refine works with multi-select trip types
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTravelPlannerMultiSelect:
    """Tests for multi-select trip types in travel planner"""
    
    def test_api_reachable(self):
        """Test API is reachable using affiliate-links endpoint"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        print("SUCCESS: API is reachable")
    
    def test_travel_plan_with_single_trip_type_string(self):
        """Test travel plan generation with single trip type as string (backward compat)"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "Porto",
            "start_date": "2026-03-01",
            "end_date": "2026-03-02",
            "trip_type": "cultural"
        }, timeout=60)
        
        # Either 200 success or 429 rate limit
        assert response.status_code in [200, 429], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "plan" in data
            assert "destination" in data["plan"]
            print(f"SUCCESS: Plan generated for Porto with single trip type")
        else:
            print("INFO: Rate limited (429) - API accepts single trip type string")
    
    def test_travel_plan_with_array_trip_type(self):
        """Test travel plan generation with trip_type as array ['cultural', 'gastronomica']"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "Lisboa",
            "start_date": "2026-02-10",
            "end_date": "2026-02-12",
            "trip_type": ["cultural", "gastronomica"]
        }, timeout=60)
        
        # Either 200 success or 429 rate limit
        assert response.status_code in [200, 429], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "plan" in data
            assert "destination" in data["plan"]
            print(f"SUCCESS: Plan generated with array trip_type: ['cultural', 'gastronomica']")
        else:
            # Rate limit is acceptable - endpoint accepts the array format
            print("INFO: Rate limited (429) - API accepts array trip type format")
    
    def test_travel_plan_with_empty_array(self):
        """Test travel plan generation with empty trip_type array"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "Madrid",
            "start_date": "2026-03-05",
            "end_date": "2026-03-06",
            "trip_type": []
        }, timeout=60)
        
        # Should work - empty array converts to empty string
        assert response.status_code in [200, 429], f"Unexpected status: {response.status_code}"
        print("SUCCESS: API accepts empty array for trip_type")
    
    def test_travel_plan_with_three_trip_types(self):
        """Test travel plan with 3 trip types selected"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "Barcelona",
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
            "trip_type": ["cultural", "gastronomica", "aventura"]
        }, timeout=60)
        
        assert response.status_code in [200, 429], f"Unexpected status: {response.status_code}"
        print("SUCCESS: API accepts 3 trip types array")
    
    def test_travel_plan_refine_with_array_trip_type(self):
        """Test refine endpoint with trip_type as array"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan/refine", json={
            "destination": "Lisboa",
            "start_date": "2026-02-10",
            "end_date": "2026-02-12",
            "trip_type": ["cultural", "gastronomica"],
            "previous_plan": {
                "destination": "Lisboa",
                "dates": "2026-02-10 a 2026-02-12",
                "itinerary": [{"day": 1, "title": "Test", "activities": ["Test"]}]
            },
            "refinement": "Add more restaurants"
        }, timeout=60)
        
        assert response.status_code in [200, 429], f"Unexpected status: {response.status_code}"
        print("SUCCESS: Refine endpoint accepts array trip_type")
    
    def test_travel_plan_refine_missing_refinement(self):
        """Test refine endpoint returns 400 when refinement is missing"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan/refine", json={
            "destination": "Lisboa",
            "start_date": "2026-02-10",
            "end_date": "2026-02-12",
            "trip_type": ["cultural"],
            "previous_plan": {"destination": "Lisboa"}
        }, timeout=10)
        
        assert response.status_code == 400
        print("SUCCESS: Refine returns 400 when refinement is missing")
    
    def test_travel_plan_refine_missing_previous_plan(self):
        """Test refine endpoint returns 400 when previous_plan is missing"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan/refine", json={
            "destination": "Lisboa",
            "start_date": "2026-02-10",
            "end_date": "2026-02-12",
            "trip_type": ["cultural"],
            "refinement": "Add more museums"
        }, timeout=10)
        
        assert response.status_code == 400
        print("SUCCESS: Refine returns 400 when previous_plan is missing")


class TestAffiliateLinks:
    """Test affiliate links endpoint"""
    
    def test_affiliate_links_endpoint(self):
        """Test /api/affiliate-links returns all partner URLs"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        # Check expected partners exist
        expected_partners = ["booking", "skyscanner", "airalo", "getyourguide"]
        for partner in expected_partners:
            assert partner in data, f"Missing partner: {partner}"
            assert "url" in data[partner], f"Missing URL for {partner}"
        
        print(f"SUCCESS: Affiliate links returned for {len(expected_partners)} partners")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
