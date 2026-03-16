"""
Support Ticket System Tests
Tests for creating/managing support tickets - user and admin flows
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"

# Test user for creating tickets
TEST_USER_EMAIL = f"test_support_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "TestPass123"
TEST_USER_NAME = "Test Support User"


class TestSupportTicketSystem:
    """Support Ticket CRUD and workflow tests"""
    
    admin_token = None
    user_token = None
    user_id = None
    created_ticket_id = None
    
    @classmethod
    def setup_class(cls):
        """Get admin token and create test user"""
        # Login as admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        cls.admin_token = response.json()["token"]
        
        # Register test user
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        if response.status_code == 200:
            cls.user_token = response.json()["token"]
            cls.user_id = response.json()["user"]["user_id"]
        elif response.status_code == 400 and "Email já registado" in response.text:
            # User exists, try login
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            if response.status_code == 200:
                cls.user_token = response.json()["token"]
                cls.user_id = response.json()["user"]["user_id"]
    
    # ==================== USER ENDPOINTS ====================
    
    def test_01_create_ticket_success(self):
        """POST /api/support/tickets - create ticket with valid data"""
        if not self.user_token:
            pytest.skip("User token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/support/tickets",
            json={
                "ticket_type": "Problema tecnico",
                "subject": "Teste automatico - Erro no sistema",
                "description": "Este e um teste automatico para verificar o sistema de tickets."
            },
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200, f"Create ticket failed: {response.text}"
        data = response.json()
        
        # Verify ticket_id format SUP-2026-XXXXX
        assert "ticket_id" in data, "Response missing ticket_id"
        assert data["ticket_id"].startswith("SUP-"), f"Invalid ticket_id format: {data['ticket_id']}"
        assert "2026" in data["ticket_id"] or "2025" in data["ticket_id"], f"Invalid year in ticket_id: {data['ticket_id']}"
        
        # Verify status is Aberto
        assert data["status"] == "Aberto", f"Expected status 'Aberto', got '{data['status']}'"
        
        # Verify priority is auto-assigned (Problema tecnico = Media)
        assert data["priority"] == "Media", f"Expected priority 'Media', got '{data['priority']}'"
        
        # Store for later tests
        TestSupportTicketSystem.created_ticket_id = data["ticket_id"]
        print(f"Created ticket: {data['ticket_id']} with status {data['status']} and priority {data['priority']}")
    
    def test_02_create_ticket_payment_type_high_priority(self):
        """POST /api/support/tickets - Pagamento type should get Alta priority"""
        if not self.user_token:
            pytest.skip("User token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/support/tickets",
            json={
                "ticket_type": "Pagamento",
                "subject": "Problema com pagamento",
                "description": "Teste de prioridade alta para pagamentos."
            },
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200, f"Create ticket failed: {response.text}"
        data = response.json()
        
        # Pagamento should have Alta priority
        assert data["priority"] == "Alta", f"Expected priority 'Alta' for Pagamento, got '{data['priority']}'"
        print(f"Payment ticket created with priority: {data['priority']}")
    
    def test_03_create_ticket_reclamacao_high_priority(self):
        """POST /api/support/tickets - Reclamacao type should get Alta priority"""
        if not self.user_token:
            pytest.skip("User token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/support/tickets",
            json={
                "ticket_type": "Reclamacao",
                "subject": "Reclamacao de teste",
                "description": "Teste de prioridade alta para reclamacoes."
            },
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200, f"Create ticket failed: {response.text}"
        data = response.json()
        
        # Reclamacao should have Alta priority
        assert data["priority"] == "Alta", f"Expected priority 'Alta' for Reclamacao, got '{data['priority']}'"
        print(f"Reclamacao ticket created with priority: {data['priority']}")
    
    def test_04_create_ticket_sugestao_low_priority(self):
        """POST /api/support/tickets - Sugestao type should get Baixa priority"""
        if not self.user_token:
            pytest.skip("User token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/support/tickets",
            json={
                "ticket_type": "Sugestao",
                "subject": "Sugestao de melhoria",
                "description": "Teste de prioridade baixa para sugestoes."
            },
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200, f"Create ticket failed: {response.text}"
        data = response.json()
        
        # Sugestao should have Baixa priority
        assert data["priority"] == "Baixa", f"Expected priority 'Baixa' for Sugestao, got '{data['priority']}'"
        print(f"Sugestao ticket created with priority: {data['priority']}")
    
    def test_05_create_ticket_validation_error(self):
        """POST /api/support/tickets - should fail without required fields"""
        if not self.user_token:
            pytest.skip("User token not available")
        
        # Missing description
        response = requests.post(
            f"{BASE_URL}/api/support/tickets",
            json={
                "ticket_type": "Problema tecnico",
                "subject": "Test subject"
            },
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for missing description, got {response.status_code}"
        print("Validation correctly rejected ticket without description")
    
    def test_06_create_ticket_invalid_type(self):
        """POST /api/support/tickets - should fail with invalid ticket type"""
        if not self.user_token:
            pytest.skip("User token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/support/tickets",
            json={
                "ticket_type": "InvalidType",
                "subject": "Test subject",
                "description": "Test description"
            },
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid type, got {response.status_code}"
        print("Validation correctly rejected invalid ticket type")
    
    def test_07_list_user_tickets(self):
        """GET /api/support/tickets - list user's tickets"""
        if not self.user_token:
            pytest.skip("User token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/support/tickets",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200, f"List tickets failed: {response.text}"
        data = response.json()
        
        assert "tickets" in data, "Response missing 'tickets' key"
        assert isinstance(data["tickets"], list), "tickets should be a list"
        assert len(data["tickets"]) >= 1, "Expected at least 1 ticket"
        
        # Verify internal_notes not exposed to user
        for ticket in data["tickets"]:
            assert "internal_notes" not in ticket, "internal_notes should not be exposed to user"
        
        print(f"User has {len(data['tickets'])} tickets")
    
    def test_08_get_ticket_detail_user(self):
        """GET /api/support/tickets/{ticket_id} - get ticket detail (no internal_notes)"""
        if not self.user_token or not self.created_ticket_id:
            pytest.skip("User token or ticket_id not available")
        
        response = requests.get(
            f"{BASE_URL}/api/support/tickets/{self.created_ticket_id}",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200, f"Get ticket failed: {response.text}"
        data = response.json()
        
        assert data["ticket_id"] == self.created_ticket_id
        assert "internal_notes" not in data, "internal_notes should NOT be exposed to user"
        assert "messages" in data, "messages should be present"
        
        print(f"Ticket detail retrieved: {data['ticket_id']} status={data['status']}")
    
    def test_09_user_reply_to_ticket(self):
        """POST /api/support/tickets/{ticket_id}/reply - user reply"""
        if not self.user_token or not self.created_ticket_id:
            pytest.skip("User token or ticket_id not available")
        
        response = requests.post(
            f"{BASE_URL}/api/support/tickets/{self.created_ticket_id}/reply",
            json={"message": "Resposta do utilizador ao ticket de teste."},
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200, f"User reply failed: {response.text}"
        data = response.json()
        
        assert data["status"] == "ok"
        assert "message" in data
        assert data["message"]["sender"] == "user"
        
        print(f"User reply added, new status: {data.get('new_status', 'unchanged')}")
    
    # ==================== ADMIN ENDPOINTS ====================
    
    def test_10_admin_list_tickets(self):
        """GET /api/admin/support/tickets - list all tickets with filters"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/support/tickets",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Admin list tickets failed: {response.text}"
        data = response.json()
        
        assert "tickets" in data
        assert "total" in data
        assert "open_count" in data
        
        print(f"Admin sees {data['total']} total tickets, {data['open_count']} open")
    
    def test_11_admin_list_tickets_filter_status(self):
        """GET /api/admin/support/tickets?status=Aberto - filter by status"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/support/tickets?status=Aberto",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Admin filter failed: {response.text}"
        data = response.json()
        
        # All returned tickets should have status Aberto
        for ticket in data["tickets"]:
            assert ticket["status"] == "Aberto", f"Expected 'Aberto', got '{ticket['status']}'"
        
        print(f"Found {len(data['tickets'])} tickets with status 'Aberto'")
    
    def test_12_admin_list_tickets_filter_type(self):
        """GET /api/admin/support/tickets?ticket_type=Pagamento - filter by type"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/support/tickets?ticket_type=Pagamento",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Admin filter failed: {response.text}"
        data = response.json()
        
        for ticket in data["tickets"]:
            assert ticket["ticket_type"] == "Pagamento"
        
        print(f"Found {len(data['tickets'])} Pagamento tickets")
    
    def test_13_admin_list_tickets_filter_priority(self):
        """GET /api/admin/support/tickets?priority=Alta - filter by priority"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/support/tickets?priority=Alta",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Admin filter failed: {response.text}"
        data = response.json()
        
        for ticket in data["tickets"]:
            assert ticket["priority"] == "Alta"
        
        print(f"Found {len(data['tickets'])} Alta priority tickets")
    
    def test_14_admin_list_tickets_search(self):
        """GET /api/admin/support/tickets?search=... - search tickets"""
        if not self.admin_token or not self.created_ticket_id:
            pytest.skip("Admin token or ticket_id not available")
        
        # Search by ticket_id
        response = requests.get(
            f"{BASE_URL}/api/admin/support/tickets?search={self.created_ticket_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Admin search failed: {response.text}"
        data = response.json()
        
        assert len(data["tickets"]) >= 1, "Expected to find ticket by ID search"
        print(f"Search found {len(data['tickets'])} tickets for '{self.created_ticket_id}'")
    
    def test_15_admin_get_ticket_detail(self):
        """GET /api/admin/support/tickets/{ticket_id} - includes internal_notes"""
        if not self.admin_token or not self.created_ticket_id:
            pytest.skip("Admin token or ticket_id not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/support/tickets/{self.created_ticket_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Admin get ticket failed: {response.text}"
        data = response.json()
        
        assert data["ticket_id"] == self.created_ticket_id
        assert "internal_notes" in data, "Admin should see internal_notes"
        assert "messages" in data
        
        print(f"Admin ticket detail: {data['ticket_id']}, internal_notes count: {len(data['internal_notes'])}")
    
    def test_16_admin_reply_to_ticket(self):
        """POST /api/admin/support/tickets/{ticket_id}/reply - admin reply"""
        if not self.admin_token or not self.created_ticket_id:
            pytest.skip("Admin token or ticket_id not available")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/support/tickets/{self.created_ticket_id}/reply",
            json={"message": "Resposta da equipa de suporte ao ticket."},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Admin reply failed: {response.text}"
        data = response.json()
        
        assert data["status"] == "ok"
        assert data["message"]["sender"] == "admin"
        assert data["message"]["sender_name"] == "Equipa 4Luis"
        
        print("Admin reply added successfully")
    
    def test_17_admin_update_status(self):
        """PUT /api/admin/support/tickets/{ticket_id}/status - change status"""
        if not self.admin_token or not self.created_ticket_id:
            pytest.skip("Admin token or ticket_id not available")
        
        response = requests.put(
            f"{BASE_URL}/api/admin/support/tickets/{self.created_ticket_id}/status",
            json={"status": "A aguardar resposta"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Update status failed: {response.text}"
        data = response.json()
        
        assert data["status"] == "ok"
        assert data["new_status"] == "A aguardar resposta"
        
        print(f"Status changed to: {data['new_status']}")
    
    def test_18_admin_update_priority(self):
        """PUT /api/admin/support/tickets/{ticket_id}/priority - change priority"""
        if not self.admin_token or not self.created_ticket_id:
            pytest.skip("Admin token or ticket_id not available")
        
        response = requests.put(
            f"{BASE_URL}/api/admin/support/tickets/{self.created_ticket_id}/priority",
            json={"priority": "Alta"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Update priority failed: {response.text}"
        data = response.json()
        
        assert data["status"] == "ok"
        assert data["new_priority"] == "Alta"
        
        print(f"Priority changed to: {data['new_priority']}")
    
    def test_19_admin_add_internal_note(self):
        """POST /api/admin/support/tickets/{ticket_id}/note - add internal note"""
        if not self.admin_token or not self.created_ticket_id:
            pytest.skip("Admin token or ticket_id not available")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/support/tickets/{self.created_ticket_id}/note",
            json={"note": "Nota interna de teste - verificar com equipa tecnica."},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Add note failed: {response.text}"
        data = response.json()
        
        assert data["status"] == "ok"
        assert "note" in data
        assert "note_id" in data["note"]
        
        print(f"Internal note added: {data['note']['note_id']}")
    
    def test_20_user_reply_changes_status_to_em_analise(self):
        """POST /api/support/tickets/{ticket_id}/reply - status changes from 'A aguardar resposta' to 'Em analise'"""
        if not self.user_token or not self.created_ticket_id:
            pytest.skip("User token or ticket_id not available")
        
        # First verify current status is 'A aguardar resposta' (set in test_17)
        response = requests.get(
            f"{BASE_URL}/api/support/tickets/{self.created_ticket_id}",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        if response.status_code != 200:
            pytest.skip("Could not get ticket")
        
        current_status = response.json().get("status")
        print(f"Current status before reply: {current_status}")
        
        # Send user reply
        response = requests.post(
            f"{BASE_URL}/api/support/tickets/{self.created_ticket_id}/reply",
            json={"message": "Nova resposta para verificar mudanca de estado."},
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200, f"Reply failed: {response.text}"
        data = response.json()
        
        # If status was 'A aguardar resposta', it should change to 'Em analise'
        if current_status == "A aguardar resposta":
            assert data["new_status"] == "Em analise", f"Expected 'Em analise', got '{data.get('new_status')}'"
            print(f"Status correctly changed from 'A aguardar resposta' to 'Em analise'")
        else:
            print(f"Status was {current_status}, new status: {data.get('new_status', 'unchanged')}")
    
    def test_21_admin_mark_resolved(self):
        """PUT /api/admin/support/tickets/{ticket_id}/status - mark as Resolvido"""
        if not self.admin_token or not self.created_ticket_id:
            pytest.skip("Admin token or ticket_id not available")
        
        response = requests.put(
            f"{BASE_URL}/api/admin/support/tickets/{self.created_ticket_id}/status",
            json={"status": "Resolvido"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Mark resolved failed: {response.text}"
        data = response.json()
        
        assert data["new_status"] == "Resolvido"
        print("Ticket marked as Resolvido")
    
    def test_22_admin_close_ticket(self):
        """PUT /api/admin/support/tickets/{ticket_id}/status - close ticket"""
        if not self.admin_token or not self.created_ticket_id:
            pytest.skip("Admin token or ticket_id not available")
        
        response = requests.put(
            f"{BASE_URL}/api/admin/support/tickets/{self.created_ticket_id}/status",
            json={"status": "Fechado"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200, f"Close ticket failed: {response.text}"
        data = response.json()
        
        assert data["new_status"] == "Fechado"
        print("Ticket closed successfully")
    
    # ==================== AUTH TESTS ====================
    
    def test_23_user_endpoints_require_auth(self):
        """User endpoints should require authentication"""
        # No token
        response = requests.get(f"{BASE_URL}/api/support/tickets")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        response = requests.post(f"{BASE_URL}/api/support/tickets", json={})
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("User endpoints correctly require auth")
    
    def test_24_admin_endpoints_require_admin(self):
        """Admin endpoints should require admin privileges"""
        if not self.user_token:
            pytest.skip("User token not available")
        
        # Regular user trying admin endpoint
        response = requests.get(
            f"{BASE_URL}/api/admin/support/tickets",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        
        print("Admin endpoints correctly require admin role")


class TestFileUpload:
    """File upload tests for support tickets"""
    
    @classmethod
    def setup_class(cls):
        # Get user token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        cls.token = response.json().get("token") if response.status_code == 200 else None
    
    def test_upload_requires_auth(self):
        """POST /api/support/upload - requires authentication"""
        response = requests.post(f"{BASE_URL}/api/support/upload")
        assert response.status_code in [401, 422], f"Expected 401/422, got {response.status_code}"
        print("Upload endpoint correctly requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
