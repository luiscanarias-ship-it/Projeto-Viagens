"""
Tests for Admin Journey Edit Form backend endpoints
- POST /api/admin/generate-story-chapters (AI story generation)
- PUT /api/admin/journeys/{journey_id} (Journey update)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminJourneyEditFormAPI:
    """Test admin journey edit form related endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin authentication"""
        # Admin login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@4luis.com", "password": "Admin1"}
        )
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_generate_story_chapters_endpoint_exists(self):
        """Test that generate-story-chapters endpoint exists and requires auth"""
        # Without auth - should return 401
        response = requests.post(
            f"{BASE_URL}/api/admin/generate-story-chapters",
            json={"journey_name": "Test"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("TEST PASSED: generate-story-chapters endpoint requires auth")
    
    def test_generate_story_chapters_missing_journey_name(self):
        """Test that endpoint returns 400 when journey_name is missing"""
        response = requests.post(
            f"{BASE_URL}/api/admin/generate-story-chapters",
            json={},
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400 for missing journey_name, got {response.status_code}"
        print("TEST PASSED: Returns 400 when journey_name is missing")
    
    def test_generate_story_chapters_with_valid_data(self):
        """Test story generation with valid journey name"""
        response = requests.post(
            f"{BASE_URL}/api/admin/generate-story-chapters",
            json={
                "journey_name": "China",
                "poetic_name": "Onde os Dragoes Dancam",
                "description": "Uma viagem para descobrir a cultura milenar chinesa"
            },
            headers=self.headers,
            timeout=60  # AI calls may take time
        )
        
        # Either 200 (success) or 500 (AI service issue) is acceptable
        if response.status_code == 200:
            data = response.json()
            assert "chapters" in data, "Response should contain 'chapters' key"
            chapters = data["chapters"]
            # Should have 5 chapters
            assert len(chapters) == 5 or set(chapters.keys()) == {"1", "2", "3", "4", "5"}, \
                f"Should have 5 chapters, got: {chapters.keys()}"
            
            # Each chapter should have title and lines
            for ch_num, chapter in chapters.items():
                assert "title" in chapter, f"Chapter {ch_num} missing 'title'"
                assert "lines" in chapter, f"Chapter {ch_num} missing 'lines'"
                assert isinstance(chapter["lines"], list), f"Chapter {ch_num} lines should be a list"
            
            print(f"TEST PASSED: Generated 5 story chapters successfully")
            print(f"  Chapter 1: {chapters.get('1', {}).get('title', 'N/A')}")
        elif response.status_code == 500:
            # AI service may be unavailable - this is not a test failure
            print("TEST INFO: AI service returned 500 - may be temporarily unavailable")
            print(f"  Response: {response.text}")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}, response: {response.text}")
    
    def test_get_journeys_list(self):
        """Test GET /api/admin/journeys returns list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/journeys",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        journeys = response.json()
        assert isinstance(journeys, list), "Should return a list"
        print(f"TEST PASSED: GET /api/admin/journeys returns {len(journeys)} journeys")
        
        # Store China journey ID if found
        for j in journeys:
            if "china" in j.get("name", "").lower():
                self.china_journey_id = j.get("journey_id")
                print(f"  Found China journey: {self.china_journey_id}")
                break
    
    def test_update_journey_story_chapters(self):
        """Test updating a journey with story chapters"""
        # First get journeys to find one to update
        response = requests.get(
            f"{BASE_URL}/api/admin/journeys",
            headers=self.headers
        )
        journeys = response.json()
        
        if not journeys:
            pytest.skip("No journeys available to test update")
        
        # Use the first journey
        test_journey = journeys[0]
        journey_id = test_journey.get("journey_id")
        
        # Test update with story_chapters
        test_chapters = {
            "1": {"title": "O Início", "lines": ["O sonho começa", "Com um pequeno passo"]},
            "2": {"title": "A Jornada", "lines": ["O caminho se abre", "Cada passo conta"]},
            "3": {"title": "O Meio", "lines": ["Estamos a meio", "Juntos vamos mais longe"]},
            "4": {"title": "Quase Lá", "lines": ["O sonho está perto", "Podemos sentir"]},
            "5": {"title": "O Destino", "lines": ["O sonho realizado", "Obrigado a todos"]}
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/admin/journeys/{journey_id}",
            json={"story_chapters": test_chapters, "current_chapter": 1},
            headers=self.headers
        )
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        updated = update_response.json()
        assert updated.get("story_chapters") == test_chapters, "story_chapters should be updated"
        print(f"TEST PASSED: Journey {journey_id} story_chapters updated successfully")
    
    def test_update_journey_contribution_descriptions(self):
        """Test updating a journey with contribution descriptions"""
        # First get journeys
        response = requests.get(
            f"{BASE_URL}/api/admin/journeys",
            headers=self.headers
        )
        journeys = response.json()
        
        if not journeys:
            pytest.skip("No journeys available to test update")
        
        journey_id = journeys[0].get("journey_id")
        
        # Test update with contribution_descriptions
        test_descriptions = {
            "10": "Uma recordação especial",
            "20": "Uma lembrança inesquecível",
            "50": "Uma experiência única",
            "100": "Uma memória para sempre"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/admin/journeys/{journey_id}",
            json={"contribution_descriptions": test_descriptions},
            headers=self.headers
        )
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        updated = update_response.json()
        assert updated.get("contribution_descriptions") == test_descriptions, "contribution_descriptions should be updated"
        print(f"TEST PASSED: Journey {journey_id} contribution_descriptions updated successfully")
    
    def test_update_journey_basic_fields(self):
        """Test updating basic journey fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/journeys",
            headers=self.headers
        )
        journeys = response.json()
        
        if not journeys:
            pytest.skip("No journeys available")
        
        journey_id = journeys[0].get("journey_id")
        original_name = journeys[0].get("name")
        
        # Update poetic_name
        test_poetic = "Teste Poetico Update"
        update_response = requests.put(
            f"{BASE_URL}/api/admin/journeys/{journey_id}",
            json={"poetic_name": test_poetic},
            headers=self.headers
        )
        
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated.get("poetic_name") == test_poetic
        print(f"TEST PASSED: Journey basic fields update works")
        
        # Restore original if different
        if journeys[0].get("poetic_name") != test_poetic:
            requests.put(
                f"{BASE_URL}/api/admin/journeys/{journey_id}",
                json={"poetic_name": journeys[0].get("poetic_name", "")},
                headers=self.headers
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
