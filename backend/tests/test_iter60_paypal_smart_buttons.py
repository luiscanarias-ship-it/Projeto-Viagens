"""
Iteration 60 - PayPal Smart Buttons & Payment Methods Cleanup Tests

Tests:
1. Backend: POST /api/contributions/create rejects 'revolut' as payment method
2. Backend: POST /api/contributions/create rejects 'wise' as payment method
3. Backend: POST /api/contributions/create accepts 'mbway' as payment method
4. Backend: POST /api/contributions/create accepts 'crypto' as payment method
5. Backend: POST /api/contributions/create accepts 'paypal' as payment method
6. Backend: GET /api/contribution-config returns only paypal, mbway, crypto methods
7. Backend: GET /api/paypal/config returns client_id for PayPal SDK
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPaymentMethodsValidation:
    """Test that only valid payment methods are accepted"""
    
    def test_reject_revolut_payment_method(self):
        """POST /api/contributions/create should reject 'revolut' as payment method"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 20,
            "payment_method": "revolut",
            "journey_id": "journey_china001"
        })
        # Should return 400 Bad Request
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "revolut" not in data["detail"].lower() or "inválido" in data["detail"].lower() or "invalid" in data["detail"].lower()
        print(f"✓ Revolut correctly rejected: {data['detail']}")
    
    def test_reject_wise_payment_method(self):
        """POST /api/contributions/create should reject 'wise' as payment method"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 20,
            "payment_method": "wise",
            "journey_id": "journey_china001"
        })
        # Should return 400 Bad Request
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Wise correctly rejected: {data['detail']}")
    
    def test_accept_mbway_payment_method(self):
        """POST /api/contributions/create should accept 'mbway' as payment method"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 20,
            "payment_method": "mbway",
            "journey_id": "journey_china001"
        })
        # Should return 200 OK with contribution created
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "contribution_id" in data
        assert "payment_reference" in data
        assert data["payment_method"] == "mbway"
        assert data["status"] == "pending"
        print(f"✓ MBWay accepted: contribution_id={data['contribution_id']}")
    
    def test_accept_crypto_payment_method(self):
        """POST /api/contributions/create should accept 'crypto' as payment method"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 50,
            "payment_method": "crypto",
            "journey_id": "journey_china001",
            "crypto_type": "btc"
        })
        # Should return 200 OK with contribution created
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "contribution_id" in data
        assert "payment_reference" in data
        assert data["payment_method"] == "crypto"
        assert data["crypto_type"] == "btc"
        print(f"✓ Crypto accepted: contribution_id={data['contribution_id']}")
    
    def test_accept_paypal_payment_method(self):
        """POST /api/contributions/create should accept 'paypal' as payment method"""
        response = requests.post(f"{BASE_URL}/api/contributions/create", json={
            "amount": 100,
            "payment_method": "paypal",
            "journey_id": "journey_china001"
        })
        # Should return 200 OK with contribution created
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "contribution_id" in data
        assert "payment_reference" in data
        assert data["payment_method"] == "paypal"
        print(f"✓ PayPal accepted: contribution_id={data['contribution_id']}")


class TestContributionConfig:
    """Test contribution configuration endpoint"""
    
    def test_contribution_config_returns_valid_methods(self):
        """GET /api/contributions/config should return only paypal, mbway, crypto methods"""
        response = requests.get(f"{BASE_URL}/api/contributions/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "payment_methods" in data
        
        payment_methods = data["payment_methods"]
        
        # Should have paypal, mbway, crypto
        assert "paypal" in payment_methods, "PayPal should be in payment_methods"
        assert "mbway" in payment_methods, "MBWay should be in payment_methods"
        assert "crypto" in payment_methods, "Crypto should be in payment_methods"
        
        # Should NOT have revolut or wise
        assert "revolut" not in payment_methods, "Revolut should NOT be in payment_methods"
        assert "wise" not in payment_methods, "Wise should NOT be in payment_methods"
        
        print(f"✓ Payment methods config correct: {list(payment_methods.keys())}")


class TestPayPalConfig:
    """Test PayPal configuration endpoint for Smart Buttons SDK"""
    
    def test_paypal_config_returns_client_id(self):
        """GET /api/paypal/config should return client_id for PayPal SDK"""
        response = requests.get(f"{BASE_URL}/api/paypal/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "client_id" in data, "Response should contain client_id"
        assert data["client_id"], "client_id should not be empty"
        assert len(data["client_id"]) > 10, "client_id should be a valid PayPal client ID"
        
        # Should also have mode (sandbox or live)
        assert "mode" in data, "Response should contain mode"
        assert data["mode"] in ["sandbox", "live"], f"Mode should be sandbox or live, got {data['mode']}"
        
        print(f"✓ PayPal config: client_id={data['client_id'][:20]}..., mode={data['mode']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
