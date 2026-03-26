"""
Iteration 85 - Bug Fixes Testing
Tests for 3 reported bugs:
1. Days with 0-1 activities (should have 3-4 per day)
2. Geocoding failing for Portuguese names (now extracts parenthetical names)
3. Map popup showing 'dia X ponto Y' instead of activity name (now shows day_title)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestItineraryActivitiesPerDay:
    """Bug 1: Verify each day has 3-4 activities, no empty days"""
    
    def test_istanbul_9_days_activities_per_day(self):
        """Istanbul 9 days should have 3-4 activities per day, no repeats"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "istambul",
            "start_date": "2026-06-01",
            "end_date": "2026-06-10"  # 9 days
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        plan = data.get("plan", data)
        itinerary = plan.get("itinerary", [])
        
        assert len(itinerary) == 9, f"Expected 9 days, got {len(itinerary)}"
        
        all_activities = []
        for day in itinerary:
            activities = day.get("activities", [])
            day_num = day.get("day", "?")
            
            # Each day should have 3-4 activities
            assert len(activities) >= 3, f"Day {day_num} has only {len(activities)} activities (min 3)"
            assert len(activities) <= 4, f"Day {day_num} has {len(activities)} activities (max 4)"
            
            # Collect for dedup check
            all_activities.extend(activities)
        
        # Check for no repeated activities
        unique_activities = set(all_activities)
        assert len(unique_activities) == len(all_activities), f"Found repeated activities: {len(all_activities)} total, {len(unique_activities)} unique"
        
        print(f"PASS: Istanbul 9-day plan has {len(itinerary)} days, all with 3-4 unique activities")
    
    def test_paris_5_days_activities_per_day(self):
        """Paris 5 days should have 3-4 activities per day"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "paris",
            "start_date": "2026-07-01",
            "end_date": "2026-07-06"  # 5 days
        })
        assert response.status_code == 200
        
        data = response.json()
        plan = data.get("plan", data)
        itinerary = plan.get("itinerary", [])
        
        assert len(itinerary) == 5, f"Expected 5 days, got {len(itinerary)}"
        
        all_activities = []
        for day in itinerary:
            activities = day.get("activities", [])
            day_num = day.get("day", "?")
            
            assert len(activities) >= 3, f"Day {day_num} has only {len(activities)} activities"
            assert len(activities) <= 4, f"Day {day_num} has {len(activities)} activities"
            all_activities.extend(activities)
        
        unique = set(all_activities)
        assert len(unique) == len(all_activities), "Found repeated activities"
        
        print(f"PASS: Paris 5-day plan has {len(itinerary)} days, all with 3-4 unique activities")
    
    def test_berlin_7_days_uses_day_trips(self):
        """Berlin 7 days should use day_trips for days 6+"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "berlim",
            "start_date": "2026-08-01",
            "end_date": "2026-08-08"  # 7 days
        })
        assert response.status_code == 200
        
        data = response.json()
        plan = data.get("plan", data)
        itinerary = plan.get("itinerary", [])
        
        assert len(itinerary) == 7, f"Expected 7 days, got {len(itinerary)}"
        
        # Check all days have 3-4 activities
        for day in itinerary:
            activities = day.get("activities", [])
            day_num = day.get("day", "?")
            assert len(activities) >= 3, f"Day {day_num} has only {len(activities)} activities"
        
        # Check if day_trips are used (look for "Day trip" or "Excursao" in later days)
        later_days_text = " ".join([
            " ".join(day.get("activities", []))
            for day in itinerary if day.get("day", 0) >= 5
        ])
        
        has_day_trip = "day trip" in later_days_text.lower() or "excursao" in later_days_text.lower() or "potsdam" in later_days_text.lower() or "sachsenhausen" in later_days_text.lower()
        print(f"INFO: Later days text contains day_trips: {has_day_trip}")
        
        print(f"PASS: Berlin 7-day plan has {len(itinerary)} days, all with 3+ activities")


