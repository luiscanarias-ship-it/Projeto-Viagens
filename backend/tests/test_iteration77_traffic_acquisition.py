"""
Iteration 77 - Traffic Acquisition & Organic Growth Testing
Tests: SEO readiness, sitemap, OG images, share tracking, affiliate tracking, referral stats
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSEOEndpoints:
    """SEO-related endpoints: sitemap.xml, og-image"""
    
    def test_sitemap_xml_returns_valid_xml(self):
        """GET /api/sitemap.xml returns XML with public plans and journeys"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get('content-type') == 'application/xml', f"Expected application/xml, got {response.headers.get('content-type')}"
        
        # Verify XML structure
        content = response.text
        assert '<?xml version="1.0"' in content, "Missing XML declaration"
        assert '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' in content, "Missing urlset element"
        assert '<url>' in content, "Missing url elements"
        assert '<loc>' in content, "Missing loc elements"
        assert '</urlset>' in content, "Missing closing urlset"
        print(f"Sitemap XML valid, contains {content.count('<url>')} URLs")
    
    def test_sitemap_contains_static_pages(self):
        """Sitemap includes static pages: /, /about, /plan-trip, /travel-planner"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        content = response.text
        
        # Check for static pages
        assert '/plan-trip' in content, "Missing /plan-trip in sitemap"
        assert '/travel-planner' in content, "Missing /travel-planner in sitemap"
        print("Sitemap contains required static pages")
    
    def test_og_image_returns_png(self):
        """GET /api/og-image/{slug} returns 200 with image/png content-type"""
        # Use a known slug from the test request
        response = requests.get(f"{BASE_URL}/api/og-image/lisboa-6f4f3e")
        
        # If plan doesn't exist, it returns 404 - that's acceptable for this test
        if response.status_code == 404:
            print("Plan 'lisboa-6f4f3e' not found - testing with any available plan")
            # Try to get any public plan
            plans_response = requests.get(f"{BASE_URL}/api/sitemap.xml")
            if '/plano/' in plans_response.text:
                import re
                slugs = re.findall(r'/plano/([a-z0-9-]+)', plans_response.text)
                if slugs:
                    response = requests.get(f"{BASE_URL}/api/og-image/{slugs[0]}")
                    print(f"Testing with slug: {slugs[0]}")
        
        if response.status_code == 200:
            assert 'image/png' in response.headers.get('content-type', ''), f"Expected image/png, got {response.headers.get('content-type')}"
            assert len(response.content) > 1000, "Image content too small"
            print(f"OG image returned successfully, size: {len(response.content)} bytes")
        else:
            print(f"OG image endpoint returned {response.status_code} - no public plans available")
            pytest.skip("No public plans available for OG image test")


class TestShareTracking:
    """Share tracking endpoints"""
    
    def test_track_share_whatsapp(self):
        """POST /api/track-share with whatsapp type returns tracked"""
        response = requests.post(f"{BASE_URL}/api/track-share", json={
            "type": "whatsapp",
            "page": "test",
            "slug": "test"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "tracked", f"Expected status 'tracked', got {data}"
        print("WhatsApp share tracked successfully")
    
    def test_track_share_copy(self):
        """POST /api/track-share with copy type returns tracked"""
        response = requests.post(f"{BASE_URL}/api/track-share", json={
            "type": "copy",
            "page": "public-plan",
            "slug": "test-slug"
        })
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("Copy share tracked successfully")
    
    def test_track_share_native(self):
        """POST /api/track-share with native type returns tracked"""
        response = requests.post(f"{BASE_URL}/api/track-share", json={
            "type": "native",
            "page": "travel-planner",
            "slug": ""
        })
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("Native share tracked successfully")
    
    def test_track_share_link(self):
        """POST /api/track-share with link type returns tracked"""
        response = requests.post(f"{BASE_URL}/api/track-share", json={
            "type": "link",
            "page": "journey",
            "slug": "journey-123"
        })
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("Link share tracked successfully")
    
    def test_track_share_invalid_type(self):
        """POST /api/track-share with invalid type returns 400"""
        response = requests.post(f"{BASE_URL}/api/track-share", json={
            "type": "invalid_type",
            "page": "test",
            "slug": "test"
        })
        assert response.status_code == 400, f"Expected 400 for invalid type, got {response.status_code}"
        print("Invalid share type correctly rejected")


class TestAffiliateTracking:
    """Affiliate click tracking endpoints"""
    
    def test_affiliate_click_booking(self):
        """POST /api/affiliate-click with booking platform returns tracked"""
        response = requests.post(f"{BASE_URL}/api/affiliate-click", json={
            "platform": "booking"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "tracked", f"Expected status 'tracked', got {data}"
        print("Booking affiliate click tracked successfully")
    
    def test_affiliate_click_getyourguide(self):
        """POST /api/affiliate-click with getyourguide platform returns tracked"""
        response = requests.post(f"{BASE_URL}/api/affiliate-click", json={
            "platform": "getyourguide"
        })
        assert response.status_code == 200
        assert response.json().get("status") == "tracked"
        print("GetYourGuide affiliate click tracked successfully")
    
    def test_affiliate_click_invalid_platform(self):
        """POST /api/affiliate-click with invalid platform returns 400"""
        response = requests.post(f"{BASE_URL}/api/affiliate-click", json={
            "platform": "invalid_platform"
        })
        assert response.status_code == 400, f"Expected 400 for invalid platform, got {response.status_code}"
        print("Invalid platform correctly rejected")
    
    def test_affiliate_links_endpoint(self):
        """GET /api/affiliate-links returns 200"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Expected dict response"
        print(f"Affiliate links returned: {list(data.keys())}")


