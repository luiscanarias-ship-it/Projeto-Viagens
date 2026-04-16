"""
Test Payment Routes Migration - Phase 1+2+3 + Admin
Tests all payment/contribution endpoints extracted from server.py to routes/payment_routes.py
Business logic in services/payment_service.py and services/referral_service.py
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPaymentRoutesReadOnly:
    """Phase 1: Read-only payment endpoints"""
    
    def test_get_contribution_config(self):
        """GET /api/contributions/config - contribution config with amounts and tips"""
        response = requests.get(f"{BASE_URL}/api/contributions/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "fixed_amounts" in data, "Missing fixed_amounts"
        assert "payment_methods" in data, "Missing payment_methods"
        assert "tip_options" in data, "Missing tip_options"
        assert "default_tip" in data, "Missing default_tip"
        assert "currency" in data, "Missing currency"
        assert data["currency"] == "EUR"
        
        # Validate tip_options structure
        assert isinstance(data["tip_options"], list)
        for tip in data["tip_options"]:
            assert "value" in tip
            assert "label" in tip
        
        print(f"Contribution config: fixed_amounts={data['fixed_amounts']}, tip_options count={len(data['tip_options'])}")
    
    def test_get_payment_info(self):
        """GET /api/contributions/payment-info - payment addresses (crypto, mbway)"""
        response = requests.get(f"{BASE_URL}/api/contributions/payment-info")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "mbway" in data, "Missing mbway payment info"
        assert "crypto" in data, "Missing crypto payment info"
        assert "paypal" in data, "Missing paypal payment info"
        
        # Validate mbway structure
        assert "phone" in data["mbway"]
        assert "name" in data["mbway"]
        
        # Validate crypto structure
        assert "btc" in data["crypto"]
        assert "eth" in data["crypto"]
        assert "usdt" in data["crypto"]
        
        print(f"Payment info: mbway={data['mbway']['phone']}, crypto types={list(data['crypto'].keys())}")
    
    def test_get_stripe_config(self):
        """GET /api/stripe/config - Stripe publishable key"""
        response = requests.get(f"{BASE_URL}/api/stripe/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "publishable_key" in data, "Missing publishable_key"
        print(f"Stripe config: publishable_key present={bool(data['publishable_key'])}")
    
    def test_get_paypal_config(self):
        """GET /api/paypal/config - PayPal client ID and mode"""
        response = requests.get(f"{BASE_URL}/api/paypal/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "client_id" in data, "Missing client_id"
        assert "mode" in data, "Missing mode"
        assert data["mode"] in ["sandbox", "live"], f"Invalid mode: {data['mode']}"
        
        print(f"PayPal config: mode={data['mode']}, client_id present={bool(data['client_id'])}")


class TestAuthHelper:
    """Helper class for authentication"""
    
    @staticmethod
    def get_admin_token():
        """Login as admin and return token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None


class TestContributionCreation:
    """Phase 2: Contribution creation and validation"""
    
    def test_create_contribution_mbway(self):
        """POST /api/contributions/create - create contribution with mbway"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_china001",
            "support_amount": 20,
            "tip_amount": 0,
            "payment_method": "mbway",
            "contributor_name": "Test User",
            "contributor_email": f"test_{uuid.uuid4().hex[:8]}@example.com"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "contribution_id" in data, "Missing contribution_id"
        assert "payment_reference" in data, "Missing payment_reference"
        assert data["payment_method"] == "mbway"
        assert data["support_amount"] == 20
        assert data["tip_amount"] == 0
        assert data["amount"] == 20  # total = support + tip
        assert data["status"] == "pending"
        
        print(f"Created contribution: {data['contribution_id']}, ref={data['payment_reference']}")
        return data["contribution_id"]
    
    def test_create_contribution_invalid_amount(self):
        """POST /api/contributions/create - invalid amount returns 400"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_china001",
            "support_amount": 15,  # Invalid - not in FIXED_CONTRIBUTION_AMOUNTS
            "tip_amount": 0,
            "payment_method": "mbway"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("Invalid amount correctly rejected")
    
    def test_create_contribution_invalid_journey(self):
        """POST /api/contributions/create - non-existent journey returns 404"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_nonexistent",
            "support_amount": 20,
            "tip_amount": 0,
            "payment_method": "mbway"
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Non-existent journey correctly rejected")
    
    def test_create_contribution_with_tip(self):
        """POST /api/contributions/create - contribution with platform tip"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_china001",
            "support_amount": 20,
            "tip_amount": 2,  # 2€ tip
            "payment_method": "mbway",
            "contributor_email": f"test_{uuid.uuid4().hex[:8]}@example.com"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["support_amount"] == 20
        assert data["tip_amount"] == 2
        assert data["amount"] == 22  # total = 20 + 2
        
        print(f"Created contribution with tip: total={data['amount']}€")


