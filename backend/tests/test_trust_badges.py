# Test Trust Badge System - Trust levels: sonhador, verificado, embaixador
# Tests: Admin user level management and journey detail enrichment with ambassador_info

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://dynamic-itinerary-1.preview.emergentagent.com').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"

class TestTrustBadgeSystem:
    """Test trust badge system with 3 levels: sonhador, verificado, embaixador"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin JWT token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_journey_with_ambassador_info(self):
        """Test GET /api/journeys/{journey_id} returns ambassador_info with member_since"""
        # Use the test journey from the review request
        journey_id = "journey_japao_amb001"
        response = requests.get(f"{BASE_URL}/api/journeys/{journey_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"Journey data: {data.get('name')}")
        
        # Check ambassador_info is present
        ambassador_info = data.get("ambassador_info")
        assert ambassador_info is not None, "ambassador_info should be present in response"
        
        # Check ambassador_info fields
        assert "display_name" in ambassador_info, "ambassador_info should have display_name"
        assert "level" in ambassador_info, "ambassador_info should have level"
        assert "member_since" in ambassador_info, "ambassador_info should have member_since"
        
        print(f"Ambassador Info: display_name={ambassador_info.get('display_name')}, level={ambassador_info.get('level')}, member_since={ambassador_info.get('member_since')}")
        
        # Verify level is one of the valid trust levels
        assert ambassador_info["level"] in ["sonhador", "verificado", "embaixador"], f"Invalid level: {ambassador_info['level']}"
    
    def test_admin_update_user_level_to_sonhador(self, admin_token):
        """Test PUT /api/admin/users/{user_id}/level - set to sonhador"""
        # First get a test user from the users dashboard
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        dashboard_response = requests.get(f"{BASE_URL}/api/admin/users/dashboard", headers=headers)
        assert dashboard_response.status_code == 200, f"Dashboard failed: {dashboard_response.status_code}"
        
        users = dashboard_response.json().get("users", [])
        # Find a non-admin user to test with
        test_user = None
        for user in users:
            if not user.get("is_admin"):
                test_user = user
                break
        
        if not test_user:
            pytest.skip("No non-admin user found for testing")
        
        user_id = test_user["user_id"]
        print(f"Testing with user: {test_user.get('name')}, current level: {test_user.get('level')}")
        
        # Test updating to sonhador
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}/level",
            json={"level": "sonhador"},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("level") == "sonhador", f"Expected level 'sonhador', got {data.get('level')}"
        print(f"SUCCESS: User level updated to sonhador")
    
    def test_admin_update_user_level_to_verificado(self, admin_token):
        """Test PUT /api/admin/users/{user_id}/level - set to verificado"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        dashboard_response = requests.get(f"{BASE_URL}/api/admin/users/dashboard", headers=headers)
        users = dashboard_response.json().get("users", [])
        
        test_user = next((u for u in users if not u.get("is_admin")), None)
        if not test_user:
            pytest.skip("No non-admin user found")
        
        user_id = test_user["user_id"]
        
        # Test updating to verificado
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}/level",
            json={"level": "verificado"},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("level") == "verificado", f"Expected level 'verificado', got {data.get('level')}"
        print(f"SUCCESS: User level updated to verificado")
    
    def test_admin_update_user_level_to_embaixador(self, admin_token):
        """Test PUT /api/admin/users/{user_id}/level - set to embaixador"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        dashboard_response = requests.get(f"{BASE_URL}/api/admin/users/dashboard", headers=headers)
        users = dashboard_response.json().get("users", [])
        
        test_user = next((u for u in users if not u.get("is_admin")), None)
        if not test_user:
            pytest.skip("No non-admin user found")
        
        user_id = test_user["user_id"]
        
        # Test updating to embaixador
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}/level",
            json={"level": "embaixador"},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("level") == "embaixador", f"Expected level 'embaixador', got {data.get('level')}"
        print(f"SUCCESS: User level updated to embaixador")
    
    def test_admin_update_user_level_invalid(self, admin_token):
        """Test PUT /api/admin/users/{user_id}/level with invalid level"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        dashboard_response = requests.get(f"{BASE_URL}/api/admin/users/dashboard", headers=headers)
        users = dashboard_response.json().get("users", [])
        
        test_user = next((u for u in users if not u.get("is_admin")), None)
        if not test_user:
            pytest.skip("No non-admin user found")
        
        user_id = test_user["user_id"]
        
        # Test with invalid level
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}/level",
            json={"level": "invalid_level"},
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid level, got {response.status_code}"
        print(f"SUCCESS: Invalid level rejected with 400")
    
    def test_admin_update_nonexistent_user_level(self, admin_token):
        """Test PUT /api/admin/users/{user_id}/level for non-existent user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/admin/users/user_nonexistent123/level",
            json={"level": "sonhador"},
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404 for nonexistent user, got {response.status_code}"
        print(f"SUCCESS: Non-existent user returns 404")
    
    def test_journey_ambassador_info_level_matches_user_level(self, admin_token):
        """Test that journey ambassador_info.level reflects the user's current level"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get journey with ambassador
        journey_id = "journey_japao_amb001"
        journey_response = requests.get(f"{BASE_URL}/api/journeys/{journey_id}")
        
        if journey_response.status_code != 200:
            pytest.skip(f"Journey {journey_id} not found")
        
        journey = journey_response.json()
        ambassador_info = journey.get("ambassador_info")
        
        if not ambassador_info:
            pytest.skip("Journey has no ambassador_info")
        
        ambassador_user_id = ambassador_info.get("user_id")
        if not ambassador_user_id:
            pytest.skip("No ambassador_user_id in journey")
        
        # Get user detail to verify level
        user_detail_response = requests.get(
            f"{BASE_URL}/api/admin/users/{ambassador_user_id}/detail",
            headers=headers
        )
        
        if user_detail_response.status_code == 200:
            user_detail = user_detail_response.json()
            user_level = user_detail.get("user", {}).get("level")
            journey_level = ambassador_info.get("level")
            
            print(f"User level from DB: {user_level}, Level in ambassador_info: {journey_level}")
            assert user_level == journey_level, f"User level {user_level} doesn't match ambassador_info level {journey_level}"
            print("SUCCESS: Level in ambassador_info matches user's actual level")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
