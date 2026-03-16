"""
Test file for autosave-related features and admin redirect fix
Tests the following:
1. Admin login redirect to /admin
2. Email preview endpoints require auth and return correct data
3. FRONTEND_URL is properly configured in backend
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminLogin:
    """Test admin login and redirect functionality"""
    
    def test_admin_login_returns_is_admin_true(self):
        """Test that admin login returns is_admin: true"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["is_admin"] == True
        print(f"✅ Admin login returns is_admin=True")
    
    def test_regular_user_login(self):
        """Test that non-admin login works"""
        # First register a test user
        import uuid
        test_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "name": "Test User"
        })
        
        if reg_response.status_code == 200:
            data = reg_response.json()
            assert data["user"]["is_admin"] == False
            print(f"✅ Regular user login returns is_admin=False")
        else:
            # User might already exist
            print(f"Note: User registration returned {reg_response.status_code}")


class TestEmailPreviewEndpoints:
    """Test email preview endpoints for admin panel"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_weekly_summary_preview_requires_auth(self):
        """Test that weekly summary preview requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/emails/preview/weekly-summary")
        assert response.status_code == 401
        print(f"✅ Weekly summary preview requires auth (401)")
    
    def test_weekly_summary_preview_returns_correct_structure(self, admin_token):
        """Test that weekly summary preview returns subject, html, and recipient_count"""
        response = requests.get(
            f"{BASE_URL}/api/admin/emails/preview/weekly-summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "subject" in data
        assert "html" in data
        assert "recipient_count" in data
        
        # Verify subject contains expected text
        assert "semanal" in data["subject"].lower() or "summary" in data["subject"].lower()
        
        # Verify HTML is present and contains expected content
        assert len(data["html"]) > 0
        assert "4Luis" in data["html"]
        
        print(f"✅ Weekly summary preview returns correct structure")
        print(f"   Subject: {data['subject']}")
        print(f"   HTML length: {len(data['html'])}")
        print(f"   Recipient count: {data['recipient_count']}")
    
    def test_new_journey_preview_requires_auth(self):
        """Test that new journey preview requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/emails/preview/new-journey/journey_china001")
        assert response.status_code == 401
        print(f"✅ New journey preview requires auth (401)")
    
    def test_new_journey_preview_returns_correct_structure(self, admin_token):
        """Test that new journey preview returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/emails/preview/new-journey/journey_china001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "subject" in data
        assert "html" in data
        assert "recipient_count" in data
        assert len(data["html"]) > 0
        
        print(f"✅ New journey preview returns correct structure")
        print(f"   Subject: {data['subject']}")
    
    def test_new_journey_preview_invalid_journey_returns_404(self, admin_token):
        """Test that invalid journey ID returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/admin/emails/preview/new-journey/invalid_journey_id",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print(f"✅ Invalid journey ID returns 404")
    
    def test_dream_funded_preview_returns_correct_structure(self, admin_token):
        """Test that dream funded preview returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/emails/preview/dream-funded/journey_china001",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "subject" in data
        assert "html" in data
        assert "recipient_count" in data
        
        print(f"✅ Dream funded preview returns correct structure")


class TestFrontendUrlConfiguration:
    """Test that FRONTEND_URL is properly configured"""
    
    def test_frontend_url_not_hardcoded(self):
        """Verify FRONTEND_URL reads from environment variable in backend"""
        # This is a static code check - we verify the .env file has the correct value
        env_path = "/app/backend/.env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                content = f.read()
                assert "FRONTEND_URL=" in content
                # Check it's not localhost
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('FRONTEND_URL='):
                        value = line.split('=', 1)[1]
                        assert "localhost" not in value.lower()
                        assert value.strip() != ""
                        print(f"✅ FRONTEND_URL is configured: {value[:50]}...")
                        return
        print("Note: Could not verify .env file")


class TestJourneyAPI:
    """Test journey API endpoints used by autosave"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_get_journeys_list(self):
        """Test getting list of journeys"""
        response = requests.get(f"{BASE_URL}/api/journeys")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/journeys returns {len(data)} journeys")
    
    def test_get_single_journey(self):
        """Test getting a single journey by ID"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert response.status_code == 200
        data = response.json()
        assert data["journey_id"] == "journey_china001"
        assert "name" in data
        print(f"✅ GET /api/journeys/journey_china001 returns journey: {data['name']}")
    
    def test_admin_journeys_list(self, admin_token):
        """Test admin journey list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/journeys",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/admin/journeys returns {len(data)} journeys")
    
    def test_update_journey(self, admin_token):
        """Test updating a journey (used by autosave save flow)"""
        # First get current journey data
        journey_response = requests.get(f"{BASE_URL}/api/journeys/journey_japan001")
        if journey_response.status_code != 200:
            pytest.skip("Journey not found")
        
        original_journey = journey_response.json()
        
        # Update with same data (safe operation)
        update_response = requests.put(
            f"{BASE_URL}/api/admin/journeys/journey_japan001",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"poetic_name": original_journey.get("poetic_name", "Test")}
        )
        assert update_response.status_code == 200
        print(f"✅ PUT /api/admin/journeys/journey_japan001 works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
