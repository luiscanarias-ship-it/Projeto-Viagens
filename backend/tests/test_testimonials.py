"""
Test Suite for Testimonial System
Tests all testimonial endpoints:
- POST /api/admin/support/tickets/{id}/testimonial - Create testimonial draft
- PUT /api/admin/testimonials/{id} - Update testimonial text
- POST /api/admin/testimonials/{id}/request-auth - Send authorization email
- GET /api/testimonials/authorize/{token} - User authorizes testimonial
- GET /api/testimonials/reject/{token} - User rejects testimonial
- POST /api/admin/testimonials/{id}/publish - Publish authorized testimonial
- GET /api/testimonials/published - Get published testimonials (public)
- GET /api/admin/testimonials - List all testimonials (admin)
- DELETE /api/admin/testimonials/{id} - Delete testimonial
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestTestimonialSystem:
    """Test the complete testimonial workflow"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed - skipping testimonial tests")
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def resolved_ticket_id(self, admin_token):
        """Find a resolved or closed ticket that doesn't have a testimonial yet"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First try to find tickets without testimonials
        for status in ["Resolvido", "Fechado"]:
            response = requests.get(f"{BASE_URL}/api/admin/support/tickets?status={status}", headers=headers)
            if response.status_code == 200:
                tickets = response.json().get("tickets", [])
                for ticket in tickets:
                    if not ticket.get("has_testimonial", False):
                        return ticket["ticket_id"]
        
        # If no suitable ticket exists, create one
        unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        
        # Register a test user first
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "name": "Test Testimonial User"
        })
        
        if reg_response.status_code == 200:
            user_token = reg_response.json().get("token")
            user_headers = {"Authorization": f"Bearer {user_token}"}
            
            # Create a support ticket
            ticket_response = requests.post(f"{BASE_URL}/api/support/tickets", 
                json={
                    "ticket_type": "Sugestao",
                    "subject": "Teste para testemunho",
                    "description": "Esta e uma experiencia incrivel com a plataforma 4Luis!"
                },
                headers=user_headers
            )
            
            if ticket_response.status_code in [200, 201]:
                ticket_id = ticket_response.json().get("ticket_id")
                
                # Mark as resolved using admin
                requests.put(f"{BASE_URL}/api/admin/support/tickets/{ticket_id}/status",
                    json={"status": "Resolvido"},
                    headers=headers
                )
                return ticket_id
        
        pytest.skip("Could not find or create suitable ticket for testimonial test")
    
    def test_01_create_testimonial_draft(self, admin_token, resolved_ticket_id):
        """Test creating a testimonial draft from a resolved ticket"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        testimonial_text = "Excelente atendimento! A equipa 4Luis foi muito prestavel."
        
        response = requests.post(
            f"{BASE_URL}/api/admin/support/tickets/{resolved_ticket_id}/testimonial",
            json={"text": testimonial_text},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "testimonial_id" in data, "Response should contain testimonial_id"
        assert data["status"] == "draft", f"Initial status should be 'draft', got {data['status']}"
        assert data["text"] == testimonial_text, "Testimonial text should match input"
        assert "user_name" in data, "Response should contain user_name"
        assert "badge" in data, "Response should contain badge (trust level)"
        assert "auth_token" in data, "Response should contain auth_token"
        
        # Store for subsequent tests
        self.__class__.created_testimonial_id = data["testimonial_id"]
        self.__class__.auth_token = data["auth_token"]
        print(f"Created testimonial: {data['testimonial_id']} with status: {data['status']}")
    
    def test_02_ticket_marked_has_testimonial(self, admin_token, resolved_ticket_id):
        """Verify ticket is marked as has_testimonial after creation"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/support/tickets/{resolved_ticket_id}", headers=headers)
        assert response.status_code == 200
        
        ticket = response.json()
        assert ticket.get("has_testimonial") == True, "Ticket should have has_testimonial=true"
        print(f"Ticket {resolved_ticket_id} marked as has_testimonial=True")
    
    def test_03_admin_list_testimonials(self, admin_token):
        """Test admin can list all testimonials"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/testimonials", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "testimonials" in data, "Response should contain 'testimonials' list"
        
        testimonials = data["testimonials"]
        assert isinstance(testimonials, list), "testimonials should be a list"
        
        # Check if our created testimonial is in the list
        if hasattr(self.__class__, 'created_testimonial_id'):
            found = any(t["testimonial_id"] == self.__class__.created_testimonial_id for t in testimonials)
            assert found, "Our created testimonial should be in the list"
        
        # Verify all testimonials have required fields
        for t in testimonials:
            assert "testimonial_id" in t
            assert "text" in t
            assert "status" in t
            assert "user_name" in t
        
        print(f"Found {len(testimonials)} testimonials in admin list")
    
    def test_04_update_testimonial_text(self, admin_token):
        """Test updating testimonial text"""
        if not hasattr(self.__class__, 'created_testimonial_id'):
            pytest.skip("No testimonial created in previous test")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        new_text = "Atualizei: O suporte foi excelente e rapido!"
        
        response = requests.put(
            f"{BASE_URL}/api/admin/testimonials/{self.__class__.created_testimonial_id}",
            json={"text": new_text},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json().get("status") == "ok"
        
        # Verify update
        list_response = requests.get(f"{BASE_URL}/api/admin/testimonials", headers=headers)
        testimonials = list_response.json().get("testimonials", [])
        found = [t for t in testimonials if t["testimonial_id"] == self.__class__.created_testimonial_id]
        assert len(found) == 1
        assert found[0]["text"] == new_text, "Text should be updated"
        print(f"Updated testimonial text successfully")
    
    def test_05_request_authorization(self, admin_token):
        """Test requesting authorization sends email and updates status"""
        if not hasattr(self.__class__, 'created_testimonial_id'):
            pytest.skip("No testimonial created in previous test")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/testimonials/{self.__class__.created_testimonial_id}/request-auth",
            json={},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json().get("status") == "ok"
        
        # Verify status changed to pending_auth
        list_response = requests.get(f"{BASE_URL}/api/admin/testimonials", headers=headers)
        testimonials = list_response.json().get("testimonials", [])
        found = [t for t in testimonials if t["testimonial_id"] == self.__class__.created_testimonial_id]
        assert len(found) == 1
        assert found[0]["status"] == "pending_auth", f"Status should be 'pending_auth', got {found[0]['status']}"
        print(f"Testimonial status changed to pending_auth, email sent")
    
    def test_06_authorize_testimonial_public_endpoint(self):
        """Test user authorizes testimonial via public URL"""
        if not hasattr(self.__class__, 'auth_token'):
            pytest.skip("No auth_token from previous test")
        
        # Note: This endpoint returns a redirect, so we don't follow
        response = requests.get(
            f"{BASE_URL}/api/testimonials/authorize/{self.__class__.auth_token}",
            allow_redirects=False
        )
        
        assert response.status_code in [302, 307], f"Expected redirect (302/307), got {response.status_code}"
        
        location = response.headers.get("location", "")
        assert "/testimonial/result?action=authorized" in location, f"Should redirect to authorized page, got {location}"
        print(f"Authorization redirect works correctly to: {location}")
    
    def test_07_testimonial_now_authorized(self, admin_token):
        """Verify testimonial is now in authorized status"""
        if not hasattr(self.__class__, 'created_testimonial_id'):
            pytest.skip("No testimonial created in previous test")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        list_response = requests.get(f"{BASE_URL}/api/admin/testimonials", headers=headers)
        testimonials = list_response.json().get("testimonials", [])
        found = [t for t in testimonials if t["testimonial_id"] == self.__class__.created_testimonial_id]
        
        assert len(found) == 1
        assert found[0]["status"] == "authorized", f"Status should be 'authorized', got {found[0]['status']}"
        print(f"Testimonial status is now 'authorized'")
    
    def test_08_publish_testimonial(self, admin_token):
        """Test publishing an authorized testimonial"""
        if not hasattr(self.__class__, 'created_testimonial_id'):
            pytest.skip("No testimonial created in previous test")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/testimonials/{self.__class__.created_testimonial_id}/publish",
            json={},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json().get("status") == "ok"
        
        # Verify status changed to published
        list_response = requests.get(f"{BASE_URL}/api/admin/testimonials", headers=headers)
        testimonials = list_response.json().get("testimonials", [])
        found = [t for t in testimonials if t["testimonial_id"] == self.__class__.created_testimonial_id]
        assert len(found) == 1
        assert found[0]["status"] == "published", f"Status should be 'published', got {found[0]['status']}"
        print(f"Testimonial successfully published")
    
    def test_09_published_testimonials_public_endpoint(self):
        """Test public endpoint returns published testimonials without sensitive data"""
        response = requests.get(f"{BASE_URL}/api/testimonials/published")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "testimonials" in data, "Response should contain 'testimonials' list"
        
        testimonials = data["testimonials"]
        assert isinstance(testimonials, list), "testimonials should be a list"
        
        # All returned testimonials should be published
        for t in testimonials:
            assert t["status"] == "published", f"All should be published, got {t['status']}"
            # Sensitive data should NOT be present
            assert "auth_token" not in t, "auth_token should not be exposed"
            assert "user_email" not in t, "user_email should not be exposed"
            assert "user_id" not in t, "user_id should not be exposed"
            # Required fields should be present
            assert "testimonial_id" in t
            assert "text" in t
            assert "user_name" in t
            assert "badge" in t
        
        print(f"Public endpoint returns {len(testimonials)} published testimonials without sensitive data")
    
    def test_10_delete_testimonial(self, admin_token):
        """Test deleting a testimonial"""
        if not hasattr(self.__class__, 'created_testimonial_id'):
            pytest.skip("No testimonial created in previous test")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/testimonials/{self.__class__.created_testimonial_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify deletion
        list_response = requests.get(f"{BASE_URL}/api/admin/testimonials", headers=headers)
        testimonials = list_response.json().get("testimonials", [])
        found = [t for t in testimonials if t["testimonial_id"] == self.__class__.created_testimonial_id]
        assert len(found) == 0, "Testimonial should be deleted from list"
        print(f"Testimonial deleted successfully")


class TestTestimonialRejectFlow:
    """Test the rejection flow for testimonials"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("token")
    
    def test_01_create_testimonial_for_rejection(self, admin_token):
        """Create a testimonial to test rejection"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Find a suitable ticket or create one
        response = requests.get(f"{BASE_URL}/api/admin/support/tickets?status=Resolvido", headers=headers)
        tickets = response.json().get("tickets", []) if response.status_code == 200 else []
        
        ticket_without_testimonial = None
        for t in tickets:
            if not t.get("has_testimonial", False):
                ticket_without_testimonial = t["ticket_id"]
                break
        
        if not ticket_without_testimonial:
            # Create test user and ticket
            unique_email = f"rejecttest_{uuid.uuid4().hex[:8]}@example.com"
            reg = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": unique_email,
                "password": "testpass",
                "name": "Reject Test User"
            })
            if reg.status_code == 200:
                user_token = reg.json()["token"]
                ticket_resp = requests.post(f"{BASE_URL}/api/support/tickets",
                    json={"ticket_type": "Outro", "subject": "Para rejeitar", "description": "Teste rejeicao"},
                    headers={"Authorization": f"Bearer {user_token}"}
                )
                if ticket_resp.status_code in [200, 201]:
                    ticket_without_testimonial = ticket_resp.json()["ticket_id"]
                    requests.put(f"{BASE_URL}/api/admin/support/tickets/{ticket_without_testimonial}/status",
                        json={"status": "Resolvido"}, headers=headers)
        
        if not ticket_without_testimonial:
            pytest.skip("No ticket available for rejection test")
        
        # Create testimonial
        resp = requests.post(
            f"{BASE_URL}/api/admin/support/tickets/{ticket_without_testimonial}/testimonial",
            json={"text": "Este testemunho sera rejeitado."},
            headers=headers
        )
        
        assert resp.status_code == 200
        data = resp.json()
        self.__class__.reject_testimonial_id = data["testimonial_id"]
        self.__class__.reject_auth_token = data["auth_token"]
        print(f"Created testimonial for rejection: {data['testimonial_id']}")
    
    def test_02_reject_testimonial_public_endpoint(self, admin_token):
        """Test user rejects testimonial via public URL"""
        if not hasattr(self.__class__, 'reject_auth_token'):
            pytest.skip("No auth_token from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/testimonials/reject/{self.__class__.reject_auth_token}",
            allow_redirects=False
        )
        
        assert response.status_code in [302, 307], f"Expected redirect, got {response.status_code}"
        
        location = response.headers.get("location", "")
        assert "/testimonial/result?action=rejected" in location, f"Should redirect to rejected page"
        print(f"Rejection redirect works correctly to: {location}")
    
    def test_03_testimonial_status_is_rejected(self, admin_token):
        """Verify testimonial status is now rejected"""
        if not hasattr(self.__class__, 'reject_testimonial_id'):
            pytest.skip("No testimonial ID")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        list_response = requests.get(f"{BASE_URL}/api/admin/testimonials", headers=headers)
        testimonials = list_response.json().get("testimonials", [])
        found = [t for t in testimonials if t["testimonial_id"] == self.__class__.reject_testimonial_id]
        
        assert len(found) == 1
        assert found[0]["status"] == "rejected", f"Status should be 'rejected', got {found[0]['status']}"
        print(f"Testimonial status is 'rejected'")
    
    def test_04_cannot_publish_rejected_testimonial(self, admin_token):
        """Verify cannot publish a rejected testimonial"""
        if not hasattr(self.__class__, 'reject_testimonial_id'):
            pytest.skip("No testimonial ID")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/testimonials/{self.__class__.reject_testimonial_id}/publish",
            json={},
            headers=headers
        )
        
        assert response.status_code == 400, f"Should fail with 400, got {response.status_code}"
        print("Correctly prevents publishing rejected testimonial")
    
    def test_05_cleanup_rejected_testimonial(self, admin_token):
        """Clean up test testimonial"""
        if hasattr(self.__class__, 'reject_testimonial_id'):
            headers = {"Authorization": f"Bearer {admin_token}"}
            requests.delete(f"{BASE_URL}/api/admin/testimonials/{self.__class__.reject_testimonial_id}", headers=headers)
            print("Cleaned up rejected testimonial")


class TestTestimonialEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("token")
    
    def test_create_testimonial_empty_text(self, admin_token):
        """Test creating testimonial with empty text fails"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get any ticket
        response = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=headers)
        tickets = response.json().get("tickets", [])
        if not tickets:
            pytest.skip("No tickets available")
        
        ticket_id = tickets[0]["ticket_id"]
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/support/tickets/{ticket_id}/testimonial",
            json={"text": ""},
            headers=headers
        )
        
        assert resp.status_code == 400, f"Should fail with empty text, got {resp.status_code}"
        print("Correctly rejects empty testimonial text")
    
    def test_create_testimonial_nonexistent_ticket(self, admin_token):
        """Test creating testimonial from nonexistent ticket fails"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/support/tickets/NONEXISTENT/testimonial",
            json={"text": "Some text"},
            headers=headers
        )
        
        assert resp.status_code == 404, f"Should return 404 for nonexistent ticket, got {resp.status_code}"
        print("Correctly returns 404 for nonexistent ticket")
    
    def test_publish_unauthorized_testimonial_fails(self, admin_token):
        """Test cannot publish a testimonial that's not authorized"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get any draft testimonial
        resp = requests.get(f"{BASE_URL}/api/admin/testimonials", headers=headers)
        testimonials = resp.json().get("testimonials", [])
        
        draft = [t for t in testimonials if t["status"] == "draft"]
        if not draft:
            pytest.skip("No draft testimonials to test")
        
        pub_resp = requests.post(
            f"{BASE_URL}/api/admin/testimonials/{draft[0]['testimonial_id']}/publish",
            json={},
            headers=headers
        )
        
        assert pub_resp.status_code == 400, f"Should fail with 400 for non-authorized, got {pub_resp.status_code}"
        print("Correctly prevents publishing non-authorized testimonial")
    
    def test_authorize_invalid_token(self):
        """Test authorizing with invalid token fails"""
        response = requests.get(
            f"{BASE_URL}/api/testimonials/authorize/INVALID_TOKEN_12345",
            allow_redirects=False
        )
        
        assert response.status_code == 404, f"Should return 404 for invalid token, got {response.status_code}"
        print("Correctly returns 404 for invalid auth token")
    
    def test_reject_invalid_token(self):
        """Test rejecting with invalid token fails"""
        response = requests.get(
            f"{BASE_URL}/api/testimonials/reject/INVALID_TOKEN_12345",
            allow_redirects=False
        )
        
        assert response.status_code == 404, f"Should return 404 for invalid token, got {response.status_code}"
        print("Correctly returns 404 for invalid reject token")
    
    def test_admin_endpoints_require_auth(self):
        """Test admin endpoints require authentication"""
        # No auth header
        endpoints = [
            ("GET", f"{BASE_URL}/api/admin/testimonials"),
            ("POST", f"{BASE_URL}/api/admin/testimonials/test123/publish"),
            ("DELETE", f"{BASE_URL}/api/admin/testimonials/test123"),
            ("PUT", f"{BASE_URL}/api/admin/testimonials/test123"),
            ("POST", f"{BASE_URL}/api/admin/testimonials/test123/request-auth"),
        ]
        
        for method, url in endpoints:
            if method == "GET":
                resp = requests.get(url)
            elif method == "POST":
                resp = requests.post(url, json={})
            elif method == "PUT":
                resp = requests.put(url, json={"text": "test"})
            elif method == "DELETE":
                resp = requests.delete(url)
            
            assert resp.status_code in [401, 403], f"{method} {url} should require auth, got {resp.status_code}"
        
        print("All admin endpoints correctly require authentication")
    
    def test_public_endpoints_no_auth(self):
        """Test public endpoints work without authentication"""
        # Published testimonials endpoint
        resp = requests.get(f"{BASE_URL}/api/testimonials/published")
        assert resp.status_code == 200, f"Published endpoint should work without auth, got {resp.status_code}"
        print("Public published endpoint works without authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
