"""
Test suite for the 'Sonhos em Fase de Materialização' section on Homepage
Tests the /api/homepage/ambassador-journeys endpoint and journey details

Test journeys:
- journey_santorini001 (Costa Amalfitana, 42%, Manuel)
- journey_bali001 (Bali, 15%, Sofia) 
- journey_pamukkale001 (Pamukkale, 60%, Ana)
- journey_halong001 (Ha Long Bay, 75%, Pedro)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://travel-celebrate.preview.emergentagent.com')


class TestAmbassadorJourneysHomepage:
    """Tests for /api/homepage/ambassador-journeys endpoint"""
    
    def test_ambassador_journeys_returns_200(self):
        """API returns 200 status code"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: /api/homepage/ambassador-journeys returns 200")
    
    def test_ambassador_journeys_returns_4_journeys(self):
        """API returns exactly 4 ambassador journeys"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_count" in data, "Response missing 'total_count' field"
        assert data["total_count"] == 4, f"Expected 4 journeys, got {data['total_count']}"
        print(f"PASS: API returns total_count=4 journeys")
    
    def test_ambassador_journeys_structure(self):
        """API returns correct structure with 'featured' and 'regions' fields"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        assert "featured" in data, "Response missing 'featured' field"
        assert "regions" in data, "Response missing 'regions' field"
        assert isinstance(data["featured"], list), "'featured' should be a list"
        assert isinstance(data["regions"], dict), "'regions' should be a dict"
        print("PASS: API response has correct structure (featured, regions)")
    
    def test_ambassador_journeys_has_europa_region(self):
        """API returns journeys in 'europa' region"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        assert "europa" in data["regions"], "Missing 'europa' region"
        europa = data["regions"]["europa"]
        assert "journeys" in europa, "'europa' region missing 'journeys'"
        assert len(europa["journeys"]) >= 1, "No journeys in europa region"
        print(f"PASS: Europa region has {len(europa['journeys'])} journeys")
    
    def test_ambassador_journeys_has_asia_region(self):
        """API returns journeys in 'asia' region"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        assert "asia" in data["regions"], "Missing 'asia' region"
        asia = data["regions"]["asia"]
        assert "journeys" in asia, "'asia' region missing 'journeys'"
        assert len(asia["journeys"]) >= 1, "No journeys in asia region"
        print(f"PASS: Asia region has {len(asia['journeys'])} journeys")
    
    def test_journey_fields_present(self):
        """Each journey has required fields: journey_id, name, image_url, ambassador_name, progress_percentage"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["journey_id", "name", "image_url", "ambassador_name", "progress_percentage"]
        
        all_journeys = []
        for region_data in data["regions"].values():
            all_journeys.extend(region_data.get("journeys", []))
        all_journeys.extend(data.get("featured", []))
        
        for journey in all_journeys:
            for field in required_fields:
                assert field in journey, f"Journey {journey.get('journey_id', 'unknown')} missing '{field}'"
        
        print(f"PASS: All {len(all_journeys)} journeys have required fields")
    
    def test_costa_amalfitana_journey(self):
        """Costa Amalfitana journey exists with correct data"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        # Find Costa Amalfitana journey
        all_journeys = []
        for region_data in data["regions"].values():
            all_journeys.extend(region_data.get("journeys", []))
        
        costa = next((j for j in all_journeys if j["journey_id"] == "journey_santorini001"), None)
        assert costa is not None, "Costa Amalfitana journey not found"
        
        assert costa["name"] == "Costa Amalfitana", f"Expected 'Costa Amalfitana', got '{costa['name']}'"
        assert costa["ambassador_name"] == "Manuel", f"Expected ambassador 'Manuel', got '{costa['ambassador_name']}'"
        assert costa["progress_percentage"] == 42.0, f"Expected 42%, got {costa['progress_percentage']}%"
        print("PASS: Costa Amalfitana journey has correct data (name, ambassador=Manuel, progress=42%)")
    
    def test_bali_journey(self):
        """Bali journey exists with correct data"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        all_journeys = []
        for region_data in data["regions"].values():
            all_journeys.extend(region_data.get("journeys", []))
        
        bali = next((j for j in all_journeys if j["journey_id"] == "journey_bali001"), None)
        assert bali is not None, "Bali journey not found"
        
        assert bali["name"] == "Bali", f"Expected 'Bali', got '{bali['name']}'"
        assert bali["ambassador_name"] == "Sofia", f"Expected ambassador 'Sofia', got '{bali['ambassador_name']}'"
        assert bali["progress_percentage"] == 15.0, f"Expected 15%, got {bali['progress_percentage']}%"
        print("PASS: Bali journey has correct data (name, ambassador=Sofia, progress=15%)")
    
    def test_pamukkale_journey(self):
        """Pamukkale journey exists with correct data"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        all_journeys = []
        for region_data in data["regions"].values():
            all_journeys.extend(region_data.get("journeys", []))
        
        pamukkale = next((j for j in all_journeys if j["journey_id"] == "journey_pamukkale001"), None)
        assert pamukkale is not None, "Pamukkale journey not found"
        
        assert pamukkale["name"] == "Pamukkale", f"Expected 'Pamukkale', got '{pamukkale['name']}'"
        assert pamukkale["ambassador_name"] == "Ana", f"Expected ambassador 'Ana', got '{pamukkale['ambassador_name']}'"
        assert pamukkale["progress_percentage"] == 60.0, f"Expected 60%, got {pamukkale['progress_percentage']}%"
        print("PASS: Pamukkale journey has correct data (name, ambassador=Ana, progress=60%)")
    
    def test_halong_bay_journey(self):
        """Ha Long Bay journey exists with correct data"""
        response = requests.get(f"{BASE_URL}/api/homepage/ambassador-journeys")
        assert response.status_code == 200
        data = response.json()
        
        all_journeys = []
        for region_data in data["regions"].values():
            all_journeys.extend(region_data.get("journeys", []))
        
        halong = next((j for j in all_journeys if j["journey_id"] == "journey_halong001"), None)
        assert halong is not None, "Ha Long Bay journey not found"
        
        assert halong["name"] == "Ha Long Bay", f"Expected 'Ha Long Bay', got '{halong['name']}'"
        assert halong["ambassador_name"] == "Pedro", f"Expected ambassador 'Pedro', got '{halong['ambassador_name']}'"
        assert halong["progress_percentage"] == 75.0, f"Expected 75%, got {halong['progress_percentage']}%"
        print("PASS: Ha Long Bay journey has correct data (name, ambassador=Pedro, progress=75%)")


