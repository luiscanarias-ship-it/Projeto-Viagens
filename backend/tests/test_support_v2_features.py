"""
Test Support V2 Features - Stats Dashboard, CTA in Emails, Quick Templates
Tests the 6 improvements to the support system:
1. CTA emocional nos emails (link para viagem principal)
2. Stats dashboard no admin (pedidos hoje, em analise, aguardar, urgentes)
3. Templates resposta rapida no admin
4. Estatisticas por tipo (ultimos 7 dias)
5. Placeholder melhorado no formulario (frontend test)
6. Mensagem de confirmacao mais humana (frontend test)
"""

import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test Credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"


class TestSupportStatsEndpoint:
    """Test admin support tickets endpoint returns extended stats"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin before each test"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"
        self.token = login_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_tickets_returns_today_count(self):
        """GET /api/admin/support/tickets returns today_count field"""
        resp = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "today_count" in data, "Response missing today_count field"
        assert isinstance(data["today_count"], int), "today_count should be an integer"
        print(f"Today count: {data['today_count']}")
    
    def test_admin_tickets_returns_in_analysis(self):
        """GET /api/admin/support/tickets returns in_analysis field"""
        resp = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "in_analysis" in data, "Response missing in_analysis field"
        assert isinstance(data["in_analysis"], int), "in_analysis should be an integer"
        print(f"In analysis count: {data['in_analysis']}")
    
    def test_admin_tickets_returns_awaiting_reply(self):
        """GET /api/admin/support/tickets returns awaiting_reply field"""
        resp = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "awaiting_reply" in data, "Response missing awaiting_reply field"
        assert isinstance(data["awaiting_reply"], int), "awaiting_reply should be an integer"
        print(f"Awaiting reply count: {data['awaiting_reply']}")
    
    def test_admin_tickets_returns_urgent_count(self):
        """GET /api/admin/support/tickets returns urgent_count field"""
        resp = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "urgent_count" in data, "Response missing urgent_count field"
        assert isinstance(data["urgent_count"], int), "urgent_count should be an integer"
        print(f"Urgent count: {data['urgent_count']}")
    
    def test_admin_tickets_returns_types_breakdown(self):
        """GET /api/admin/support/tickets returns types_breakdown (last 7 days)"""
        resp = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "types_breakdown" in data, "Response missing types_breakdown field"
        assert isinstance(data["types_breakdown"], dict), "types_breakdown should be a dict"
        print(f"Types breakdown: {data['types_breakdown']}")
        
        # If there are ticket types, validate the structure
        if data["types_breakdown"]:
            for type_name, count in data["types_breakdown"].items():
                assert isinstance(type_name, str), "Type name should be string"
                assert isinstance(count, int), "Type count should be integer"
    
    def test_all_stats_fields_in_single_response(self):
        """Verify all new stats fields are present in a single API call"""
        resp = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        required_fields = ["total", "open_count", "today_count", "in_analysis", 
                          "awaiting_reply", "urgent_count", "types_breakdown", "tickets"]
        
        for field in required_fields:
            assert field in data, f"Response missing required field: {field}"
        
        print(f"\n=== Support Stats Dashboard Data ===")
        print(f"Total tickets: {data['total']}")
        print(f"Open tickets: {data['open_count']}")
        print(f"Today: {data['today_count']}")
        print(f"In analysis: {data['in_analysis']}")
        print(f"Awaiting reply: {data['awaiting_reply']}")
        print(f"Urgent: {data['urgent_count']}")
        print(f"Types (7 days): {data['types_breakdown']}")


class TestSupportEmailsCTA:
    """Test that support emails contain CTA with link to main journey"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200
        self.token = login_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_main_journey_exists_with_is_main_trip(self):
        """Verify there is an active journey with is_main_trip=true"""
        resp = requests.get(f"{BASE_URL}/api/journeys")
        assert resp.status_code == 200
        journeys = resp.json()
        
        main_journeys = [j for j in journeys if j.get("is_main_trip") is True]
        assert len(main_journeys) >= 1, "No journey with is_main_trip=true found"
        
        main_journey = main_journeys[0]
        print(f"Main journey found: {main_journey.get('name')} (ID: {main_journey.get('journey_id')})")
        assert main_journey.get("is_active") is True, "Main journey should be active"
    
    def test_get_support_cta_block_endpoint_exists(self):
        """The get_support_cta_block function is internal, we verify its effect through email preview if available"""
        # This is an internal function - we'll verify CTA presence in emails through integration test
        # Checking that main journey exists (which is required for CTA to work)
        resp = requests.get(f"{BASE_URL}/api/journeys")
        assert resp.status_code == 200
        journeys = resp.json()
        main_journeys = [j for j in journeys if j.get("is_main_trip") is True]
        assert len(main_journeys) >= 1, "CTA requires a main journey to exist"
        print("Main journey exists - CTA block can be generated for support emails")


