"""
Test suite for backend refactoring and new features:
1. Backend refactoring (config, models, auth, email_service extracted from server.py)
2. Notification endpoints CRUD
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"


class TestHealthAndRefactoring:
    """Test that the refactored backend is working correctly"""
    
    def test_backend_health(self):
        """Test basic backend health"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✅ Backend health check passed")
    
    def test_homepage_main_journey_after_refactoring(self):
        """Test /api/homepage/main-journey returns data correctly after refactoring"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        data = response.json()
        # Should have journey data
        assert "journey" in data or "name" in data or "journey_id" in data
        print(f"✅ Homepage main-journey API working - returned data: {list(data.keys())[:5]}...")
    
    def test_contributions_config_after_refactoring(self):
        """Test /api/contributions/config returns configuration correctly"""
        response = requests.get(f"{BASE_URL}/api/contributions/config")
        assert response.status_code == 200
        data = response.json()
        assert "fixed_amounts" in data
        assert "payment_methods" in data
        assert "crypto_types" in data
        print(f"✅ Contributions config API working - fixed_amounts: {data['fixed_amounts']}")


class TestAuthentication:
    """Test authentication after refactoring"""
    
    def test_admin_login(self):
        """Test admin login works with correct credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True
        print(f"✅ Admin login successful - user_id: {data['user']['user_id']}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        print("✅ Invalid credentials correctly rejected")
    
    def test_auth_me_with_token(self):
        """Test /api/auth/me returns user data when authenticated"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        token = login_response.json()["token"]
        
        # Then check /auth/me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✅ Auth/me endpoint working - user: {data['name']}")


class TestNotificationsEndpoints:
    """Test notification CRUD endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_notifications(self):
        """Test GET /api/notifications returns notifications list and unread_count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        assert isinstance(data["notifications"], list)
        assert isinstance(data["unread_count"], int)
        print(f"✅ GET /api/notifications working - count: {len(data['notifications'])}, unread: {data['unread_count']}")
    
    def test_mark_all_notifications_read(self):
        """Test PUT /api/notifications/read-all marks all as read"""
        response = requests.put(
            f"{BASE_URL}/api/notifications/read-all",
            headers=self.headers
        )
        assert response.status_code == 200
        print("✅ PUT /api/notifications/read-all working")
        
        # Verify unread_count is now 0
        check_response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        data = check_response.json()
        assert data["unread_count"] == 0
        print(f"✅ After marking all read, unread_count is 0")
    
    def test_notifications_require_auth(self):
        """Test notifications endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 401
        print("✅ Notifications endpoint correctly requires authentication")


class TestJourneyEndpoints:
    """Test journey endpoints after refactoring"""
    
    def test_get_journeys(self):
        """Test GET /api/journeys returns list of journeys"""
        response = requests.get(f"{BASE_URL}/api/journeys")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/journeys working - found {len(data)} journeys")
    
    def test_get_journey_by_id(self):
        """Test GET /api/journeys/{journey_id} returns journey details"""
        # First get list to find a journey ID
        list_response = requests.get(f"{BASE_URL}/api/journeys")
        journeys = list_response.json()
        
        if journeys:
            journey_id = journeys[0]["journey_id"]
            response = requests.get(f"{BASE_URL}/api/journeys/{journey_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["journey_id"] == journey_id
            print(f"✅ GET /api/journeys/{journey_id} working - name: {data.get('name')}")
        else:
            print("⚠️ No journeys found to test individual journey endpoint")
    
    def test_get_journey_progress(self):
        """Test GET /api/journeys/{journey_id}/progress returns progress data"""
        # First get list to find a journey ID
        list_response = requests.get(f"{BASE_URL}/api/journeys")
        journeys = list_response.json()
        
        if journeys:
            journey_id = journeys[0]["journey_id"]
            response = requests.get(f"{BASE_URL}/api/journeys/{journey_id}/progress")
            assert response.status_code == 200
            data = response.json()
            assert "percentage" in data
            assert "contributor_count" in data
            print(f"✅ GET /api/journeys/{journey_id}/progress working - percentage: {data['percentage']}%")
        else:
            print("⚠️ No journeys found to test progress endpoint")


class TestModulesImport:
    """Test that refactored modules are correctly imported and working"""
    
    def test_stripe_config_endpoint(self):
        """Test /api/stripe/config works (uses config.py)"""
        response = requests.get(f"{BASE_URL}/api/stripe/config")
        assert response.status_code == 200
        data = response.json()
        assert "publishable_key" in data
        print("✅ Stripe config endpoint working (config.py imported correctly)")
    
    def test_payment_info_endpoint(self):
        """Test /api/contributions/payment-info works (uses config.py constants)"""
        response = requests.get(f"{BASE_URL}/api/contributions/payment-info")
        assert response.status_code == 200
        data = response.json()
        assert "mbway" in data
        assert "crypto" in data
        print("✅ Payment info endpoint working (config.py constants used correctly)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
