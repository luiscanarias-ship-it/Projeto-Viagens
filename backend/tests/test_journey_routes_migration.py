"""
Test Journey Routes Migration - Phase 2 & 3
Tests all journey endpoints migrated from server.py to routes/journey_routes.py
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestJourneyRoutesPublic:
    """Public journey endpoints (no auth required)"""
    
    def test_get_journeys_list(self):
        """GET /api/journeys - list active journeys"""
        response = requests.get(f"{BASE_URL}/api/journeys")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/journeys - Found {len(data)} active journeys")
    
    def test_get_journey_by_id(self):
        """GET /api/journeys/{journey_id} - get single journey"""
        journey_id = "journey_china001"
        response = requests.get(f"{BASE_URL}/api/journeys/{journey_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "journey_id" in data, "Response should contain journey_id"
        assert data["journey_id"] == journey_id
        print(f"✓ GET /api/journeys/{journey_id} - Journey name: {data.get('name')}")
    
    def test_get_journey_not_found(self):
        """GET /api/journeys/{journey_id} - 404 for non-existent journey"""
        response = requests.get(f"{BASE_URL}/api/journeys/nonexistent_journey_xyz")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ GET /api/journeys/nonexistent - Returns 404 as expected")
    
    def test_get_journey_progress(self):
        """GET /api/journeys/{journey_id}/progress - journey progress"""
        journey_id = "journey_china001"
        response = requests.get(f"{BASE_URL}/api/journeys/{journey_id}/progress")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "percentage" in data, "Response should contain percentage"
        assert "current_amount" in data, "Response should contain current_amount"
        assert "is_funded" in data, "Response should contain is_funded"
        print(f"✓ GET /api/journeys/{journey_id}/progress - {data.get('percentage')}% funded")
    
    def test_get_journey_contributions(self):
        """GET /api/journeys/{journey_id}/contributions - journey contributions"""
        journey_id = "journey_china001"
        response = requests.get(f"{BASE_URL}/api/journeys/{journey_id}/contributions")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "contributions" in data, "Response should contain contributions"
        assert "total" in data, "Response should contain total"
        print(f"✓ GET /api/journeys/{journey_id}/contributions - {data.get('total')} contributions")
    
    def test_get_journey_payment_info(self):
        """GET /api/journey/{journey_id}/payment-info - payment info"""
        journey_id = "journey_china001"
        response = requests.get(f"{BASE_URL}/api/journey/{journey_id}/payment-info")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "payment_mode" in data, "Response should contain payment_mode"
        assert "journey_id" in data, "Response should contain journey_id"
        print(f"✓ GET /api/journey/{journey_id}/payment-info - mode: {data.get('payment_mode')}")
    
    def test_get_success_stories(self):
        """GET /api/success-stories - success stories"""
        response = requests.get(f"{BASE_URL}/api/success-stories")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "stories" in data, "Response should contain stories"
        print(f"✓ GET /api/success-stories - {len(data.get('stories', []))} stories")


class TestHomepageEndpoints:
    """Homepage journey endpoints"""
    
    def test_get_main_journey(self):
        """GET /api/homepage/main-journey - homepage main journey data"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Can be null if no main journey
        assert "journey" in data, "Response should contain journey key"
        assert "progress" in data, "Response should contain progress key"
        assert "contributions" in data, "Response should contain contributions key"
        print(f"✓ GET /api/homepage/main-journey - Journey: {data.get('journey', {}).get('name') if data.get('journey') else 'None'}")
    
    def test_get_ambassador_journeys(self):
        """GET /api/homepage/ambassador-journeys - homepage ambassador journeys"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_count" in data, "Response should contain total_count"
        assert "featured" in data, "Response should contain featured"
        assert "regions" in data, "Response should contain regions"
        print(f"✓ GET /api/homepage/ambassador-journeys - {data.get('total_count')} journeys")
    
    def test_get_curated_dreams(self):
        """GET /api/homepage/curated-dreams - curated dreams fallback"""
        response = requests.get(f"{BASE_URL}/api/homepage/curated-dreams")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "use_curated" in data, "Response should contain use_curated"
        assert "curated_dreams" in data, "Response should contain curated_dreams"
        print(f"✓ GET /api/homepage/curated-dreams - use_curated: {data.get('use_curated')}")
    
    def test_get_realized_journeys(self):
        """GET /api/homepage/realized-journeys - realized journeys"""
        response = requests.get(f"{BASE_URL}/api/homepage/realized-journeys")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_count" in data, "Response should contain total_count"
        assert "countries" in data, "Response should contain countries"
        print(f"✓ GET /api/homepage/realized-journeys - {data.get('total_count')} realized")


class TestAuthEndpoints:
    """Auth endpoints (already migrated to auth_routes.py)"""
    
    def test_login_success(self):
        """POST /api/auth/login - login still works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["is_admin"] == True, "User should be admin"
        print(f"✓ POST /api/auth/login - Admin login successful")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ POST /api/auth/login - Invalid credentials returns 401")