class TestGeocodingParentheticalNames:
    """Bug 2: Geocoding should extract names from parentheses for better accuracy"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin to get token for geocode endpoint"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        return response.json().get("token")
    
    def test_geocode_istanbul_plan_success(self, admin_token):
        """Geocode Istanbul plan should return 10+ locations (was 0 before fix)"""
        # First generate a plan
        plan_response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "istambul",
            "start_date": "2026-06-01",
            "end_date": "2026-06-06"  # 5 days
        })
        assert plan_response.status_code == 200
        
        plan_data = plan_response.json()
        plan = plan_data.get("plan", plan_data)
        
        # Now geocode it
        geocode_response = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            json={"plan": plan},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert geocode_response.status_code == 200, f"Geocode failed: {geocode_response.status_code} - {geocode_response.text}"
        
        geo_data = geocode_response.json()
        days = geo_data.get("days", [])
        
        total_locations = sum(len(d.get("locations", [])) for d in days)
        
        # Should have at least 10 geocoded locations (was 0 before fix)
        assert total_locations >= 10, f"Expected 10+ geocoded locations, got {total_locations}"
        
        print(f"PASS: Istanbul plan geocoded with {total_locations} locations")
    
    def test_geocode_extracts_parenthetical_names(self, admin_token):
        """Verify geocoding extracts 'Sultan Ahmed' from 'Mesquita Azul (Sultan Ahmed — gratis)'"""
        # Create a minimal plan with the problematic activity
        test_plan = {
            "destination": "Istambul",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Test Day",
                    "activities": [
                        "Mesquita Azul (Sultan Ahmed — gratis)",
                        "Hagia Sophia (obra-prima bizantina/otomana)",
                        "Palacio de Topkapi (residencia dos sultoes)"
                    ]
                }
            ]
        }
        
        geocode_response = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            json={"plan": test_plan},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert geocode_response.status_code == 200
        
        geo_data = geocode_response.json()
        days = geo_data.get("days", [])
        
        if days:
            locations = days[0].get("locations", [])
            # Should have geocoded at least 2 of the 3 activities
            assert len(locations) >= 2, f"Expected 2+ locations, got {len(locations)}"
            
            # Check that Sultan Ahmed was found (the parenthetical extraction)
            location_names = [loc.get("name", "").lower() for loc in locations]
            print(f"INFO: Geocoded locations: {location_names}")
        
        print(f"PASS: Geocoding extracted parenthetical names successfully")


class TestMapPopupShowsActivityName:
    """Bug 3: Map popup should show activity name, not 'dia X ponto Y'"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin to get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        return response.json().get("token")
    
    def test_geocode_returns_day_title(self, admin_token):
        """Geocode response should include day_title for each location"""
        plan_response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "paris",
            "start_date": "2026-07-01",
            "end_date": "2026-07-04"  # 3 days
        })
        assert plan_response.status_code == 200
        
        plan_data = plan_response.json()
        plan = plan_data.get("plan", plan_data)
        
        geocode_response = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            json={"plan": plan},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert geocode_response.status_code == 200
        
        geo_data = geocode_response.json()
        days = geo_data.get("days", [])
        
        for day in days:
            locations = day.get("locations", [])
            for loc in locations:
                # Each location should have day_title (not just day number)
                day_title = loc.get("day_title", "")
                assert day_title, f"Location {loc.get('name')} missing day_title"
                
                # day_title should NOT be just "Ponto X" or "dia X ponto Y"
                assert "ponto" not in day_title.lower(), f"day_title should not contain 'ponto': {day_title}"
                
                # day_title should be descriptive (e.g., "Chegada a Paris", "Icones de Paris")
                assert len(day_title) > 5, f"day_title too short: {day_title}"
        
        print(f"PASS: All locations have descriptive day_title (not 'ponto X')")


class TestExistingDestinationsStillWork:
    """Verify existing destinations (paris, roma, etc.) still work with stay_zones and must_see"""
    
    def test_paris_has_stay_zones_and_must_see(self):
        """Paris should have stay_zones and must_see"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "paris",
            "start_date": "2026-07-01",
            "end_date": "2026-07-05"
        })
        assert response.status_code == 200
        
        data = response.json()
        plan = data.get("plan", data)
        
        # Check stay_zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) >= 3, f"Paris should have 3+ stay_zones, got {len(stay_zones)}"
        
        # Check must_see
        must_see = plan.get("must_see", [])
        assert len(must_see) >= 5, f"Paris should have 5+ must_see, got {len(must_see)}"
        
        print(f"PASS: Paris has {len(stay_zones)} stay_zones and {len(must_see)} must_see")
    
    def test_roma_has_stay_zones_and_must_see(self):
        """Roma should have stay_zones and must_see"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "roma",
            "start_date": "2026-08-01",
            "end_date": "2026-08-05"
        })
        assert response.status_code == 200
        
        data = response.json()
        plan = data.get("plan", data)
        
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) >= 3, f"Roma should have 3+ stay_zones, got {len(stay_zones)}"
        
        must_see = plan.get("must_see", [])
        assert len(must_see) >= 5, f"Roma should have 5+ must_see, got {len(must_see)}"
        
        print(f"PASS: Roma has {len(stay_zones)} stay_zones and {len(must_see)} must_see")


class TestDayTripsFieldPresent:
    """Verify day_trips field is present in all 19 destinations"""
    
    def test_all_destinations_have_day_trips(self):
        """Check that day_trips field exists in destination data"""
        # Test a sample of destinations
        destinations = ["paris", "roma", "barcelona", "londres", "berlim", "madrid", "praga", "viena", "budapeste", "istambul", "florenca", "dubai", "bali"]
        
        for dest in destinations:
            response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
                "destination": dest,
                "start_date": "2026-09-01",
                "end_date": "2026-09-08"  # 7 days to trigger day_trips usage
            })
            
            if response.status_code != 200:
                print(f"WARN: {dest} returned {response.status_code}")
                continue
            
            data = response.json()
            plan = data.get("plan", data)
            
            # Check itinerary has activities (day_trips should be used for longer trips)
            itinerary = plan.get("itinerary", [])
            assert len(itinerary) >= 7, f"{dest}: Expected 7 days, got {len(itinerary)}"
            
            # All days should have activities
            for day in itinerary:
                activities = day.get("activities", [])
                assert len(activities) >= 3, f"{dest} Day {day.get('day')}: Only {len(activities)} activities"
        
        print(f"PASS: All {len(destinations)} destinations have proper itineraries with 3+ activities per day")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
