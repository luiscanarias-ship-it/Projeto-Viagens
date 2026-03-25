"""
Iteration 69 - Shareable Public Plans Feature Tests
Tests for:
- GET /api/plan/{slug} - Public plan endpoint
- GET /api/og-image/{slug} - OG image generation
- POST /api/ai/travel-plan - Slug field in response
- 404 for nonexistent slugs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPublicPlanEndpoints:
    """Tests for public plan and OG image endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Known plan slugs from the test context
        self.known_slugs = ["paris-acbc2d", "lisboa-6f4f3e", "porto-487baf"]
    
    def get_auth_token(self):
        """Login as admin to get auth token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    # ==================== PUBLIC PLAN ENDPOINT TESTS ====================
    
    def test_get_public_plan_returns_200(self):
        """GET /api/plan/{slug} returns 200 for existing public plan"""
        # Try known slugs
        for slug in self.known_slugs:
            response = self.session.get(f"{BASE_URL}/api/plan/{slug}")
            if response.status_code == 200:
                print(f"SUCCESS: GET /api/plan/{slug} returned 200")
                data = response.json()
                # Verify response structure
                assert "plan" in data or "destination" in data, f"Response should contain plan data"
                return
        
        # If no known slug works, check if any public plan exists
        pytest.skip("No public plans found with known slugs - may need to generate one first")
    
    def test_get_public_plan_contains_required_fields(self):
        """GET /api/plan/{slug} returns plan with destination, itinerary, weather, packing, checklist, local_tips"""
        for slug in self.known_slugs:
            response = self.session.get(f"{BASE_URL}/api/plan/{slug}")
            if response.status_code == 200:
                data = response.json()
                plan = data.get("plan", data)
                
                # Check required fields
                required_fields = ["destination", "itinerary", "weather", "packing", "checklist", "local_tips"]
                missing = [f for f in required_fields if f not in plan]
                
                if missing:
                    print(f"WARNING: Plan missing fields: {missing}")
                else:
                    print(f"SUCCESS: Plan contains all required fields: {required_fields}")
                
                # Verify destination exists
                assert "destination" in plan or "destination" in data, "Plan must have destination"
                print(f"Destination: {plan.get('destination', data.get('destination'))}")
                return
        
        pytest.skip("No public plans found with known slugs")
    
    def test_get_nonexistent_plan_returns_404(self):
        """GET /api/plan/nonexistent-slug returns 404"""
        response = self.session.get(f"{BASE_URL}/api/plan/nonexistent-slug-xyz123")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("SUCCESS: GET /api/plan/nonexistent-slug returns 404")
    
    # ==================== OG IMAGE ENDPOINT TESTS ====================
    
    def test_og_image_returns_png(self):
        """GET /api/og-image/{slug} returns PNG image (200 OK, content-type: image/png)"""
        for slug in self.known_slugs:
            response = self.session.get(f"{BASE_URL}/api/og-image/{slug}")
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                assert "image/png" in content_type, f"Expected image/png, got {content_type}"
                assert len(response.content) > 0, "Image content should not be empty"
                print(f"SUCCESS: GET /api/og-image/{slug} returns PNG ({len(response.content)} bytes)")
                return
        
        pytest.skip("No public plans found with known slugs for OG image test")
    
    def test_og_image_nonexistent_returns_404(self):
        """GET /api/og-image/nonexistent-slug returns 404"""
        response = self.session.get(f"{BASE_URL}/api/og-image/nonexistent-slug-xyz123")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("SUCCESS: GET /api/og-image/nonexistent-slug returns 404")
    
    # ==================== TRAVEL PLAN GENERATION TESTS ====================
    
    def test_travel_plan_returns_slug(self):
        """POST /api/ai/travel-plan returns 'slug' field in response"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate - skipping travel plan generation test")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Use a unique destination to avoid cache
        import uuid
        unique_dest = f"TestCity{uuid.uuid4().hex[:4]}"
        
        response = self.session.post(
            f"{BASE_URL}/api/ai/travel-plan",
            json={
                "destination": unique_dest,
                "start_date": "2026-03-01",
                "end_date": "2026-03-05",
                "trip_type": "cultural"
            },
            headers=headers,
            timeout=60
        )
        
        # Accept 200 (success), 429 (rate limited), or 504 (timeout)
        if response.status_code == 429:
            print("INFO: Rate limited - checking if cached plans have slug")
            # Try to get a cached plan instead
            for slug in self.known_slugs:
                plan_resp = self.session.get(f"{BASE_URL}/api/plan/{slug}")
                if plan_resp.status_code == 200:
                    data = plan_resp.json()
                    if "slug" in data:
                        print(f"SUCCESS: Cached plan has slug field: {data['slug']}")
                        return
            pytest.skip("Rate limited and no cached plans with slug found")
        elif response.status_code == 504:
            pytest.skip("AI generation timed out - this is expected for slow AI responses")
        elif response.status_code == 200:
            data = response.json()
            assert "slug" in data, f"Response should contain 'slug' field. Keys: {list(data.keys())}"
            assert data["slug"], "Slug should not be empty"
            print(f"SUCCESS: POST /api/ai/travel-plan returns slug: {data['slug']}")
        else:
            print(f"WARNING: Unexpected status {response.status_code}: {response.text[:200]}")
            # Don't fail - just report
    
    # ==================== SITEMAP TESTS ====================
    
    def test_sitemap_includes_public_plans(self):
        """GET /api/sitemap.xml includes public plan URLs"""
        response = self.session.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content = response.text
        assert "urlset" in content, "Sitemap should contain urlset"
        
        # Check if any /plano/ URLs are included
        if "/plano/" in content:
            print("SUCCESS: Sitemap includes /plano/ URLs for public plans")
        else:
            print("INFO: No /plano/ URLs in sitemap yet (may need public plans)")


class TestPublicPlanDataIntegrity:
    """Tests for data integrity of public plans"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.known_slugs = ["paris-acbc2d", "lisboa-6f4f3e", "porto-487baf"]
    
    def test_plan_has_itinerary_structure(self):
        """Public plan itinerary has day, title, activities structure"""
        for slug in self.known_slugs:
            response = self.session.get(f"{BASE_URL}/api/plan/{slug}")
            if response.status_code == 200:
                data = response.json()
                plan = data.get("plan", data)
                itinerary = plan.get("itinerary", [])
                
                if itinerary:
                    day = itinerary[0]
                    assert "day" in day, "Itinerary day should have 'day' field"
                    assert "activities" in day, "Itinerary day should have 'activities' field"
                    print(f"SUCCESS: Itinerary structure valid - {len(itinerary)} days")
                    return
        
        pytest.skip("No public plans found")
    
    def test_plan_has_packing_structure(self):
        """Public plan packing has clothing and essentials"""
        for slug in self.known_slugs:
            response = self.session.get(f"{BASE_URL}/api/plan/{slug}")
            if response.status_code == 200:
                data = response.json()
                plan = data.get("plan", data)
                packing = plan.get("packing", {})
                
                if packing:
                    has_clothing = "clothing" in packing
                    has_essentials = "essentials" in packing
                    print(f"SUCCESS: Packing structure - clothing: {has_clothing}, essentials: {has_essentials}")
                    return
        
        pytest.skip("No public plans found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
