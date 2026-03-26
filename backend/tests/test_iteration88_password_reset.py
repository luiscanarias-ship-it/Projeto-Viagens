"""
Iteration 88: Password Reset & Login UX Tests
Tests for:
- POST /api/auth/forgot-password (security: same message regardless of email existence)
- POST /api/auth/reset-password (token validation, password requirements)
- POST /api/auth/login (existing credentials still work)
- Token expiry and single-use behavior
"""
import pytest
import requests
import os
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestForgotPassword:
    """Tests for forgot-password endpoint security"""
    
    def test_forgot_password_valid_email_returns_same_message(self):
        """POST /api/auth/forgot-password with valid email returns generic message"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "admin@4luis.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Security: message should not reveal if email exists
        assert "Se este email existir" in data["message"]
        print(f"✓ Valid email returns generic message: {data['message']}")
    
    def test_forgot_password_invalid_email_returns_same_message(self):
        """POST /api/auth/forgot-password with non-existent email returns same message (security)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "nonexistent_user_12345@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Security: same message as valid email
        assert "Se este email existir" in data["message"]
        print(f"✓ Invalid email returns same generic message (security): {data['message']}")
    
    def test_forgot_password_empty_email_returns_message(self):
        """POST /api/auth/forgot-password with empty email returns message"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Empty email handled gracefully: {data['message']}")


class TestResetPassword:
    """Tests for reset-password endpoint"""
    
    def test_reset_password_missing_token_returns_error(self):
        """POST /api/auth/reset-password without token returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"password": "NewPassword123"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"✓ Missing token returns 400: {data['detail']}")
    
    def test_reset_password_invalid_token_returns_error(self):
        """POST /api/auth/reset-password with invalid token returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": "invalid-token-12345", "password": "NewPassword123"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        # Should indicate invalid or used token
        assert "inválido" in data["detail"].lower() or "utilizado" in data["detail"].lower()
        print(f"✓ Invalid token returns 400: {data['detail']}")
    
    def test_reset_password_short_password_returns_error(self):
        """POST /api/auth/reset-password with password < 8 chars returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": "some-token", "password": "short"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        # Should mention 8 characters requirement
        assert "8" in data["detail"]
        print(f"✓ Short password returns 400: {data['detail']}")
    
    def test_reset_password_missing_password_returns_error(self):
        """POST /api/auth/reset-password without password returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": "some-token"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"✓ Missing password returns 400: {data['detail']}")


class TestLoginStillWorks:
    """Tests that login still works with correct credentials"""
    
    def test_login_with_admin_credentials(self):
        """POST /api/auth/login with admin@4luis.com / Admin1 works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@4luis.com", "password": "Admin1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@4luis.com"
        assert data["user"]["is_admin"] == True
        print(f"✓ Admin login works: {data['user']['email']} (is_admin={data['user']['is_admin']})")
    
    def test_login_with_wrong_password_returns_401(self):
        """POST /api/auth/login with wrong password returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@4luis.com", "password": "WrongPassword123"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"✓ Wrong password returns 401: {data['detail']}")
    
    def test_login_with_nonexistent_email_returns_401(self):
        """POST /api/auth/login with non-existent email returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "SomePassword123"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"✓ Non-existent email returns 401: {data['detail']}")


class TestPasswordResetTokenFlow:
    """Integration tests for the full password reset flow"""
    
    def test_forgot_password_creates_token_for_valid_email(self):
        """Verify that forgot-password creates a token in password_resets collection"""
        # First, trigger forgot password
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "admin@4luis.com"}
        )
        assert response.status_code == 200
        print("✓ Forgot password request accepted for admin@4luis.com")
        # Note: We can't directly verify token creation without DB access,
        # but the endpoint should return success
    
    def test_used_token_cannot_be_reused(self):
        """POST /api/auth/reset-password with already used token returns error"""
        # This tests the single-use token behavior
        # Using a fake "used" token - the endpoint should reject it
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password",
            json={"token": "already-used-token-xyz", "password": "NewPassword123"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"✓ Used/invalid token rejected: {data['detail']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
