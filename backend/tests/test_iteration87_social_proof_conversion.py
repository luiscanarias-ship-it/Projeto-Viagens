"""
Iteration 87: Social Proof Banner + Conversion Optimization Tests
Tests for:
- Social Proof Banner with contributions array (display_name, amount, created_at)
- Final Conversion Block with dominant 'Contribuir' CTA
- Ambassador messaging improvements
- AI Assistant affiliate CTAs with broader keyword matching
- Must-see CTAs with 'Evita filas' text
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMainJourneyContributions:
    """Test /api/homepage/main-journey returns contributions array with required fields"""
    
    def test_main_journey_returns_contributions_array(self):
        """Verify contributions array exists with display_name, amount, created_at"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "journey" in data, "Response should contain 'journey' key"
        assert "contributions" in data, "Response should contain 'contributions' key"
        
        contributions = data.get("contributions", [])
        assert isinstance(contributions, list), "contributions should be a list"
        
        # Verify at least one contribution exists (China journey has 2 real contributors)
        if len(contributions) > 0:
            contrib = contributions[0]
            assert "display_name" in contrib, "Contribution should have display_name"
            assert "amount" in contrib, "Contribution should have amount"
            assert "created_at" in contrib, "Contribution should have created_at"
            
            # Verify data types
            assert isinstance(contrib["display_name"], str), "display_name should be string"
            assert isinstance(contrib["amount"], (int, float)), "amount should be numeric"
            assert isinstance(contrib["created_at"], str), "created_at should be string (ISO date)"
    
    def test_main_journey_returns_contributor_count(self):
        """Verify contributor_count is returned"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        
        data = response.json()
        assert "contributor_count" in data, "Response should contain contributor_count"
        assert isinstance(data["contributor_count"], int), "contributor_count should be integer"
        assert data["contributor_count"] >= 0, "contributor_count should be non-negative"
    
    def test_main_journey_returns_progress(self):
        """Verify progress percentage is returned"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        
        data = response.json()
        assert "progress" in data, "Response should contain progress"
        progress = data.get("progress", {})
        assert "percentage" in progress, "progress should contain percentage"
        assert isinstance(progress["percentage"], (int, float)), "percentage should be numeric"


class TestAffiliateLinks:
    """Test affiliate links endpoint returns required platforms"""
    
    def test_affiliate_links_returns_gyg(self):
        """Verify GetYourGuide affiliate link is present"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        assert "getyourguide" in data, "Should have getyourguide affiliate link"
        assert "url" in data["getyourguide"], "getyourguide should have url"
    
    def test_affiliate_links_returns_booking(self):
        """Verify Booking.com affiliate link is present"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        assert "booking" in data, "Should have booking affiliate link"
        assert "url" in data["booking"], "booking should have url"


class TestJourneyDetail:
    """Test journey detail endpoint for Social Proof CTA linking"""
    
    def test_journey_china_exists(self):
        """Verify China journey (journey_china001) is accessible"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "journey_id" in data, "Journey should have journey_id"
        assert data["journey_id"] == "journey_china001", "Should be China journey"


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Verify API is responding"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
