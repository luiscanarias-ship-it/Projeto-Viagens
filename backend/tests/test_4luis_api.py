"""
4Luis Crowdfunding Platform - Backend API Tests
Tests for: Authentication, Journeys, Payments, Sponsor Links, Dashboard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crowdtrip.preview.emergentagent.com').rstrip('/')

class TestHealthAndBasicEndpoints:
    """Basic API health and public endpoints"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ API root: {data['message']}")
    
    def test_get_journeys(self):
        """Test public journeys endpoint"""
        response = requests.get(f"{BASE_URL}/api/journeys")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Found {len(data)} journeys")
    
    def test_get_single_journey(self):
        """Test single journey endpoint"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_china001")
        assert response.status_code == 200
        data = response.json()
        assert data["journey_id"] == "journey_china001"
        assert data["name"] == "China"
        print(f"✓ Journey: {data['name']} - {data['poetic_name']}")
    
    def test_get_payment_info(self):
        """Test payment info endpoint"""
        response = requests.get(f"{BASE_URL}/api/payment-info")
        assert response.status_code == 200
        data = response.json()
        assert "mbway" in data
        assert "paypal" in data
        assert "crypto" in data
        assert data["mbway"]["phone"] == "+351968068535"
        assert data["crypto"]["address"] == "TGcWs89gTkkxARVT8UJsCFUMc9sQkvUmtL"
        print(f"✓ Payment info: MBWay={data['mbway']['phone']}, Crypto={data['crypto']['address'][:20]}...")
    
    def test_get_site_settings(self):
        """Test public site settings"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert "contact_email" in data
        print(f"✓ Site settings: contact_email={data['contact_email']}")
    
    def test_get_dreamers_stats(self):
        """Test dreamers statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/dreamers-stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_dreamers" in data
        print(f"✓ Dreamers stats: {data['total_dreamers']} dreamers")
    
    def test_get_raffle_stats(self):
        """Test public raffle stats"""
        response = requests.get(f"{BASE_URL}/api/raffle-stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_raffles" in data
        print(f"✓ Raffle stats: {data['total_raffles']} raffles")


class TestAuthentication:
    """Authentication endpoints tests"""
    
    def test_login_success(self):
        """Test successful login with test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@test.com"
        print(f"✓ Login successful: {data['user']['name']}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials rejected correctly")
    
    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": "test@test.com",
            "password": "test123",
            "name": "Test User"
        })
        assert response.status_code == 400
        print("✓ Duplicate email registration rejected")
    
    def test_get_me_unauthorized(self):
        """Test /auth/me without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ Unauthorized access to /auth/me rejected")
    
    def test_get_me_authorized(self):
        """Test /auth/me with valid token"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test"
        })
        token = login_response.json()["token"]
        
        # Then get me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@test.com"
        print(f"✓ /auth/me returned: {data['name']}")


