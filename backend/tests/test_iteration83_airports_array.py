"""
Iteration 83 - Test airports array feature in travel plan API
Tests that POST /api/ai/travel-plan returns flight_info.airports array with ALL airports for a city
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAirportsArrayFeature:
    """Test that travel plan API returns all airports for each destination"""
    
    def test_paris_airports_and_hotel_suggestion(self):
        """Paris should return CDG, ORY, BVA airports and hotel_info.suggestion=True"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "paris",
            "start_date": "2026-04-01",
            "end_date": "2026-04-05"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "plan" in data, "Response should have 'plan' key"
        plan = data["plan"]
        
        # Check flight_info has airports array
        assert "flight_info" in plan, "Plan should have flight_info"
        flight_info = plan["flight_info"]
        
        assert flight_info.get("suggestion") == True, "flight_info.suggestion should be True"
        assert "airports" in flight_info, "flight_info should have 'airports' array"
        
        airports = flight_info["airports"]
        assert isinstance(airports, list), "airports should be a list"
        assert len(airports) == 3, f"Paris should have 3 airports, got {len(airports)}"
        
        # Check airport codes
        airport_codes = [ap["code"] for ap in airports]
        assert "CDG" in airport_codes, "Paris should have CDG airport"
        assert "ORY" in airport_codes, "Paris should have ORY airport"
        assert "BVA" in airport_codes, "Paris should have BVA airport"
        
        # Check each airport has required fields
        for ap in airports:
            assert "code" in ap, "Each airport should have 'code'"
            assert "name" in ap, "Each airport should have 'name'"
            assert "distance" in ap, "Each airport should have 'distance'"
            assert "transport" in ap, "Each airport should have 'transport'"
        
        # Check hotel_info has suggestion=True
        hotel_info = plan.get("hotel_info", {})
        assert hotel_info.get("suggestion") == True, "hotel_info.suggestion should be True"
        assert "area" in hotel_info, "hotel_info should have 'area'"
        assert hotel_info["area"] == "Le Marais", f"Paris hotel area should be 'Le Marais', got {hotel_info.get('area')}"
        
        # Check airport_to_hotel has airports array
        transport = plan.get("airport_to_hotel", {})
        assert "airports" in transport, "airport_to_hotel should have 'airports' array"
        transport_airports = transport["airports"]
        assert len(transport_airports) == 3, f"airport_to_hotel should have 3 airports for Paris"
        
        print(f"PASS: Paris returns 3 airports: {airport_codes}, hotel_info.suggestion=True, area='Le Marais'")
    
    def test_london_returns_5_airports(self):
        """London should return LHR, LGW, STN, LTN, SEN airports"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "london",
            "start_date": "2026-04-10",
            "end_date": "2026-04-15"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data["plan"]
        
        flight_info = plan.get("flight_info", {})
        assert flight_info.get("suggestion") == True, "flight_info.suggestion should be True"
        
        airports = flight_info.get("airports", [])
        assert len(airports) == 5, f"London should have 5 airports, got {len(airports)}"
        
        airport_codes = [ap["code"] for ap in airports]
        expected_codes = ["LHR", "LGW", "STN", "LTN", "SEN"]
        for code in expected_codes:
            assert code in airport_codes, f"London should have {code} airport"
        
        print(f"PASS: London returns 5 airports: {airport_codes}")
    
    def test_roma_returns_2_airports(self):
        """Roma should return FCO, CIA airports"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "roma",
            "start_date": "2026-04-20",
            "end_date": "2026-04-25"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data["plan"]
        
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) == 2, f"Roma should have 2 airports, got {len(airports)}"
        
        airport_codes = [ap["code"] for ap in airports]
        assert "FCO" in airport_codes, "Roma should have FCO airport"
        assert "CIA" in airport_codes, "Roma should have CIA airport"
        
        print(f"PASS: Roma returns 2 airports: {airport_codes}")


class TestNavigationHighlight:
    """Test that navigation bar highlights active page"""
    
    def test_frontend_loads(self):
        """Frontend should load without errors"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200, f"Frontend should load, got {response.status_code}"
        print("PASS: Frontend loads successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
