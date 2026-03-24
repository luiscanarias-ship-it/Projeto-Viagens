"""
Social Proof Features Backend API Tests
Tests for 'momentos de prova' (social proof moments) across the user journey

Features tested:
1. Homepage main journey API returns contributor_count and journey_contributor_count
2. Journey progress API returns contributor_count and journey_contributor_count
3. Contributor count includes the seed offset of +57
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geo-payouts-preview.preview.emergentagent.com').rstrip('/')

class TestHomepageSocialProof:
    """Tests for homepage main journey social proof data"""
    
    def test_homepage_main_journey_has_contributor_count(self):
        """Test that homepage main-journey endpoint returns contributor_count"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        
        data = response.json()
        assert "contributor_count" in data, "Response should contain contributor_count"
        assert isinstance(data["contributor_count"], int), "contributor_count should be an integer"
        assert data["contributor_count"] >= 57, "contributor_count should be at least 57 (seed offset)"
        print(f"✅ Homepage contributor_count: {data['contributor_count']}")
    
    def test_homepage_main_journey_has_journey_contributor_count(self):
        """Test that homepage main-journey endpoint returns journey_contributor_count"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        
        data = response.json()
        assert "journey_contributor_count" in data, "Response should contain journey_contributor_count"
        assert isinstance(data["journey_contributor_count"], int), "journey_contributor_count should be an integer"
        assert data["journey_contributor_count"] >= 0, "journey_contributor_count should be non-negative"
        print(f"✅ Homepage journey_contributor_count: {data['journey_contributor_count']}")
    
    def test_homepage_main_journey_returns_journey_data(self):
        """Test that homepage main-journey endpoint returns complete journey data"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        
        data = response.json()
        assert "journey" in data, "Response should contain journey object"
        assert "progress" in data, "Response should contain progress object"
        
        journey = data["journey"]
        assert "journey_id" in journey, "Journey should have journey_id"
        assert "name" in journey, "Journey should have name"
        print(f"✅ Homepage main journey: {journey.get('name')} ({journey.get('journey_id')})")


class TestJourneyProgressSocialProof:
    """Tests for journey progress endpoint social proof data"""
    
    @pytest.fixture
    def main_journey_id(self):
        """Get the main journey ID from homepage API"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        if response.status_code == 200:
            data = response.json()
            return data.get("journey", {}).get("journey_id")
        return "journey_china001"  # fallback
    
    def test_journey_progress_has_contributor_count(self, main_journey_id):
        """Test that journey progress endpoint returns contributor_count"""
        response = requests.get(f"{BASE_URL}/api/journeys/{main_journey_id}/progress")
        assert response.status_code == 200
        
        data = response.json()
        assert "contributor_count" in data, "Response should contain contributor_count"
        assert isinstance(data["contributor_count"], int), "contributor_count should be an integer"
        assert data["contributor_count"] >= 57, "contributor_count should be at least 57 (seed offset)"
        print(f"✅ Journey progress contributor_count: {data['contributor_count']}")
    
    def test_journey_progress_has_journey_contributor_count(self, main_journey_id):
        """Test that journey progress endpoint returns journey_contributor_count"""
        response = requests.get(f"{BASE_URL}/api/journeys/{main_journey_id}/progress")
        assert response.status_code == 200
        
        data = response.json()
        assert "journey_contributor_count" in data, "Response should contain journey_contributor_count"
        assert isinstance(data["journey_contributor_count"], int), "journey_contributor_count should be an integer"
        assert data["journey_contributor_count"] >= 0, "journey_contributor_count should be non-negative"
        print(f"✅ Journey progress journey_contributor_count: {data['journey_contributor_count']}")
    
    def test_journey_progress_has_percentage(self, main_journey_id):
        """Test that journey progress endpoint returns percentage"""
        response = requests.get(f"{BASE_URL}/api/journeys/{main_journey_id}/progress")
        assert response.status_code == 200
        
        data = response.json()
        assert "percentage" in data, "Response should contain percentage"
        assert isinstance(data["percentage"], (int, float)), "percentage should be a number"
        assert data["percentage"] >= 0, "percentage should be non-negative"
        print(f"✅ Journey progress percentage: {data['percentage']}%")
    
    def test_contributor_count_seed_offset(self, main_journey_id):
        """Test that contributor_count includes the seed offset of +57"""
        response = requests.get(f"{BASE_URL}/api/journeys/{main_journey_id}/progress")
        assert response.status_code == 200
        
        data = response.json()
        contributor_count = data["contributor_count"]
        journey_contributor_count = data["journey_contributor_count"]
        
        # The contributor_count should always be >= 57 due to seed offset
        assert contributor_count >= 57, f"contributor_count ({contributor_count}) should include seed offset of 57"
        
        # journey_contributor_count is actual count for this specific journey (no offset)
        assert journey_contributor_count >= 0, "journey_contributor_count should be non-negative"
        
        print(f"✅ Seed offset verified: platform={contributor_count} (includes +57 seed), journey={journey_contributor_count}")


class TestJourneyEndpoint:
    """Tests for individual journey endpoint"""
    
    @pytest.fixture
    def main_journey_id(self):
        """Get the main journey ID from homepage API"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        if response.status_code == 200:
            data = response.json()
            return data.get("journey", {}).get("journey_id")
        return "journey_china001"  # fallback
    
    def test_journey_detail_returns_complete_data(self, main_journey_id):
        """Test that journey detail endpoint returns complete journey data"""
        response = requests.get(f"{BASE_URL}/api/journeys/{main_journey_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "journey_id" in data, "Journey should have journey_id"
        assert "name" in data, "Journey should have name"
        assert "poetic_name" in data, "Journey should have poetic_name"
        assert "description" in data, "Journey should have description"
        assert "emotional_message" in data, "Journey should have emotional_message"
        print(f"✅ Journey detail for {data.get('name')}: complete data returned")


class TestContributionsEndpoint:
    """Tests for contributions endpoint"""
    
    @pytest.fixture
    def main_journey_id(self):
        """Get the main journey ID from homepage API"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        if response.status_code == 200:
            data = response.json()
            return data.get("journey", {}).get("journey_id")
        return "journey_china001"  # fallback
    
    def test_journey_contributions_list(self, main_journey_id):
        """Test that journey contributions endpoint returns contribution list"""
        response = requests.get(f"{BASE_URL}/api/journeys/{main_journey_id}/contributions")
        assert response.status_code == 200
        
        data = response.json()
        assert "contributions" in data, "Response should contain contributions array"
        assert "count" in data, "Response should contain count"
        assert isinstance(data["contributions"], list), "contributions should be a list"
        print(f"✅ Journey contributions: {data.get('count')} total")


class TestContributionConfig:
    """Tests for contribution configuration"""
    
    def test_contribution_config_endpoint(self):
        """Test that contribution config endpoint returns valid configuration"""
        response = requests.get(f"{BASE_URL}/api/contributions/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "fixed_amounts" in data, "Response should contain fixed_amounts"
        assert "payment_methods" in data, "Response should contain payment_methods"
        
        # Verify fixed amounts
        fixed_amounts = data["fixed_amounts"]
        assert 10 in fixed_amounts, "10€ should be in fixed amounts"
        assert 20 in fixed_amounts, "20€ should be in fixed amounts"
        assert 50 in fixed_amounts, "50€ should be in fixed amounts"
        
        print(f"✅ Contribution config: fixed_amounts={fixed_amounts}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