class TestSponsorLinks:
    """Sponsor links functionality tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test"
        })
        return response.json()["token"]
    
    def test_create_sponsor_link(self, auth_token):
        """Test creating a sponsor link"""
        response = requests.post(
            f"{BASE_URL}/api/sponsor-links/create",
            json={"journey_id": "journey_japan001"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "link_id" in data
        assert data["journey_id"] == "journey_japan001"
        print(f"✓ Sponsor link created: {data['link_id']}")
    
    def test_get_my_sponsor_links(self, auth_token):
        """Test getting user's sponsor links"""
        response = requests.get(
            f"{BASE_URL}/api/sponsor-links/my-links",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Found {len(data)} sponsor links")
    
    def test_get_sponsor_link_unauthorized(self):
        """Test sponsor links without auth"""
        response = requests.get(f"{BASE_URL}/api/sponsor-links/my-links")
        assert response.status_code == 401
        print("✓ Unauthorized sponsor links access rejected")


class TestPaymentEndpoints:
    """Payment-related endpoints tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test"
        })
        return response.json()["token"]
    
    def test_create_stripe_checkout(self, auth_token):
        """Test Stripe checkout creation"""
        response = requests.post(
            f"{BASE_URL}/api/contributions/create-checkout",
            json={
                "amount_key": "20",
                "journey_id": "journey_china001",
                "origin_url": "https://crowdtrip.preview.emergentagent.com"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "session_id" in data
        assert "checkout.stripe.com" in data["url"]
        print(f"✓ Stripe checkout created: {data['session_id'][:20]}...")
    
    def test_create_stripe_checkout_invalid_amount(self, auth_token):
        """Test Stripe checkout with invalid amount"""
        response = requests.post(
            f"{BASE_URL}/api/contributions/create-checkout",
            json={
                "amount_key": "999",
                "journey_id": "journey_china001",
                "origin_url": "https://crowdtrip.preview.emergentagent.com"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
        print("✓ Invalid amount rejected correctly")
    
    def test_manual_contribution_mbway(self, auth_token):
        """Test manual contribution (MBWay)"""
        response = requests.post(
            f"{BASE_URL}/api/contributions/manual",
            json={
                "journey_id": "journey_china001",
                "amount_key": "10",
                "payment_method": "mbway",
                "is_crypto": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "contribution_id" in data
        assert data["tickets_count"] == 2  # 10€ = 2 tickets
        print(f"✓ Manual contribution created: {data['contribution_id']}")
    
    def test_manual_contribution_crypto(self, auth_token):
        """Test manual crypto contribution (double tickets)"""
        response = requests.post(
            f"{BASE_URL}/api/contributions/manual",
            json={
                "journey_id": "journey_china001",
                "amount_key": "10",
                "payment_method": "crypto",
                "is_crypto": True
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tickets_count"] == 4  # 10€ = 2 tickets * 2 (crypto bonus)
        print(f"✓ Crypto contribution: {data['tickets_count']} tickets (double)")


class TestUserProfile:
    """User profile endpoints tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test"
        })
        return response.json()["token"]
    
    def test_get_profile(self, auth_token):
        """Test getting user profile"""
        response = requests.get(
            f"{BASE_URL}/api/profile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "name" in data
        print(f"✓ Profile: {data['name']} ({data['email']})")
    
    def test_update_profile(self, auth_token):
        """Test updating user profile"""
        response = requests.put(
            f"{BASE_URL}/api/profile",
            json={
                "alias": "Test Dreamer",
                "use_real_name": True
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("alias") == "Test Dreamer"
        print(f"✓ Profile updated: alias={data.get('alias')}")


class TestTickets:
    """Tickets endpoints tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test"
        })
        return response.json()["token"]
    
    def test_get_my_tickets(self, auth_token):
        """Test getting user's tickets"""
        response = requests.get(
            f"{BASE_URL}/api/tickets/my-tickets",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Found {len(data)} tickets")
    
    def test_get_journey_tickets(self, auth_token):
        """Test getting tickets for specific journey"""
        response = requests.get(
            f"{BASE_URL}/api/tickets/journey/journey_china001",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Found {len(data)} tickets for China journey")


class TestTravelResources:
    """Travel resources and AI planner tests"""
    
    def test_get_travel_resources(self):
        """Test travel resources endpoint"""
        response = requests.get(f"{BASE_URL}/api/journey/journey_china001/travel-resources")
        assert response.status_code == 200
        data = response.json()
        assert "destination" in data
        assert "hotels" in data
        assert "flights" in data
        assert "social" in data
        assert data["destination"] == "China"
        print(f"✓ Travel resources for {data['destination']}: {len(data['hotels'])} hotels, {len(data['flights'])} flights")


class TestGallery:
    """Gallery endpoints tests"""
    
    def test_get_gallery(self):
        """Test public gallery endpoint"""
        response = requests.get(f"{BASE_URL}/api/gallery")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Gallery: {len(data)} photos")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
