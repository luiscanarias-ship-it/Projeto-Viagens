"""
Iteration 45 - Journey Detail Page Refactor Tests
Tests for:
- GET /api/journeys/:id - Returns journey data correctly
- GET /api/journeys/:id/progress - Returns progress data
- GET /api/journeys/:id/contributions - Returns contributions list
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
JOURNEY_ID = "journey_china001"


class TestJourneyDetailEndpoints:
    """Test journey detail API endpoints"""
    
    def test_get_journey_returns_correct_data(self):
        """GET /api/journeys/:id returns journey with all required fields"""
        response = requests.get(f"{BASE_URL}/api/journeys/{JOURNEY_ID}")
        
        assert response.status_code == 200
        
        data = response.json()
        # Verify required fields
        assert "journey_id" in data
        assert data["journey_id"] == JOURNEY_ID
        assert "name" in data
        assert data["name"] == "China"
        assert "poetic_name" in data
        assert "description" in data
        assert "image_url" in data
        assert "is_active" in data
        assert data["is_active"] == True
        assert "current_amount" in data
        assert "goal_amount" in data
        
        # Verify story chapters for StoryChapter component
        assert "story_chapters" in data
        assert isinstance(data["story_chapters"], dict)
        
    def test_get_journey_not_found(self):
        """GET /api/journeys/:id returns 404 for non-existent journey"""
        response = requests.get(f"{BASE_URL}/api/journeys/nonexistent_journey")
        
        assert response.status_code == 404
        
    def test_get_journey_progress(self):
        """GET /api/journeys/:id/progress returns progress data"""
        response = requests.get(f"{BASE_URL}/api/journeys/{JOURNEY_ID}/progress")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "journey_id" in data
        assert data["journey_id"] == JOURNEY_ID
        assert "current_amount" in data
        assert "percentage" in data
        assert isinstance(data["percentage"], (int, float))
        assert "is_funded" in data
        assert isinstance(data["is_funded"], bool)
        assert "status" in data
        assert "contributor_count" in data
        
    def test_get_journey_progress_not_found(self):
        """GET /api/journeys/:id/progress returns 404 for non-existent journey"""
        response = requests.get(f"{BASE_URL}/api/journeys/nonexistent_journey/progress")
        
        assert response.status_code == 404
        
    def test_get_journey_contributions(self):
        """GET /api/journeys/:id/contributions returns contributions list"""
        response = requests.get(f"{BASE_URL}/api/journeys/{JOURNEY_ID}/contributions")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        assert "contributions" in data
        assert isinstance(data["contributions"], list)
        
        # If there are contributions, verify structure
        if data["count"] > 0:
            contrib = data["contributions"][0]
            assert "contribution_id" in contrib
            assert "amount" in contrib
            assert "created_at" in contrib
            

class TestContributionConfig:
    """Test contribution configuration endpoint for checkout modal"""
    
    def test_get_contribution_config(self):
        """GET /api/contributions/config returns valid configuration"""
        response = requests.get(f"{BASE_URL}/api/contributions/config")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "fixed_amounts" in data
        assert isinstance(data["fixed_amounts"], list)
        # Verify our fixed amounts
        assert 10 in data["fixed_amounts"]
        assert 20 in data["fixed_amounts"]
        assert 50 in data["fixed_amounts"]
        assert 100 in data["fixed_amounts"]
        
        assert "payment_methods" in data
        assert "currency" in data
        
    def test_get_payment_info(self):
        """GET /api/contributions/payment-info returns payment details"""
        response = requests.get(f"{BASE_URL}/api/contributions/payment-info")
        
        assert response.status_code == 200
        
        data = response.json()
        # Check payment method info exists
        assert "mbway" in data
        assert "paypal" in data
        assert "crypto" in data
        
        # Verify crypto addresses structure
        assert "btc" in data["crypto"]
        assert "eth" in data["crypto"]
        assert "usdt" in data["crypto"]


class TestContributionCreate:
    """Test contribution creation for checkout flow"""
    
    def test_create_contribution_invalid_amount(self):
        """POST /api/contributions/create with invalid amount returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/contributions/create",
            json={
                "amount": 15,  # Not in fixed amounts
                "payment_method": "mbway",
                "journey_id": JOURNEY_ID
            }
        )
        
        assert response.status_code == 400
        
    def test_create_contribution_invalid_payment_method(self):
        """POST /api/contributions/create with invalid payment method returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/contributions/create",
            json={
                "amount": 10,
                "payment_method": "invalid_method",
                "journey_id": JOURNEY_ID
            }
        )
        
        assert response.status_code == 400
        
    def test_create_contribution_valid(self):
        """POST /api/contributions/create with valid data succeeds"""
        response = requests.post(
            f"{BASE_URL}/api/contributions/create",
            json={
                "amount": 10,
                "payment_method": "mbway",
                "journey_id": JOURNEY_ID,
                "contributor_name": "TEST_Iter45_User"
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "contribution_id" in data
        assert "payment_reference" in data
        assert data["amount"] == 10
        assert data["status"] == "pending"


class TestAITravelPlannerIntegration:
    """Test AI Travel Planner endpoint for CTA integration"""
    
    def test_travel_planner_destination_validation(self):
        """POST /api/ai/travel-plan validates destination"""
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan",
            json={
                "destination": "",  # Empty destination
                "start_date": "2026-04-01",
                "end_date": "2026-04-05"
            }
        )
        
        # Should return 400 for empty destination
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
