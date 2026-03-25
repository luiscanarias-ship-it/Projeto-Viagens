"""
Iteration 68 - Exploration Mode Tests
Tests for the SmartMap exploration mode feature:
- Backend: POST /api/ai/improve-location supports types: what_to_see, where_to_eat, how_to_next
- Frontend: SmartMap popup shows Explorar and Otimizar sections with 6 buttons
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"


class TestExplorationModeBackend:
    """Backend tests for exploration mode - improve-location endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin/ambassador user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
    
    def test_improve_location_what_to_see(self, auth_headers):
        """Test improve-location with type 'what_to_see' returns suggestions"""
        response = requests.post(
            f"{BASE_URL}/api/ai/improve-location",
            headers=auth_headers,
            json={
                "location": "Torre Eiffel",
                "type": "what_to_see",
                "destination": "Paris",
                "day": 1
            },
            timeout=30
        )
        
        # Should return 200 for ambassador users
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "response" in data, "Response should have 'response' field"
        assert "suggestions" in data, "Response should have 'suggestions' field"
        assert isinstance(data["suggestions"], list), "Suggestions should be a list"
        assert len(data["suggestions"]) > 0, "Should have at least one suggestion"
        print(f"what_to_see response: {data['response']}")
        print(f"what_to_see suggestions: {data['suggestions']}")
    
    def test_improve_location_where_to_eat(self, auth_headers):
        """Test improve-location with type 'where_to_eat' returns restaurant suggestions"""
        response = requests.post(
            f"{BASE_URL}/api/ai/improve-location",
            headers=auth_headers,
            json={
                "location": "Museu do Louvre",
                "type": "where_to_eat",
                "destination": "Paris",
                "day": 2
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "response" in data, "Response should have 'response' field"
        assert "suggestions" in data, "Response should have 'suggestions' field"
        assert isinstance(data["suggestions"], list), "Suggestions should be a list"
        print(f"where_to_eat response: {data['response']}")
        print(f"where_to_eat suggestions: {data['suggestions']}")
    
    def test_improve_location_how_to_next(self, auth_headers):
        """Test improve-location with type 'how_to_next' returns transport suggestions"""
        response = requests.post(
            f"{BASE_URL}/api/ai/improve-location",
            headers=auth_headers,
            json={
                "location": "Sacre Coeur",
                "type": "how_to_next",
                "destination": "Paris",
                "day": 3
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "response" in data, "Response should have 'response' field"
        assert "suggestions" in data, "Response should have 'suggestions' field"
        assert isinstance(data["suggestions"], list), "Suggestions should be a list"
        print(f"how_to_next response: {data['response']}")
        print(f"how_to_next suggestions: {data['suggestions']}")
    
    def test_improve_location_less_queues(self, auth_headers):
        """Test improve-location with type 'less_queues' (optimization)"""
        response = requests.post(
            f"{BASE_URL}/api/ai/improve-location",
            headers=auth_headers,
            json={
                "location": "Torre Eiffel",
                "type": "less_queues",
                "destination": "Paris",
                "day": 1
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "response" in data
        assert "suggestions" in data
        print(f"less_queues response: {data['response']}")
    
    def test_improve_location_cheaper(self, auth_headers):
        """Test improve-location with type 'cheaper' (optimization)"""
        response = requests.post(
            f"{BASE_URL}/api/ai/improve-location",
            headers=auth_headers,
            json={
                "location": "Museu do Louvre",
                "type": "cheaper",
                "destination": "Paris",
                "day": 2
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "response" in data
        assert "suggestions" in data
        print(f"cheaper response: {data['response']}")
    
    def test_improve_location_best_time(self, auth_headers):
        """Test improve-location with type 'best_time' (optimization)"""
        response = requests.post(
            f"{BASE_URL}/api/ai/improve-location",
            headers=auth_headers,
            json={
                "location": "Arco do Triunfo",
                "type": "best_time",
                "destination": "Paris",
                "day": 1
            },
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "response" in data
        assert "suggestions" in data
        print(f"best_time response: {data['response']}")
    
    def test_improve_location_requires_auth(self):
        """Test that improve-location requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/ai/improve-location",
            headers={"Content-Type": "application/json"},
            json={
                "location": "Torre Eiffel",
                "type": "what_to_see",
                "destination": "Paris",
                "day": 1
            },
            timeout=10
        )
        
        # Should return 401 without auth
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"


class TestSmartMapCodeReview:
    """Code review tests for SmartMap exploration mode buttons"""
    
    def test_smartmap_has_explore_buttons_testids(self):
        """Verify SmartMap.js has data-testid for explore buttons"""
        with open("/app/frontend/src/components/SmartMap.js", "r") as f:
            content = f.read()
        
        # Check for explore button testids
        assert 'data-testid={`explore-${opt.id}`}' in content or "data-testid=\"explore-what_to_see\"" in content, \
            "SmartMap should have data-testid for explore buttons"
        
        # Check for the three explore types
        assert "'what_to_see'" in content, "SmartMap should have what_to_see option"
        assert "'where_to_eat'" in content, "SmartMap should have where_to_eat option"
        assert "'how_to_next'" in content, "SmartMap should have how_to_next option"
        
        print("SmartMap has all explore button testids")
    
    def test_smartmap_has_optimize_buttons_testids(self):
        """Verify SmartMap.js has data-testid for optimize buttons"""
        with open("/app/frontend/src/components/SmartMap.js", "r") as f:
            content = f.read()
        
        # Check for optimize button testids
        assert 'data-testid={`improve-${opt.id}`}' in content or "data-testid=\"improve-less_queues\"" in content, \
            "SmartMap should have data-testid for improve buttons"
        
        # Check for the three optimize types
        assert "'less_queues'" in content, "SmartMap should have less_queues option"
        assert "'cheaper'" in content, "SmartMap should have cheaper option"
        assert "'best_time'" in content, "SmartMap should have best_time option"
        
        print("SmartMap has all optimize button testids")
    
    def test_smartmap_has_explorar_section(self):
        """Verify SmartMap popup has 'Explorar:' section label"""
        with open("/app/frontend/src/components/SmartMap.js", "r") as f:
            content = f.read()
        
        assert "Explorar:" in content, "SmartMap popup should have 'Explorar:' section"
        print("SmartMap has 'Explorar:' section")
    
    def test_smartmap_has_otimizar_section(self):
        """Verify SmartMap popup has 'Otimizar:' section label"""
        with open("/app/frontend/src/components/SmartMap.js", "r") as f:
            content = f.read()
        
        assert "Otimizar:" in content, "SmartMap popup should have 'Otimizar:' section"
        print("SmartMap has 'Otimizar:' section")
    
    def test_smartmap_button_labels_portuguese(self):
        """Verify button labels are in Portuguese"""
        with open("/app/frontend/src/components/SmartMap.js", "r") as f:
            content = f.read()
        
        # Explore buttons
        assert "O que ver aqui" in content, "Should have 'O que ver aqui' label"
        assert "Onde comer" in content, "Should have 'Onde comer' label"
        assert "Como chegar ao proximo" in content, "Should have 'Como chegar ao proximo' label"
        
        # Optimize buttons
        assert "Menos filas" in content, "Should have 'Menos filas' label"
        assert "Mais barato" in content, "Should have 'Mais barato' label"
        assert "Melhor horario" in content, "Should have 'Melhor horario' label"
        
        print("All button labels are in Portuguese")
    
    def test_smartmap_has_special_pins_sidebar(self):
        """Verify SmartMap has special pins (airport, hotel) in sidebar"""
        with open("/app/frontend/src/components/SmartMap.js", "r") as f:
            content = f.read()
        
        assert "Referências" in content, "SmartMap should have 'Referências' section in sidebar"
        assert "sidebar-special-" in content, "SmartMap should have sidebar-special testids"
        print("SmartMap has special pins sidebar with 'Referências' section")


class TestBackendTypeLabels:
    """Verify backend type_labels include all exploration types"""
    
    def test_server_has_exploration_types(self):
        """Verify server.py has all exploration type labels"""
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
        
        # Check type_labels dict has all types
        assert '"what_to_see"' in content, "Server should have what_to_see type"
        assert '"where_to_eat"' in content, "Server should have where_to_eat type"
        assert '"how_to_next"' in content, "Server should have how_to_next type"
        assert '"less_queues"' in content, "Server should have less_queues type"
        assert '"cheaper"' in content, "Server should have cheaper type"
        assert '"best_time"' in content, "Server should have best_time type"
        
        print("Backend has all 6 type labels configured")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
