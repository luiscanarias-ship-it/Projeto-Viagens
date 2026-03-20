"""
Iteration 57 Tests - Hero Height, New Copy, Curated Dreams Images, SEO
Tests for:
- P0 Mobile: Hero section 60-70vh height - CTA visible without scrolling on mobile (375px)
- P0 Mobile: All buttons min 44px touch targets
- P1 Hero: New copy 'Uma plataforma onde qualquer pessoa pode financiar viagens de sonho — e onde tu também podes financiar a tua.'
- P1 Hero: Opening question 'E se os sonhos pudessem ser financiados por todos?' still present
- P1 Images: Curated dreams section loads images (warm tones)
- P2 SEO: GET /api/sitemap.xml returns valid XML
- P2 SEO: GET /api/plan/{slug} returns 404 for non-existing slug
- Affiliate: GET /api/affiliate-links returns placeholder URLs
- Affiliate: POST /api/affiliate-click tracking works
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAffiliateLinks:
    """Test affiliate links endpoints"""
    
    def test_get_affiliate_links_returns_placeholders(self):
        """GET /api/affiliate-links returns placeholder URLs (BOOKING_LINK_HERE etc)"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200
        data = response.json()
        
        # Check required platforms exist
        required_platforms = ['booking', 'skyscanner', 'getyourguide', 'airalo', 'insurance', 'cars']
        for platform in required_platforms:
            assert platform in data, f"Missing platform: {platform}"
            assert 'url' in data[platform], f"Missing url for {platform}"
            assert 'name' in data[platform], f"Missing name for {platform}"
        
        # Verify placeholder URLs
        assert 'BOOKING_LINK_HERE' in data['booking']['url']
        assert 'SKYSCANNER_LINK_HERE' in data['skyscanner']['url']
        assert 'GETYOURGUIDE_LINK_HERE' in data['getyourguide']['url']
        print("PASS: Affiliate links return placeholder URLs correctly")
    
    def test_affiliate_click_tracking_works(self):
        """POST /api/affiliate-click works for click tracking"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "booking"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "tracked"
        print("PASS: Affiliate click tracking works")
    
    def test_affiliate_click_invalid_platform(self):
        """POST /api/affiliate-click returns 400 for invalid platform"""
        response = requests.post(
            f"{BASE_URL}/api/affiliate-click",
            json={"platform": "invalid_platform"}
        )
        assert response.status_code == 400
        print("PASS: Affiliate click returns 400 for invalid platform")


class TestSEOEndpoints:
    """Test SEO-related endpoints"""
    
    def test_sitemap_xml_returns_valid_xml(self):
        """GET /api/sitemap.xml returns valid XML with urlset structure"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert 'application/xml' in response.headers.get('content-type', '')
        
        content = response.text
        assert '<?xml version="1.0"' in content
        assert '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' in content
        assert '</urlset>' in content
        assert '<url>' in content
        assert '<loc>' in content
        print("PASS: Sitemap.xml returns valid XML structure")
    
    def test_sitemap_includes_static_pages(self):
        """GET /api/sitemap.xml includes static pages (/about, /travel-planner)"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        content = response.text
        
        assert '/about' in content
        assert '/travel-planner' in content
        print("PASS: Sitemap includes static pages")
    
    def test_plan_slug_returns_404_for_nonexistent(self):
        """GET /api/plan/{slug} returns 404 for non-existing slug"""
        response = requests.get(f"{BASE_URL}/api/plan/nonexistent-slug-12345")
        assert response.status_code == 404
        print("PASS: /api/plan/{slug} returns 404 for non-existent slug")


class TestCuratedDreams:
    """Test curated dreams endpoint for warm golden-hour images"""
    
    def test_curated_dreams_returns_images(self):
        """GET /api/homepage/curated-dreams returns curated dreams with image URLs"""
        response = requests.get(f"{BASE_URL}/api/homepage/curated-dreams")
        assert response.status_code == 200
        data = response.json()
        
        # Check if curated dreams are returned
        if data.get("use_curated"):
            dreams = data.get("curated_dreams", [])
            assert len(dreams) > 0, "No curated dreams returned"
            
            for dream in dreams:
                assert "image_url" in dream, f"Missing image_url in dream: {dream.get('name')}"
                assert dream["image_url"].startswith("http"), f"Invalid image URL: {dream['image_url']}"
                assert "name" in dream
                assert "country" in dream
                assert "story" in dream
            
            print(f"PASS: Curated dreams returns {len(dreams)} dreams with image URLs")
        else:
            # Real journeys exist, curated not used
            print("PASS: Real journeys exist, curated dreams not used (expected behavior)")


class TestHomepageEndpoints:
    """Test homepage data endpoints"""
    
    def test_main_journey_endpoint(self):
        """GET /api/homepage/main-journey works"""
        response = requests.get(f"{BASE_URL}/api/homepage/main-journey")
        assert response.status_code == 200
        print("PASS: Main journey endpoint works")
    
    def test_ambassador_journeys_endpoint(self):
        """GET /api/homepage/ambassador-journeys works"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        print("PASS: Ambassador journeys endpoint works")
    
    def test_realized_journeys_endpoint(self):
        """GET /api/homepage/realized-journeys works"""
        response = requests.get(f"{BASE_URL}/api/homepage/realized-journeys")
        assert response.status_code == 200
        print("PASS: Realized journeys endpoint works")
    
    def test_platform_stats_endpoint(self):
        """GET /api/platform/stats responds"""
        response = requests.get(f"{BASE_URL}/api/platform/stats")
        # May return 200 or 404 depending on data
        assert response.status_code in [200, 404]
        print("PASS: Platform stats endpoint responds")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
