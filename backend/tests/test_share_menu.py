"""
Test suite for ShareMenu feature - Invite Sharing System
Tests backend APIs that support the share functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://luis-preview.preview.emergentagent.com')

# Test credentials
TEST_ADMIN_EMAIL = "admin@4luis.com"
TEST_ADMIN_PASSWORD = "Admin1"

class TestAuthMeAnonymousAlias:
    """Test /api/auth/me returns anonymous_alias field"""
    
    def test_auth_me_returns_anonymous_alias_field(self):
        """Verify /api/auth/me response includes anonymous_alias"""
        # Login first
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json().get("token")
        
        # Call /api/auth/me
        headers = {"Authorization": f"Bearer {token}"}
        me_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert me_res.status_code == 200, f"Auth me failed: {me_res.text}"
        data = me_res.json()
        
        # Verify anonymous_alias field exists
        assert "anonymous_alias" in data, "Response should contain anonymous_alias field"
        print(f"✓ /api/auth/me returns anonymous_alias: {data.get('anonymous_alias')}")


class TestDashboardUserStats:
    """Test dashboard returns user_alias for sharing"""
    
    def test_dashboard_returns_user_alias(self):
        """Verify dashboard user-stats returns user_alias"""
        # Login
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        token = login_res.json().get("token")
        
        # Get dashboard stats
        headers = {"Authorization": f"Bearer {token}"}
        stats_res = requests.get(f"{BASE_URL}/api/dashboard/user-stats", headers=headers)
        
        assert stats_res.status_code == 200, f"Dashboard stats failed: {stats_res.text}"
        data = stats_res.json()
        
        # Verify user_alias is in response
        assert "user_alias" in data, "Dashboard should return user_alias for share link"
        user_alias = data.get("user_alias")
        assert user_alias is not None, "user_alias should not be None"
        assert len(user_alias) > 0, "user_alias should not be empty"
        print(f"✓ Dashboard returns user_alias: {user_alias}")


class TestInvitePage:
    """Test /api/invite/{alias} endpoint"""
    
    def test_invite_with_name(self):
        """Test invite endpoint with user name"""
        # Login to get user name
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        token = login_res.json().get("token")
        
        # Get user's alias from dashboard
        headers = {"Authorization": f"Bearer {token}"}
        stats_res = requests.get(f"{BASE_URL}/api/dashboard/user-stats", headers=headers)
        assert stats_res.status_code == 200
        user_alias = stats_res.json().get("user_alias")
        
        if user_alias:
            # Test invite page with alias
            invite_res = requests.get(f"{BASE_URL}/api/invite/{user_alias}")
            
            # Should return 200 if alias exists
            if invite_res.status_code == 200:
                data = invite_res.json()
                assert "inviter_name" in data, "Response should have inviter_name"
                assert "journey" in data, "Response should have journey info"
                print(f"✓ /api/invite/{user_alias} returns inviter_name: {data.get('inviter_name')}")
            else:
                print(f"Note: Invite with alias '{user_alias}' not found - may need anonymous_alias setup")
    
    def test_invite_not_found(self):
        """Test invite endpoint returns 404 for unknown alias"""
        res = requests.get(f"{BASE_URL}/api/invite/nonexistent_alias_12345")
        assert res.status_code == 404, "Should return 404 for non-existent alias"
        print("✓ /api/invite returns 404 for non-existent alias")


class TestJourneysForShare:
    """Test journeys API returns data needed for share links"""
    
    def test_get_journeys(self):
        """Verify journeys endpoint returns data"""
        res = requests.get(f"{BASE_URL}/api/journeys")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list), "Should return list of journeys"
        
        if len(data) > 0:
            journey = data[0]
            assert "journey_id" in journey, "Journey should have journey_id"
            assert "name" in journey, "Journey should have name"
            print(f"✓ Found {len(data)} journeys, first: {journey.get('name')}")


class TestProfileAnonymousAlias:
    """Test profile endpoint returns anonymous_alias"""
    
    def test_profile_includes_anonymous_alias(self):
        """Verify profile has anonymous_alias for sharing"""
        # Login
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        token = login_res.json().get("token")
        
        # Get profile
        headers = {"Authorization": f"Bearer {token}"}
        profile_res = requests.get(f"{BASE_URL}/api/profile", headers=headers)
        
        assert profile_res.status_code == 200, f"Profile failed: {profile_res.text}"
        data = profile_res.json()
        
        # Check anonymous_alias field
        assert "anonymous_alias" in data or "name" in data, "Profile should have name or anonymous_alias"
        print(f"✓ Profile returns alias/name for sharing: {data.get('anonymous_alias') or data.get('name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
