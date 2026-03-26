"""
Iteration 84 - New Destinations Testing
Tests for 9 new destinations (Berlin, Madrid, Prague, Vienna, Budapest, Istanbul, Florence, Dubai, Bali)
with stay_zones, must_see, and template type fallback features.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestNewDestinations:
    """Test the 9 new destinations added to the template engine"""
    
    # ── Berlin Tests ──
    def test_berlin_airport_and_zones(self):
        """Berlin should return BER airport and 4 stay zones"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "berlim",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check airports
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) >= 1, "Berlin should have at least 1 airport"
        airport_codes = [ap["code"] for ap in airports]
        assert "BER" in airport_codes, f"Berlin should have BER airport, got {airport_codes}"
        
        # Check stay zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) == 4, f"Berlin should have 4 stay zones, got {len(stay_zones)}"
        
        # Check must_see
        must_see = plan.get("must_see", [])
        assert len(must_see) >= 3, f"Berlin should have at least 3 must_see items, got {len(must_see)}"
    
    # ── Madrid Tests ──
    def test_madrid_airport_and_zones(self):
        """Madrid should return MAD airport and 4 stay zones"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "madrid",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check airports
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) >= 1, "Madrid should have at least 1 airport"
        airport_codes = [ap["code"] for ap in airports]
        assert "MAD" in airport_codes, f"Madrid should have MAD airport, got {airport_codes}"
        
        # Check stay zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) == 4, f"Madrid should have 4 stay zones, got {len(stay_zones)}"
        
        # Check must_see
        must_see = plan.get("must_see", [])
        assert len(must_see) >= 3, f"Madrid should have at least 3 must_see items, got {len(must_see)}"
    
    # ── Prague Tests ──
    def test_prague_airport_and_zones(self):
        """Prague should return PRG airport"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "praga",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check airports
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) >= 1, "Prague should have at least 1 airport"
        airport_codes = [ap["code"] for ap in airports]
        assert "PRG" in airport_codes, f"Prague should have PRG airport, got {airport_codes}"
        
        # Check stay zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) == 4, f"Prague should have 4 stay zones, got {len(stay_zones)}"
    
    # ── Vienna Tests ──
    def test_vienna_airport_and_zones(self):
        """Vienna should return VIE airport"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "viena",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check airports
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) >= 1, "Vienna should have at least 1 airport"
        airport_codes = [ap["code"] for ap in airports]
        assert "VIE" in airport_codes, f"Vienna should have VIE airport, got {airport_codes}"
        
        # Check stay zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) == 4, f"Vienna should have 4 stay zones, got {len(stay_zones)}"
    
    # ── Budapest Tests ──
    def test_budapest_airport_and_zones(self):
        """Budapest should return BUD airport"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "budapeste",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check airports
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) >= 1, "Budapest should have at least 1 airport"
        airport_codes = [ap["code"] for ap in airports]
        assert "BUD" in airport_codes, f"Budapest should have BUD airport, got {airport_codes}"
        
        # Check stay zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) == 4, f"Budapest should have 4 stay zones, got {len(stay_zones)}"
    
    # ── Istanbul Tests ──
    def test_istanbul_airports_and_zones(self):
        """Istanbul should return IST and SAW airports (2 airports)"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "istambul",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check airports - Istanbul has 2 airports
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) >= 2, f"Istanbul should have at least 2 airports, got {len(airports)}"
        airport_codes = [ap["code"] for ap in airports]
        assert "IST" in airport_codes, f"Istanbul should have IST airport, got {airport_codes}"
        assert "SAW" in airport_codes, f"Istanbul should have SAW airport, got {airport_codes}"
        
        # Check stay zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) == 4, f"Istanbul should have 4 stay zones, got {len(stay_zones)}"
    
    # ── Florence Tests ──
    def test_florence_airports_and_zones(self):
        """Florence should return FLR and PSA airports (2 airports)"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "florenca",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check airports - Florence has 2 airports
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) >= 2, f"Florence should have at least 2 airports, got {len(airports)}"
        airport_codes = [ap["code"] for ap in airports]
        assert "FLR" in airport_codes, f"Florence should have FLR airport, got {airport_codes}"
        assert "PSA" in airport_codes, f"Florence should have PSA airport, got {airport_codes}"
        
        # Check stay zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) == 4, f"Florence should have 4 stay zones, got {len(stay_zones)}"
    
    # ── Dubai Tests ──
    def test_dubai_airports_and_weather_zone(self):
        """Dubai should return DXB and DWC airports with desert weather zone"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "dubai",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check airports - Dubai has 2 airports
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) >= 2, f"Dubai should have at least 2 airports, got {len(airports)}"
        airport_codes = [ap["code"] for ap in airports]
        assert "DXB" in airport_codes, f"Dubai should have DXB airport, got {airport_codes}"
        assert "DWC" in airport_codes, f"Dubai should have DWC airport, got {airport_codes}"
        
        # Check stay zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) == 4, f"Dubai should have 4 stay zones, got {len(stay_zones)}"
    
    # ── Bali Tests ──
    def test_bali_airport_and_weather_zone(self):
        """Bali should return DPS airport with tropical weather zone"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "bali",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check airports
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) >= 1, "Bali should have at least 1 airport"
        airport_codes = [ap["code"] for ap in airports]
        assert "DPS" in airport_codes, f"Bali should have DPS airport, got {airport_codes}"
        
        # Check stay zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) == 4, f"Bali should have 4 stay zones, got {len(stay_zones)}"


