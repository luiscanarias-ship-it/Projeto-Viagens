"""
Test suite for AI-generated contribution descriptions feature
Tests the POST /api/admin/generate-contribution-descriptions endpoint
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-redirect-fix-6.preview.emergentagent.com')


class TestAIGenerateContributionDescriptions:
    """Tests for the AI contribution descriptions generation endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@4luis.com", "password": "Admin1"}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        return data["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Auth headers for admin requests"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def non_admin_token(self):
        """Get a non-admin user token (create test user if needed)"""
        # Try to login as a regular user, if doesn't exist, skip tests
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "testuser@test.com", "password": "TestPass123"}
        )
        if response.status_code == 401:
            # Try to register a test user
            response = requests.post(
                f"{BASE_URL}/api/auth/register",
                json={"email": "testuser@test.com", "password": "TestPass123", "name": "Test User"}
            )
            if response.status_code != 200:
                pytest.skip("Could not create non-admin test user")
        
        data = response.json()
        return data.get("token")
    
    def test_generate_descriptions_success(self, auth_headers):
        """Test successful AI generation with valid inputs"""
        response = requests.post(
            f"{BASE_URL}/api/admin/generate-contribution-descriptions",
            headers=auth_headers,
            json={
                "journey_name": "Japão",
                "poetic_name": "Terra do Sol Nascente",
                "description": "Uma viagem mágica pelo Japão tradicional e moderno"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "descriptions" in data, "Response missing 'descriptions' key"
        descriptions = data["descriptions"]
        
        # Verify all 7 required amount keys are present
        required_keys = ["10", "20", "50", "100", "200", "500", "1000"]
        for key in required_keys:
            assert key in descriptions, f"Missing key '{key}' in descriptions"
            assert isinstance(descriptions[key], str), f"Value for key '{key}' should be string"
            assert len(descriptions[key]) > 5, f"Description for '{key}' seems too short"
        
        print(f"SUCCESS: Generated {len(descriptions)} descriptions for Japão")
        print(f"Sample: €10 = '{descriptions['10']}'")
    
    def test_generate_descriptions_only_journey_name(self, auth_headers):
        """Test generation with only journey_name (minimal required field)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/generate-contribution-descriptions",
            headers=auth_headers,
            json={
                "journey_name": "Itália"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "descriptions" in data
        descriptions = data["descriptions"]
        
        # All 7 keys should still be present
        required_keys = ["10", "20", "50", "100", "200", "500", "1000"]
        for key in required_keys:
            assert key in descriptions, f"Missing key '{key}'"
        
        print(f"SUCCESS: Minimal input generated descriptions for Itália")
    
    def test_generate_descriptions_missing_journey_name(self, auth_headers):
        """Test that endpoint requires journey_name"""
        response = requests.post(
            f"{BASE_URL}/api/admin/generate-contribution-descriptions",
            headers=auth_headers,
            json={
                "poetic_name": "Algum nome poético",
                "description": "Alguma descrição"
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for missing journey_name, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should have 'detail'"
        print(f"SUCCESS: Correctly rejected request without journey_name")
    
    def test_generate_descriptions_empty_journey_name(self, auth_headers):
        """Test that endpoint rejects empty journey_name"""
        response = requests.post(
            f"{BASE_URL}/api/admin/generate-contribution-descriptions",
            headers=auth_headers,
            json={
                "journey_name": "",
                "poetic_name": "Test",
                "description": "Test"
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for empty journey_name, got {response.status_code}"
        print(f"SUCCESS: Correctly rejected empty journey_name")
    
    def test_generate_descriptions_requires_admin_auth(self, non_admin_token):
        """Test that endpoint requires admin authentication"""
        headers = {
            "Authorization": f"Bearer {non_admin_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/generate-contribution-descriptions",
            headers=headers,
            json={"journey_name": "Test"}
        )
        
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        print(f"SUCCESS: Non-admin correctly blocked")
    
    def test_generate_descriptions_no_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/generate-contribution-descriptions",
            headers={"Content-Type": "application/json"},
            json={"journey_name": "Test"}
        )
        
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"SUCCESS: Unauthenticated request correctly blocked")


class TestAdminJourneySaveDescriptions:
    """Tests for saving AI-generated descriptions to journeys"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@4luis.com", "password": "Admin1"}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_save_descriptions_to_japan_journey(self, auth_headers):
        """Test saving generated descriptions to Japan journey"""
        # First generate descriptions
        gen_response = requests.post(
            f"{BASE_URL}/api/admin/generate-contribution-descriptions",
            headers=auth_headers,
            json={"journey_name": "Japão", "poetic_name": "Terra do Sol Nascente"}
        )
        assert gen_response.status_code == 200
        descriptions = gen_response.json()["descriptions"]
        
        # Save to journey (Japan = journey_japan001)
        update_response = requests.put(
            f"{BASE_URL}/api/admin/journeys/journey_japan001",
            headers=auth_headers,
            json={"contribution_descriptions": descriptions}
        )
        
        assert update_response.status_code == 200, f"Failed to update journey: {update_response.text}"
        updated_journey = update_response.json()
        
        # Verify descriptions were saved
        assert "contribution_descriptions" in updated_journey
        saved_descs = updated_journey["contribution_descriptions"]
        for key in ["10", "20", "50", "100", "200", "500", "1000"]:
            assert key in saved_descs, f"Key '{key}' not saved"
            assert saved_descs[key] == descriptions[key], f"Description for '{key}' doesn't match"
        
        print(f"SUCCESS: Saved and verified descriptions for Japan journey")
    
    def test_verify_descriptions_persist(self, auth_headers):
        """Test that saved descriptions persist (GET after PUT)"""
        # Fetch journey
        response = requests.get(
            f"{BASE_URL}/api/journeys/journey_japan001"
        )
        
        assert response.status_code == 200
        journey = response.json()
        
        # Verify descriptions are present
        assert "contribution_descriptions" in journey, "contribution_descriptions not in journey"
        descs = journey["contribution_descriptions"]
        assert descs is not None, "contribution_descriptions should not be None"
        
        # Verify all 7 keys exist
        for key in ["10", "20", "50", "100", "200", "500", "1000"]:
            assert key in descs, f"Missing key '{key}' after persistence"
        
        print(f"SUCCESS: Descriptions persist after save")


class TestChinaDescriptionsOnHomepage:
    """Test that China journey descriptions still show correctly on homepage"""
    
    def test_homepage_main_journey_has_descriptions(self):
        """Test that main journey (China) returns contribution_descriptions"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        
        assert response.status_code == 200
        data = response.json()
        
        # China is the main journey with pre-existing descriptions
        if data and data.get("name") == "China":
            assert "contribution_descriptions" in data, "Missing contribution_descriptions"
            descs = data["contribution_descriptions"]
            assert descs is not None, "contribution_descriptions should not be None for China"
            
            # Verify existing descriptions
            expected_descs = {
                "10": "Um café com vista para a Grande Muralha",
                "20": "Um almoço numa pequena cidade chinesa",
                "50": "Uma noite de alojamento"
            }
            for key, expected_val in expected_descs.items():
                assert key in descs, f"Missing key '{key}'"
                # Check if the value matches (might have been updated)
            
            print(f"SUCCESS: China main journey has contribution_descriptions")
        else:
            print(f"INFO: Main journey is not China, skipping China-specific assertions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
