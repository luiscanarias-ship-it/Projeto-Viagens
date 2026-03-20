"""
Iteration 56 - Testing new features:
1. P0 Mobile: Touch targets, responsive hero, sticky bar, search stacking
2. P1 Hero: Updated copy, trust signals
3. P2 SEO: sitemap.xml, /plan/{slug} endpoint
4. Affiliate Links: Placeholder URLs, click tracking, dynamic params
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAffiliateLinks:
    """Test affiliate links with placeholder URLs"""
    
    def test_affiliate_links_returns_placeholder_urls(self):
        """Verify affiliate links return placeholder URLs (BOOKING_LINK_HERE, etc.)"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check that placeholder URLs are present
        assert "booking" in data, "Missing 'booking' key"
        assert "skyscanner" in data, "Missing 'skyscanner' key"
        assert "getyourguide" in data, "Missing 'getyourguide' key"
        assert "airalo" in data, "Missing 'airalo' key"
        assert "insurance" in data, "Missing 'insurance' key"
        
        # Verify placeholder format
        assert "BOOKING_LINK_HERE" in data["booking"]["url"], f"Expected BOOKING_LINK_HERE, got {data['booking']['url']}"
        assert "SKYSCANNER_LINK_HERE" in data["skyscanner"]["url"], f"Expected SKYSCANNER_LINK_HERE, got {data['skyscanner']['url']}"
        assert "GETYOURGUIDE_LINK_HERE" in data["getyourguide"]["url"], f"Expected GETYOURGUIDE_LINK_HERE, got {data['getyourguide']['url']}"
        assert "AIRALO_LINK_HERE" in data["airalo"]["url"], f"Expected AIRALO_LINK_HERE, got {data['airalo']['url']}"
        assert "IATI_LINK_HERE" in data["insurance"]["url"], f"Expected IATI_LINK_HERE, got {data['insurance']['url']}"
        
        print("✓ All affiliate links return placeholder URLs correctly")
    
    def test_affiliate_links_include_affiliate_id(self):
        """Verify affiliate_id field is included in response"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check affiliate_id is present
        for platform, info in data.items():
            assert "affiliate_id" in info, f"Missing affiliate_id for {platform}"
        
        # Check specific affiliate_ids
        assert data["booking"]["affiliate_id"] == "4luis", f"Expected '4luis', got {data['booking']['affiliate_id']}"
        assert data["skyscanner"]["affiliate_id"] == "4luis", f"Expected '4luis', got {data['skyscanner']['affiliate_id']}"
        
        print("✓ affiliate_id field included in response")
    
    def test_affiliate_click_tracking_works(self):
        """Verify POST /api/affiliate-click works for click tracking"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "booking"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "tracked", f"Expected 'tracked', got {data}"
        
        print("✓ Affiliate click tracking works")
    
    def test_affiliate_click_invalid_platform(self):
        """Verify invalid platform returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "invalid_platform"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print("✓ Invalid platform returns 400")


class TestSEOEndpoints:
    """Test SEO endpoints: sitemap.xml and /plan/{slug}"""
    
    def test_sitemap_xml_returns_valid_xml(self):
        """Verify GET /api/sitemap.xml returns valid XML"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        assert "xml" in content_type.lower(), f"Expected XML content type, got {content_type}"
        
        # Check XML structure
        content = response.text
        assert '<?xml version="1.0"' in content, "Missing XML declaration"
        assert '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' in content, "Missing urlset element"
        assert '</urlset>' in content, "Missing closing urlset"
        
        # Check static pages are included
        assert '/about' in content or 'about' in content, "Missing /about page"
        assert '/travel-planner' in content or 'travel-planner' in content, "Missing /travel-planner page"
        
        print("✓ Sitemap.xml returns valid XML with static pages")
    
    def test_sitemap_includes_journeys(self):
        """Verify sitemap includes journey URLs"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        
        content = response.text
        # Check for journey URLs (may or may not have journeys)
        # Just verify the structure is correct
        assert '<url>' in content, "Missing url elements"
        assert '<loc>' in content, "Missing loc elements"
        assert '<priority>' in content, "Missing priority elements"
        
        print("✓ Sitemap has correct URL structure")
    
    def test_plan_slug_returns_404_for_nonexistent(self):
        """Verify GET /api/plan/{slug} returns 404 for non-existing slug"""
        response = requests.get(f"{BASE_URL}/api/plan/seo-ready-4-nonexistent-slug-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print("✓ Non-existent plan slug returns 404")
    
    def test_plan_slug_endpoint_exists(self):
        """Verify /api/plan/{slug} endpoint exists and handles requests"""
        # Test with a random slug - should return 404 (not 500 or other error)
        response = requests.get(f"{BASE_URL}/api/plan/test-slug-abc123")
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
        
        print("✓ Plan slug endpoint exists and handles requests")


class TestHomepageEndpoints:
    """Test homepage endpoints for hero and trust signals"""
    
    def test_homepage_main_journey_loads(self):
        """Verify main journey endpoint works"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # May or may not have a journey
        assert isinstance(data, dict), "Expected dict response"
        
        print("✓ Homepage main journey endpoint works")
    
    def test_homepage_ambassador_journeys_loads(self):
        """Verify ambassador journeys endpoint works"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        print("✓ Homepage ambassador journeys endpoint works")
    
    def test_platform_stats_loads(self):
        """Verify platform stats endpoint works"""
        response = requests.get(f"{BASE_URL}/api/platform/stats")
        # May return 200 or 404 depending on implementation
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
        
        print("✓ Platform stats endpoint responds")


class TestTravelPlannerEndpoints:
    """Test travel planner related endpoints"""
    
    def test_affiliate_links_for_travel_planner(self):
        """Verify affiliate links are available for travel planner"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check all required platforms for travel planner
        required_platforms = ["booking", "skyscanner", "getyourguide", "airalo", "insurance", "cars"]
        for platform in required_platforms:
            assert platform in data, f"Missing required platform: {platform}"
            assert "url" in data[platform], f"Missing url for {platform}"
            assert "name" in data[platform], f"Missing name for {platform}"
        
        print("✓ All required affiliate platforms available for travel planner")


class TestContributionConfig:
    """Test contribution configuration endpoint"""
    
    def test_contribution_config_loads(self):
        """Verify contribution config endpoint works"""
        response = requests.get(f"{BASE_URL}/api/contributions/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "fixed_amounts" in data, "Missing fixed_amounts"
        assert "payment_methods" in data, "Missing payment_methods"
        
        print("✓ Contribution config endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