class TestContributionConfirmation:
    """Phase 2: User confirms payment details"""
    
    def test_confirm_contribution_details(self):
        """PUT /api/contributions/{id}/confirm-details - user confirms payment"""
        # First create a contribution
        create_response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_china001",
            "support_amount": 20,
            "tip_amount": 0,
            "payment_method": "mbway"
        })
        assert create_response.status_code == 200
        contribution_id = create_response.json()["contribution_id"]
        
        # Now confirm details
        confirm_response = requests.put(
            f"{BASE_URL}/api/contributions/{contribution_id}/confirm-details",
            json={
                "contributor_name": "Test Confirmer",
                "contributor_email": f"confirm_{uuid.uuid4().hex[:8]}@example.com"
            }
        )
        assert confirm_response.status_code == 200, f"Expected 200, got {confirm_response.status_code}: {confirm_response.text}"
        
        data = confirm_response.json()
        assert "status" in data
        assert "message" in data
        
        print(f"Confirmed contribution: status={data['status']}")
    
    def test_confirm_contribution_missing_email(self):
        """PUT /api/contributions/{id}/confirm-details - missing email returns 400"""
        # First create a contribution
        create_response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_china001",
            "support_amount": 20,
            "tip_amount": 0,
            "payment_method": "mbway"
        })
        assert create_response.status_code == 200
        contribution_id = create_response.json()["contribution_id"]
        
        # Try to confirm without email
        confirm_response = requests.put(
            f"{BASE_URL}/api/contributions/{contribution_id}/confirm-details",
            json={"contributor_name": "Test User"}
        )
        assert confirm_response.status_code == 400, f"Expected 400, got {confirm_response.status_code}"
        print("Missing email correctly rejected")


