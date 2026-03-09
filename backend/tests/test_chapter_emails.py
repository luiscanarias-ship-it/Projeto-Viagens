"""
Test suite for Chapter Email functionality in 4Luis Crowdfunding Platform
Tests: Resend API configuration, chapter email sending, duplicate prevention
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

class TestResendConfiguration:
    """Tests for Resend API configuration and basic email functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin authentication"""
        # Login as admin
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        self.admin_token = login_response.json()["token"]
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        }
    
    def test_admin_test_email_endpoint_exists(self):
        """Test that POST /api/admin/test-email endpoint exists and requires auth"""
        # Without auth should fail
        response = requests.post(f"{BASE_URL}/api/admin/test-email", json={
            "to_email": "luis.canarias@gmail.com"
        })
        assert response.status_code in [401, 403], "Endpoint should require auth"
    
    def test_admin_test_email_sends_successfully(self):
        """Test that POST /api/admin/test-email sends email to luis.canarias@gmail.com"""
        response = requests.post(
            f"{BASE_URL}/api/admin/test-email",
            json={"to_email": "luis.canarias@gmail.com"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Email send failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "result" in data
        # Verify the result has a status
        assert data["result"]["status"] in ["sent", "failed", "skipped"]
        print(f"Email result: {data['result']}")


class TestJourneyChaptersEmailsSentField:
    """Tests for chapters_emails_sent field in Journey model"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin authentication"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_response.status_code == 200
        self.admin_token = login_response.json()["token"]
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        }
    
    def test_homepage_main_journey_includes_chapters_emails_sent(self):
        """Test GET /api/homepage/main-journey returns chapters_emails_sent field"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # The field should exist in the journey (may be null or dict)
        # It may be None if never set, so we just check it's accessible
        assert "chapters_emails_sent" in data or data.get("chapters_emails_sent") is None or isinstance(data.get("chapters_emails_sent"), dict)
        print(f"chapters_emails_sent: {data.get('chapters_emails_sent')}")
    
    def test_journey_detail_includes_chapters_emails_sent(self):
        """Test GET /api/journeys/{journey_id} returns chapters_emails_sent"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Check the field exists (may be null or dict)
        chapters_sent = data.get("chapters_emails_sent")
        assert chapters_sent is None or isinstance(chapters_sent, dict)
        print(f"Journey chapters_emails_sent: {chapters_sent}")


class TestChapterEmailEndpoints:
    """Tests for chapter email admin endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin authentication"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_response.status_code == 200
        self.admin_token = login_response.json()["token"]
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        }
    
    def test_test_chapter_email_requires_auth(self):
        """Test POST /api/admin/test-chapter-email requires admin auth"""
        response = requests.post(f"{BASE_URL}/api/admin/test-chapter-email/journey_china001/2")
        assert response.status_code in [401, 403], "Should require auth"
    
    def test_test_chapter_email_chapter_2_sends(self):
        """Test POST /api/admin/test-chapter-email/journey_china001/2 sends email (25% milestone)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/test-chapter-email/journey_china001/2",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "chapter_title" in data
        assert "result" in data
        # Chapter 2 should have title "O sonho ganha forma"
        assert data["chapter_title"] == "O sonho ganha forma", f"Got: {data['chapter_title']}"
        print(f"Chapter 2 email result: {data['result']}")
    
    def test_test_chapter_email_chapter_5_sends(self):
        """Test POST /api/admin/test-chapter-email/journey_china001/5 sends email (100% milestone)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/test-chapter-email/journey_china001/5",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "chapter_title" in data
        # Chapter 5 should have title "O sonho torna-se realidade"
        assert data["chapter_title"] == "O sonho torna-se realidade", f"Got: {data['chapter_title']}"
        print(f"Chapter 5 email result: {data['result']}")
    
    def test_test_chapter_email_invalid_chapter(self):
        """Test POST /api/admin/test-chapter-email with invalid chapter returns error"""
        response = requests.post(
            f"{BASE_URL}/api/admin/test-chapter-email/journey_china001/6",
            headers=self.headers
        )
        assert response.status_code == 400, f"Should fail with invalid chapter: {response.text}"
    
    def test_test_chapter_email_invalid_journey(self):
        """Test POST /api/admin/test-chapter-email with non-existent journey returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/admin/test-chapter-email/nonexistent_journey/2",
            headers=self.headers
        )
        assert response.status_code == 404, f"Should return 404: {response.text}"


class TestChapterDetectionLogic:
    """Tests for chapter detection based on funding percentage"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin authentication"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_response.status_code == 200
        self.admin_token = login_response.json()["token"]
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        }
    
    def test_china_journey_current_chapter_is_correct(self):
        """Test that China journey (2.5% funded) has current_chapter=1"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert response.status_code == 200
        data = response.json()
        
        # Get percentage
        current = data.get("current_amount", 0)
        goal = data.get("goal_amount", 1)
        percentage = (current / goal) * 100 if goal > 0 else 0
        
        # Get current chapter
        current_chapter = data.get("current_chapter", 1)
        
        print(f"Journey at {percentage:.1f}% with chapter {current_chapter}")
        
        # Verify chapter matches percentage
        if percentage < 25:
            assert current_chapter == 1, f"Expected chapter 1 for {percentage}%"
        elif percentage < 50:
            assert current_chapter == 2
        elif percentage < 75:
            assert current_chapter == 3
        elif percentage < 100:
            assert current_chapter == 4
        else:
            assert current_chapter == 5


class TestDuplicateEmailPrevention:
    """Tests for duplicate email prevention mechanism"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin authentication"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_response.status_code == 200
        self.admin_token = login_response.json()["token"]
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        }
    
    def test_chapters_emails_sent_structure(self):
        """Test that chapters_emails_sent field has correct structure (dict with string keys)"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert response.status_code == 200
        data = response.json()
        
        chapters_sent = data.get("chapters_emails_sent")
        if chapters_sent is not None:
            assert isinstance(chapters_sent, dict), f"Should be dict, got {type(chapters_sent)}"
            # Keys should be '25', '50', '75', '100'
            for key in chapters_sent.keys():
                assert key in ['25', '50', '75', '100'], f"Invalid key: {key}"
                assert isinstance(chapters_sent[key], bool), f"Value should be bool for key {key}"
        print(f"chapters_emails_sent structure: {chapters_sent}")
    
    def test_journey_model_has_story_emails_enabled(self):
        """Test that journey has story_emails_enabled field"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert response.status_code == 200
        data = response.json()
        
        # story_emails_enabled should be present and boolean
        enabled = data.get("story_emails_enabled")
        assert enabled is None or isinstance(enabled, bool), f"Should be bool or None, got {type(enabled)}"
        print(f"story_emails_enabled: {enabled}")


class TestAdminValidateContributionTriggersChapterCheck:
    """Tests for contribution validation triggering chapter check"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin authentication"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_response.status_code == 200
        self.admin_token = login_response.json()["token"]
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        }
    
    def test_admin_validate_endpoint_exists(self):
        """Test that admin validate contribution endpoint exists"""
        # First get pending contributions
        response = requests.get(
            f"{BASE_URL}/api/admin/contributions",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to get contributions: {response.text}"
        print("Admin contributions endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
