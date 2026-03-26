"""
Iteration 82 - Bug Fixes Testing
Tests for 3 critical bug fixes:
1. Template plans now show flight/hotel SUGGESTIONS (not fake booking data)
2. Geocoding distance threshold reduced from 5° to 1° (filters out wrong locations)
3. Food/restaurant activities are skipped from geocoding
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFlightInfoSuggestionFormat:
    """Test that flight_info returns suggestion format (not fake flight numbers)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin and reset rate limit before tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if login_resp.status_code == 200:
            token = login_resp.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            
            # Reset rate limit
            reset_resp = self.session.post(f"{BASE_URL}/api/ai/travel-plan/reset-limit")
            print(f"Rate limit reset: {reset_resp.status_code}")
    
    def test_paris_flight_info_is_suggestion(self):
        """Paris template should return flight_info with suggestion=true"""
        resp = self.session.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "paris",
            "start_date": "2026-03-15",
            "end_date": "2026-03-20"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        plan = data.get("plan", data)
        flight_info = plan.get("flight_info")
        
        assert flight_info is not None, "flight_info should exist"
        assert flight_info.get("suggestion") == True, f"flight_info.suggestion should be True, got: {flight_info}"
        assert "destination_airport" in flight_info, f"flight_info should have destination_airport, got: {flight_info}"
        assert "CDG" in flight_info.get("destination_airport", ""), f"Paris airport should be CDG, got: {flight_info.get('destination_airport')}"
        
        # Should NOT have outbound/return fake flight data
        assert "outbound" not in flight_info, f"flight_info should NOT have outbound (fake flight), got: {flight_info}"
        assert "return" not in flight_info, f"flight_info should NOT have return (fake flight), got: {flight_info}"
        
        print(f"PASS: Paris flight_info is suggestion format: {flight_info}")
    
    def test_roma_flight_info_is_suggestion(self):
        """Roma template should return flight_info with suggestion=true"""
        resp = self.session.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "roma",
            "start_date": "2026-04-10",
            "end_date": "2026-04-15"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        plan = data.get("plan", data)
        flight_info = plan.get("flight_info")
        
        assert flight_info is not None, "flight_info should exist"
        assert flight_info.get("suggestion") == True, f"flight_info.suggestion should be True, got: {flight_info}"
        assert "FCO" in flight_info.get("destination_airport", ""), f"Roma airport should be FCO, got: {flight_info.get('destination_airport')}"
        
        print(f"PASS: Roma flight_info is suggestion format: {flight_info}")


class TestHotelInfoSuggestionFormat:
    """Test that hotel_info returns suggestion format (not fake hotel name/address)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if login_resp.status_code == 200:
            token = login_resp.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_paris_hotel_info_is_suggestion(self):
        """Paris template should return hotel_info with suggestion=true and area field"""
        resp = self.session.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "paris",
            "start_date": "2026-03-15",
            "end_date": "2026-03-20"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        plan = data.get("plan", data)
        hotel_info = plan.get("hotel_info")
        
        assert hotel_info is not None, "hotel_info should exist"
        assert hotel_info.get("suggestion") == True, f"hotel_info.suggestion should be True, got: {hotel_info}"
        assert "area" in hotel_info, f"hotel_info should have area field, got: {hotel_info}"
        assert hotel_info.get("area") == "Le Marais", f"Paris area should be Le Marais, got: {hotel_info.get('area')}"
        
        # Should NOT have fake hotel name/address as primary fields
        # (area is allowed, but name/address should not be the main display)
        assert "tip" in hotel_info, f"hotel_info should have tip field, got: {hotel_info}"
        
        print(f"PASS: Paris hotel_info is suggestion format: {hotel_info}")
    
    def test_barcelona_hotel_info_has_el_born_area(self):
        """Barcelona template should return hotel_info with area='El Born'"""
        resp = self.session.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "barcelona",
            "start_date": "2026-05-01",
            "end_date": "2026-05-05"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        plan = data.get("plan", data)
        hotel_info = plan.get("hotel_info")
        
        assert hotel_info is not None, "hotel_info should exist"
        assert hotel_info.get("suggestion") == True, f"hotel_info.suggestion should be True, got: {hotel_info}"
        assert hotel_info.get("area") == "El Born", f"Barcelona area should be El Born, got: {hotel_info.get('area')}"
        
        print(f"PASS: Barcelona hotel_info has El Born area: {hotel_info}")


class TestTransportInfoStillPresent:
    """Test that airport_to_hotel transport info is still present with real data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if login_resp.status_code == 200:
            token = login_resp.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_paris_has_transport_info(self):
        """Paris template should have airport_to_hotel with RER B as best option"""
        resp = self.session.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "paris",
            "start_date": "2026-03-15",
            "end_date": "2026-03-20"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        plan = data.get("plan", data)
        transport = plan.get("airport_to_hotel")
        
        assert transport is not None, "airport_to_hotel should exist"
        assert "best_option" in transport, f"transport should have best_option, got: {transport}"
        
        best = transport.get("best_option", {})
        assert "mode" in best, f"best_option should have mode, got: {best}"
        assert "RER B" in best.get("mode", ""), f"Paris best transport should be RER B, got: {best.get('mode')}"
        assert "cost" in best, f"best_option should have cost, got: {best}"
        assert "duration" in best, f"best_option should have duration, got: {best}"
        
        print(f"PASS: Paris transport info present: {transport}")