class TestJourneyDetailPages:
    """Tests for individual journey detail pages"""
    
    def test_costa_amalfitana_detail_page(self):
        """Costa Amalfitana journey detail page returns 200"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_santorini001")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data["journey_id"] == "journey_santorini001"
        assert data["name"] == "Costa Amalfitana"
        assert "image_url" in data and data["image_url"]
        print("PASS: Costa Amalfitana detail page loads correctly")
    
    def test_bali_detail_page(self):
        """Bali journey detail page returns 200"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_bali001")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data["journey_id"] == "journey_bali001"
        assert data["name"] == "Bali"
        assert "image_url" in data and data["image_url"]
        print("PASS: Bali detail page loads correctly")
    
    def test_pamukkale_detail_page(self):
        """Pamukkale journey detail page returns 200"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_pamukkale001")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data["journey_id"] == "journey_pamukkale001"
        assert data["name"] == "Pamukkale"
        assert "image_url" in data and data["image_url"]
        print("PASS: Pamukkale detail page loads correctly")
    
    def test_halong_bay_detail_page(self):
        """Ha Long Bay journey detail page returns 200"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_halong001")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data["journey_id"] == "journey_halong001"
        assert data["name"] == "Ha Long Bay"
        assert "image_url" in data and data["image_url"]
        print("PASS: Ha Long Bay detail page loads correctly")
    
    def test_journey_progress_endpoint(self):
        """Journey progress endpoint returns correct percentage"""
        response = requests.get(f"{BASE_URL}/api/journeys/journey_halong001/progress")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "percentage" in data, "Response missing 'percentage' field"
        assert "current_amount" in data, "Response missing 'current_amount' field"
        assert data["percentage"] == 75.0, f"Expected 75%, got {data['percentage']}%"
        print(f"PASS: Ha Long Bay progress endpoint returns correct percentage (75%)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
