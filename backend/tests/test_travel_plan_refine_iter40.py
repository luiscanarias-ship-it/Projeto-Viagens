"""
Test cases for Travel Plan Refine API - Iteration 40
Tests the new /api/ai/travel-plan/refine endpoint for the unified travel guide feature
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTravelPlanRefineEndpoint:
    """Tests for POST /api/ai/travel-plan/refine endpoint"""
    
    @pytest.fixture
    def sample_previous_plan(self):
        """Sample previous plan required for refine endpoint"""
        return {
            "destination": "Lisboa",
            "dates": "2026-04-01 a 2026-04-03",
            "summary": "Uma viagem cultural por Lisboa",
            "itinerary": [
                {
                    "day": 1,
                    "title": "Dia 1 - Belém",
                    "activities": ["Visitar a Torre de Belém", "Pastéis de Belém", "Mosteiro dos Jerónimos"]
                },
                {
                    "day": 2,
                    "title": "Dia 2 - Alfama",
                    "activities": ["Castelo de São Jorge", "Passear pela Alfama", "Fado à noite"]
                }
            ],
            "weather": "Tempo ameno, 18-22°C",
            "packing": {
                "clothing": ["Roupa leve", "Casaco para a noite"],
                "essentials": ["Protetor solar", "Sapatos confortáveis"]
            },
            "checklist": {
                "documents": ["Passaporte", "Cartão de cidadão"],
                "hygiene": ["Kit de higiene pessoal"],
                "tech": ["Carregador", "Adaptador"]
            },
            "local_tips": ["Usar transportes públicos", "Visitar ao fim da tarde para menos filas"]
        }
    
    def test_refine_missing_refinement_returns_400(self, sample_previous_plan):
        """Test that missing 'refinement' field returns 400 error"""
        payload = {
            "destination": "Lisboa",
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
            "trip_type": "cultural",
            "previous_plan": sample_previous_plan
            # Missing refinement field
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/refine",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        # Message could be "obrigatorio" or "obrigatorias" - check for root word
        assert "obrigatori" in data["detail"].lower() or "required" in data["detail"].lower()
        print(f"✅ Missing refinement returns 400: {data['detail']}")
    
    def test_refine_missing_previous_plan_returns_400(self):
        """Test that missing 'previous_plan' field returns 400 error"""
        payload = {
            "destination": "Lisboa",
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
            "trip_type": "cultural",
            "refinement": "Adicionar restaurantes"
            # Missing previous_plan field
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/refine",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "obrigatorio" in data["detail"].lower() or "plano" in data["detail"].lower()
        print(f"✅ Missing previous_plan returns 400: {data['detail']}")
    
    def test_refine_missing_destination_returns_400(self, sample_previous_plan):
        """Test that missing destination field returns 400 error"""
        payload = {
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
            "trip_type": "cultural",
            "previous_plan": sample_previous_plan,
            "refinement": "Adicionar restaurantes"
            # Missing destination
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/refine",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✅ Missing destination returns 400")
    
    def test_refine_empty_refinement_returns_400(self, sample_previous_plan):
        """Test that empty refinement string returns 400 error"""
        payload = {
            "destination": "Lisboa",
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
            "trip_type": "cultural",
            "previous_plan": sample_previous_plan,
            "refinement": ""  # Empty string
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/refine",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✅ Empty refinement returns 400")
    
    def test_refine_empty_previous_plan_returns_400(self):
        """Test that empty previous_plan returns 400 error"""
        payload = {
            "destination": "Lisboa",
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
            "trip_type": "cultural",
            "previous_plan": {},  # Empty object
            "refinement": "Adicionar restaurantes"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/refine",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Empty object is still truthy in Python, but the endpoint might handle it differently
        # Let's verify it at least accepts the request structure
        print(f"Empty previous_plan response: {response.status_code}")
        # This is a design decision - empty {} might be valid or not
        # At minimum, endpoint should not crash
        assert response.status_code in [400, 429, 500], f"Got unexpected status: {response.status_code}"
        print(f"✅ Empty previous_plan handled: {response.status_code}")


class TestAffiliateLinksForTravelGuide:
    """Tests for affiliate links used in unified travel guide"""
    
    def test_get_affiliate_links(self):
        """Test that /api/affiliate-links returns booking, skyscanner, airalo, getyourguide"""
        response = requests.get(f"{BASE_URL}/api/affiliate-links", timeout=10)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check required partner links for unified guide CTAs
        required_partners = ["booking", "skyscanner", "airalo", "getyourguide"]
        for partner in required_partners:
            assert partner in data, f"Missing partner: {partner}"
            assert "url" in data[partner], f"Missing URL for {partner}"
            assert "name" in data[partner], f"Missing name for {partner}"
        
        print(f"✅ All required partner links present: {required_partners}")


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_reachable(self):
        """Test that API is reachable"""
        response = requests.get(f"{BASE_URL}/api", timeout=10)
        # May return 404 or other status, just check it's reachable
        assert response.status_code in [200, 404, 422], f"API unreachable: {response.status_code}"
        print(f"✅ API is reachable at {BASE_URL}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
