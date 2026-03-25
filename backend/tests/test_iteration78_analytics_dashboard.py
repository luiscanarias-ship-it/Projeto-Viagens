"""
Iteration 78 - Analytics Dashboard Tests
Tests for the admin analytics dashboard endpoint and frontend integration.
Features tested:
- GET /api/admin/analytics endpoint (auth, response structure)
- Funnel metrics (total_users, contributions, total_raised, ambassadors)
- Affiliate performance (total_clicks, by_platform)
- Share metrics (total, by_type)
- Referral system (total_valid, active_referrers, avg_per_referrer, ambassador_conversion)
- Top plans (shared, affiliate, converting journeys)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAnalyticsEndpointAuth:
    """Test authentication requirements for analytics endpoint"""
    
    def test_analytics_requires_auth(self):
        """GET /api/admin/analytics returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: GET /api/admin/analytics returns 401 without auth")
    
    def test_analytics_with_non_admin_fails(self):
        """GET /api/admin/analytics returns 401/403 for non-admin users"""
        # First register a non-admin user
        import uuid
        test_email = f"test_nonadmin_{uuid.uuid4().hex[:8]}@test.com"
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "name": "Test User",
            "surname": "NonAdmin",
            "password": "testpass123"
        })
        
        if register_response.status_code == 200:
            token = register_response.json().get("token")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
            # Should be 401 or 403 for non-admin
            assert response.status_code in [401, 403], f"Expected 401/403 for non-admin, got {response.status_code}"
            print("PASS: GET /api/admin/analytics returns 401/403 for non-admin users")
        else:
            # User might already exist, skip this test
            pytest.skip("Could not create test user")


class TestAnalyticsEndpointWithAdmin:
    """Test analytics endpoint with admin authentication"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin and get token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_analytics_returns_200_with_admin(self):
        """GET /api/admin/analytics returns 200 with admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: GET /api/admin/analytics returns 200 with admin auth")
    
    def test_analytics_has_all_required_keys(self):
        """Analytics response has all required top-level keys"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        required_keys = ["funnel", "affiliates", "shares", "referrals", 
                        "top_plans_shared", "top_plans_affiliate", "top_converting_journeys"]
        
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"
        
        print(f"PASS: Analytics response has all required keys: {required_keys}")
    
    def test_funnel_object_structure(self):
        """Funnel object has correct structure"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        funnel = data.get("funnel", {})
        required_funnel_keys = ["total_users", "total_contributions", "completed_contributions", 
                               "pending_contributions", "total_raised", "ambassadors", "ambassador_rate"]
        
        for key in required_funnel_keys:
            assert key in funnel, f"Missing funnel key: {key}"
        
        # Validate types
        assert isinstance(funnel["total_users"], int), "total_users should be int"
        assert isinstance(funnel["total_contributions"], int), "total_contributions should be int"
        assert isinstance(funnel["completed_contributions"], int), "completed_contributions should be int"
        assert isinstance(funnel["pending_contributions"], int), "pending_contributions should be int"
        assert isinstance(funnel["total_raised"], (int, float)), "total_raised should be numeric"
        assert isinstance(funnel["ambassadors"], int), "ambassadors should be int"
        assert isinstance(funnel["ambassador_rate"], (int, float)), "ambassador_rate should be numeric"
        
        print(f"PASS: Funnel object has correct structure: {funnel}")
    
    def test_affiliates_object_structure(self):
        """Affiliates object has correct structure"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        affiliates = data.get("affiliates", {})
        assert "total_clicks" in affiliates, "Missing affiliates.total_clicks"
        assert "by_platform" in affiliates, "Missing affiliates.by_platform"
        
        assert isinstance(affiliates["total_clicks"], int), "total_clicks should be int"
        assert isinstance(affiliates["by_platform"], dict), "by_platform should be dict"
        
        print(f"PASS: Affiliates object has correct structure: total_clicks={affiliates['total_clicks']}, platforms={list(affiliates['by_platform'].keys())}")
    
    def test_shares_object_structure(self):
        """Shares object has correct structure"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        shares = data.get("shares", {})
        assert "total" in shares, "Missing shares.total"
        assert "by_type" in shares, "Missing shares.by_type"
        
        assert isinstance(shares["total"], int), "total should be int"
        assert isinstance(shares["by_type"], dict), "by_type should be dict"
        
        print(f"PASS: Shares object has correct structure: total={shares['total']}, types={list(shares['by_type'].keys())}")
    
    def test_referrals_object_structure(self):
        """Referrals object has correct structure"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        referrals = data.get("referrals", {})
        required_referral_keys = ["total_valid", "active_referrers", "avg_per_referrer", "ambassador_conversion"]
        
        for key in required_referral_keys:
            assert key in referrals, f"Missing referrals key: {key}"
        
        assert isinstance(referrals["total_valid"], int), "total_valid should be int"
        assert isinstance(referrals["active_referrers"], int), "active_referrers should be int"
        assert isinstance(referrals["avg_per_referrer"], (int, float)), "avg_per_referrer should be numeric"
        assert isinstance(referrals["ambassador_conversion"], (int, float)), "ambassador_conversion should be numeric"
        
        print(f"PASS: Referrals object has correct structure: {referrals}")
    
    def test_top_plans_shared_structure(self):
        """top_plans_shared is array with correct object structure"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        top_plans = data.get("top_plans_shared", [])
        assert isinstance(top_plans, list), "top_plans_shared should be a list"
        
        # If there are items, check structure
        if len(top_plans) > 0:
            for plan in top_plans:
                assert "slug" in plan, "Missing slug in top_plans_shared item"
                assert "destination" in plan, "Missing destination in top_plans_shared item"
                assert "shares" in plan, "Missing shares in top_plans_shared item"
        
        print(f"PASS: top_plans_shared is array with {len(top_plans)} items")
    
    def test_top_plans_affiliate_structure(self):
        """top_plans_affiliate is array with correct object structure"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        top_plans = data.get("top_plans_affiliate", [])
        assert isinstance(top_plans, list), "top_plans_affiliate should be a list"
        
        # If there are items, check structure
        if len(top_plans) > 0:
            for plan in top_plans:
                assert "slug" in plan, "Missing slug in top_plans_affiliate item"
                assert "destination" in plan, "Missing destination in top_plans_affiliate item"
                assert "clicks" in plan, "Missing clicks in top_plans_affiliate item"
        
        print(f"PASS: top_plans_affiliate is array with {len(top_plans)} items")
    
    def test_top_converting_journeys_structure(self):
        """top_converting_journeys is array with correct object structure"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        top_journeys = data.get("top_converting_journeys", [])
        assert isinstance(top_journeys, list), "top_converting_journeys should be a list"
        
        # If there are items, check structure
        if len(top_journeys) > 0:
            for journey in top_journeys:
                assert "journey_id" in journey, "Missing journey_id in top_converting_journeys item"
                assert "name" in journey, "Missing name in top_converting_journeys item"
                assert "amount" in journey, "Missing amount in top_converting_journeys item"
                assert "contributions" in journey, "Missing contributions in top_converting_journeys item"
        
        print(f"PASS: top_converting_journeys is array with {len(top_journeys)} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
