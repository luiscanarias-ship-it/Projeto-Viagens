"""
4Luis Crowdfunding Platform - Homepage API Tests
Tests for: Homepage sections, Main journey, Ambassador journeys, Curated content, Lifecycle
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://consent-flow-4.preview.emergentagent.com').rstrip('/')


class TestHomepageMainJourney:
    """Tests for /api/homepage/main-journey endpoint"""
    
    def test_main_journey_returns_valid_response(self):
        """Test main journey endpoint returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "journey" in data
        assert "progress" in data
        assert "contributions" in data
        assert "updates" in data
        print(f"✓ Main journey endpoint returns valid structure")
    
    def test_main_journey_when_no_active_journey(self):
        """Test main journey returns null when no journey is active"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        data = response.json()
        
        # Either journey is null or it has proper structure
        if data["journey"] is None:
            assert data["progress"] is None
            assert data["contributions"] == []
            print("✓ Correctly returns null/empty when no main journey active")
        else:
            assert "journey_id" in data["journey"]
            assert "name" in data["journey"]
            assert "percentage" in data["progress"]
            print(f"✓ Main journey found: {data['journey']['name']}")
    
    def test_main_journey_hides_sensitive_fields(self):
        """Test that goal_amount is hidden from public response"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        data = response.json()
        
        if data["journey"] is not None:
            # goal_amount should be hidden from public
            assert "goal_amount" not in data["journey"]
            print("✓ Sensitive field goal_amount hidden from public")
        else:
            print("○ No journey to check (expected when no active journey)")


class TestHomepageAmbassadorJourneys:
    """Tests for /api/homepage/ambassador-journeys endpoint"""
    
    def test_ambassador_journeys_returns_valid_response(self):
        """Test ambassador journeys endpoint returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_count" in data
        assert "regions" in data
        assert isinstance(data["regions"], dict)
        print(f"✓ Ambassador journeys: {data['total_count']} journeys")
    
    def test_ambassador_journeys_empty_state(self):
        """Test empty state when no ambassador journeys"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        if data["total_count"] == 0:
            assert data["regions"] == {}
            print("✓ Empty state: no ambassador journeys (regions empty)")
        else:
            # Check regions are properly organized
            for region_key, region_data in data["regions"].items():
                assert "name" in region_data
                assert "journeys" in region_data
                assert isinstance(region_data["journeys"], list)
            print(f"✓ Found ambassador journeys in {len(data['regions'])} regions")
    
    def test_ambassador_journeys_region_structure(self):
        """Test region data structure"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        valid_regions = ["europa", "asia", "africa", "americas", "oceania", "outro"]
        
        for region_key in data["regions"].keys():
            assert region_key in valid_regions, f"Invalid region: {region_key}"
        
        print(f"✓ All regions have valid keys")


class TestHomepageCuratedDreams:
    """Tests for /api/homepage/curated-dreams endpoint"""
    
    def test_curated_dreams_returns_valid_response(self):
        """Test curated dreams endpoint returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/homepage/curated-dreams")
        assert response.status_code == 200
        data = response.json()
        
        assert "use_curated" in data
        assert "curated_dreams" in data
        assert isinstance(data["curated_dreams"], list)
        print(f"✓ Curated dreams endpoint returns valid structure")
    
    def test_curated_dreams_content(self):
        """Test curated dreams have proper content structure"""
        response = requests.get(f"{BASE_URL}/api/homepage/curated-dreams")
        assert response.status_code == 200
        data = response.json()
        
        if data["use_curated"]:
            assert len(data["curated_dreams"]) > 0
            assert "message" in data
            
            # Check each dream has required fields
            for dream in data["curated_dreams"]:
                assert "id" in dream
                assert "name" in dream
                assert "country" in dream
                assert "image_url" in dream
                assert "story" in dream
                assert "is_curated" in dream
                assert dream["is_curated"] == True
            
            print(f"✓ Curated dreams: {len(data['curated_dreams'])} inspirational journeys")
            print(f"  Message: '{data['message']}'")
        else:
            # No curated needed means there are real journeys
            print("✓ No curated content needed (real journeys exist)")


