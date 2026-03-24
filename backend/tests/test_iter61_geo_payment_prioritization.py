"""
Iteration 61 - Geolocation-based Payment Prioritization Tests
Tests:
1. POST /api/contributions/create accepts 'mbway' method
2. POST /api/contributions/create accepts 'crypto' method
3. POST /api/contributions/create rejects 'revolut' and 'wise'
4. GET /api/paypal/config returns client_id
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestGeoPaymentPrioritization:
    """Tests for geolocation-based payment prioritization feature"""
    
    def test_paypal_config_returns_client_id(self):
        """GET /api/paypal/config should return client_id for PayPal SDK"""
        response = requests.get(f"{BASE_URL}/api/paypal/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "client_id" in data, "Response should contain client_id"
        assert data["client_id"], "client_id should not be empty"
        assert "mode" in data, "Response should contain mode"
        print(f"PayPal config: client_id present, mode={data.get('mode')}")
    
    def test_contributions_create_accepts_mbway(self):
        """POST /api/contributions/create should accept 'mbway' as payment method"""
        # First get a valid journey_id
        journeys_response = requests.get(f"{BASE_URL}/api/journeys")
        assert journeys_response.status_code == 200
        journeys = journeys_response.json()
        assert len(journeys) > 0, "Need at least one journey for testing"
        journey_id = journeys[0]["journey_id"]
        
        payload = {
            "amount": 10,
            "payment_method": "mbway",
            "journey_id": journey_id,
            "contributor_name": "Test User",
            "contributor_email": "test@example.com"
        }
        response = requests.post(f"{BASE_URL}/api/contributions/create", json=payload)
        assert response.status_code == 200, f"Expected 200 for mbway, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("payment_method") == "mbway"
        assert "payment_reference" in data
        print(f"MBWay contribution created: {data.get('contribution_id')}")
    
    def test_contributions_create_accepts_crypto(self):
        """POST /api/contributions/create should accept 'crypto' as payment method"""
        journeys_response = requests.get(f"{BASE_URL}/api/journeys")
        journeys = journeys_response.json()
        journey_id = journeys[0]["journey_id"]
        
        payload = {
            "amount": 20,
            "payment_method": "crypto",
            "journey_id": journey_id,
            "crypto_type": "btc",
            "contributor_name": "Crypto User",
            "contributor_email": "crypto@example.com"
        }
        response = requests.post(f"{BASE_URL}/api/contributions/create", json=payload)
        assert response.status_code == 200, f"Expected 200 for crypto, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("payment_method") == "crypto"
        assert data.get("crypto_type") == "btc"
        print(f"Crypto contribution created: {data.get('contribution_id')}")
    
    def test_contributions_create_rejects_revolut(self):
        """POST /api/contributions/create should reject 'revolut' as payment method"""
        journeys_response = requests.get(f"{BASE_URL}/api/journeys")
        journeys = journeys_response.json()
        journey_id = journeys[0]["journey_id"]
        
        payload = {
            "amount": 10,
            "payment_method": "revolut",
            "journey_id": journey_id
        }
        response = requests.post(f"{BASE_URL}/api/contributions/create", json=payload)
        assert response.status_code == 400, f"Expected 400 for revolut, got {response.status_code}"
        print("Revolut correctly rejected with 400")
    
    def test_contributions_create_rejects_wise(self):
        """POST /api/contributions/create should reject 'wise' as payment method"""
        journeys_response = requests.get(f"{BASE_URL}/api/journeys")
        journeys = journeys_response.json()
        journey_id = journeys[0]["journey_id"]
        
        payload = {
            "amount": 10,
            "payment_method": "wise",
            "journey_id": journey_id
        }
        response = requests.post(f"{BASE_URL}/api/contributions/create", json=payload)
        assert response.status_code == 400, f"Expected 400 for wise, got {response.status_code}"
        print("Wise correctly rejected with 400")
    
    def test_contributions_config_returns_valid_methods(self):
        """GET /api/contributions/config should return only valid payment methods"""
        response = requests.get(f"{BASE_URL}/api/contributions/config")
        assert response.status_code == 200
        data = response.json()
        assert "payment_methods" in data
        methods = data["payment_methods"]
        # Should only have crypto, mbway, paypal
        assert "crypto" in methods, "crypto should be in payment_methods"
        assert "mbway" in methods, "mbway should be in payment_methods"
        assert "paypal" in methods, "paypal should be in payment_methods"
        # Should NOT have revolut or wise
        assert "revolut" not in methods, "revolut should NOT be in payment_methods"
        assert "wise" not in methods, "wise should NOT be in payment_methods"
        print(f"Payment methods: {list(methods.keys())}")
    
    def test_payment_info_returns_mbway_phone(self):
        """GET /api/contributions/payment-info should return MBWay phone number"""
        response = requests.get(f"{BASE_URL}/api/contributions/payment-info")
        assert response.status_code == 200
        data = response.json()
        assert "mbway" in data
        assert "phone" in data["mbway"]
        # Phone should be +351968068535 (without spaces in API)
        phone = data["mbway"]["phone"]
        assert "351" in phone and "968068535" in phone, f"MBWay phone should contain 351968068535, got {phone}"
        print(f"MBWay phone: {phone}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
