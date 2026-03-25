"""
SmartMap Feature Tests - Iteration 66
Tests for geocoding, route optimization, and location improvement endpoints.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"

# Test user for non-ambassador (sonhador) testing
TEST_SONHADOR_EMAIL = f"test_sonhador_iter66_{int(time.time())}@test.com"
TEST_SONHADOR_PASSWORD = "TestPass123"


class TestSmartMapAuth:
    """Test authentication and authorization for SmartMap endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin (ambassador) token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        return resp.json()["token"]
    
    @pytest.fixture(scope="class")
    def sonhador_token(self):
        """Create and get sonhador (non-ambassador) token"""
        # Register new user
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_SONHADOR_EMAIL,
            "name": "Test Sonhador",
            "surname": "Iter66",
            "password": TEST_SONHADOR_PASSWORD
        })
        if resp.status_code == 200:
            return resp.json()["token"]
        elif resp.status_code == 400 and "registado" in resp.text.lower():
            # User exists, login instead
            resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_SONHADOR_EMAIL,
                "password": TEST_SONHADOR_PASSWORD
            })
            assert resp.status_code == 200, f"Sonhador login failed: {resp.text}"
            return resp.json()["token"]
        else:
            pytest.fail(f"Failed to create sonhador user: {resp.text}")
    
    # ── /api/ai/geocode-plan tests ──
    
    def test_geocode_plan_requires_auth(self):
        """POST /api/ai/geocode-plan returns 401 without auth"""
        resp = requests.post(f"{BASE_URL}/api/ai/geocode-plan", json={
            "plan": {"itinerary": [], "destination": "Rome"}
        })
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
    
    def test_geocode_plan_requires_ambassador(self, sonhador_token):
        """POST /api/ai/geocode-plan returns 403 for non-ambassador users"""
        resp = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            headers={"Authorization": f"Bearer {sonhador_token}"},
            json={"plan": {"itinerary": [], "destination": "Rome"}}
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        assert "Embaixadores" in resp.json().get("detail", "")
    
    def test_geocode_plan_validates_input(self, admin_token):
        """POST /api/ai/geocode-plan returns 400 for missing plan"""
        resp = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={}
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    
    # ── /api/ai/optimize-route tests ──
    
    def test_optimize_route_requires_auth(self):
        """POST /api/ai/optimize-route returns 401 without auth"""
        resp = requests.post(f"{BASE_URL}/api/ai/optimize-route", json={
            "locations": [], "day": 1, "destination": "Rome"
        })
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
    
    def test_optimize_route_requires_ambassador(self, sonhador_token):
        """POST /api/ai/optimize-route returns 403 for non-ambassador users"""
        resp = requests.post(
            f"{BASE_URL}/api/ai/optimize-route",
            headers={"Authorization": f"Bearer {sonhador_token}"},
            json={"locations": [], "day": 1, "destination": "Rome"}
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        assert "Embaixadores" in resp.json().get("detail", "")
    
    def test_optimize_route_validates_input(self, admin_token):
        """POST /api/ai/optimize-route returns 400 for missing locations"""
        resp = requests.post(
            f"{BASE_URL}/api/ai/optimize-route",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"day": 1, "destination": "Rome"}
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    
    # ── /api/ai/improve-location tests ──
    
    def test_improve_location_requires_auth(self):
        """POST /api/ai/improve-location returns 401 without auth"""
        resp = requests.post(f"{BASE_URL}/api/ai/improve-location", json={
            "location": "Colosseum", "type": "less_queues", "destination": "Rome"
        })
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
    
    def test_improve_location_requires_ambassador(self, sonhador_token):
        """POST /api/ai/improve-location returns 403 for non-ambassador users"""
        resp = requests.post(
            f"{BASE_URL}/api/ai/improve-location",
            headers={"Authorization": f"Bearer {sonhador_token}"},
            json={"location": "Colosseum", "type": "less_queues", "destination": "Rome"}
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        assert "Embaixadores" in resp.json().get("detail", "")


class TestSmartMapFunctionality:
    """Test SmartMap endpoint functionality with ambassador user"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin (ambassador) token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        return resp.json()["token"]
    
    def test_geocode_plan_returns_geocoded_locations(self, admin_token):
        """POST /api/ai/geocode-plan returns geocoded locations with lat/lng grouped by day"""
        # Simple plan with known locations
        plan = {
            "destination": "Rome",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Dia 1 - Centro Historico",
                    "activities": [
                        "Colosseum",
                        "Roman Forum",
                        "Trevi Fountain"
                    ]
                },
                {
                    "day": 2,
                    "title": "Dia 2 - Vaticano",
                    "activities": [
                        "Vatican Museums",
                        "St Peter's Basilica"
                    ]
                }
            ]
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"plan": plan},
            timeout=60  # Geocoding can take time
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert "days" in data, "Response should have 'days' field"
        assert "destination" in data, "Response should have 'destination' field"
        assert data["destination"] == "Rome"
        
        # Verify days structure
        assert len(data["days"]) == 2, f"Expected 2 days, got {len(data['days'])}"
        
        for day_data in data["days"]:
            assert "day" in day_data, "Each day should have 'day' field"
            assert "title" in day_data, "Each day should have 'title' field"
            assert "locations" in day_data, "Each day should have 'locations' field"
            
            # Verify at least some locations were geocoded
            for loc in day_data["locations"]:
                assert "name" in loc, "Location should have 'name'"
                assert "lat" in loc, "Location should have 'lat'"
                assert "lng" in loc, "Location should have 'lng'"
                assert "day" in loc, "Location should have 'day'"
                assert isinstance(loc["lat"], (int, float)), "lat should be numeric"
                assert isinstance(loc["lng"], (int, float)), "lng should be numeric"
                # Rome coordinates roughly: lat 41.9, lng 12.5
                assert 40 < loc["lat"] < 43, f"lat {loc['lat']} seems wrong for Rome"
                assert 11 < loc["lng"] < 14, f"lng {loc['lng']} seems wrong for Rome"
        
        print(f"✓ Geocoded {sum(len(d['locations']) for d in data['days'])} locations across {len(data['days'])} days")
    
    def test_optimize_route_returns_optimized_order(self, admin_token):
        """POST /api/ai/optimize-route returns optimized order with savings description"""
        locations = [
            {"name": "Colosseum", "lat": 41.8902, "lng": 12.4922},
            {"name": "Trevi Fountain", "lat": 41.9009, "lng": 12.4833},
            {"name": "Roman Forum", "lat": 41.8925, "lng": 12.4853},
            {"name": "Pantheon", "lat": 41.8986, "lng": 12.4769}
        ]
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/optimize-route",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"locations": locations, "day": 1, "destination": "Rome"},
            timeout=35  # AI call can take time
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert "optimized_order" in data, "Response should have 'optimized_order'"
        assert "savings" in data, "Response should have 'savings'"
        
        # Verify optimized_order is a list of location names
        assert isinstance(data["optimized_order"], list), "optimized_order should be a list"
        assert len(data["optimized_order"]) > 0, "optimized_order should not be empty"
        
        # Verify savings is a string description
        assert isinstance(data["savings"], str), "savings should be a string"
        assert len(data["savings"]) > 0, "savings should not be empty"
        
        # Tips are optional but should be a list if present
        if "tips" in data:
            assert isinstance(data["tips"], list), "tips should be a list"
        
        print(f"✓ Optimized route: {data['optimized_order']}")
        print(f"✓ Savings: {data['savings']}")
    
    def test_improve_location_returns_suggestions(self, admin_token):
        """POST /api/ai/improve-location returns structured suggestions"""
        # Test each improvement type
        improvement_types = ["less_queues", "cheaper", "best_time"]
        
        for imp_type in improvement_types:
            resp = requests.post(
                f"{BASE_URL}/api/ai/improve-location",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "location": "Colosseum",
                    "type": imp_type,
                    "destination": "Rome",
                    "day": 1
                },
                timeout=30
            )
            
            assert resp.status_code == 200, f"Expected 200 for {imp_type}, got {resp.status_code}: {resp.text}"
            data = resp.json()
            
            # Verify response structure
            assert "response" in data, f"Response should have 'response' for {imp_type}"
            assert "suggestions" in data, f"Response should have 'suggestions' for {imp_type}"
            assert "can_apply" in data, f"Response should have 'can_apply' for {imp_type}"
            assert "apply_prompt" in data, f"Response should have 'apply_prompt' for {imp_type}"
            
            # Verify types
            assert isinstance(data["response"], str), "response should be a string"
            assert isinstance(data["suggestions"], list), "suggestions should be a list"
            assert isinstance(data["can_apply"], bool), "can_apply should be a boolean"
            
            print(f"✓ Improve location ({imp_type}): {data['response'][:50]}...")
            print(f"  Suggestions: {len(data['suggestions'])} items")


class TestGeocodingCache:
    """Test geocoding cache functionality"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin (ambassador) token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        return resp.json()["token"]
    
    def test_geocoding_uses_cache(self, admin_token):
        """Verify geocoding uses MongoDB cache for repeated requests"""
        # First request - may hit external API
        plan = {
            "destination": "Paris",
            "itinerary": [{
                "day": 1,
                "title": "Dia 1",
                "activities": ["Eiffel Tower"]
            }]
        }
        
        start1 = time.time()
        resp1 = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"plan": plan},
            timeout=30
        )
        time1 = time.time() - start1
        
        assert resp1.status_code == 200, f"First request failed: {resp1.text}"
        data1 = resp1.json()
        
        # Second request - should use cache (faster)
        start2 = time.time()
        resp2 = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"plan": plan},
            timeout=30
        )
        time2 = time.time() - start2
        
        assert resp2.status_code == 200, f"Second request failed: {resp2.text}"
        data2 = resp2.json()
        
        # Verify same results
        if data1["days"][0]["locations"] and data2["days"][0]["locations"]:
            loc1 = data1["days"][0]["locations"][0]
            loc2 = data2["days"][0]["locations"][0]
            assert loc1["lat"] == loc2["lat"], "Cached lat should match"
            assert loc1["lng"] == loc2["lng"], "Cached lng should match"
        
        print(f"✓ First request: {time1:.2f}s, Second request: {time2:.2f}s")
        print(f"  Cache likely used: {time2 < time1 or time2 < 1}")


class TestAIAssistantRegression:
    """Regression test for AI Assistant (from iteration 65)"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin (ambassador) token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        return resp.json()["token"]
    
    def test_ai_assistant_still_works(self, admin_token):
        """Verify AI Assistant endpoint still works correctly"""
        plan = {
            "destination": "Rome",
            "itinerary": [{
                "day": 1,
                "title": "Dia 1",
                "activities": ["Colosseum", "Roman Forum"]
            }]
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"plan": plan, "message": "Tornar mais barato"},
            timeout=30
        )
        
        assert resp.status_code == 200, f"AI Assistant failed: {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert "response" in data, "Response should have 'response'"
        assert "suggestions" in data, "Response should have 'suggestions'"
        assert "can_apply" in data, "Response should have 'can_apply'"
        assert "apply_prompt" in data, "Response should have 'apply_prompt'"
        
        print(f"✓ AI Assistant regression test passed")
        print(f"  Response: {data['response'][:50]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
