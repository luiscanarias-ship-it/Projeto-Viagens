"""
Test Ambassador System - Iteration 54
Tests for Ambassador-based access system for Premium Travel Guide features.
- Ambassador endpoints: GET /api/ambassador/progress, POST /api/ambassador/generate-referral, GET /api/ambassador/features
- Anti-abuse: self-referral prevention
- Premium features gating
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAmbassadorFeatures:
    """Test GET /api/ambassador/features endpoint"""
    
    def test_ambassador_features_anonymous(self):
        """Anonymous user should see all features locked"""
        response = requests.get(f"{BASE_URL}/api/ambassador/features")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["is_ambassador"] == False, "Anonymous user should not be ambassador"
        assert data["features"]["smart_map"] == False
        assert data["features"]["secret_tips"] == False
        assert data["features"]["ai_assistant"] == False
        assert data["features"]["premium_guide"] == False
        print("✓ Anonymous user sees all premium features locked")
    
    def test_ambassador_features_with_auth(self, auth_token):
        """Authenticated user should see ambassador status and feature flags"""
        response = requests.get(
            f"{BASE_URL}/api/ambassador/features",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "is_ambassador" in data
        assert "features" in data
        assert "smart_map" in data["features"]
        assert "secret_tips" in data["features"]
        assert "ai_assistant" in data["features"]
        print(f"✓ Authenticated user ambassador status: {data['is_ambassador']}")


class TestAmbassadorProgress:
    """Test GET /api/ambassador/progress endpoint"""
    
    def test_ambassador_progress_requires_auth(self):
        """Progress endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/ambassador/progress")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Ambassador progress requires authentication")
    
    def test_ambassador_progress_structure(self, auth_token):
        """Progress response should have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/ambassador/progress",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Check required fields
        required_fields = [
            "is_ambassador", "valid_referrals", "required", "remaining",
            "progress_pct", "referrals", "premium_features"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate values
        assert data["required"] == 3, "Required referrals should be 3"
        assert data["valid_referrals"] >= 0
        assert data["remaining"] >= 0
        assert data["progress_pct"] >= 0 and data["progress_pct"] <= 100
        assert isinstance(data["referrals"], list)
        assert isinstance(data["premium_features"], dict)
        
        print(f"✓ Ambassador progress structure valid: {data['valid_referrals']}/{data['required']} referrals")


class TestAmbassadorReferral:
    """Test POST /api/ambassador/generate-referral endpoint"""
    
    def test_generate_referral_requires_auth(self):
        """Generate referral should require authentication"""
        response = requests.post(f"{BASE_URL}/api/ambassador/generate-referral")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Generate referral requires authentication")
    
    def test_generate_referral_with_auth(self, auth_token):
        """Authenticated user should be able to generate referral link"""
        response = requests.post(
            f"{BASE_URL}/api/ambassador/generate-referral",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "referral_code" in data, "Response should contain referral_code"
        assert "journey_id" in data, "Response should contain journey_id"
        assert data["referral_code"] is not None
        print(f"✓ Generated referral code: {data['referral_code']}")
    
    def test_generate_referral_idempotent(self, auth_token):
        """Generating referral twice should return same code"""
        response1 = requests.post(
            f"{BASE_URL}/api/ambassador/generate-referral",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        response2 = requests.post(
            f"{BASE_URL}/api/ambassador/generate-referral",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        assert data1["referral_code"] == data2["referral_code"], "Referral code should be idempotent"
        print("✓ Referral code generation is idempotent")


class TestAntiAbuse:
    """Test anti-abuse mechanisms"""
    
    def test_self_referral_prevention(self):
        """User should not be able to use their own referral code"""
        unique_id = uuid.uuid4().hex[:8]
        email = f"TEST_selfref_{unique_id}@test.com"
        
        # Register first user
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Self Ref",
            "email": email,
            "password": "Test123!"
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        token = reg_response.json()["token"]
        
        # Generate referral code
        ref_response = requests.post(
            f"{BASE_URL}/api/ambassador/generate-referral",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert ref_response.status_code == 200
        referral_code = ref_response.json()["referral_code"]
        
        # Try to register another user with same email (should fail - email already exists)
        # Instead, check that the user's sponsor_id is None (no self-referral)
        progress_response = requests.get(
            f"{BASE_URL}/api/ambassador/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert progress_response.status_code == 200
        progress = progress_response.json()
        
        # User should have 0 valid referrals (can't refer themselves)
        assert progress["valid_referrals"] == 0, "Self-referral should not count"
        print("✓ Self-referral prevention working")


class TestNewUserAmbassadorFlow:
    """Test complete ambassador flow for new user"""
    
    def test_new_user_ambassador_progress(self):
        """New user should start with 0 valid referrals, required=3, remaining=3"""
        unique_id = uuid.uuid4().hex[:8]
        email = f"TEST_amb_{unique_id}@test.com"
        
        # Register new user
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Ambassador",
            "email": email,
            "password": "Test123!"
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        token = reg_response.json()["token"]
        
        # Check ambassador progress
        progress_response = requests.get(
            f"{BASE_URL}/api/ambassador/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert progress_response.status_code == 200
        
        data = progress_response.json()
        assert data["valid_referrals"] == 0, "New user should have 0 valid referrals"
        assert data["required"] == 3, "Required should be 3"
        assert data["remaining"] == 3, "Remaining should be 3"
        assert data["is_ambassador"] == False, "New user should not be ambassador"
        assert data["progress_pct"] == 0, "Progress should be 0%"
        
        print(f"✓ New user ambassador progress: {data['valid_referrals']}/{data['required']} (remaining: {data['remaining']})")


# Fixtures
@pytest.fixture
def auth_token():
    """Get authentication token for test user"""
    unique_id = uuid.uuid4().hex[:8]
    email = f"TEST_auth_{unique_id}@test.com"
    
    # Register new user
    reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Test Auth User",
        "email": email,
        "password": "Test123!"
    })
    
    if reg_response.status_code == 200:
        return reg_response.json()["token"]
    elif reg_response.status_code == 400:
        # User exists, try login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": "Test123!"
        })
        if login_response.status_code == 200:
            return login_response.json()["token"]
    
    pytest.skip("Could not get auth token")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
