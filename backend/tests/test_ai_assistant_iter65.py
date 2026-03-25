"""
Test AI Assistant Premium Feature - Iteration 65
Tests the POST /api/ai/assistant endpoint for ambassador-only access
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"

# Sample plan for testing
SAMPLE_PLAN = {
    "destination": "Paris",
    "dates": "2026-04-10 a 2026-04-14",
    "itinerary": [
        {
            "day": 1,
            "title": "Chegada a Paris",
            "activities": ["Check-in no hotel", "Torre Eiffel", "Jantar no Quartier Latin"]
        },
        {
            "day": 2,
            "title": "Museus e Arte",
            "activities": ["Museu do Louvre", "Jardins das Tulherias", "Champs-Élysées"]
        }
    ]
}


class TestAIAssistantEndpoint:
    """Tests for POST /api/ai/assistant endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin (ambassador level) token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def sonhador_user(self):
        """Create a sonhador level user for testing non-ambassador access"""
        import uuid
        test_email = f"test_sonhador_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register new user (will be sonhador level by default)
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "name": "Test Sonhador",
            "surname": "User",
            "password": "TestPass123"
        })
        
        if response.status_code == 200:
            return {
                "email": test_email,
                "token": response.json()["token"],
                "user_id": response.json()["user"]["user_id"]
            }
        elif response.status_code == 400 and "já registado" in response.text:
            # User exists, try login
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": test_email,
                "password": "TestPass123"
            })
            if login_resp.status_code == 200:
                return {
                    "email": test_email,
                    "token": login_resp.json()["token"],
                    "user_id": login_resp.json()["user"]["user_id"]
                }
        
        pytest.skip("Could not create sonhador test user")
    
    def test_endpoint_exists(self):
        """Test that the AI assistant endpoint exists"""
        # Without auth, should return 401
        response = requests.post(f"{BASE_URL}/api/ai/assistant", json={
            "plan": SAMPLE_PLAN,
            "message": "Test"
        })
        # Should be 401 (unauthorized) not 404 (not found)
        assert response.status_code in [401, 422], f"Endpoint should exist but require auth. Got: {response.status_code}"
        print(f"✓ Endpoint exists, returns {response.status_code} without auth")
    
    def test_requires_authentication(self):
        """Test that endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/ai/assistant", json={
            "plan": SAMPLE_PLAN,
            "message": "Sugere formas de tornar esta viagem mais economica"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("✓ Endpoint requires authentication (401 without token)")
    
    def test_returns_403_for_non_ambassador(self, sonhador_user):
        """Test that non-ambassador users get 403 Forbidden"""
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers={"Authorization": f"Bearer {sonhador_user['token']}"},
            json={
                "plan": SAMPLE_PLAN,
                "message": "Sugere formas de tornar esta viagem mais economica"
            }
        )
        assert response.status_code == 403, f"Expected 403 for non-ambassador, got {response.status_code}: {response.text}"
        data = response.json()
        assert "Embaixador" in data.get("detail", ""), f"Error should mention Embaixador: {data}"
        print(f"✓ Non-ambassador user gets 403: {data.get('detail')}")
    
    def test_ambassador_can_access(self, admin_token):
        """Test that ambassador users can access the endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plan": SAMPLE_PLAN,
                "message": "Sugere formas de tornar esta viagem mais economica"
            },
            timeout=45  # LLM can take time
        )
        assert response.status_code == 200, f"Expected 200 for ambassador, got {response.status_code}: {response.text}"
        print(f"✓ Ambassador user can access endpoint (200)")
    
    def test_response_structure(self, admin_token):
        """Test that response has correct JSON structure"""
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plan": SAMPLE_PLAN,
                "message": "Sugere experiencias unicas em Paris"
            },
            timeout=45
        )
        assert response.status_code == 200, f"Request failed: {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check required fields
        assert "response" in data, f"Missing 'response' field: {data}"
        assert "suggestions" in data, f"Missing 'suggestions' field: {data}"
        assert "can_apply" in data, f"Missing 'can_apply' field: {data}"
        assert "apply_prompt" in data, f"Missing 'apply_prompt' field: {data}"
        
        # Check types
        assert isinstance(data["response"], str), f"'response' should be string: {type(data['response'])}"
        assert isinstance(data["suggestions"], list), f"'suggestions' should be list: {type(data['suggestions'])}"
        assert isinstance(data["can_apply"], bool), f"'can_apply' should be bool: {type(data['can_apply'])}"
        
        print(f"✓ Response has correct structure:")
        print(f"  - response: {data['response'][:50]}...")
        print(f"  - suggestions: {len(data['suggestions'])} items")
        print(f"  - can_apply: {data['can_apply']}")
        print(f"  - apply_prompt: {data['apply_prompt']}")
    
    def test_requires_plan_and_message(self, admin_token):
        """Test that plan and message are required"""
        # Missing plan
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"message": "Test message"}
        )
        assert response.status_code == 400, f"Expected 400 for missing plan, got {response.status_code}"
        
        # Missing message
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"plan": SAMPLE_PLAN}
        )
        assert response.status_code == 400, f"Expected 400 for missing message, got {response.status_code}"
        
        print("✓ Endpoint validates required fields (plan and message)")
    
    def test_quick_action_cheaper(self, admin_token):
        """Test 'Tornar mais barato' quick action"""
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plan": SAMPLE_PLAN,
                "message": "Sugere formas de tornar esta viagem mais economica, mantendo as experiencias essenciais."
            },
            timeout=45
        )
        assert response.status_code == 200, f"Request failed: {response.status_code}"
        data = response.json()
        assert len(data.get("suggestions", [])) > 0, "Should return suggestions"
        print(f"✓ 'Tornar mais barato' returns {len(data['suggestions'])} suggestions")
    
    def test_quick_action_experiences(self, admin_token):
        """Test 'Experiencias unicas' quick action"""
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "plan": SAMPLE_PLAN,
                "message": "Sugere experiencias unicas e autenticas que nao estejam no roteiro atual."
            },
            timeout=45
        )
        assert response.status_code == 200, f"Request failed: {response.status_code}"
        data = response.json()
        assert len(data.get("suggestions", [])) > 0, "Should return suggestions"
        print(f"✓ 'Experiencias unicas' returns {len(data['suggestions'])} suggestions")


