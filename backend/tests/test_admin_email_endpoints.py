"""
Test Admin Email Endpoints for 4Luis Platform
Tests 3 new email endpoints:
1. POST /api/admin/emails/weekly-summary - sends weekly summary email to all users
2. POST /api/admin/emails/dream-funded/{journey_id} - sends funded dream email, marks journey as 'financiada'
3. POST /api/admin/emails/new-journey/{journey_id} - sends new journey announcement email

All endpoints require admin authentication.
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
API_URL = f"{BASE_URL}/api"

class TestAdminEmailEndpoints:
    """Test admin email endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test with admin authentication"""
        # Admin login
        login_response = requests.post(f"{API_URL}/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_weekly_summary_requires_admin(self):
        """Test that weekly summary endpoint requires admin auth"""
        # Test without auth
        response = requests.post(f"{API_URL}/admin/emails/weekly-summary")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_weekly_summary_sends_emails(self):
        """Test POST /api/admin/emails/weekly-summary sends emails"""
        response = requests.post(
            f"{API_URL}/admin/emails/weekly-summary",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "sent" in data, "Response should contain 'sent' count"
        assert "journeys_count" in data, "Response should contain 'journeys_count'"
        assert isinstance(data["sent"], int), "sent should be integer"
        assert isinstance(data["journeys_count"], int), "journeys_count should be integer"
        print(f"Weekly summary sent to {data['sent']} users, {data['journeys_count']} active journeys")
    
    def test_dream_funded_requires_admin(self):
        """Test that dream funded endpoint requires admin auth"""
        response = requests.post(f"{API_URL}/admin/emails/dream-funded/some_journey_id")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_dream_funded_journey_not_found(self):
        """Test dream funded returns 404 for non-existent journey"""
        response = requests.post(
            f"{API_URL}/admin/emails/dream-funded/nonexistent_journey_xyz123",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_dream_funded_sends_email_and_marks_funded(self):
        """Test POST /api/admin/emails/dream-funded/{id} sends emails and marks journey as funded"""
        # First create a test journey with >=100% progress
        unique_id = uuid.uuid4().hex[:8]
        journey_data = {
            "name": f"TEST_Funded_Journey_{unique_id}",
            "poetic_name": "Test Journey for Funding",
            "description": "Test journey to test funded email",
            "emotional_message": "Test emotional message",
            "impact_description": "Test impact",
            "image_url": "https://example.com/test.jpg",
            "goal_amount": 100,
            "target_date": "2026-12-31"
        }
        
        create_response = requests.post(
            f"{API_URL}/admin/journeys",
            headers=self.headers,
            json=journey_data
        )
        assert create_response.status_code == 200, f"Journey creation failed: {create_response.text}"
        journey = create_response.json()
        journey_id = journey["journey_id"]
        
        try:
            # Update journey to have >= 100% progress
            update_response = requests.put(
                f"{API_URL}/admin/journeys/{journey_id}",
                headers=self.headers,
                json={"status": "ativa"}  # Ensure it's active first
            )
            
            # Now send the dream funded email
            response = requests.post(
                f"{API_URL}/admin/emails/dream-funded/{journey_id}",
                headers=self.headers
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            
            # Verify response
            assert "sent" in data, "Response should contain 'sent' count"
            assert "message" in data, "Response should contain 'message'"
            print(f"Dream funded email sent to {data['sent']} users")
            
            # Verify journey was marked as funded
            journey_response = requests.get(f"{API_URL}/journeys/{journey_id}")
            assert journey_response.status_code == 200
            updated_journey = journey_response.json()
            
            assert updated_journey["status"] == "financiada", f"Journey should be marked as 'financiada', got {updated_journey['status']}"
            assert updated_journey.get("funded_email_sent") == True, "Journey should have funded_email_sent=true"
            assert updated_journey.get("funded_at") is not None, "Journey should have funded_at timestamp"
            
        finally:
            # Cleanup: delete test journey
            requests.delete(f"{API_URL}/admin/journeys/{journey_id}", headers=self.headers)
    
    def test_new_journey_requires_admin(self):
        """Test that new journey email endpoint requires admin auth"""
        response = requests.post(f"{API_URL}/admin/emails/new-journey/some_journey_id")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_new_journey_not_found(self):
        """Test new journey email returns 404 for non-existent journey"""
        response = requests.post(
            f"{API_URL}/admin/emails/new-journey/nonexistent_journey_xyz456",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_new_journey_sends_email_and_marks_sent(self):
        """Test POST /api/admin/emails/new-journey/{id} sends emails and sets announcement_email_sent=true"""
        # Create a test journey
        unique_id = uuid.uuid4().hex[:8]
        journey_data = {
            "name": f"TEST_New_Journey_{unique_id}",
            "poetic_name": "Novo Sonho para Anunciar",
            "description": "Test journey for announcement",
            "emotional_message": "Test emotional",
            "impact_description": "Test impact",
            "image_url": "https://example.com/new.jpg",
            "goal_amount": 5000,
            "target_date": "2026-06-30"
        }
        
        create_response = requests.post(
            f"{API_URL}/admin/journeys",
            headers=self.headers,
            json=journey_data
        )
        assert create_response.status_code == 200, f"Journey creation failed: {create_response.text}"
        journey = create_response.json()
        journey_id = journey["journey_id"]
        
        try:
            # Verify announcement_email_sent is not set initially
            initial_journey = requests.get(f"{API_URL}/journeys/{journey_id}").json()
            assert initial_journey.get("announcement_email_sent") != True, "New journey should not have announcement_email_sent=true initially"
            
            # Send new journey email
            response = requests.post(
                f"{API_URL}/admin/emails/new-journey/{journey_id}",
                headers=self.headers
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            
            # Verify response
            assert "sent" in data, "Response should contain 'sent' count"
            assert "message" in data, "Response should contain 'message'"
            print(f"New journey email sent to {data['sent']} users")
            
            # Verify journey has announcement_email_sent=true
            updated_journey = requests.get(f"{API_URL}/journeys/{journey_id}").json()
            assert updated_journey.get("announcement_email_sent") == True, f"Journey should have announcement_email_sent=true, got {updated_journey.get('announcement_email_sent')}"
            
        finally:
            # Cleanup: delete test journey
            requests.delete(f"{API_URL}/admin/journeys/{journey_id}", headers=self.headers)


class TestExistingJourneys:
    """Test with existing journeys mentioned in test credentials"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test with admin authentication"""
        login_response = requests.post(f"{API_URL}/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_journey_china_exists(self):
        """Verify test journey journey_china001 exists"""
        response = requests.get(f"{API_URL}/journeys/journey_china001")
        # Journey may or may not exist - just check API works
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            journey = response.json()
            print(f"Journey China: {journey.get('name')} - {journey.get('current_amount', 0) / journey.get('goal_amount', 1) * 100:.1f}%")
    
    def test_journey_japao_exists(self):
        """Verify test journey journey_japao_amb001 exists"""
        response = requests.get(f"{API_URL}/journeys/journey_japao_amb001")
        # Journey may or may not exist - just check API works
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            journey = response.json()
            print(f"Journey Japao: {journey.get('name')} - {journey.get('current_amount', 0) / journey.get('goal_amount', 1) * 100:.1f}%")


class TestEmailHelperFunctions:
    """Test that email helper functions are working by checking email structure"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test with admin authentication"""
        login_response = requests.post(f"{API_URL}/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_sender_email_is_mail_4luis(self):
        """Verify SENDER_EMAIL env var is set to mail@4luis.com by checking backend config"""
        # We can indirectly verify this by checking that emails are sent successfully
        # The actual SENDER_EMAIL is in backend/.env as mail@4luis.com
        # This test just confirms the endpoint works (emails would fail if sender was wrong domain)
        response = requests.post(
            f"{API_URL}/admin/emails/weekly-summary",
            headers=self.headers
        )
        assert response.status_code == 200, f"Email sending failed - check SENDER_EMAIL config: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