class TestExistingTicketOperations:
    """Test ticket operations that trigger emails with CTA"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200
        self.token = login_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_existing_tickets(self):
        """Get list of existing tickets from database"""
        resp = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        tickets = data.get("tickets", [])
        print(f"\nFound {len(tickets)} existing tickets")
        
        if tickets:
            # Show first few tickets
            for ticket in tickets[:3]:
                print(f"  - {ticket.get('ticket_id')}: {ticket.get('subject')} [{ticket.get('status')}]")
        
        return tickets
    
    def test_admin_reply_sends_email_with_cta(self):
        """Admin reply should trigger email with CTA (async, we just verify the endpoint works)"""
        # Get a ticket to reply to
        resp = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=self.headers)
        tickets = resp.json().get("tickets", [])
        
        if not tickets:
            pytest.skip("No tickets available to test admin reply")
        
        # Find a non-closed ticket
        open_tickets = [t for t in tickets if t.get("status") not in ["Fechado"]]
        if not open_tickets:
            pytest.skip("No open tickets to reply to")
        
        ticket = open_tickets[0]
        ticket_id = ticket["ticket_id"]
        
        # Send admin reply
        reply_resp = requests.post(
            f"{BASE_URL}/api/admin/support/tickets/{ticket_id}/reply",
            headers=self.headers,
            json={"message": "TEST: Testing CTA in email notification"}
        )
        
        # Should succeed (202 for async or 200)
        assert reply_resp.status_code in [200, 202], f"Admin reply failed: {reply_resp.text}"
        print(f"Admin reply sent to ticket {ticket_id}")
        print("Email with CTA block should be sent asynchronously")
    
    def test_status_change_sends_email_with_cta(self):
        """Status change to 'Resolvido' should send email with CTA"""
        # Get tickets
        resp = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=self.headers)
        tickets = resp.json().get("tickets", [])
        
        # Find ticket in "Em analise" state
        em_analise_tickets = [t for t in tickets if t.get("status") == "Em analise"]
        if not em_analise_tickets:
            pytest.skip("No tickets in 'Em analise' status to test")
        
        ticket = em_analise_tickets[0]
        ticket_id = ticket["ticket_id"]
        
        # Change status to "A aguardar resposta" (will trigger email with CTA)
        status_resp = requests.put(
            f"{BASE_URL}/api/admin/support/tickets/{ticket_id}/status",
            headers=self.headers,
            json={"status": "A aguardar resposta"}
        )
        
        assert status_resp.status_code == 200, f"Status change failed: {status_resp.text}"
        print(f"Status changed for ticket {ticket_id}")
        print("Email with CTA block should be sent for status change")


class TestQuickTemplatesBackend:
    """Quick templates are frontend-only, but we verify reply endpoint accepts template text"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200
        self.token = login_resp.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_reply_accepts_template_text(self):
        """Admin reply endpoint accepts quick template text"""
        # Quick template texts from AdminSupportSection.js
        template_texts = [
            "Recebemos o teu pedido e estamos a analisar.",
            "Podes enviar mais detalhes ou uma screenshot do problema?",
            "O problema foi resolvido. Podes confirmar se ja esta tudo a funcionar?",
            "Obrigado pelo teu feedback. A tua sugestao foi registada."
        ]
        
        # Get a ticket
        resp = requests.get(f"{BASE_URL}/api/admin/support/tickets", headers=self.headers)
        tickets = resp.json().get("tickets", [])
        
        open_tickets = [t for t in tickets if t.get("status") not in ["Fechado"]]
        if not open_tickets:
            pytest.skip("No open tickets to test template reply")
        
        ticket = open_tickets[0]
        ticket_id = ticket["ticket_id"]
        
        # Use first template
        template_text = template_texts[0]
        
        reply_resp = requests.post(
            f"{BASE_URL}/api/admin/support/tickets/{ticket_id}/reply",
            headers=self.headers,
            json={"message": template_text}
        )
        
        assert reply_resp.status_code in [200, 202], f"Template reply failed: {reply_resp.text}"
        print(f"Quick template reply sent successfully: '{template_text[:50]}...'")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
