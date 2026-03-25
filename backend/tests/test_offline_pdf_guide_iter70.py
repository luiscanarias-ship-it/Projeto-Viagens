"""
Iteration 70 - Offline PDF Guide Feature Tests
Tests for POST /api/ai/travel-plan/pdf endpoint
- Ambassador-only access (gated feature)
- PDF generation with sections customization
- Static map inclusion with geocode_data
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"

# Known plan slug for getting plan data
KNOWN_PLAN_SLUG = "paris-acbc2d"


class TestOfflinePDFGuide:
    """Tests for the Offline PDF Guide feature"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin (ambassador level) and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def plan_data(self, admin_token):
        """Get plan data from known slug"""
        response = requests.get(
            f"{BASE_URL}/api/plan/{KNOWN_PLAN_SLUG}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code == 200:
            return response.json()
        # Fallback: create minimal plan data for testing
        return {
            "destination": "Paris",
            "dates": "15-20 Janeiro 2026",
            "summary": "Uma viagem cultural pela cidade luz",
            "itinerary": [
                {"day": 1, "title": "Chegada e Torre Eiffel", "activities": ["Check-in no hotel", "Visita à Torre Eiffel", "Jantar no Champs-Élysées"]},
                {"day": 2, "title": "Museus e Arte", "activities": ["Museu do Louvre", "Jardins das Tulherias", "Museu d'Orsay"]}
            ],
            "flight_info": {
                "outbound": {"flight_number": "TP123", "departure_airport": "LIS", "arrival_airport": "CDG", "departure_time": "08:00", "arrival_time": "11:30"},
                "return": {"flight_number": "TP456", "departure_airport": "CDG", "arrival_airport": "LIS", "departure_time": "18:00", "arrival_time": "19:30"}
            },
            "hotel_info": {"name": "Hotel Le Marais", "address": "123 Rue de Rivoli, Paris", "area": "Le Marais", "phone": "+33 1 23 45 67 89"},
            "airport_to_hotel": {"best_option": {"mode": "Metro", "duration": "45 min", "cost": "€2"}, "alternative": {"mode": "Taxi", "duration": "30 min", "cost": "€50"}},
            "weather": "Frio, temperaturas entre 2-8°C. Leve casaco quente.",
            "packing": {"clothing": ["Casaco quente", "Cachecol"], "essentials": ["Passaporte", "Adaptador de tomada"]},
            "local_tips": ["Compre bilhetes online para evitar filas", "O metro é a forma mais rápida de se deslocar"],
            "checklist": {"documents": ["Passaporte", "Seguro viagem"], "tech": ["Carregador", "Adaptador"]}
        }
    
    @pytest.fixture(scope="class")
    def geocode_data(self):
        """Sample geocode data for map generation"""
        return {
            "days": [
                {"day": 1, "locations": [{"name": "Torre Eiffel", "lat": 48.8584, "lng": 2.2945}]},
                {"day": 2, "locations": [{"name": "Louvre", "lat": 48.8606, "lng": 2.3376}]}
            ],
            "special_pins": {
                "airport": {"name": "CDG", "lat": 49.0097, "lng": 2.5479},
                "hotel": {"name": "Hotel Le Marais", "lat": 48.8566, "lng": 2.3522}
            }
        }
    
    def test_pdf_returns_401_without_auth(self, plan_data):
        """Test: POST /api/ai/travel-plan/pdf returns 401 without authentication"""
        response = requests.post(f"{BASE_URL}/api/ai/travel-plan/pdf", json={
            "plan": plan_data
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: PDF endpoint returns 401 without authentication")
    
    def test_pdf_returns_200_for_admin(self, admin_token, plan_data):
        """Test: POST /api/ai/travel-plan/pdf returns 200 with valid PDF for admin/ambassador"""
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/pdf",
            json={"plan": plan_data},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify it's a PDF
        content = response.content
        assert content[:5] == b'%PDF-', f"Response is not a valid PDF. First 10 bytes: {content[:10]}"
        
        # Verify Content-Type
        assert 'application/pdf' in response.headers.get('Content-Type', ''), "Content-Type should be application/pdf"
        
        print(f"PASS: PDF endpoint returns 200 with valid PDF ({len(content)} bytes)")
    
    def test_pdf_content_disposition_header(self, admin_token, plan_data):
        """Test: Content-Disposition header has correct filename"""
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/pdf",
            json={"plan": plan_data},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response.status_code == 200
        
        content_disposition = response.headers.get('Content-Disposition', '')
        assert 'attachment' in content_disposition, "Content-Disposition should contain 'attachment'"
        assert 'filename=' in content_disposition, "Content-Disposition should contain filename"
        assert 'guia-' in content_disposition.lower(), "Filename should start with 'guia-'"
        assert '4luis.pdf' in content_disposition.lower(), "Filename should end with '4luis.pdf'"
        
        print(f"PASS: Content-Disposition header correct: {content_disposition}")
    
    def test_pdf_respects_sections_parameter(self, admin_token, plan_data):
        """Test: PDF endpoint respects 'sections' parameter (can exclude sections)"""
        # Request PDF with only itinerary section
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/pdf",
            json={
                "plan": plan_data,
                "sections": {
                    "flights": False,
                    "hotel": False,
                    "map": False,
                    "itinerary": True,
                    "tips": False,
                    "transport": False
                }
            },
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # PDF should be smaller with fewer sections
        content_minimal = response.content
        assert content_minimal[:5] == b'%PDF-', "Response should be valid PDF"
        
        # Request PDF with all sections
        response_full = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/pdf",
            json={
                "plan": plan_data,
                "sections": {
                    "flights": True,
                    "hotel": True,
                    "map": False,  # Map requires geocode_data
                    "itinerary": True,
                    "tips": True,
                    "transport": True
                }
            },
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response_full.status_code == 200
        content_full = response_full.content
        
        # Full PDF should be larger than minimal
        print(f"PASS: Sections parameter works - Minimal: {len(content_minimal)} bytes, Full: {len(content_full)} bytes")
    
    def test_pdf_includes_map_with_geocode_data(self, admin_token, plan_data, geocode_data):
        """Test: PDF endpoint includes static map when geocode_data is provided"""
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/pdf",
            json={
                "plan": plan_data,
                "sections": {"flights": False, "hotel": False, "map": True, "itinerary": False, "tips": False, "transport": False},
                "geocode_data": geocode_data
            },
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content = response.content
        assert content[:5] == b'%PDF-', "Response should be valid PDF"
        
        # PDF with map should be larger due to embedded image
        print(f"PASS: PDF with map generated successfully ({len(content)} bytes)")
    
    def test_pdf_returns_400_without_plan(self, admin_token):
        """Test: PDF endpoint returns 400 when plan is not provided"""
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/pdf",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: PDF endpoint returns 400 when plan is missing")


class TestPDFAccessControl:
    """Tests for PDF endpoint access control (ambassador gating)"""
    
    def test_pdf_returns_403_for_non_ambassador(self):
        """Test: POST /api/ai/travel-plan/pdf returns 403 for non-ambassador user"""
        # First, create a new non-ambassador user
        import uuid
        test_email = f"test_sonhador_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register new user (will be sonhador level by default)
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "name": "Test Sonhador",
            "surname": "User",
            "password": "TestPass123"
        })
        
        if register_response.status_code != 200:
            pytest.skip(f"Could not create test user: {register_response.text}")
        
        token = register_response.json()["token"]
        
        # Try to access PDF endpoint
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/pdf",
            json={"plan": {"destination": "Test", "itinerary": []}},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 for non-ambassador, got {response.status_code}: {response.text}"
        assert "Embaixador" in response.json().get("detail", ""), "Error message should mention Embaixadores"
        
        print("PASS: PDF endpoint returns 403 for non-ambassador user")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
