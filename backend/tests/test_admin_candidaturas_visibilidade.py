"""
Test Admin Candidaturas (Applications) and Visibilidade (Visibility) features
Tests for:
- Tab Candidaturas - list applications, approve/reject
- Tab Visibilidade - list journeys, feature/hide/boost visibility
- Status filters
- Action buttons: Aprovar, Rejeitar, Ativar
- Visibility buttons: Destacar, Boost, Ocultar
- Recalculate Scores
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data prefix for cleanup
TEST_PREFIX = "TEST_"

class TestAuth:
    """Authentication tests - get admin token first"""
    
    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    def test_admin_login(self, api_client):
        """Test admin login to get auth token"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "admin_password"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["is_admin"] == True
        # Store token for other tests
        api_client.headers.update({"Authorization": f"Bearer {data['token']}"})
        print(f"Admin login successful, token obtained")
        return data["token"]


class TestCandidaturas:
    """Test Candidaturas (Applications) admin features"""
    
    @pytest.fixture(scope="class")
    def authenticated_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        # Login as admin
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "admin_password"
        })
        if response.status_code == 200:
            token = response.json().get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_ambassador_journeys_all(self, authenticated_client):
        """Test GET /api/admin/ambassador-journeys - list all ambassador applications"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/ambassador-journeys")
        assert response.status_code == 200, f"Failed to get ambassador journeys: {response.text}"
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "journeys" in data
        # Check status categories exist
        assert "candidatura" in data["by_status"]
        assert "aprovada" in data["by_status"]
        assert "ativa" in data["by_status"]
        print(f"Ambassador journeys found: total={data['total']}")
        print(f"By status breakdown: {[(k, len(v)) for k, v in data['by_status'].items() if len(v) > 0]}")
    
    def test_get_ambassador_journeys_with_filter(self, authenticated_client):
        """Test GET /api/admin/ambassador-journeys?status=candidatura - filter by status"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/ambassador-journeys?status=candidatura")
        assert response.status_code == 200, f"Failed to get filtered journeys: {response.text}"
        data = response.json()
        assert "journeys" in data
        # All returned journeys should have status 'candidatura' or be empty
        for journey in data["journeys"]:
            assert journey.get("status") == "candidatura", f"Journey has wrong status: {journey.get('status')}"
        print(f"Candidatura journeys (pending): {len(data['journeys'])}")
    
    def test_get_ambassador_journeys_all_statuses(self, authenticated_client):
        """Test filtering by all possible statuses"""
        statuses = ["candidatura", "aprovada", "ativa", "financiada", "realizada", "encerrada"]
        for status in statuses:
            response = authenticated_client.get(f"{BASE_URL}/api/admin/ambassador-journeys?status={status}")
            assert response.status_code == 200, f"Failed to filter by status {status}: {response.text}"
            data = response.json()
            print(f"  - Status '{status}': {len(data['journeys'])} journeys")


class TestVisibilidade:
    """Test Visibilidade (Visibility) admin features"""
    
    @pytest.fixture(scope="class")
    def authenticated_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "admin_password"
        })
        if response.status_code == 200:
            token = response.json().get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_journeys_visibility(self, authenticated_client):
        """Test GET /api/admin/journeys-visibility - list journeys with visibility data"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/journeys-visibility")
        assert response.status_code == 200, f"Failed to get visibility data: {response.text}"
        data = response.json()
        assert "count" in data
        assert "journeys" in data
        print(f"Journeys with visibility data: {data['count']}")
        # Check each journey has visibility fields
        for journey in data["journeys"][:3]:  # Check first 3
            assert "calculated_score" in journey, "Missing calculated_score field"
            print(f"  - {journey.get('name', 'N/A')}: score={journey.get('calculated_score', 0)}, boost={journey.get('visibility_boost', 0)}")
    
    def test_get_journeys_visibility_filtered(self, authenticated_client):
        """Test GET /api/admin/journeys-visibility?status=ativa - filter by status"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/journeys-visibility?status=ativa")
        assert response.status_code == 200, f"Failed to get ativa visibility: {response.text}"
        data = response.json()
        print(f"Active journeys with visibility: {data['count']}")
    
    def test_recalculate_all_visibility(self, authenticated_client):
        """Test POST /api/admin/recalculate-all-visibility - recalculate scores"""
        response = authenticated_client.post(f"{BASE_URL}/api/admin/recalculate-all-visibility")
        assert response.status_code == 200, f"Failed to recalculate visibility: {response.text}"
        data = response.json()
        assert "message" in data
        assert "updated_count" in data
        print(f"Recalculate result: {data['message']}")