class TestPaymentEndpoints:
    """Payment endpoints (still in server.py)"""
    
    def test_get_contributions_config(self):
        """GET /api/contributions/config - payments still work"""
        response = requests.get(f"{BASE_URL}/api/contributions/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "fixed_amounts" in data, "Response should contain fixed_amounts"
        assert "payment_methods" in data, "Response should contain payment_methods"
        assert "tip_options" in data, "Response should contain tip_options"
        print(f"✓ GET /api/contributions/config - Fixed amounts: {data.get('fixed_amounts')}")


class TestAdminJourneyEndpoints:
    """Admin journey endpoints (require authentication)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed - skipping admin tests")
    
    def test_get_all_journeys_admin(self):
        """GET /api/admin/journeys - list all journeys admin"""
        response = requests.get(f"{BASE_URL}/api/admin/journeys", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/admin/journeys - {len(data)} total journeys (admin)")
    
    def test_get_ambassador_journeys_admin(self):
        """GET /api/admin/ambassador-journeys - list ambassador journeys (admin)"""
        response = requests.get(f"{BASE_URL}/api/admin/ambassador-journeys", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total" in data, "Response should contain total"
        assert "by_status" in data, "Response should contain by_status"
        assert "journeys" in data, "Response should contain journeys"
        print(f"✓ GET /api/admin/ambassador-journeys - {data.get('total')} ambassador journeys")
    
    def test_get_journeys_visibility_admin(self):
        """GET /api/admin/journeys-visibility - visibility data (admin)"""
        response = requests.get(f"{BASE_URL}/api/admin/journeys-visibility", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "count" in data, "Response should contain count"
        assert "journeys" in data, "Response should contain journeys"
        print(f"✓ GET /api/admin/journeys-visibility - {data.get('count')} journeys with visibility")
    
    def test_get_journeys_ready_for_raffle(self):
        """GET /api/admin/journeys-ready-for-raffle - raffle-ready journeys (admin)"""
        response = requests.get(f"{BASE_URL}/api/admin/journeys-ready-for-raffle", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "ready_journeys" in data, "Response should contain ready_journeys"
        assert "total_ready" in data, "Response should contain total_ready"
        print(f"✓ GET /api/admin/journeys-ready-for-raffle - {data.get('total_ready')} ready")
    
    def test_admin_journeys_unauthorized(self):
        """GET /api/admin/journeys - unauthorized without token"""
        response = requests.get(f"{BASE_URL}/api/admin/journeys")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/journeys - Unauthorized returns 401/403")


class TestSeedAndMigration:
    """Seed and migration endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed - skipping admin tests")
    
    def test_seed_journeys_idempotent(self):
        """POST /api/seed-journeys - seed journeys (idempotent)"""
        response = requests.post(f"{BASE_URL}/api/seed-journeys")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Should return "Dados já existem" if data exists
        assert "message" in data, "Response should contain message"
        print(f"✓ POST /api/seed-journeys - {data.get('message')}")
    
    def test_migrate_journey_status(self):
        """POST /api/admin/migrate-journey-status - migration utility (admin)"""
        response = requests.post(f"{BASE_URL}/api/admin/migrate-journey-status", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "modified_count" in data, "Response should contain modified_count"
        print(f"✓ POST /api/admin/migrate-journey-status - {data.get('modified_count')} migrated")


class TestJourneyCRUD:
    """Journey CRUD operations (admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed - skipping admin tests")
    
    def test_create_update_delete_journey(self):
        """Full CRUD cycle: POST, PUT, DELETE /api/admin/journeys"""
        import uuid
        test_id = f"test_journey_{uuid.uuid4().hex[:8]}"
        
        # CREATE
        create_data = {
            "journey_id": test_id,
            "name": "Test Journey",
            "poetic_name": "Test Poetic Name",
            "description": "Test description",
            "emotional_message": "Test emotional message",
            "impact_description": "Test impact",
            "image_url": "https://example.com/image.jpg",
            "goal_amount": 1000.0,
            "currency": "EUR"
        }
        response = requests.post(f"{BASE_URL}/api/admin/journeys", json=create_data, headers=self.headers)
        assert response.status_code == 200, f"Create failed: {response.status_code}: {response.text}"
        created = response.json()
        journey_id = created.get("journey_id")
        print(f"✓ POST /api/admin/journeys - Created journey: {journey_id}")
        
        # UPDATE
        update_data = {"name": "Updated Test Journey", "goal_amount": 2000.0}
        response = requests.put(f"{BASE_URL}/api/admin/journeys/{journey_id}", json=update_data, headers=self.headers)
        assert response.status_code == 200, f"Update failed: {response.status_code}: {response.text}"
        updated = response.json()
        assert updated.get("name") == "Updated Test Journey", "Name should be updated"
        print(f"✓ PUT /api/admin/journeys/{journey_id} - Updated journey")
        
        # DELETE
        response = requests.delete(f"{BASE_URL}/api/admin/journeys/{journey_id}", headers=self.headers)
        assert response.status_code == 200, f"Delete failed: {response.status_code}: {response.text}"
        print(f"✓ DELETE /api/admin/journeys/{journey_id} - Deleted journey")
        
        # VERIFY DELETED
        response = requests.get(f"{BASE_URL}/api/journeys/{journey_id}")
        assert response.status_code == 404, "Journey should be deleted"
        print(f"✓ Verified journey {journey_id} is deleted")


class TestSetMainJourney:
    """Set main journey endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed - skipping admin tests")
    
    def test_set_main_journey(self):
        """POST /api/admin/set-main-journey/{journey_id} - set main journey (admin)"""
        journey_id = "journey_china001"
        response = requests.post(f"{BASE_URL}/api/admin/set-main-journey/{journey_id}", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Response should contain message"
        print(f"✓ POST /api/admin/set-main-journey/{journey_id} - {data.get('message')}")


class TestJourneyProgressWithAdmin:
    """Test journey progress endpoint with admin auth (shows goal_amount)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin login failed - skipping admin tests")
    
    def test_journey_progress_admin_sees_goal(self):
        """GET /api/journeys/{journey_id}/progress - admin sees goal_amount"""
        journey_id = "journey_china001"
        response = requests.get(f"{BASE_URL}/api/journeys/{journey_id}/progress", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "goal_amount" in data, "Admin should see goal_amount"
        print(f"✓ GET /api/journeys/{journey_id}/progress (admin) - goal: {data.get('goal_amount')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
