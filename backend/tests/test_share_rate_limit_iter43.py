"""
Iteration 43: Test share functionality and rate limit UX improvements
- Test rate limit (429 response with correct message)
- Test reset-limit endpoint
- Test buildPlanText contains all required sections
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRateLimitAndShare:
    """Test rate limiting and share-related endpoints"""
    
    @pytest.fixture(autouse=True)
    def reset_rate_limit(self):
        """Clear rate limit before each test"""
        requests.post(f"{BASE_URL}/api/ai/travel-plan/reset-limit", timeout=10)
        yield
        requests.post(f"{BASE_URL}/api/ai/travel-plan/reset-limit", timeout=10)
    
    def test_reset_limit_endpoint_exists(self):
        """Test POST /api/ai/travel-plan/reset-limit returns 200 and clears cache"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan/reset-limit", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "cleared"
        print("PASS: Reset limit endpoint working")
    
    def test_travel_plan_basic_request(self):
        """Test POST /api/ai/travel-plan returns plan with all required fields"""
        payload = {
            "destination": "Lisboa, Portugal",
            "start_date": "2026-03-01",
            "end_date": "2026-03-03",
            "trip_type": ["cultural"]
        }
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json=payload, timeout=60)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        plan = data.get("plan", {})
        
        # Verify all required fields for buildPlanText
        assert "destination" in plan, "Missing destination in plan"
        assert "dates" in plan, "Missing dates in plan"
        assert "summary" in plan, "Missing summary in plan"
        assert "weather" in plan, "Missing weather in plan"
        assert "packing" in plan, "Missing packing in plan"
        assert "itinerary" in plan, "Missing itinerary in plan"
        assert "checklist" in plan, "Missing checklist in plan"
        assert "local_tips" in plan, "Missing local_tips in plan"
        
        # Verify packing structure
        packing = plan.get("packing", {})
        assert "clothing" in packing or "essentials" in packing, "Missing packing sub-fields"
        
        # Verify itinerary structure
        itinerary = plan.get("itinerary", [])
        assert len(itinerary) > 0, "Itinerary should not be empty"
        for day in itinerary:
            assert "day" in day, "Missing day field in itinerary"
            assert "title" in day, "Missing title field in itinerary"
            assert "activities" in day, "Missing activities field in itinerary"
        
        # Verify checklist structure
        checklist = plan.get("checklist", {})
        assert any(k in checklist for k in ["documents", "hygiene", "tech"]), "Missing checklist categories"
        
        print("PASS: Travel plan contains all required fields for buildPlanText")
    
    def test_rate_limit_429_response(self):
        """Test that after 5 requests, API returns 429 with correct message"""
        import uuid
        
        # Use unique destinations to bypass caching - each request counts toward limit
        destinations = [
            f"TEST_Porto_{uuid.uuid4().hex[:6]}, Portugal",
            f"TEST_Braga_{uuid.uuid4().hex[:6]}, Portugal",
            f"TEST_Faro_{uuid.uuid4().hex[:6]}, Portugal",
            f"TEST_Coimbra_{uuid.uuid4().hex[:6]}, Portugal",
            f"TEST_Aveiro_{uuid.uuid4().hex[:6]}, Portugal"
        ]
        
        # Make 5 requests with unique destinations (will not be cached)
        for i, dest in enumerate(destinations):
            payload = {
                "destination": dest,
                "start_date": "2026-04-01",
                "end_date": "2026-04-02",
                "trip_type": "passeio"
            }
            response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json=payload, timeout=60)
            print(f"Request {i+1}/5: status={response.status_code} (destination: {dest[:30]}...)")
            assert response.status_code in [200], f"Request {i+1} failed: {response.text}"
        
        # 6th request should be rate limited
        payload = {
            "destination": f"TEST_Setubal_{uuid.uuid4().hex[:6]}, Portugal",
            "start_date": "2026-04-01",
            "end_date": "2026-04-02",
            "trip_type": "passeio"
        }
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json=payload, timeout=10)
        assert response.status_code == 429, f"Expected 429, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", "")
        
        # Verify rate limit message contains airplane emoji and correct text
        assert "✈️" in detail, f"Rate limit message should contain ✈️. Got: {detail}"
        assert "1 hora" in detail or "hora" in detail, f"Rate limit message should mention '1 hora'. Got: {detail}"
        
        print(f"PASS: 429 response with correct message: {detail}")
    
    def test_refine_endpoint_exists(self):
        """Test POST /api/ai/travel-plan/refine exists and works"""
        # First create a plan
        payload = {
            "destination": "Madrid, Espanha",
            "start_date": "2026-05-01",
            "end_date": "2026-05-02",
            "trip_type": "gastronomica"
        }
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan", json=payload, timeout=60)
        assert response.status_code == 200
        
        plan = response.json().get("plan", {})
        
        # Now refine it
        refine_payload = {
            "destination": "Madrid, Espanha",
            "start_date": "2026-05-01",
            "end_date": "2026-05-02",
            "trip_type": "gastronomica",
            "previous_plan": plan,
            "refinement": "Adicionar mais restaurantes"
        }
        refine_response = requests.post(f"{BASE_URL}/api/ai/travel-plan/refine", json=refine_payload, timeout=60)
        assert refine_response.status_code == 200, f"Refine failed: {refine_response.text}"
        
        refined_plan = refine_response.json().get("plan", {})
        assert "destination" in refined_plan
        assert "itinerary" in refined_plan
        
        print("PASS: Refine endpoint working")
    
    def test_affiliate_links_endpoint(self):
        """Test GET /api/affiliate-links returns all required platforms"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        required_platforms = ["booking", "skyscanner", "getyourguide", "airalo", "cars"]
        
        for platform in required_platforms:
            assert platform in data, f"Missing platform: {platform}"
            assert "url" in data[platform], f"Missing URL for {platform}"
        
        print("PASS: All affiliate platforms present")
    
    def test_affiliate_click_tracking(self):
        """Test POST /api/affiliate-click tracks clicks"""
        platforms = ["booking", "skyscanner", "getyourguide", "airalo", "cars"]
        
        for platform in platforms:
            response = requests.post(f"{BASE_URL}/api/affiliate-click", json={"platform": platform}, timeout=10)
            assert response.status_code == 200, f"Failed to track {platform}: {response.text}"
        
        print("PASS: Affiliate click tracking working for all platforms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