class TestAmbassadorProgressEndpoint:
    """Tests for ambassador progress endpoint to verify feature flags"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin (ambassador level) token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    def test_ambassador_progress_includes_ai_assistant_feature(self, admin_token):
        """Test that ambassador progress shows ai_assistant feature"""
        response = requests.get(
            f"{BASE_URL}/api/ambassador/progress",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Request failed: {response.status_code}"
        
        data = response.json()
        assert "premium_features" in data, f"Missing premium_features: {data}"
        assert "ai_assistant" in data["premium_features"], f"Missing ai_assistant feature: {data['premium_features']}"
        
        # For ambassador user, ai_assistant should be True
        if data.get("is_ambassador"):
            assert data["premium_features"]["ai_assistant"] == True, "Ambassador should have ai_assistant enabled"
            print("✓ Ambassador has ai_assistant feature enabled")
        else:
            print(f"⚠ User is not ambassador (level check needed)")
    
    def test_ambassador_features_endpoint(self, admin_token):
        """Test the /ambassador/features endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ambassador/features",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Request failed: {response.status_code}"
        
        data = response.json()
        assert "is_ambassador" in data, f"Missing is_ambassador: {data}"
        assert "features" in data, f"Missing features: {data}"
        assert "ai_assistant" in data["features"], f"Missing ai_assistant in features: {data['features']}"
        
        print(f"✓ Ambassador features endpoint works:")
        print(f"  - is_ambassador: {data['is_ambassador']}")
        print(f"  - ai_assistant: {data['features']['ai_assistant']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
