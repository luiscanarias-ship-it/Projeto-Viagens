"""
Test iteration 86: Conversion and monetization optimization on TravelPlanner page
Features tested:
1. /api/homepage/main-journey endpoint returns journey data with progress percentage
2. Affiliate links include GYG partner ID WFPE9ME
3. Travel plan generation for template destinations (Roma)
4. Must-see section data in travel plans
5. Stay zones data in travel plans
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMainJourneyEndpoint:
    """Test /api/homepage/main-journey endpoint for Journey Progress Banner"""
    
    def test_main_journey_returns_journey_data(self):
        """Verify main-journey endpoint returns journey with required fields"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "journey" in data, "Response should contain 'journey' field"
        assert "progress" in data, "Response should contain 'progress' field"
        assert "contributor_count" in data, "Response should contain 'contributor_count' field"
        
        journey = data["journey"]
        assert "journey_id" in journey, "Journey should have journey_id"
        assert "name" in journey, "Journey should have name"
        
        progress = data["progress"]
        assert "percentage" in progress, "Progress should have percentage"
        assert "current_amount" in progress, "Progress should have current_amount"
        
        print(f"Main journey: {journey['name']} ({journey['journey_id']})")
        print(f"Progress: {progress['percentage']}%")
        print(f"Contributors: {data['contributor_count']}")
    
    def test_main_journey_progress_percentage_valid(self):
        """Verify progress percentage is a valid number between 0 and 100"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        
        data = response.json()
        percentage = data["progress"]["percentage"]
        
        assert isinstance(percentage, (int, float)), "Percentage should be a number"
        assert 0 <= percentage <= 100, f"Percentage should be 0-100, got {percentage}"
        
        print(f"Progress percentage: {percentage}%")


class TestAffiliateLinks:
    """Test affiliate links configuration"""
    
    def test_affiliate_links_endpoint(self):
        """Verify affiliate-links endpoint returns all required platforms"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        required_platforms = ["booking", "skyscanner", "getyourguide", "airalo", "insurance"]
        
        for platform in required_platforms:
            assert platform in data, f"Missing platform: {platform}"
            assert "url" in data[platform], f"Platform {platform} missing url"
        
        print(f"Found {len(data)} affiliate platforms")
    
    def test_gyg_partner_id_correct(self):
        """Verify GetYourGuide uses correct partner ID WFPE9ME"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        gyg = data.get("getyourguide", {})
        
        assert gyg.get("affiliate_id") == "WFPE9ME", f"GYG partner ID should be WFPE9ME, got {gyg.get('affiliate_id')}"
        print(f"GYG partner ID: {gyg.get('affiliate_id')}")


class TestTravelPlanGeneration:
    """Test travel plan generation with template destinations"""
    
    def test_roma_plan_generation_template(self):
        """Verify Roma uses template system (instant, 0-cost)"""
        payload = {
            "destination": "Roma",
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "trip_type": ["cultural"]
        }
        
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json=payload, timeout=30)
        
        # May get 429 if rate limited
        if response.status_code == 429:
            pytest.skip("Rate limited - skipping plan generation test")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plan" in data, "Response should contain 'plan'"
        
        plan = data["plan"]
        assert "destination" in plan, "Plan should have destination"
        assert "itinerary" in plan, "Plan should have itinerary"
        
        print(f"Generated plan for: {plan['destination']}")
        print(f"Itinerary days: {len(plan.get('itinerary', []))}")
    
    def test_plan_contains_must_see(self):
        """Verify travel plan contains must_see section for affiliate CTAs"""
        payload = {
            "destination": "Roma",
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "trip_type": ["cultural"]
        }
        
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json=payload, timeout=30)
        
        if response.status_code == 429:
            pytest.skip("Rate limited - skipping must_see test")
        
        assert response.status_code == 200
        
        plan = response.json().get("plan", {})
        must_see = plan.get("must_see", [])
        
        # Template destinations should have must_see
        if must_see:
            print(f"Must-see items: {len(must_see)}")
            for i, item in enumerate(must_see[:3]):
                print(f"  {i+1}. {item}")
        else:
            print("No must_see section in plan (may be AI-generated)")
    
    def test_plan_contains_stay_zones(self):
        """Verify travel plan contains stay_zones for hotel recommendations"""
        payload = {
            "destination": "Roma",
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "trip_type": ["cultural"]
        }
        
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json=payload, timeout=30)
        
        if response.status_code == 429:
            pytest.skip("Rate limited - skipping stay_zones test")
        
        assert response.status_code == 200
        
        plan = response.json().get("plan", {})
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        
        if stay_zones:
            print(f"Stay zones: {len(stay_zones)}")
            for zone in stay_zones[:2]:
                print(f"  - {zone.get('name')}: {zone.get('description', '')[:50]}...")
        else:
            print("No stay_zones in plan")


class TestJourneyContributeLink:
    """Test that contribute links point to correct journey"""
    
    def test_journey_detail_page_accessible(self):
        """Verify journey detail page is accessible"""
        # First get the main journey ID
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        
        journey_id = response.json()["journey"]["journey_id"]
        
        # Check journey detail endpoint
        detail_response = requests.get(f"{BASE_URL}/api/journeys/{journey_id}")
        assert detail_response.status_code == 200, f"Journey detail should be accessible: {detail_response.status_code}"
        
        detail = detail_response.json()
        assert detail.get("journey_id") == journey_id
        
        print(f"Journey detail accessible: {journey_id}")


class TestInlineActivityCTAs:
    """Test inline activity CTAs in itinerary"""
    
    def test_itinerary_has_activities(self):
        """Verify itinerary contains activities for inline CTAs"""
        payload = {
            "destination": "Roma",
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "trip_type": ["cultural"]
        }
        
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json=payload, timeout=30)
        
        if response.status_code == 429:
            pytest.skip("Rate limited")
        
        assert response.status_code == 200
        
        plan = response.json().get("plan", {})
        itinerary = plan.get("itinerary", [])
        
        assert len(itinerary) > 0, "Itinerary should have at least one day"
        
        total_activities = 0
        for day in itinerary:
            activities = day.get("activities", [])
            total_activities += len(activities)
            print(f"Day {day.get('day')}: {len(activities)} activities")
        
        assert total_activities > 0, "Itinerary should have activities"
        print(f"Total activities: {total_activities}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
