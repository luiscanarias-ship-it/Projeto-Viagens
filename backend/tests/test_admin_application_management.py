"""
Test Admin Ambassador Application Management Features - 4Luis Platform
Tests for: listing applications, viewing details, approving, rejecting, requesting adjustments

Features tested:
1. Lista de candidaturas no Admin com botão Ver Detalhes
2. Modal de detalhes com: dados da viagem, perfil do embaixador, histórico de contribuições, referrals
3. Aprovar candidatura - deve ativar viagem automaticamente e enviar email
4. Pedir Ajustes - deve mudar estado para 'ajustes_pedidos' e enviar email
5. Rejeitar candidatura - deve mudar estado para 'encerrada'
6. Endpoint GET /api/admin/ambassador-journeys/{journey_id}/details
7. Endpoint PUT /api/admin/ambassador-journeys/{journey_id}/status com auto_activate=true
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "admin_password"

# Test data - will be populated during tests
TEST_JOURNEY_ID = None
ORIGINAL_STATUS = None


class TestAdminAuthentication:
    """Test admin authentication"""
    
    def test_admin_login(self):
        """Test admin can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in login response"
        assert data["user"]["is_admin"] == True, "User is not admin"
        print(f"✅ Admin login successful: {data['user']['email']}")
        return data["token"]
    
    def test_unauthorized_access_to_admin_endpoints(self):
        """Test that admin endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/ambassador-journeys")
        assert response.status_code == 401, "Admin endpoint should require auth"
        print("✅ Admin endpoints properly require authentication")


class TestListAmbassadorApplications:
    """Test listing ambassador applications - Feature 1"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    def test_list_all_applications(self, auth_token):
        """Test GET /api/admin/ambassador-journeys lists all ambassador applications"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to list applications: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total" in data, "Missing 'total' in response"
        assert "by_status" in data, "Missing 'by_status' in response"
        assert "journeys" in data, "Missing 'journeys' in response"
        
        # Verify by_status has all expected statuses
        expected_statuses = ["candidatura", "ajustes_pedidos", "aprovada", "ativa", "financiada", "realizada", "encerrada"]
        for status in expected_statuses:
            assert status in data["by_status"], f"Missing status '{status}' in by_status"
        
        print(f"✅ Listed {data['total']} ambassador applications")
        print(f"   Applications by status: {[(s, len(v)) for s, v in data['by_status'].items() if v]}")
        return data
    
    def test_filter_applications_by_candidatura_status(self, auth_token):
        """Test filtering applications by 'candidatura' (pending) status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys?status=candidatura",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned journeys should have status 'candidatura'
        for journey in data["journeys"]:
            assert journey["status"] == "candidatura", f"Journey {journey['journey_id']} has wrong status"
        
        print(f"✅ Filtered by 'candidatura' status: {len(data['journeys'])} applications")
        return data
    
    def test_application_contains_required_fields(self, auth_token):
        """Test that application objects contain all required fields for display"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        
        if data["journeys"]:
            app = data["journeys"][0]
            required_fields = [
                "journey_id", "name", "description", "image_url", "goal_amount",
                "status", "ambassador_name", "ambassador_user_id", "is_ambassador_journey"
            ]
            for field in required_fields:
                assert field in app, f"Missing required field '{field}' in application"
            
            print(f"✅ Application contains all required fields: {list(app.keys())[:10]}...")
        else:
            print("⚠️ No applications to verify fields")


class TestApplicationDetails:
    """Test application details endpoint - Feature 2"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture
    def test_journey_id(self, auth_token):
        """Get a journey ID to test with"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        if data["journeys"]:
            return data["journeys"][0]["journey_id"]
        pytest.skip("No ambassador journeys available for testing")
    
    def test_get_application_details(self, auth_token, test_journey_id):
        """Test GET /api/admin/ambassador-journeys/{journey_id}/details"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys/{test_journey_id}/details",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to get details: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "journey" in data, "Missing 'journey' in response"
        assert "ambassador" in data, "Missing 'ambassador' in response"
        assert "ambassador_history" in data, "Missing 'ambassador_history' in response"
        
        print(f"✅ Got application details for journey: {test_journey_id}")
        return data
    
    def test_details_include_journey_data(self, auth_token, test_journey_id):
        """Test that details include complete journey data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys/{test_journey_id}/details",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        
        journey = data["journey"]
        required_journey_fields = [
            "journey_id", "name", "poetic_name", "description", 
            "emotional_message", "impact_description", "image_url",
            "goal_amount", "current_amount", "status", "ambassador_name"
        ]
        
        for field in required_journey_fields:
            assert field in journey, f"Missing '{field}' in journey data"
        
        print(f"✅ Journey data complete: {journey['name']} ({journey['status']})")
    
    def test_details_include_ambassador_history(self, auth_token, test_journey_id):
        """Test that details include ambassador history with contributions and referrals"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys/{test_journey_id}/details",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        
        history = data["ambassador_history"]
        
        # Verify history structure
        assert "contributions" in history, "Missing 'contributions' in ambassador_history"
        assert "total_contributed" in history, "Missing 'total_contributed' in ambassador_history"
        assert "referrals" in history, "Missing 'referrals' in ambassador_history"
        assert "valid_referrals_count" in history, "Missing 'valid_referrals_count' in ambassador_history"
        assert "journeys_created" in history, "Missing 'journeys_created' in ambassador_history"
        
        print(f"✅ Ambassador history included:")
        print(f"   - Contributions: {len(history['contributions'])}")
        print(f"   - Total contributed: €{history['total_contributed']}")
        print(f"   - Referrals: {len(history['referrals'])}")
        print(f"   - Valid referrals: {history['valid_referrals_count']}")
    
    def test_details_not_found_for_invalid_id(self, auth_token):
        """Test 404 for non-existent journey ID"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys/invalid_journey_123/details",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404, "Should return 404 for invalid journey ID"
        print("✅ Correctly returns 404 for invalid journey ID")


class TestApproveApplication:
    """Test approving applications - Feature 3: auto-activates and sends email"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture
    def candidatura_journey_id(self, auth_token):
        """Get a journey in 'candidatura' status to test approval"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys?status=candidatura",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        if data["journeys"]:
            journey = data["journeys"][0]
            # Store original status for cleanup
            global TEST_JOURNEY_ID, ORIGINAL_STATUS
            TEST_JOURNEY_ID = journey["journey_id"]
            ORIGINAL_STATUS = journey["status"]
            return journey["journey_id"]
        pytest.skip("No candidatura journeys available for testing")
    
    def test_approve_with_auto_activate(self, auth_token, candidatura_journey_id):
        """Test PUT /api/admin/ambassador-journeys/{id}/status with auto_activate=true
        
        When approving a candidatura with auto_activate=true:
        - Status should change to 'ativa' (not just 'aprovada')
        - Journey should be visible in 'Sonhos em Materialização'
        - Email should be sent to ambassador
        """
        response = requests.put(
            f"{BASE_URL}/api/admin/ambassador-journeys/{candidatura_journey_id}/status",
            json={"status": "aprovada", "auto_activate": True},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to approve: {response.text}"
        data = response.json()
        
        # Verify the response indicates auto-activation
        assert data["new_status"] == "ativa", f"Expected 'ativa' but got {data['new_status']}"
        assert data.get("is_now_live") == True, "Should indicate journey is now live"
        assert data.get("published_in") == "Sonhos em Materialização", "Should specify where published"
        
        print(f"✅ Approved and activated journey: {candidatura_journey_id}")
        print(f"   - New status: {data['new_status']}")
        print(f"   - Is now live: {data.get('is_now_live')}")
        print(f"   - Email sent: {data.get('email_sent')}")
        
        # Verify journey is actually in 'ativa' status
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys/{candidatura_journey_id}/details",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        journey_data = verify_response.json()
        assert journey_data["journey"]["status"] == "ativa", "Journey status should be 'ativa'"
        assert journey_data["journey"]["is_active"] == True, "Journey should be active"
        
        print(f"✅ Verified journey is now 'ativa' and active")
        return data


class TestRequestAdjustments:
    """Test requesting adjustments - Feature 4"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture
    def ativa_journey_id(self, auth_token):
        """Get a journey to test adjustment request (using the one we just activated)"""
        global TEST_JOURNEY_ID
        if TEST_JOURNEY_ID:
            return TEST_JOURNEY_ID
        
        # Fall back to any available journey
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        if data["journeys"]:
            return data["journeys"][0]["journey_id"]
        pytest.skip("No journeys available for testing")
    
    def test_request_adjustments(self, auth_token, ativa_journey_id):
        """Test PUT /api/admin/ambassador-journeys/{id}/status with status='ajustes_pedidos'
        
        When requesting adjustments:
        - Status should change to 'ajustes_pedidos'
        - Adjustment request message should be stored
        - Email should be sent to ambassador
        """
        adjustment_message = "Por favor adiciona mais detalhes sobre o impacto da viagem e uma foto mais inspiradora."
        
        response = requests.put(
            f"{BASE_URL}/api/admin/ambassador-journeys/{ativa_journey_id}/status",
            json={
                "status": "ajustes_pedidos",
                "adjustment_request": adjustment_message
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to request adjustments: {response.text}"
        data = response.json()
        
        assert data["new_status"] == "ajustes_pedidos", f"Expected 'ajustes_pedidos' but got {data['new_status']}"
        
        # Verify the adjustment request was stored
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys/{ativa_journey_id}/details",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        journey_data = verify_response.json()
        assert journey_data["journey"]["status"] == "ajustes_pedidos"
        assert journey_data["journey"].get("adjustment_request") == adjustment_message
        
        print(f"✅ Requested adjustments for journey: {ativa_journey_id}")
        print(f"   - New status: {data['new_status']}")
        print(f"   - Adjustment request stored: '{adjustment_message[:50]}...'")


class TestRejectApplication:
    """Test rejecting applications - Feature 5"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture
    def test_journey_id(self, auth_token):
        """Get a journey to test rejection"""
        global TEST_JOURNEY_ID
        if TEST_JOURNEY_ID:
            return TEST_JOURNEY_ID
        
        response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        if data["journeys"]:
            return data["journeys"][0]["journey_id"]
        pytest.skip("No journeys available for testing")
    
    def test_reject_application(self, auth_token, test_journey_id):
        """Test PUT /api/admin/ambassador-journeys/{id}/status with status='encerrada'
        
        When rejecting:
        - Status should change to 'encerrada'
        - Journey should become inactive
        """
        response = requests.put(
            f"{BASE_URL}/api/admin/ambassador-journeys/{test_journey_id}/status",
            json={
                "status": "encerrada",
                "admin_notes": "Candidatura rejeitada - não cumpre os critérios"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to reject: {response.text}"
        data = response.json()
        
        assert data["new_status"] == "encerrada", f"Expected 'encerrada' but got {data['new_status']}"
        
        # Verify journey status
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/ambassador-journeys/{test_journey_id}/details",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        journey_data = verify_response.json()
        assert journey_data["journey"]["status"] == "encerrada"
        assert journey_data["journey"]["is_active"] == False
        
        print(f"✅ Rejected journey: {test_journey_id}")
        print(f"   - New status: {data['new_status']}")
        print(f"   - Is active: {journey_data['journey']['is_active']}")


class TestStatusValidation:
    """Test status validation and error handling"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    def test_invalid_status_rejected(self, auth_token):
        """Test that invalid status values are rejected"""
        response = requests.put(
            f"{BASE_URL}/api/admin/ambassador-journeys/any_id/status",
            json={"status": "invalid_status"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400, "Invalid status should return 400"
        print("✅ Invalid status values are properly rejected")
    
    def test_nonexistent_journey_returns_404(self, auth_token):
        """Test that updating non-existent journey returns 404"""
        response = requests.put(
            f"{BASE_URL}/api/admin/ambassador-journeys/nonexistent_123/status",
            json={"status": "aprovada"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404, "Non-existent journey should return 404"
        print("✅ Non-existent journey returns 404")


class TestCleanup:
    """Reset test journey to original state"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["token"]
    
    def test_reset_journey_to_candidatura(self, auth_token):
        """Reset test journey back to 'candidatura' status for future tests"""
        global TEST_JOURNEY_ID
        if not TEST_JOURNEY_ID:
            pytest.skip("No test journey to reset")
        
        response = requests.put(
            f"{BASE_URL}/api/admin/ambassador-journeys/{TEST_JOURNEY_ID}/status",
            json={"status": "candidatura", "admin_notes": "Reset for testing"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 200:
            print(f"✅ Reset journey {TEST_JOURNEY_ID} back to 'candidatura'")
        else:
            print(f"⚠️ Could not reset journey: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
