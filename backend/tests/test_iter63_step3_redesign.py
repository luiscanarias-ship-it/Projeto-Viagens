"""
Iteration 63 - Step 3 Redesign Tests
Tests for the new CheckoutModal Step 3 (Payment Instructions & Confirmation)
- PUT /api/contributions/{contribution_id}/confirm-details endpoint
- Email required validation
- Contributor details update
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestConfirmDetailsEndpoint:
    """Tests for PUT /api/contributions/{contribution_id}/confirm-details"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data - create a contribution first"""
        self.test_journey_id = "journey_china001"
        self.test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_name = "Test User"
        
    def create_test_contribution(self):
        """Helper to create a test contribution"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 10,
            "payment_method": "mbway",
            "journey_id": self.test_journey_id,
            "contributor_name": None,
            "contributor_email": None
        })
        assert response.status_code == 200, f"Failed to create contribution: {response.text}"
        return response.json()
    
    def test_confirm_details_with_email_only(self):
        """Test confirming with email only (name is optional)"""
        # Create contribution
        contrib = self.create_test_contribution()
        contribution_id = contrib["contribution_id"]
        
        # Confirm with email only
        response = requests.put(
            f"{BASE_URL}/api/contributions/{contribution_id}/confirm-details",
            json={"contributor_email": self.test_email}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["status"] == "ok"
        assert "Obrigado" in data["message"]
        print(f"✓ Confirm details with email only: {data['message']}")
    
    def test_confirm_details_with_name_and_email(self):
        """Test confirming with both name and email"""
        # Create contribution
        contrib = self.create_test_contribution()
        contribution_id = contrib["contribution_id"]
        
        # Confirm with name and email
        response = requests.put(
            f"{BASE_URL}/api/contributions/{contribution_id}/confirm-details",
            json={
                "contributor_name": self.test_name,
                "contributor_email": self.test_email
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["status"] == "ok"
        print(f"✓ Confirm details with name and email: {data['message']}")
    
    def test_confirm_details_missing_email_returns_400(self):
        """Test that missing email returns 400 error"""
        # Create contribution
        contrib = self.create_test_contribution()
        contribution_id = contrib["contribution_id"]
        
        # Try to confirm without email
        response = requests.put(
            f"{BASE_URL}/api/contributions/{contribution_id}/confirm-details",
            json={"contributor_name": self.test_name}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "Email" in data.get("detail", "") or "email" in data.get("detail", "").lower()
        print(f"✓ Missing email returns 400: {data['detail']}")
    
    def test_confirm_details_empty_email_returns_400(self):
        """Test that empty email returns 400 error"""
        # Create contribution
        contrib = self.create_test_contribution()
        contribution_id = contrib["contribution_id"]
        
        # Try to confirm with empty email
        response = requests.put(
            f"{BASE_URL}/api/contributions/{contribution_id}/confirm-details",
            json={"contributor_email": ""}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✓ Empty email returns 400")
    
    def test_confirm_details_nonexistent_contribution_returns_404(self):
        """Test that non-existent contribution returns 404"""
        fake_id = f"contrib_{uuid.uuid4().hex[:12]}"
        
        response = requests.put(
            f"{BASE_URL}/api/contributions/{fake_id}/confirm-details",
            json={"contributor_email": self.test_email}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ Non-existent contribution returns 404")


class TestMBWayContributionFlow:
    """Tests for MBWay contribution creation flow"""
    
    def test_create_mbway_contribution(self):
        """Test creating an MBWay contribution returns payment_reference"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 20,
            "payment_method": "mbway",
            "journey_id": "journey_china001"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "contribution_id" in data
        assert "payment_reference" in data
        assert data["payment_method"] == "mbway"
        assert data["amount"] == 20
        assert data["status"] == "pending"
        
        # Payment reference should be in format CN-XXXX
        assert data["payment_reference"].startswith("CN-")
        print(f"✓ MBWay contribution created: {data['contribution_id']} with ref {data['payment_reference']}")
        
        return data
    
    def test_mbway_contribution_all_amounts(self):
        """Test MBWay contribution accepts all valid amounts"""
        valid_amounts = [10, 20, 50, 100, 200, 500, 1000]
        
        for amount in valid_amounts:
            response = requests.post(f"{BASE_URL}/api/contributions/create", json={
                "amount": amount,
                "payment_method": "mbway",
                "journey_id": "journey_china001"
            })
            assert response.status_code == 200, f"Amount {amount} failed: {response.text}"
            print(f"✓ MBWay accepts amount: €{amount}")
    
    def test_mbway_contribution_invalid_amount(self):
        """Test MBWay contribution rejects invalid amounts"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 15,  # Invalid amount
            "payment_method": "mbway",
            "journey_id": "journey_china001"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ MBWay rejects invalid amount (15)")


class TestCryptoContributionFlow:
    """Tests for Crypto contribution creation flow"""
    
    def test_create_crypto_contribution(self):
        """Test creating a crypto contribution"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 50,
            "payment_method": "crypto",
            "crypto_type": "btc",
            "journey_id": "journey_china001"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "contribution_id" in data
        assert "payment_reference" in data
        assert data["payment_method"] == "crypto"
        assert data["crypto_type"] == "btc"
        print(f"✓ Crypto contribution created: {data['contribution_id']}")
    
    def test_crypto_requires_crypto_type(self):
        """Test crypto contribution requires crypto_type"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 50,
            "payment_method": "crypto",
            "journey_id": "journey_china001"
            # Missing crypto_type
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Crypto requires crypto_type")


class TestPaymentInfo:
    """Tests for payment info endpoint"""
    
    def test_get_payment_info(self):
        """Test GET /api/contributions/payment-info returns MBWay phone"""
        response = requests.get(f"{BASE_URL}/api/contributions/payment-info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check MBWay info
        assert "mbway" in data
        assert "phone" in data["mbway"]
        assert "+351" in data["mbway"]["phone"]
        print(f"✓ Payment info returns MBWay phone: {data['mbway']['phone']}")
        
        # Check crypto addresses
        assert "crypto" in data
        assert "btc" in data["crypto"]
        assert "address" in data["crypto"]["btc"]
        print(f"✓ Payment info returns crypto addresses")


class TestJourneyProgress:
    """Tests for journey progress endpoint"""
    
    def test_get_journey_progress(self):
        """Test GET /api/journeys/{journey_id}/progress returns contributor count"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_china001/progress")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields for social proof
        assert "percentage" in data
        assert "contributor_count" in data
        assert "journey_contributor_count" in data
        
        print(f"✓ Journey progress: {data['percentage']}% funded, {data['journey_contributor_count']} contributors")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