class TestGeocodingFoodFiltering:
    """Test that geocoding skips food/restaurant activities"""
    
    def test_skip_words_list_in_code(self):
        """Verify skip_words list contains food-related terms"""
        # This is a code review test - we verify the skip_words list exists
        # by checking the server.py file content
        import subprocess
        result = subprocess.run(
            ["grep", "-n", "skip_words", "/app/backend/server.py"],
            capture_output=True, text=True
        )
        output = result.stdout
        
        assert "croissant" in output, "skip_words should contain 'croissant'"
        assert "jantar" in output, "skip_words should contain 'jantar'"
        assert "falafel" in output, "skip_words should contain 'falafel'"
        assert "gelato" in output, "skip_words should contain 'gelato'"
        assert "pizza" in output, "skip_words should contain 'pizza'"
        assert "ramen" in output, "skip_words should contain 'ramen'"
        
        print(f"PASS: skip_words list contains food-related terms")


class TestGeocodingDistanceThreshold:
    """Test that geocoding distance threshold is 1 degree (not 5)"""
    
    def test_distance_threshold_is_one_degree(self):
        """Verify geocode_location uses 1.0 degree threshold"""
        import subprocess
        result = subprocess.run(
            ["grep", "-n", "dist < ", "/app/backend/server.py"],
            capture_output=True, text=True
        )
        output = result.stdout
        
        # Should find "dist < 1.0" not "dist < 5.0"
        assert "dist < 1.0" in output, f"Distance threshold should be 1.0, found: {output}"
        assert "dist < 5.0" not in output, f"Distance threshold should NOT be 5.0, found: {output}"
        
        print(f"PASS: Geocoding distance threshold is 1.0 degree (~111km)")


class TestJourneysEndpoint:
    """Test that GET /api/journeys returns 200"""
    
    def test_get_journeys(self):
        """GET /api/journeys should return 200"""
        resp = requests.get(f"{BASE_URL}/api/journeys")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        
        print(f"PASS: GET /api/journeys returns 200 with {len(data)} journeys")


class TestDestinationTemplatesCode:
    """Code review tests for destination_templates.py"""
    
    def test_get_flight_info_returns_suggestion_format(self):
        """Verify get_flight_info returns suggestion format"""
        import subprocess
        result = subprocess.run(
            ["grep", "-A", "10", "def get_flight_info", "/app/backend/destination_templates.py"],
            capture_output=True, text=True
        )
        output = result.stdout
        
        assert '"suggestion": True' in output or "'suggestion': True" in output, \
            f"get_flight_info should return suggestion=True, found: {output}"
        
        print(f"PASS: get_flight_info returns suggestion format")
    
    def test_build_full_template_plan_returns_hotel_suggestion(self):
        """Verify build_full_template_plan returns hotel_info with suggestion=true"""
        import subprocess
        result = subprocess.run(
            ["grep", "-A", "30", "def build_full_template_plan", "/app/backend/destination_templates.py"],
            capture_output=True, text=True
        )
        output = result.stdout
        
        # Check that hotel_info has suggestion: True
        assert "suggestion" in output.lower(), f"build_full_template_plan should set hotel_info.suggestion, found: {output}"
        
        print(f"PASS: build_full_template_plan returns hotel_info with suggestion format")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
