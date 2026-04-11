"""
Test suite for contribution descriptions feature in 4Luis platform.
Tests the backend API endpoints for:
- /api/homepage/main-journey returning contribution_descriptions field
- /api/journeys/{journey_id} returning contribution_descriptions field
- /api/admin/journeys PUT endpoint accepting and saving contribution_descriptions
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://comeback-point.preview.emergentagent.com')
API = f"{BASE_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"


class TestContributionDescriptions:
    """Test contribution descriptions API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{API}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.auth_token = token
        else:
            self.auth_token = None
        
        yield
        
        self.session.close()
    
    def test_homepage_main_journey_returns_contribution_descriptions(self):
        """Test that /api/homepage/main-journey returns contribution_descriptions field"""
        response = self.session.get(f"{API}/homepage/main-journey")
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Data assertions
        data = response.json()
        assert "journey" in data, "Response should contain 'journey' key"
        
        journey = data["journey"]
        assert journey is not None, "Journey should not be null"
        
        # Check contribution_descriptions field exists (can be null for some journeys)
        assert "contribution_descriptions" in journey, "Journey should have 'contribution_descriptions' field"
        
        # For China journey (main journey), it should have descriptions
        if journey.get("journey_id") == "journey_china001":
            assert journey["contribution_descriptions"] is not None, "China journey should have contribution descriptions"
            assert isinstance(journey["contribution_descriptions"], dict), "contribution_descriptions should be a dict"
            
            # Verify expected amounts
            expected_amounts = ["10", "20", "50", "100", "200", "500", "1000"]
            for amt in expected_amounts:
                assert amt in journey["contribution_descriptions"], f"Missing description for €{amt}"
        
        print(f"✅ Main journey {journey.get('journey_id')} returns contribution_descriptions")
    
    def test_journey_detail_returns_contribution_descriptions(self):
        """Test that /api/journeys/{journey_id} returns contribution_descriptions field"""
        # Test with China journey (has descriptions)
        response = self.session.get(f"{API}/journeys/journey_china001")
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Data assertions
        journey = response.json()
        assert "contribution_descriptions" in journey, "Journey should have 'contribution_descriptions' field"
        assert journey["contribution_descriptions"] is not None, "China journey should have contribution descriptions"
        
        # Verify specific descriptions
        descs = journey["contribution_descriptions"]
        assert "10" in descs and "café" in descs["10"].lower(), "€10 should have café description"
        assert "50" in descs and "alojamento" in descs["50"].lower(), "€50 should have alojamento description"
        assert "1000" in descs and "impulso" in descs["1000"].lower(), "€1000 should have impulso description"
        
        print("✅ Journey detail returns contribution_descriptions with correct values")
    
    def test_journey_without_descriptions_returns_null(self):
        """Test that journeys without descriptions return null for contribution_descriptions"""
        # Test with Japan journey (no descriptions)
        response = self.session.get(f"{API}/journeys/journey_japan001")
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Data assertions
        journey = response.json()
        # contribution_descriptions should be null or not present
        contrib_descs = journey.get("contribution_descriptions")
        assert contrib_descs is None or contrib_descs == {}, "Japan journey should have no contribution descriptions"
        
        print("✅ Japan journey correctly returns null/empty contribution_descriptions")
    
    def test_admin_can_read_contribution_descriptions(self):
        """Test that admin can read journey with contribution_descriptions"""
        if not self.auth_token:
            pytest.skip("Admin authentication failed")
        
        response = self.session.get(f"{API}/admin/journeys")
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Data assertions
        journeys = response.json()
        assert isinstance(journeys, list), "Response should be a list of journeys"
        
        # Find China journey
        china_journey = next((j for j in journeys if j.get("journey_id") == "journey_china001"), None)
        assert china_journey is not None, "China journey should be in admin journeys list"
        
        # Verify contribution_descriptions
        assert "contribution_descriptions" in china_journey, "Journey should have contribution_descriptions field"
        if china_journey["contribution_descriptions"]:
            assert "10" in china_journey["contribution_descriptions"], "Should have €10 description"
        
        print("✅ Admin can read journeys with contribution_descriptions")
    
    def test_admin_can_update_contribution_descriptions(self):
        """Test that admin can update contribution_descriptions via PUT endpoint"""
        if not self.auth_token:
            pytest.skip("Admin authentication failed")
        
        # Prepare update data with modified descriptions
        test_descriptions = {
            "10": "Test description for €10",
            "20": "Test description for €20",
            "50": "Test description for €50",
            "100": "Test description for €100",
            "200": "Test description for €200",
            "500": "Test description for €500",
            "1000": "Test description for €1000"
        }
        
        # Update journey with new contribution_descriptions
        update_response = self.session.put(
            f"{API}/admin/journeys/journey_china001",
            json={"contribution_descriptions": test_descriptions}
        )
        
        # Status assertion
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        # Verify the update was saved
        verify_response = self.session.get(f"{API}/journeys/journey_china001")
        assert verify_response.status_code == 200
        
        updated_journey = verify_response.json()
        assert "contribution_descriptions" in updated_journey
        assert updated_journey["contribution_descriptions"]["10"] == "Test description for €10"
        
        print("✅ Admin successfully updated contribution_descriptions")
        
        # Restore original descriptions
        original_descriptions = {
            "10": "Um café com vista para a Grande Muralha",
            "20": "Um almoço numa pequena cidade chinesa",
            "50": "Uma noite de alojamento",
            "100": "Uma viagem de comboio entre cidades",
            "200": "Explorar um parque natural chinês",
            "500": "Vários dias de descoberta cultural",
            "1000": "Um grande impulso para este sonho"
        }
        
        restore_response = self.session.put(
            f"{API}/admin/journeys/journey_china001",
            json={"contribution_descriptions": original_descriptions}
        )
        assert restore_response.status_code == 200, "Failed to restore original descriptions"
        print("✅ Restored original contribution_descriptions")
    
    def test_contribution_descriptions_with_empty_values(self):
        """Test that admin can clear specific contribution descriptions"""
        if not self.auth_token:
            pytest.skip("Admin authentication failed")
        
        # Test updating with partial descriptions (some empty)
        partial_descriptions = {
            "10": "Test €10 description",
            "20": "",  # Empty - should be allowed
            "50": "Test €50 description"
            # 100, 200, 500, 1000 not included
        }
        
        update_response = self.session.put(
            f"{API}/admin/journeys/journey_china001",
            json={"contribution_descriptions": partial_descriptions}
        )
        
        # Status assertion - should accept partial data
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        
        print("✅ Admin can update with partial contribution_descriptions")
        
        # Restore original
        original_descriptions = {
            "10": "Um café com vista para a Grande Muralha",
            "20": "Um almoço numa pequena cidade chinesa",
            "50": "Uma noite de alojamento",
            "100": "Uma viagem de comboio entre cidades",
            "200": "Explorar um parque natural chinês",
            "500": "Vários dias de descoberta cultural",
            "1000": "Um grande impulso para este sonho"
        }
        self.session.put(
            f"{API}/admin/journeys/journey_china001",
            json={"contribution_descriptions": original_descriptions}
        )


class TestJourneyModel:
    """Test that Journey model includes contribution_descriptions field"""
    
    def test_journey_model_field_exists(self):
        """Verify contribution_descriptions field is returned in journey responses"""
        response = requests.get(f"{API}/journeys/journey_china001")
        assert response.status_code == 200
        
        journey = response.json()
        
        # Check all expected journey fields exist
        expected_fields = [
            "journey_id", "name", "poetic_name", "description",
            "emotional_message", "image_url", "goal_amount",
            "current_amount", "is_active", "contribution_descriptions"
        ]
        
        for field in expected_fields:
            assert field in journey, f"Missing field: {field}"
        
        print("✅ Journey model includes all expected fields including contribution_descriptions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