class TestAmbassadorValidations:
    """Ambassador pending validations endpoint"""
    
    def test_ambassador_pending_validations_unauthenticated(self):
        """GET /api/ambassador/pending-validations - requires auth"""
        response = requests.get(f"{BASE_URL}/api/ambassador/pending-validations")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Unauthenticated access correctly rejected")
    
    def test_ambassador_pending_validations_authenticated(self):
        """GET /api/ambassador/pending-validations - authenticated user"""
        token = TestAuthHelper.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        response = requests.get(
            f"{BASE_URL}/api/ambassador/pending-validations",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "pending" in data
        assert "pending_count" in data
        assert "recently_validated" in data
        
        print(f"Ambassador pending validations: count={data['pending_count']}")


class TestMyContributions:
    """User's contributions endpoint"""
    
    def test_my_contributions_unauthenticated(self):
        """GET /api/contributions/my-contributions - requires auth"""
        response = requests.get(f"{BASE_URL}/api/contributions/my-contributions")
        # Should return 401 or 403 for unauthenticated
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Unauthenticated access correctly rejected")
    
    def test_my_contributions_authenticated(self):
        """GET /api/contributions/my-contributions - authenticated user"""
        token = TestAuthHelper.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        response = requests.get(
            f"{BASE_URL}/api/contributions/my-contributions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "contributions" in data
        assert "total_amount" in data
        assert "total_count" in data
        
        print(f"My contributions: count={data['total_count']}, total={data['total_amount']}€")


class TestAdminContributions:
    """Admin contribution management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for all tests"""
        self.token = TestAuthHelper.get_admin_token()
        if not self.token:
            pytest.skip("Could not get admin token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_get_all_contributions(self):
        """GET /api/admin/contributions - list all contributions (admin)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/contributions",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of contributions"
        
        if data:
            contrib = data[0]
            assert "contribution_id" in contrib
            assert "journey_id" in contrib
            assert "amount" in contrib
            assert "status" in contrib
        
        print(f"Admin contributions: count={len(data)}")
    
    def test_admin_get_pending_contributions(self):
        """GET /api/admin/contributions/pending - pending contributions (admin)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/contributions/pending",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "count" in data
        assert "contributions" in data
        
        print(f"Pending contributions: count={data['count']}")
    
    def test_admin_contribution_reports(self):
        """GET /api/admin/contributions/reports - contribution reports (admin)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/contributions/reports",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "summary" in data
        assert "by_amount" in data
        assert "by_payment_method" in data
        assert "temporal_history" in data
        
        summary = data["summary"]
        assert "total_confirmed" in summary
        assert "total_amount" in summary
        assert "average_contribution" in summary
        
        print(f"Contribution reports: total_confirmed={summary['total_confirmed']}, total_amount={summary['total_amount']}€")
    
    def test_admin_search_contributions_by_reference(self):
        """GET /api/admin/contributions/search?ref=CN - search by reference (admin)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/contributions/search?ref=CN",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "count" in data
        assert "contributions" in data
        
        print(f"Search results for 'CN': count={data['count']}")
    
    def test_admin_search_contributions_missing_ref(self):
        """GET /api/admin/contributions/search - missing ref returns 400"""
        response = requests.get(
            f"{BASE_URL}/api/admin/contributions/search",
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("Missing ref parameter correctly rejected")


class TestAdminContributionActions:
    """Admin confirm/reject/validate contribution endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token and create test contribution"""
        self.token = TestAuthHelper.get_admin_token()
        if not self.token:
            pytest.skip("Could not get admin token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_confirm_contribution(self):
        """PUT /api/admin/contributions/{id}/confirm - admin confirm contribution"""
        # Create a contribution first
        create_response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_china001",
            "support_amount": 20,
            "tip_amount": 0,
            "payment_method": "mbway",
            "contributor_email": f"admin_confirm_{uuid.uuid4().hex[:8]}@example.com"
        })
        assert create_response.status_code == 200
        contribution_id = create_response.json()["contribution_id"]
        
        # Admin confirms
        confirm_response = requests.put(
            f"{BASE_URL}/api/admin/contributions/{contribution_id}/confirm",
            headers=self.headers
        )
        assert confirm_response.status_code == 200, f"Expected 200, got {confirm_response.status_code}: {confirm_response.text}"
        
        data = confirm_response.json()
        assert "message" in data
        
        print(f"Admin confirmed contribution: {contribution_id}")
    
    def test_admin_reject_contribution(self):
        """PUT /api/admin/contributions/{id}/reject - admin reject contribution"""
        # Create a contribution first
        create_response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_china001",
            "support_amount": 20,
            "tip_amount": 0,
            "payment_method": "mbway",
            "contributor_email": f"admin_reject_{uuid.uuid4().hex[:8]}@example.com"
        })
        assert create_response.status_code == 200
        contribution_id = create_response.json()["contribution_id"]
        
        # Admin rejects
        reject_response = requests.put(
            f"{BASE_URL}/api/admin/contributions/{contribution_id}/reject",
            headers=self.headers
        )
        assert reject_response.status_code == 200, f"Expected 200, got {reject_response.status_code}: {reject_response.text}"
        
        data = reject_response.json()
        assert "message" in data
        
        print(f"Admin rejected contribution: {contribution_id}")
    
    def test_admin_validate_contribution_confirm(self):
        """PUT /api/admin/contributions/{id}/validate - admin validate with action=confirm"""
        # Create a contribution first
        create_response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_china001",
            "support_amount": 20,
            "tip_amount": 0,
            "payment_method": "mbway",
            "contributor_email": f"admin_validate_{uuid.uuid4().hex[:8]}@example.com"
        })
        assert create_response.status_code == 200
        contribution_id = create_response.json()["contribution_id"]
        
        # Admin validates with action
        validate_response = requests.put(
            f"{BASE_URL}/api/admin/contributions/{contribution_id}/validate",
            headers=self.headers,
            json={"action": "confirm", "notes": "Test validation"}
        )
        assert validate_response.status_code == 200, f"Expected 200, got {validate_response.status_code}: {validate_response.text}"
        
        data = validate_response.json()
        assert "status" in data
        assert data["status"] == "confirmed"
        
        print(f"Admin validated contribution: {contribution_id}, status={data['status']}")
    
    def test_admin_validate_contribution_reject(self):
        """PUT /api/admin/contributions/{id}/validate - admin validate with action=reject"""
        # Create a contribution first
        create_response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_china001",
            "support_amount": 20,
            "tip_amount": 0,
            "payment_method": "mbway",
            "contributor_email": f"admin_validate_rej_{uuid.uuid4().hex[:8]}@example.com"
        })
        assert create_response.status_code == 200
        contribution_id = create_response.json()["contribution_id"]
        
        # Admin validates with reject action
        validate_response = requests.put(
            f"{BASE_URL}/api/admin/contributions/{contribution_id}/validate",
            headers=self.headers,
            json={"action": "reject", "notes": "Test rejection"}
        )
        assert validate_response.status_code == 200, f"Expected 200, got {validate_response.status_code}: {validate_response.text}"
        
        data = validate_response.json()
        assert "status" in data
        assert data["status"] == "rejected"
        
        print(f"Admin rejected via validate: {contribution_id}, status={data['status']}")
    
    def test_admin_validate_invalid_action(self):
        """PUT /api/admin/contributions/{id}/validate - invalid action returns 400"""
        # Create a contribution first
        create_response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "journey_id": "journey_china001",
            "support_amount": 20,
            "tip_amount": 0,
            "payment_method": "mbway",
            "contributor_email": f"admin_invalid_{uuid.uuid4().hex[:8]}@example.com"
        })
        assert create_response.status_code == 200
        contribution_id = create_response.json()["contribution_id"]
        
        # Try invalid action
        validate_response = requests.put(
            f"{BASE_URL}/api/admin/contributions/{contribution_id}/validate",
            headers=self.headers,
            json={"action": "invalid_action"}
        )
        assert validate_response.status_code == 400, f"Expected 400, got {validate_response.status_code}"
        print("Invalid action correctly rejected")


