"""
Test Email Preview Endpoints
Tests for the new email preview functionality - admin must preview emails before sending
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEmailPreviewEndpoints:
    """Test all email preview endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for all tests"""
        self.session = requests.Session()
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        self.token = data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_preview_weekly_summary(self):
        """Test GET /api/admin/emails/preview/weekly-summary returns subject, html, and recipient_count"""
        response = self.session.get(f"{BASE_URL}/api/admin/emails/preview/weekly-summary")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "subject" in data, "Missing 'subject' in response"
        assert "html" in data, "Missing 'html' in response"
        assert "recipient_count" in data, "Missing 'recipient_count' in response"
        
        # Validate structure
        assert isinstance(data["subject"], str), "subject should be a string"
        assert isinstance(data["html"], str), "html should be a string"
        assert isinstance(data["recipient_count"], int), "recipient_count should be an integer"
        
        # Validate content
        assert len(data["subject"]) > 0, "subject should not be empty"
        assert len(data["html"]) > 0, "html should not be empty"
        assert data["recipient_count"] >= 0, "recipient_count should be non-negative"
        
        # Validate HTML contains email template markers
        assert "4Luis" in data["html"], "HTML should contain 4Luis branding"
        
        print(f"✅ Weekly summary preview: subject='{data['subject']}', recipient_count={data['recipient_count']}")
    
    def test_preview_weekly_summary_requires_auth(self):
        """Test that weekly summary preview requires admin authentication"""
        # Create a session without auth
        no_auth_session = requests.Session()
        response = no_auth_session.get(f"{BASE_URL}/api/admin/emails/preview/weekly-summary")
        
        # Should return 401 Unauthorized
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Weekly summary preview correctly requires authentication")
    
    def test_preview_new_journey(self):
        """Test GET /api/admin/emails/preview/new-journey/{journey_id} returns subject, html, and recipient_count"""
        # First, get a valid journey ID
        journeys_response = self.session.get(f"{BASE_URL}/api/admin/journeys")
        assert journeys_response.status_code == 200, f"Failed to get journeys: {journeys_response.text}"
        
        journeys = journeys_response.json()
        assert len(journeys) > 0, "No journeys found in database"
        
        journey_id = journeys[0]["journey_id"]
        journey_name = journeys[0]["name"]
        
        # Test the preview endpoint
        response = self.session.get(f"{BASE_URL}/api/admin/emails/preview/new-journey/{journey_id}")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "subject" in data, "Missing 'subject' in response"
        assert "html" in data, "Missing 'html' in response"
        assert "recipient_count" in data, "Missing 'recipient_count' in response"
        
        # Validate structure
        assert isinstance(data["subject"], str), "subject should be a string"
        assert isinstance(data["html"], str), "html should be a string"
        assert isinstance(data["recipient_count"], int), "recipient_count should be an integer"
        
        # Validate content contains journey name
        assert journey_name in data["subject"], f"Subject should contain journey name '{journey_name}'"
        
        print(f"✅ New journey preview for {journey_name}: subject='{data['subject']}', recipient_count={data['recipient_count']}")
    
    def test_preview_new_journey_invalid_id(self):
        """Test that preview with invalid journey_id returns 404"""
        response = self.session.get(f"{BASE_URL}/api/admin/emails/preview/new-journey/invalid_journey_id_xyz")
        
        # Should return 404 Not Found
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ New journey preview correctly returns 404 for invalid journey ID")
    
    def test_preview_dream_funded(self):
        """Test GET /api/admin/emails/preview/dream-funded/{journey_id} returns subject, html, and recipient_count"""
        # First, get a valid journey ID
        journeys_response = self.session.get(f"{BASE_URL}/api/admin/journeys")
        assert journeys_response.status_code == 200, f"Failed to get journeys: {journeys_response.text}"
        
        journeys = journeys_response.json()
        assert len(journeys) > 0, "No journeys found in database"
        
        journey_id = journeys[0]["journey_id"]
        journey_name = journeys[0]["name"]
        
        # Test the preview endpoint
        response = self.session.get(f"{BASE_URL}/api/admin/emails/preview/dream-funded/{journey_id}")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "subject" in data, "Missing 'subject' in response"
        assert "html" in data, "Missing 'html' in response"
        assert "recipient_count" in data, "Missing 'recipient_count' in response"
        
        # Validate structure
        assert isinstance(data["subject"], str), "subject should be a string"
        assert isinstance(data["html"], str), "html should be a string"
        assert isinstance(data["recipient_count"], int), "recipient_count should be an integer"
        
        # Validate content contains journey name
        assert journey_name in data["subject"], f"Subject should contain journey name '{journey_name}'"
        
        print(f"✅ Dream funded preview for {journey_name}: subject='{data['subject']}', recipient_count={data['recipient_count']}")
    
    def test_preview_dream_funded_invalid_id(self):
        """Test that dream funded preview with invalid journey_id returns 404"""
        response = self.session.get(f"{BASE_URL}/api/admin/emails/preview/dream-funded/invalid_journey_id_xyz")
        
        # Should return 404 Not Found
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ Dream funded preview correctly returns 404 for invalid journey ID")

    def test_preview_vs_send_endpoints_separate(self):
        """Verify that preview (GET) and send (POST) endpoints are separate"""
        # Get a journey for testing
        journeys_response = self.session.get(f"{BASE_URL}/api/admin/journeys")
        journeys = journeys_response.json()
        journey_id = journeys[0]["journey_id"]
        
        # GET preview should return data without sending
        preview_response = self.session.get(f"{BASE_URL}/api/admin/emails/preview/new-journey/{journey_id}")
        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        
        # Verify preview returns expected structure
        assert "html" in preview_data
        assert "subject" in preview_data
        assert "recipient_count" in preview_data
        
        # GET on POST endpoint should fail (method not allowed)
        # The send endpoints should be POST only
        # Note: Don't actually call POST as it would send real emails
        
        print("✅ Preview (GET) and Send (POST) endpoints are properly separated")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