class TestVisibilityActions:
    """Test visibility action buttons: Destacar, Boost, Ocultar"""
    
    @pytest.fixture(scope="class")
    def authenticated_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "admin_password"
        })
        if response.status_code == 200:
            token = response.json().get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def test_journey_id(self, authenticated_client):
        """Get first available journey for testing visibility actions"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/journeys")
        if response.status_code == 200:
            journeys = response.json()
            if journeys:
                return journeys[0]["journey_id"]
        pytest.skip("No journeys available for testing visibility actions")
    
    def test_update_visibility_feature(self, authenticated_client, test_journey_id):
        """Test POST /api/admin/journeys/{id}/update-visibility - feature a journey"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/journeys/{test_journey_id}/update-visibility",
            json={"is_featured": True}
        )
        assert response.status_code == 200, f"Failed to feature journey: {response.text}"
        data = response.json()
        assert data.get("is_featured") == True
        print(f"Featured journey: {test_journey_id}")
        
        # Verify by getting the journey
        verify = authenticated_client.get(f"{BASE_URL}/api/journeys/{test_journey_id}")
        assert verify.status_code == 200
        journey_data = verify.json()
        assert journey_data.get("is_featured") == True
    
    def test_update_visibility_boost_positive(self, authenticated_client, test_journey_id):
        """Test POST /api/admin/journeys/{id}/update-visibility - boost +10"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/journeys/{test_journey_id}/update-visibility",
            json={"visibility_boost": 10}
        )
        assert response.status_code == 200, f"Failed to boost journey: {response.text}"
        data = response.json()
        assert data.get("visibility_boost") == 10
        print(f"Boosted journey +10: {test_journey_id}")
    
    def test_update_visibility_boost_negative(self, authenticated_client, test_journey_id):
        """Test POST /api/admin/journeys/{id}/update-visibility - boost -10"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/journeys/{test_journey_id}/update-visibility",
            json={"visibility_boost": -10}
        )
        assert response.status_code == 200, f"Failed to negative boost journey: {response.text}"
        data = response.json()
        assert data.get("visibility_boost") == -10
        print(f"Boosted journey -10: {test_journey_id}")
    
    def test_update_visibility_hide(self, authenticated_client, test_journey_id):
        """Test POST /api/admin/journeys/{id}/update-visibility - hide from listings"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/journeys/{test_journey_id}/update-visibility",
            json={"hide_from_listings": True}
        )
        assert response.status_code == 200, f"Failed to hide journey: {response.text}"
        print(f"Hidden journey from listings: {test_journey_id}")
    
    def test_update_visibility_unhide(self, authenticated_client, test_journey_id):
        """Test POST /api/admin/journeys/{id}/update-visibility - unhide"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/journeys/{test_journey_id}/update-visibility",
            json={"hide_from_listings": False}
        )
        assert response.status_code == 200, f"Failed to unhide journey: {response.text}"
        print(f"Unhidden journey: {test_journey_id}")
    
    def test_update_visibility_unfeature(self, authenticated_client, test_journey_id):
        """Test POST /api/admin/journeys/{id}/update-visibility - unfeature to reset"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/journeys/{test_journey_id}/update-visibility",
            json={"is_featured": False, "visibility_boost": 0}
        )
        assert response.status_code == 200, f"Failed to reset visibility: {response.text}"
        print(f"Reset visibility for journey: {test_journey_id}")


class TestApplicationStatusChange:
    """Test changing application status: Aprovar, Rejeitar, Ativar"""
    
    @pytest.fixture(scope="class")
    def authenticated_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "admin_password"
        })
        if response.status_code == 200:
            token = response.json().get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_status_change_endpoint_exists(self, authenticated_client):
        """Test that the status change endpoint exists and validates properly"""
        # Try with a non-existent journey ID
        response = authenticated_client.put(
            f"{BASE_URL}/api/admin/ambassador-journeys/nonexistent_id/status",
            json={"status": "aprovada"}
        )
        # Should return 404 for non-existent journey
        assert response.status_code == 404, f"Expected 404 for non-existent journey, got {response.status_code}"
        print("Status change endpoint exists and validates journey existence")
    
    def test_status_change_invalid_status(self, authenticated_client):
        """Test that invalid status values are rejected"""
        response = authenticated_client.put(
            f"{BASE_URL}/api/admin/ambassador-journeys/test_id/status",
            json={"status": "invalid_status"}
        )
        # Should return 400 for invalid status
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"
        print("Invalid status values are properly rejected")


class TestAdminAccess:
    """Test admin-only access restrictions"""
    
    def test_candidaturas_requires_auth(self):
        """Test that /api/admin/ambassador-journeys requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/ambassador-journeys")
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("Candidaturas endpoint properly requires authentication")
    
    def test_visibility_requires_auth(self):
        """Test that /api/admin/journeys-visibility requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/journeys-visibility")
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("Visibility endpoint properly requires authentication")
    
    def test_recalculate_requires_auth(self):
        """Test that /api/admin/recalculate-all-visibility requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/recalculate-all-visibility")
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("Recalculate endpoint properly requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