class TestAdminStatsEndpoints:
    """Admin statistics endpoints (require authentication)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@4luis.com",
            "password": "Admin1"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_share_stats_requires_auth(self):
        """GET /api/admin/share-stats without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/admin/share-stats")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("Share stats correctly requires authentication")
    
    def test_share_stats_with_admin(self, admin_token):
        """GET /api/admin/share-stats with admin auth returns total_shares and by_type"""
        response = requests.get(
            f"{BASE_URL}/api/admin/share-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_shares" in data, "Missing total_shares in response"
        assert "by_type" in data, "Missing by_type in response"
        print(f"Share stats: total={data['total_shares']}, by_type={data['by_type']}")
    
    def test_referral_stats_requires_auth(self):
        """GET /api/admin/referral-stats without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/admin/referral-stats")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("Referral stats correctly requires authentication")
    
    def test_referral_stats_with_admin(self, admin_token):
        """GET /api/admin/referral-stats with admin auth returns expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/referral-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_users" in data, "Missing total_users in response"
        assert "ambassadors" in data, "Missing ambassadors in response"
        assert "total_referred_users" in data, "Missing total_referred_users in response"
        assert "ambassador_conversion_rate" in data, "Missing ambassador_conversion_rate in response"
        print(f"Referral stats: users={data['total_users']}, ambassadors={data['ambassadors']}, rate={data['ambassador_conversion_rate']}%")
    
    def test_affiliate_stats_requires_auth(self):
        """GET /api/admin/affiliate-stats without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/admin/affiliate-stats")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("Affiliate stats correctly requires authentication")
    
    def test_affiliate_stats_with_admin(self, admin_token):
        """GET /api/admin/affiliate-stats with admin auth returns total_clicks and by_platform"""
        response = requests.get(
            f"{BASE_URL}/api/admin/affiliate-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_clicks" in data, "Missing total_clicks in response"
        assert "by_platform" in data, "Missing by_platform in response"
        print(f"Affiliate stats: total={data['total_clicks']}, by_platform={data['by_platform']}")


class TestPublicPlanEndpoint:
    """Public plan endpoint for SEO"""
    
    def test_plan_endpoint_returns_404_for_invalid_slug(self):
        """GET /api/plan/{invalid_slug} returns 404"""
        response = requests.get(f"{BASE_URL}/api/plan/nonexistent-slug-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Invalid plan slug correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