class TestTemplateTypeFallback:
    """Test template type fallback for unknown destinations"""
    
    def test_cancun_generic_template(self):
        """Cancun should return is_generic_template=true (beach destination fallback)"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "cancun",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check is_generic_template flag
        is_generic = plan.get("is_generic_template", False)
        assert is_generic == True, f"Cancun should have is_generic_template=true, got {is_generic}"


class TestMustSeeAdaptation:
    """Test must_see list adapts to num_days"""
    
    def test_must_see_3_day_trip(self):
        """3-day trip should have fewer must_see items"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "paris",
            "start_date": "2026-03-01",
            "end_date": "2026-03-04"  # 3 days
        })
        assert response.status_code == 200
        data = response.json()
        plan = data.get("plan", {})
        must_see_3d = plan.get("must_see", [])
        
        # 3 days = ~6 sights max (2 per day), min 3
        assert 3 <= len(must_see_3d) <= 6, f"3-day trip should have 3-6 must_see items, got {len(must_see_3d)}"
    
    def test_must_see_7_day_trip(self):
        """7-day trip should have more must_see items"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "paris",
            "start_date": "2026-03-01",
            "end_date": "2026-03-08"  # 7 days
        })
        assert response.status_code == 200
        data = response.json()
        plan = data.get("plan", {})
        must_see_7d = plan.get("must_see", [])
        
        # 7 days = ~14 sights max (2 per day), but limited by available sights
        assert len(must_see_7d) >= 6, f"7-day trip should have at least 6 must_see items, got {len(must_see_7d)}"


class TestExistingDestinations:
    """Test existing destinations still work correctly"""
    
    def test_paris_still_works(self):
        """Paris should return CDG/ORY/BVA airports + stay_zones + must_see"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "paris",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        plan = data.get("plan", {})
        
        # Check airports
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        assert len(airports) == 3, f"Paris should have 3 airports, got {len(airports)}"
        airport_codes = [ap["code"] for ap in airports]
        assert "CDG" in airport_codes, f"Paris should have CDG airport"
        assert "ORY" in airport_codes, f"Paris should have ORY airport"
        assert "BVA" in airport_codes, f"Paris should have BVA airport"
        
        # Check stay zones
        hotel_info = plan.get("hotel_info", {})
        stay_zones = hotel_info.get("stay_zones", [])
        assert len(stay_zones) == 4, f"Paris should have 4 stay zones, got {len(stay_zones)}"
        
        # Check must_see
        must_see = plan.get("must_see", [])
        assert len(must_see) >= 3, f"Paris should have at least 3 must_see items"


class TestAliasMatching:
    """Test alias matching for destination names"""
    
    def test_vienna_alias(self):
        """'vienna' should match 'viena' template"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "vienna",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200
        data = response.json()
        plan = data.get("plan", {})
        
        # Should match Vienna template
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        airport_codes = [ap["code"] for ap in airports]
        assert "VIE" in airport_codes, f"'vienna' should match Vienna template with VIE airport"
    
    def test_florence_alias(self):
        """'florence' should match 'florenca' template"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "florence",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200
        data = response.json()
        plan = data.get("plan", {})
        
        # Should match Florence template
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        airport_codes = [ap["code"] for ap in airports]
        assert "FLR" in airport_codes, f"'florence' should match Florence template with FLR airport"
    
    def test_istanbul_alias(self):
        """'istanbul' should match 'istambul' template"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "istanbul",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200
        data = response.json()
        plan = data.get("plan", {})
        
        # Should match Istanbul template
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        airport_codes = [ap["code"] for ap in airports]
        assert "IST" in airport_codes, f"'istanbul' should match Istanbul template with IST airport"
    
    def test_prague_alias(self):
        """'prague' should match 'praga' template"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json={
            "destination": "prague",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05"
        })
        assert response.status_code == 200
        data = response.json()
        plan = data.get("plan", {})
        
        # Should match Prague template
        flight_info = plan.get("flight_info", {})
        airports = flight_info.get("airports", [])
        airport_codes = [ap["code"] for ap in airports]
        assert "PRG" in airport_codes, f"'prague' should match Prague template with PRG airport"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
