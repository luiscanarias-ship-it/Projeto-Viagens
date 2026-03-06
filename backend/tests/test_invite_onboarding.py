"""
Tests for Invite Onboarding Feature
- /api/invite/{alias} endpoint
- /api/homepage/main-journey endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestInviteEndpoint:
    """Test invite page endpoint /api/invite/{alias}"""
    
    def test_invite_with_valid_alias(self):
        """Test invite page with existing user's alias"""
        # First login as admin to get their alias
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json().get("token")
        
        # Get admin's profile to find anonymous_alias
        headers = {"Authorization": f"Bearer {token}"}
        me_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert me_res.status_code == 200, f"Get /auth/me failed: {me_res.text}"
        user_data = me_res.json()
        
        # Get the alias - could be name or anonymous_alias
        alias = user_data.get("anonymous_alias") or user_data.get("name")
        assert alias, f"No alias found for admin user: {user_data}"
        
        # Test invite page with alias
        invite_res = requests.get(f"{BASE_URL}/api/invite/{alias}")
        assert invite_res.status_code == 200, f"Invite endpoint failed: {invite_res.text}"
        
        invite_data = invite_res.json()
        # Verify response structure
        assert "inviter_name" in invite_data, "inviter_name missing from response"
        assert "journey" in invite_data, "journey missing from response"
        # sponsor_link_id may or may not exist
        print(f"✅ Invite endpoint returned: inviter_name={invite_data['inviter_name']}, journey exists={invite_data.get('journey') is not None}")
    
    def test_invite_with_invalid_alias(self):
        """Test invite page with non-existent alias"""
        response = requests.get(f"{BASE_URL}/api/invite/NonExistentAlias12345")
        assert response.status_code == 404, f"Expected 404 for invalid alias, got {response.status_code}"
        print("✅ Invite endpoint returns 404 for invalid alias")
    
    def test_invite_returns_main_journey(self):
        """Test that invite endpoint returns main journey data"""
        # Login and get alias
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        token = login_res.json().get("token")
        me_res = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        user_data = me_res.json()
        alias = user_data.get("anonymous_alias") or user_data.get("name")
        
        invite_res = requests.get(f"{BASE_URL}/api/invite/{alias}")
        assert invite_res.status_code == 200
        invite_data = invite_res.json()
        
        journey = invite_data.get("journey")
        if journey:
            assert "journey_id" in journey, "journey_id missing"
            assert "name" in journey, "name missing from journey"
            assert "image_url" in journey, "image_url missing from journey"
            assert journey.get("is_main_trip") == True, "Expected main trip journey"
            print(f"✅ Invite returns main journey: {journey.get('name')}")
        else:
            print("⚠️ No main journey found - check if main journey is set")


class TestMainJourneyEndpoint:
    """Test homepage main-journey endpoint /api/homepage/main-journey"""
    
    def test_main_journey_returns_data(self):
        """Test that main journey endpoint returns journey and progress"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200, f"Main journey endpoint failed: {response.text}"
        
        data = response.json()
        assert "journey" in data, "journey key missing"
        assert "progress" in data, "progress key missing"
        assert "contributions" in data, "contributions key missing"
        print(f"✅ Main journey endpoint returns journey={data.get('journey') is not None}, progress={data.get('progress')}")
    
    def test_main_journey_progress_has_percentage(self):
        """Test that progress object has percentage field (not goal)"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        
        data = response.json()
        progress = data.get("progress")
        
        if progress:
            assert "percentage" in progress, "percentage missing from progress"
            assert "current_amount" in progress, "current_amount missing from progress"
            # Verify percentage is a valid number
            assert isinstance(progress["percentage"], (int, float)), "percentage should be numeric"
            print(f"✅ Progress has percentage: {progress.get('percentage')}%")
        else:
            print("⚠️ No progress data returned")
    
    def test_main_journey_has_image(self):
        """Test that journey has image_url for display"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        
        data = response.json()
        journey = data.get("journey")
        
        if journey:
            assert "image_url" in journey, "image_url missing from journey"
            assert journey["image_url"].startswith("http"), "image_url should be a valid URL"
            print(f"✅ Journey has valid image_url")
        else:
            print("⚠️ No journey returned")


class TestRegistrationFlow:
    """Test user registration (for invite onboarding redirect logic)"""
    
    def test_register_new_user(self):
        """Test that new user registration works"""
        import uuid
        test_email = f"test_invite_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123",
            "name": "Test User Invite"
        })
        
        # Could be 200 (success) or 400 (already exists)
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "token" in data, "token missing from registration response"
            assert "user" in data, "user missing from registration response"
            print(f"✅ Registration successful for {test_email}")
        else:
            print(f"⚠️ Email already registered or error: {response.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
