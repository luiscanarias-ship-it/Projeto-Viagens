"""
Test Suite for Server-Side Drafts / Autosave System
Tests PUT/GET/DELETE /api/admin/drafts/{type}/{ref_id} and GET /api/admin/drafts

Features tested:
- Create/update draft (journey_edit, journey_create)
- Get specific draft (404 for nonexistent)
- Delete draft
- List all drafts
- Admin authentication requirement (401 without token)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "token" in data or "access_token" in data, f"No token in response: {data}"
    return data.get("token") or data.get("access_token")

@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Authorization headers for admin requests"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestDraftEndpointsAuth:
    """Test that all draft endpoints require admin authentication"""
    
    def test_put_draft_requires_auth(self, api_client):
        """PUT /api/admin/drafts/{type}/{ref_id} - 401 without token"""
        response = api_client.put(
            f"{BASE_URL}/api/admin/drafts/journey_edit/test123",
            json={"data": {"name": "Test"}}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: PUT draft returns 401 without auth")
    
    def test_get_draft_requires_auth(self, api_client):
        """GET /api/admin/drafts/{type}/{ref_id} - 401 without token"""
        response = api_client.get(f"{BASE_URL}/api/admin/drafts/journey_edit/test123")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: GET draft returns 401 without auth")
    
    def test_delete_draft_requires_auth(self, api_client):
        """DELETE /api/admin/drafts/{type}/{ref_id} - 401 without token"""
        response = api_client.delete(f"{BASE_URL}/api/admin/drafts/journey_edit/test123")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: DELETE draft returns 401 without auth")
    
    def test_list_drafts_requires_auth(self, api_client):
        """GET /api/admin/drafts - 401 without token"""
        response = api_client.get(f"{BASE_URL}/api/admin/drafts")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: GET /admin/drafts returns 401 without auth")


class TestDraftCRUD:
    """Test CRUD operations for server-side drafts"""
    
    def test_create_journey_edit_draft(self, api_client, auth_headers):
        """PUT /api/admin/drafts/journey_edit/{journey_id} - create draft"""
        test_journey_id = "journey_china001"
        draft_data = {
            "name": "TEST_China Draft",
            "poetic_name": "Onde os Dragões Dançam",
            "goal_amount": 6000
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/admin/drafts/journey_edit/{test_journey_id}",
            json={"data": draft_data},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "saved", f"Expected status='saved', got {data}"
        assert "updated_at" in data, f"Missing 'updated_at' in response: {data}"
        print(f"PASS: Create journey_edit draft returns {data}")
    
    def test_get_journey_edit_draft(self, api_client, auth_headers):
        """GET /api/admin/drafts/journey_edit/{journey_id} - retrieve draft"""
        test_journey_id = "journey_china001"
        
        response = api_client.get(
            f"{BASE_URL}/api/admin/drafts/journey_edit/{test_journey_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "data" in data, f"Missing 'data' in response: {data}"
        assert "draft_type" in data, f"Missing 'draft_type' in response: {data}"
        assert "reference_id" in data, f"Missing 'reference_id' in response: {data}"
        assert "user_id" in data, f"Missing 'user_id' in response: {data}"
        
        # Validate data values
        assert data["draft_type"] == "journey_edit", f"Expected draft_type='journey_edit', got {data['draft_type']}"
        assert data["reference_id"] == test_journey_id, f"Expected reference_id='{test_journey_id}', got {data['reference_id']}"
        assert data["data"]["name"] == "TEST_China Draft", f"Expected name='TEST_China Draft', got {data['data']['name']}"
        
        print(f"PASS: GET draft returns correct structure with data: {data['data']}")
    
    def test_update_journey_edit_draft(self, api_client, auth_headers):
        """PUT /api/admin/drafts/journey_edit/{journey_id} - update existing draft"""
        test_journey_id = "journey_china001"
        updated_data = {
            "name": "TEST_China Updated",
            "poetic_name": "Onde os Dragões Voam",
            "goal_amount": 7500
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/admin/drafts/journey_edit/{test_journey_id}",
            json={"data": updated_data},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "saved", f"Expected status='saved', got {data}"
        
        # Verify update
        get_response = api_client.get(
            f"{BASE_URL}/api/admin/drafts/journey_edit/{test_journey_id}",
            headers=auth_headers
        )
        get_data = get_response.json()
        assert get_data["data"]["name"] == "TEST_China Updated", f"Update not persisted: {get_data['data']}"
        assert get_data["data"]["goal_amount"] == 7500, f"goal_amount not updated: {get_data['data']}"
        
        print("PASS: Update draft persists changes correctly")
    
    def test_get_nonexistent_draft_returns_404(self, api_client, auth_headers):
        """GET /api/admin/drafts/journey_edit/nonexistent - returns 404"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/drafts/journey_edit/nonexistent_journey_id_12345",
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("PASS: GET nonexistent draft returns 404")
    
    def test_create_journey_create_draft(self, api_client, auth_headers):
        """PUT /api/admin/drafts/journey_create/new - create new journey draft"""
        draft_data = {
            "name": "TEST_Nova Viagem",
            "poetic_name": "Um Novo Começo",
            "goal_amount": 4000
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/admin/drafts/journey_create/new",
            json={"data": draft_data},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "saved", f"Expected status='saved', got {data}"
        assert "updated_at" in data, f"Missing 'updated_at' in response: {data}"
        
        print(f"PASS: Create journey_create/new draft returns {data}")
    
    def test_get_journey_create_draft(self, api_client, auth_headers):
        """GET /api/admin/drafts/journey_create/new - retrieve create draft"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/drafts/journey_create/new",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["draft_type"] == "journey_create", f"Expected draft_type='journey_create', got {data['draft_type']}"
        assert data["reference_id"] == "new", f"Expected reference_id='new', got {data['reference_id']}"
        assert data["data"]["name"] == "TEST_Nova Viagem", f"Expected name='TEST_Nova Viagem', got {data['data'].get('name')}"
        
        print(f"PASS: GET journey_create/new draft returns correct data")
    
    def test_list_all_drafts(self, api_client, auth_headers):
        """GET /api/admin/drafts - list all admin drafts"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/drafts",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "drafts" in data, f"Missing 'drafts' key in response: {data}"
        assert isinstance(data["drafts"], list), f"Expected 'drafts' to be a list: {data}"
        
        # Should have at least 2 drafts (journey_edit and journey_create)
        assert len(data["drafts"]) >= 2, f"Expected at least 2 drafts, got {len(data['drafts'])}"
        
        # Validate draft structure
        for draft in data["drafts"]:
            assert "draft_type" in draft, f"Missing 'draft_type' in draft: {draft}"
            assert "reference_id" in draft, f"Missing 'reference_id' in draft: {draft}"
            assert "user_id" in draft, f"Missing 'user_id' in draft: {draft}"
            assert "data" in draft, f"Missing 'data' in draft: {draft}"
        
        print(f"PASS: List drafts returns {len(data['drafts'])} drafts with correct structure")
    
    def test_delete_journey_edit_draft(self, api_client, auth_headers):
        """DELETE /api/admin/drafts/journey_edit/{journey_id} - delete draft"""
        test_journey_id = "journey_china001"
        
        response = api_client.delete(
            f"{BASE_URL}/api/admin/drafts/journey_edit/{test_journey_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "deleted", f"Expected status='deleted', got {data}"
        
        # Verify deletion - should return 404
        get_response = api_client.get(
            f"{BASE_URL}/api/admin/drafts/journey_edit/{test_journey_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404, f"Draft still exists after deletion: {get_response.text}"
        
        print("PASS: DELETE draft removes it from server")
    
    def test_delete_journey_create_draft(self, api_client, auth_headers):
        """DELETE /api/admin/drafts/journey_create/new - cleanup"""
        response = api_client.delete(
            f"{BASE_URL}/api/admin/drafts/journey_create/new",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "deleted", f"Expected status='deleted', got {data}"
        
        print("PASS: DELETE journey_create/new draft works")


class TestDraftTimestamps:
    """Test that drafts include proper timestamps"""
    
    def test_draft_includes_updated_at_timestamp(self, api_client, auth_headers):
        """Verify updated_at timestamp in PUT response and GET"""
        test_ref = f"TEST_timestamp_{uuid.uuid4().hex[:8]}"
        
        # Create draft
        put_response = api_client.put(
            f"{BASE_URL}/api/admin/drafts/journey_edit/{test_ref}",
            json={"data": {"test": "timestamp"}},
            headers=auth_headers
        )
        
        assert put_response.status_code == 200
        put_data = put_response.json()
        assert "updated_at" in put_data, "PUT response missing updated_at"
        
        # Get draft and check timestamps
        get_response = api_client.get(
            f"{BASE_URL}/api/admin/drafts/journey_edit/{test_ref}",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert "updated_at" in get_data, "GET response missing updated_at"
        
        # Cleanup
        api_client.delete(
            f"{BASE_URL}/api/admin/drafts/journey_edit/{test_ref}",
            headers=auth_headers
        )
        
        print("PASS: Drafts include proper timestamps")


class TestCleanup:
    """Cleanup any remaining test drafts"""
    
    def test_cleanup_test_drafts(self, api_client, auth_headers):
        """Remove any remaining TEST_ drafts"""
        # List all drafts
        response = api_client.get(f"{BASE_URL}/api/admin/drafts", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            for draft in data.get("drafts", []):
                draft_data = draft.get("data", {})
                if isinstance(draft_data.get("name"), str) and draft_data["name"].startswith("TEST_"):
                    api_client.delete(
                        f"{BASE_URL}/api/admin/drafts/{draft['draft_type']}/{draft['reference_id']}",
                        headers=auth_headers
                    )
                    print(f"Cleaned up draft: {draft['draft_type']}/{draft['reference_id']}")
        
        print("PASS: Test drafts cleaned up")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