class TestAdminPayouts:
    """Admin payouts endpoint"""
    
    def test_admin_get_payouts(self):
        """GET /api/admin/payouts - list payouts (admin)"""
        token = TestAuthHelper.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/payouts",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "payouts" in data
        assert "summary" in data
        
        summary = data["summary"]
        assert "total" in summary
        assert "pending" in summary
        assert "completed" in summary
        
        print(f"Admin payouts: total={summary['total']}, pending={summary['pending']}, completed={summary['completed']}")
    
    def test_admin_payouts_unauthenticated(self):
        """GET /api/admin/payouts - requires admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/payouts")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Unauthenticated access correctly rejected")


class TestAmbassadorProgress:
    """Ambassador progress endpoint (still in server.py)"""
    
    def test_ambassador_progress_unauthenticated(self):
        """GET /api/ambassador/progress - requires auth"""
        response = requests.get(f"{BASE_URL}/api/ambassador/progress")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Unauthenticated access correctly rejected")
    
    def test_ambassador_progress_authenticated(self):
        """GET /api/ambassador/progress - authenticated user"""
        token = TestAuthHelper.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        response = requests.get(
            f"{BASE_URL}/api/ambassador/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Check expected fields
        assert "is_ambassador" in data or "level" in data
        
        print(f"Ambassador progress: {data}")


class TestExistingRoutesStillWork:
    """Verify existing routes still work after migration"""
    
    def test_journeys_still_work(self):
        """GET /api/journeys - journeys still work (from journey_routes.py)"""
        response = requests.get(f"{BASE_URL}/api/journeys")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        
        print(f"Journeys endpoint works: count={len(data)}")
    
    def test_homepage_main_journey_still_works(self):
        """GET /api/homepage/main-journey - homepage still loads"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "journey" in data
        assert "progress" in data
        
        print(f"Homepage main journey works: journey={data['journey'].get('name') if data['journey'] else 'None'}")
    
    def test_auth_login_still_works(self):
        """POST /api/auth/login - auth still works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data
        assert "user" in data
        
        print(f"Auth login works: user={data['user'].get('email')}")
    
    def test_auth_login_invalid_credentials(self):
        """POST /api/auth/login - invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Invalid credentials correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
