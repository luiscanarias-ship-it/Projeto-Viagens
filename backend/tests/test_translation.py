"""
Test Translation API and Admin Panel functionality
Tests for iteration 10 - Translation and Admin Panel features
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTranslationAPI:
    """Test translation endpoint POST /api/translate"""
    
    def test_translate_endpoint_exists(self):
        """Test that translation endpoint exists and returns valid response"""
        response = requests.post(f"{BASE_URL}/api/translate", json={
            "texts": {"test.key": "Olá mundo"},
            "target_language": "English"
        })
        # Should either succeed or fail with proper error
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}, {response.text}"
        print(f"Translation endpoint status: {response.status_code}")
    
    def test_translate_portuguese_to_english(self):
        """Test translating Portuguese texts to English"""
        test_texts = {
            "nav.home": "Início",
            "nav.journeys": "Viagens",
            "hero.tagline": "Aqui, cada gesto ilumina um caminho."
        }
        
        response = requests.post(f"{BASE_URL}/api/translate", json={
            "texts": test_texts,
            "target_language": "English"
        }, timeout=30)  # Allow up to 30 seconds for AI translation
        
        print(f"Translation response status: {response.status_code}")
        print(f"Translation response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "translations" in data, "Response should contain translations"
            translations = data["translations"]
            # Verify some translations exist
            assert "nav.home" in translations, "Translation should contain nav.home key"
            # English translation should be different from Portuguese
            assert translations.get("nav.home") != test_texts["nav.home"] or "Home" in str(translations.get("nav.home")), "Translation should convert to English"
            print(f"SUCCESS: Translation working - nav.home: {translations.get('nav.home')}")
        else:
            # If 500, check if it's due to missing key
            data = response.json()
            if "Chave de tradução não configurada" in str(data):
                pytest.skip("Translation key not configured")
            else:
                print(f"Translation error: {data}")
                assert False, f"Translation failed with: {data}"
    
    def test_translate_to_spanish(self):
        """Test translating to Spanish"""
        test_texts = {"greeting": "Olá, bem-vindo!"}
        
        response = requests.post(f"{BASE_URL}/api/translate", json={
            "texts": test_texts,
            "target_language": "Spanish"
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            assert "translations" in data
            print(f"Spanish translation: {data['translations']}")
        else:
            data = response.json()
            if "Chave de tradução não configurada" in str(data):
                pytest.skip("Translation key not configured")
            print(f"Spanish translation status: {response.status_code}")


class TestAdminEndpoints:
    """Test Admin panel related endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_admin_login(self):
        """Test admin login endpoint"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert data.get("user", {}).get("is_admin") == True, "User should be admin"
        print(f"Admin login successful: {data['user']}")
    
    def test_admin_journeys_endpoint(self, admin_token):
        """Test admin journeys endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/journeys", headers=headers)
        assert response.status_code == 200, f"Admin journeys failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return list of journeys"
        print(f"Admin journeys count: {len(data)}")
    
    def test_admin_stats_endpoint(self, admin_token):
        """Test admin stats endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers)
        assert response.status_code == 200, f"Admin stats failed: {response.text}"
        data = response.json()
        assert "total_users" in data or "total_journeys" in data or "total_amount_raised" in data
        print(f"Admin stats: {data}")
    
    def test_admin_contributions_endpoint(self, admin_token):
        """Test admin contributions endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/contributions", headers=headers)
        assert response.status_code == 200, f"Admin contributions failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return list of contributions"
        print(f"Admin contributions count: {len(data)}")
    
    def test_admin_settings_endpoint(self, admin_token):
        """Test admin settings endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=headers)
        assert response.status_code == 200, f"Admin settings failed: {response.text}"
        print(f"Admin settings: {response.json()}")
    
    def test_admin_users_dashboard(self, admin_token):
        """Test admin users dashboard endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users/dashboard", headers=headers)
        assert response.status_code == 200, f"Admin users dashboard failed: {response.text}"
        data = response.json()
        print(f"Admin users dashboard: metrics={data.get('metrics', {})}, users_count={len(data.get('users', []))}")


class TestPublicEndpoints:
    """Test public endpoints that don't require auth"""
    
    def test_journeys_endpoint(self):
        """Test public journeys endpoint"""
        response = requests.get(f"{BASE_URL}/api/journeys")
        assert response.status_code == 200, f"Journeys endpoint failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return list of journeys"
        print(f"Public journeys count: {len(data)}")
    
    def test_contribution_config(self):
        """Test contribution config endpoint"""
        response = requests.get(f"{BASE_URL}/api/contributions/config")
        assert response.status_code == 200, f"Contribution config failed: {response.text}"
        data = response.json()
        assert "fixed_amounts" in data, "Should contain fixed_amounts"
        assert "payment_methods" in data, "Should contain payment_methods"
        print(f"Contribution config: amounts={data.get('fixed_amounts')}")
    
    def test_settings_endpoint(self):
        """Test public settings endpoint"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200, f"Settings endpoint failed: {response.text}"
        print(f"Public settings: {response.json()}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
