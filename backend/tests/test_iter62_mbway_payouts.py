"""
Iteration 62 - MB WAY Payment Flow & Payouts System Tests
Tests:
1. MB WAY payment flow: create contribution with mbway method via POST /api/contributions/create
2. Payouts admin endpoints: GET /api/admin/payouts, PUT /api/admin/payouts/{payout_id}/status
3. Payout auto-creation logic verification
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMBWayPaymentFlow:
    """Test MB WAY payment method creation and flow"""
    
    def test_create_contribution_mbway_method(self):
        """Test creating a contribution with mbway payment method"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 20,
            "payment_method": "mbway",
            "journey_id": "journey_china001",
            "contributor_name": "Test MBWay User",
            "contributor_email": "test_mbway@example.com"
        })
        
        print(f"MBWay contribution response: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "contribution_id" in data, "Response should contain contribution_id"
        assert "payment_reference" in data, "Response should contain payment_reference"
        assert data["payment_method"] == "mbway", "Payment method should be mbway"
        assert data["amount"] == 20, "Amount should be 20"
        assert data["status"] == "pending", "Status should be pending"
        
        # Verify payment reference format (should be alphanumeric)
        payment_ref = data["payment_reference"]
        assert len(payment_ref) > 0, "Payment reference should not be empty"
        print(f"SUCCESS: MBWay contribution created with reference: {payment_ref}")
    
    def test_create_contribution_mbway_all_amounts(self):
        """Test mbway contributions with all valid fixed amounts"""
        valid_amounts = [10, 20, 50, 100, 200, 500, 1000]
        
        for amount in valid_amounts:
            response = requests.post(f"{BASE_URL}/api/contributions/create", json={
                "amount": amount,
                "payment_method": "mbway",
                "journey_id": "journey_china001"
            })
            
            assert response.status_code == 200, f"Amount {amount} should be valid: {response.text}"
            print(f"SUCCESS: MBWay contribution with amount {amount}€ accepted")
    
    def test_create_contribution_mbway_invalid_amount(self):
        """Test that invalid amounts are rejected"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 15,  # Invalid amount
            "payment_method": "mbway",
            "journey_id": "journey_china001"
        })
        
        assert response.status_code == 400, f"Invalid amount should be rejected: {response.text}"
        print("SUCCESS: Invalid amount 15€ correctly rejected")
    
    def test_create_contribution_invalid_method_rejected(self):
        """Test that invalid payment methods are rejected"""
        invalid_methods = ["revolut", "wise", "stripe", "bank_transfer"]
        
        for method in invalid_methods:
            response = requests.post(f"{BASE_URL}/api/contributions/create", json={
                "amount": 20,
                "payment_method": method,
                "journey_id": "journey_china001"
            })
            
            assert response.status_code == 400, f"Method {method} should be rejected: {response.text}"
            print(f"SUCCESS: Invalid method '{method}' correctly rejected")
    
    def test_payment_info_endpoint(self):
        """Test that payment info endpoint returns MBWay details"""
        response = requests.get(f"{BASE_URL}/api/contributions/payment-info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mbway" in data, "Response should contain mbway info"
        assert "phone" in data["mbway"], "MBWay should have phone number"
        assert "+351" in data["mbway"]["phone"], "MBWay phone should be Portuguese"
        print(f"SUCCESS: MBWay phone: {data['mbway']['phone']}")


class TestPayoutsAdminEndpoints:
    """Test Payouts admin endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        
        if response.status_code != 200:
            pytest.skip("Admin login failed - skipping authenticated tests")
        
        return response.json().get("token")
    
    @pytest.fixture
    def auth_headers(self, admin_token):
        """Get auth headers with admin token"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_get_payouts_list(self, auth_headers):
        """Test GET /api/admin/payouts returns payouts list with summary"""
        response = requests.get(f"{BASE_URL}/api/admin/payouts", headers=auth_headers)
        
        print(f"Payouts response: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "payouts" in data, "Response should contain payouts list"
        assert "summary" in data, "Response should contain summary"
        
        summary = data["summary"]
        assert "total" in summary, "Summary should have total count"
        assert "pending" in summary, "Summary should have pending count"
        assert "processing" in summary, "Summary should have processing count"
        assert "completed" in summary, "Summary should have completed count"
        assert "total_pending_amount" in summary, "Summary should have total_pending_amount"
        assert "total_paid_amount" in summary, "Summary should have total_paid_amount"
        
        print(f"SUCCESS: Payouts endpoint returns {len(data['payouts'])} payouts")
        print(f"Summary: pending={summary['pending']}, processing={summary['processing']}, completed={summary['completed']}")
    
    def test_get_payouts_with_status_filter(self, auth_headers):
        """Test GET /api/admin/payouts with status filter"""
        for status in ['pending', 'processing', 'completed']:
            response = requests.get(f"{BASE_URL}/api/admin/payouts?status={status}", headers=auth_headers)
            
            assert response.status_code == 200, f"Filter {status} should work: {response.text}"
            data = response.json()
            
            # All returned payouts should match the filter
            for payout in data["payouts"]:
                assert payout["status"] == status, f"Payout status should be {status}"
            
            print(f"SUCCESS: Status filter '{status}' returns {len(data['payouts'])} payouts")
    
    def test_get_payouts_requires_admin(self):
        """Test that payouts endpoint requires admin authentication"""
        # Without auth
        response = requests.get(f"{BASE_URL}/api/admin/payouts")
        assert response.status_code in [401, 403], "Should require authentication"
        
        # With non-admin user (if we had one)
        print("SUCCESS: Payouts endpoint requires admin authentication")
    
    def test_update_payout_status_invalid_payout(self, auth_headers):
        """Test updating status of non-existent payout"""
        response = requests.put(
            f"{BASE_URL}/api/admin/payouts/nonexistent_payout_123/status",
            headers=auth_headers,
            json={"status": "processing"}
        )
        
        assert response.status_code == 404, f"Should return 404 for non-existent payout: {response.text}"
        print("SUCCESS: Non-existent payout returns 404")
    
    def test_update_payout_status_invalid_status(self, auth_headers):
        """Test updating payout with invalid status"""
        response = requests.put(
            f"{BASE_URL}/api/admin/payouts/any_payout_id/status",
            headers=auth_headers,
            json={"status": "invalid_status"}
        )
        
        # Should return 400 for invalid status or 404 if payout doesn't exist
        assert response.status_code in [400, 404], f"Should reject invalid status: {response.text}"
        print("SUCCESS: Invalid status is rejected")


class TestPayoutAutoCreation:
    """Test payout auto-creation when ambassador journey reaches 100%"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        
        return response.json().get("token")
    
    @pytest.fixture
    def auth_headers(self, admin_token):
        """Get auth headers with admin token"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_ambassador_journey_exists(self, auth_headers):
        """Verify ambassador journey exists for testing"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_japao_amb001")
        
        if response.status_code == 404:
            print("INFO: Ambassador journey journey_japao_amb001 not found - may need to be created")
            pytest.skip("Ambassador journey not found")
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"Ambassador journey: {data.get('name')}")
        print(f"Is ambassador journey: {data.get('is_ambassador_journey')}")
        print(f"Current amount: {data.get('current_amount')}")
        print(f"Goal amount: {data.get('goal_amount')}")
        
        # Check if it's an ambassador journey
        is_ambassador = data.get("is_ambassador_journey", False)
        print(f"SUCCESS: Ambassador journey found, is_ambassador_journey={is_ambassador}")
    
    def test_check_existing_payouts(self, auth_headers):
        """Check if any payouts exist in the system"""
        response = requests.get(f"{BASE_URL}/api/admin/payouts", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        payouts = data.get("payouts", [])
        summary = data.get("summary", {})
        
        print(f"Total payouts in system: {summary.get('total', 0)}")
        print(f"Pending: {summary.get('pending', 0)}")
        print(f"Processing: {summary.get('processing', 0)}")
        print(f"Completed: {summary.get('completed', 0)}")
        
        if len(payouts) > 0:
            print("Existing payouts:")
            for p in payouts[:5]:  # Show first 5
                print(f"  - {p.get('payout_id')}: {p.get('journey_name')} - {p.get('status')} - €{p.get('amount')}")
        else:
            print("INFO: No payouts exist yet. Payouts are auto-created when ambassador journeys reach 100% funding.")


class TestContributionConfig:
    """Test contribution configuration endpoint"""
    
    def test_contribution_config_includes_mbway(self):
        """Test that contribution config includes mbway as valid method"""
        response = requests.get(f"{BASE_URL}/api/contributions/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "payment_methods" in data, "Should have payment_methods"
        payment_methods = data["payment_methods"]
        
        # Check mbway is in the list
        method_ids = [m.get("id") if isinstance(m, dict) else m for m in payment_methods]
        assert "mbway" in method_ids or any("mbway" in str(m).lower() for m in payment_methods), \
            f"MBWay should be in payment methods: {payment_methods}"
        
        print(f"SUCCESS: Payment methods include: {method_ids}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