class TestHomepageRealizedJourneys:
    """Tests for /api/homepage/realized-journeys endpoint"""
    
    def test_realized_journeys_returns_valid_response(self):
        """Test realized journeys endpoint returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/homepage/realized-journeys")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_count" in data
        assert "countries" in data
        assert isinstance(data["countries"], dict)
        print(f"✓ Realized journeys: {data['total_count']} journeys")
    
    def test_realized_journeys_country_structure(self):
        """Test country data structure"""
        response = requests.get(f"{BASE_URL}/api/homepage/realized-journeys")
        assert response.status_code == 200
        data = response.json()
        
        if data["total_count"] > 0:
            for country_name, country_data in data["countries"].items():
                assert "name" in country_data
                assert "journeys" in country_data
                assert isinstance(country_data["journeys"], list)
                assert len(country_data["journeys"]) > 0
            print(f"✓ Found realized journeys in {len(data['countries'])} countries")
        else:
            assert data["countries"] == {}
            print("✓ Empty state: no realized journeys yet")


class TestHomepageIntegration:
    """Integration tests for homepage data flow"""
    
    def test_homepage_all_endpoints_accessible(self):
        """Test all homepage endpoints are accessible"""
        endpoints = [
            "/api/homepage/main-journey",
            "/api/homepage/ambassador-journeys",
            "/api/homepage/realized-journeys",
            "/api/homepage/curated-dreams"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 200, f"Failed: {endpoint}"
            print(f"✓ {endpoint} - accessible")
    
    def test_curated_replaces_realized(self):
        """Test curated content shows when no realized journeys"""
        # Get realized journeys
        realized = requests.get(f"{BASE_URL}/api/homepage/realized-journeys").json()
        curated = requests.get(f"{BASE_URL}/api/homepage/curated-dreams").json()
        
        if realized["total_count"] == 0:
            # Curated should be active
            assert curated["use_curated"] == True
            assert len(curated["curated_dreams"]) > 0
            print("✓ Curated content fills 'Sonhos Realizados' when empty")
        else:
            # Curated should be inactive
            assert curated["use_curated"] == False
            print("✓ Real journeys shown (curated disabled)")


class TestJourneyLifecycle:
    """Tests for journey status lifecycle - requires admin auth"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_journey_status_values(self, admin_token):
        """Test journey status field has valid values"""
        response = requests.get(
            f"{BASE_URL}/api/admin/journeys",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        journeys = response.json()
        
        valid_statuses = ["candidatura", "aprovada", "ativa", "financiada", "realizada", "encerrada", "active"]
        
        for journey in journeys:
            status = journey.get("status")
            if status:
                assert status in valid_statuses, f"Invalid status: {status}"
        
        print(f"✓ All {len(journeys)} journeys have valid status values")
    
    def test_funded_journey_status_change_logic(self, admin_token):
        """Test the funding check logic (check_and_update_journey_funding_status)"""
        # Get a journey to verify the logic
        response = requests.get(
            f"{BASE_URL}/api/admin/journeys",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        journeys = response.json()
        
        for journey in journeys:
            current = journey.get("current_amount", 0)
            goal = journey.get("goal_amount", 1)
            status = journey.get("status", "")
            
            if current >= goal and goal > 0:
                # Should be either "financiada" or already "realizada"/"encerrada"
                assert status in ["financiada", "realizada", "encerrada"], \
                    f"Journey {journey.get('name')} should be funded but has status: {status}"
                print(f"✓ {journey.get('name')}: funded (status={status})")
        
        print("✓ Funding status logic verified")


class TestTravelPlannerAPI:
    """Tests for travel resources API used in 'Planeia a tua viagem'"""
    
    def test_travel_resources_by_destination(self):
        """Test travel resources for custom destination"""
        response = requests.get(f"{BASE_URL}/api/travel-resources/Paris")
        assert response.status_code == 200
        data = response.json()
        
        assert "destination" in data
        assert data["destination"] == "Paris"
        assert "hotels" in data
        assert "flights" in data
        assert "social" in data
        assert "map" in data
        print(f"✓ Travel resources for Paris: {len(data['hotels'])} hotels, {len(data['flights'])} flights")
    
    def test_travel_resources_special_characters(self):
        """Test destination with special characters"""
        response = requests.get(f"{BASE_URL}/api/travel-resources/São%20Paulo")
        assert response.status_code == 200
        data = response.json()
        assert "destination" in data
        print(f"✓ Travel resources work with special characters")


class TestDreamersStats:
    """Tests for dreamers statistics shown on homepage"""
    
    def test_dreamers_stats_returns_valid_response(self):
        """Test dreamers stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/dreamers-stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_dreamers" in data
        assert isinstance(data["total_dreamers"], int)
        print(f"✓ Dreamers stats: {data['total_dreamers']} total dreamers")
        
        # top_dreamer may or may not exist
        if "top_dreamer" in data and data["top_dreamer"]:
            assert "name" in data["top_dreamer"]
            print(f"  Top dreamer: {data['top_dreamer']['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
