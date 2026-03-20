"""
Iteration 46 - Affiliate Link Tests
Tests for:
1. GET /api/affiliate-links - returns base links
2. POST /api/affiliate-click - tracking clicks
3. Verifies link structure for dynamic URL building in frontend
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAffiliateLinks:
    """Affiliate links endpoint tests"""
    
    def test_get_affiliate_links_returns_200(self):
        """GET /api/affiliate-links should return 200 with links object"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        print(f"✓ GET /api/affiliate-links returned {len(data)} links")
    
    def test_affiliate_links_contains_booking(self):
        """Affiliate links should contain booking.com link"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        assert "booking" in data
        assert "url" in data["booking"]
        assert "booking.com" in data["booking"]["url"]
        print(f"✓ Booking.com link: {data['booking']['url']}")
    
    def test_affiliate_links_contains_skyscanner(self):
        """Affiliate links should contain skyscanner link"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        assert "skyscanner" in data
        assert "url" in data["skyscanner"]
        assert "skyscanner" in data["skyscanner"]["url"]
        print(f"✓ Skyscanner link: {data['skyscanner']['url']}")
    
    def test_affiliate_links_contains_getyourguide(self):
        """Affiliate links should contain getyourguide link"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        assert "getyourguide" in data
        assert "url" in data["getyourguide"]
        assert "getyourguide.com" in data["getyourguide"]["url"]
        print(f"✓ GetYourGuide link: {data['getyourguide']['url']}")
    
    def test_affiliate_links_contains_airalo(self):
        """Affiliate links should contain airalo (eSIM) link"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        assert "airalo" in data
        assert "url" in data["airalo"]
        assert "airalo.com" in data["airalo"]["url"]
        print(f"✓ Airalo eSIM link: {data['airalo']['url']}")


class TestAffiliateClickTracking:
    """Affiliate click tracking tests"""
    
    def test_track_click_booking(self):
        """POST /api/affiliate-click should track booking clicks"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "booking"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "tracked"
        print("✓ Booking click tracked successfully")
    
    def test_track_click_skyscanner(self):
        """POST /api/affiliate-click should track skyscanner clicks"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "skyscanner"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "tracked"
        print("✓ Skyscanner click tracked successfully")
    
    def test_track_click_getyourguide(self):
        """POST /api/affiliate-click should track getyourguide clicks"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "getyourguide"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "tracked"
        print("✓ GetYourGuide click tracked successfully")
    
    def test_track_click_airalo(self):
        """POST /api/affiliate-click should track airalo (eSIM) clicks"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "airalo"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "tracked"
        print("✓ Airalo eSIM click tracked successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
