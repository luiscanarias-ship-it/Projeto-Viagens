"""
Iteration 79 - Affiliate Links Audit & Repair Tests
Tests that all 9 affiliate links have valid HTTP URLs (no placeholders)
and that click tracking works for all platforms.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAffiliateLinksBackend:
    """Backend tests for affiliate links - verify no placeholders remain"""
    
    def test_get_affiliate_links_returns_all_9_links(self):
        """GET /api/affiliate-links returns all 9 links"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        expected_platforms = ['skyscanner', 'booking', 'hotels', 'getyourguide', 
                              'cars', 'airalo', 'holafly', 'insurance', 'googlemaps']
        
        for platform in expected_platforms:
            assert platform in data, f"Missing platform: {platform}"
            assert 'url' in data[platform], f"Missing 'url' for {platform}"
            assert 'name' in data[platform], f"Missing 'name' for {platform}"
        
        print(f"✓ All 9 affiliate links present: {list(data.keys())}")
    
    def test_no_placeholder_urls(self):
        """All URLs are valid HTTP URLs, not placeholders"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        placeholder_patterns = ['_LINK_HERE', 'PLACEHOLDER', 'TODO', 'FIXME', '#']
        
        for platform, info in data.items():
            url = info.get('url', '')
            # Check it starts with http
            assert url.startswith('http'), f"{platform} URL doesn't start with http: {url}"
            # Check no placeholder patterns
            for pattern in placeholder_patterns:
                assert pattern not in url.upper(), f"{platform} URL contains placeholder '{pattern}': {url}"
        
        print("✓ No placeholder URLs found - all are valid HTTP URLs")
    
    def test_skyscanner_url_correct(self):
        """Skyscanner URL starts with https://www.skyscanner.pt"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        url = data['skyscanner']['url']
        assert url.startswith('https://www.skyscanner.pt'), f"Skyscanner URL incorrect: {url}"
        print(f"✓ Skyscanner URL correct: {url}")
    
    def test_booking_url_correct(self):
        """Booking URL starts with https://www.booking.com"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        url = data['booking']['url']
        assert url.startswith('https://www.booking.com'), f"Booking URL incorrect: {url}"
        print(f"✓ Booking URL correct: {url}")
    
    def test_hotels_url_correct(self):
        """Hotels URL starts with https://pt.hotels.com"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        url = data['hotels']['url']
        assert url.startswith('https://pt.hotels.com'), f"Hotels URL incorrect: {url}"
        print(f"✓ Hotels URL correct: {url}")
    
    def test_getyourguide_url_correct(self):
        """GetYourGuide URL starts with https://www.getyourguide.com"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        url = data['getyourguide']['url']
        assert url.startswith('https://www.getyourguide.com'), f"GetYourGuide URL incorrect: {url}"
        print(f"✓ GetYourGuide URL correct: {url}")
    
    def test_cars_url_correct(self):
        """Cars URL starts with https://www.discovercars.com"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        url = data['cars']['url']
        assert url.startswith('https://www.discovercars.com'), f"Cars URL incorrect: {url}"
        print(f"✓ Cars URL correct: {url}")
    
    def test_airalo_url_correct(self):
        """Airalo URL starts with https://www.airalo.com"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        url = data['airalo']['url']
        assert url.startswith('https://www.airalo.com'), f"Airalo URL incorrect: {url}"
        print(f"✓ Airalo URL correct: {url}")
    
    def test_holafly_url_correct(self):
        """Holafly URL starts with https://www.holafly.com"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        url = data['holafly']['url']
        assert url.startswith('https://www.holafly.com'), f"Holafly URL incorrect: {url}"
        print(f"✓ Holafly URL correct: {url}")
    
    def test_insurance_url_correct(self):
        """Insurance URL starts with https://www.iatiseguros.com"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        url = data['insurance']['url']
        assert url.startswith('https://www.iatiseguros.com'), f"Insurance URL incorrect: {url}"
        print(f"✓ Insurance URL correct: {url}")
    
    def test_googlemaps_url_correct(self):
        """Google Maps URL starts with https://maps.google.com"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        url = data['googlemaps']['url']
        assert url.startswith('https://maps.google.com'), f"Google Maps URL incorrect: {url}"
        print(f"✓ Google Maps URL correct: {url}")


class TestAffiliateClickTracking:
    """Test click tracking for all platforms"""
    
    @pytest.mark.parametrize("platform", [
        'skyscanner', 'booking', 'hotels', 'getyourguide', 
        'cars', 'airalo', 'holafly', 'insurance', 'googlemaps'
    ])
    def test_click_tracking_works(self, platform):
        """POST /api/affiliate-click tracking works for all platforms"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": platform}
        )
        assert response.status_code == 200, f"Click tracking failed for {platform}: {response.status_code}"
        
        data = response.json()
        assert data.get('status') == 'tracked', f"Expected 'tracked' status for {platform}"
        print(f"✓ Click tracking works for {platform}")
    
    def test_invalid_platform_rejected(self):
        """POST /api/affiliate-click rejects invalid platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "invalid_platform"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid platform, got {response.status_code}"
        print("✓ Invalid platform correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
