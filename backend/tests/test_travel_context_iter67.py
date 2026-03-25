"""
Travel Context Feature Tests - Iteration 67
Tests for flight_info, hotel_info, airport_to_hotel in travel plan generation,
geocode special_pins (airport, hotel), and refine endpoint preservation.
"""
import pytest
import requests
import os
import time
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@4luis.com"
ADMIN_PASSWORD = "Admin1"


class TestTravelPlanGeneration:
    """Test that travel plan generation includes flight_info, hotel_info, airport_to_hotel"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin (ambassador) token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        return resp.json()["token"]
    
    def test_travel_plan_includes_flight_info(self, admin_token):
        """POST /api/ai/travel-plan generates flight_info in the plan JSON"""
        # Use a simple destination for faster response
        tomorrow = (time.time() + 86400)
        start_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow))
        end_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow + 3*86400))
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/travel-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "destination": "Paris",
                "start_date": start_date,
                "end_date": end_date,
                "trip_type": "cultural"
            },
            timeout=60
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        plan = data.get("plan", {})
        
        # Verify flight_info structure
        assert "flight_info" in plan, "Plan should include flight_info"
        flight_info = plan["flight_info"]
        
        # Check outbound flight
        assert "outbound" in flight_info, "flight_info should have outbound"
        outbound = flight_info["outbound"]
        assert "flight_number" in outbound, "outbound should have flight_number"
        assert "departure_airport" in outbound, "outbound should have departure_airport"
        assert "arrival_airport" in outbound, "outbound should have arrival_airport"
        assert "departure_time" in outbound, "outbound should have departure_time"
        assert "arrival_time" in outbound, "outbound should have arrival_time"
        
        # Check return flight
        assert "return" in flight_info, "flight_info should have return"
        return_flight = flight_info["return"]
        assert "flight_number" in return_flight, "return should have flight_number"
        assert "departure_airport" in return_flight, "return should have departure_airport"
        assert "arrival_airport" in return_flight, "return should have arrival_airport"
        
        print(f"✓ flight_info.outbound: {outbound.get('flight_number')} {outbound.get('departure_airport')} -> {outbound.get('arrival_airport')}")
        print(f"✓ flight_info.return: {return_flight.get('flight_number')}")
    
    def test_travel_plan_includes_hotel_info(self, admin_token):
        """POST /api/ai/travel-plan generates hotel_info in the plan JSON"""
        tomorrow = (time.time() + 86400)
        start_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow))
        end_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow + 3*86400))
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/travel-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "destination": "Rome",
                "start_date": start_date,
                "end_date": end_date,
                "trip_type": "cultural"
            },
            timeout=60
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        plan = data.get("plan", {})
        
        # Verify hotel_info structure
        assert "hotel_info" in plan, "Plan should include hotel_info"
        hotel_info = plan["hotel_info"]
        
        assert "name" in hotel_info, "hotel_info should have name"
        assert hotel_info["name"], "hotel_info.name should not be empty"
        
        # Address and area are expected
        assert "address" in hotel_info, "hotel_info should have address"
        assert "area" in hotel_info, "hotel_info should have area"
        
        print(f"✓ hotel_info.name: {hotel_info.get('name')}")
        print(f"✓ hotel_info.address: {hotel_info.get('address')}")
        print(f"✓ hotel_info.area: {hotel_info.get('area')}")
    
    def test_travel_plan_includes_airport_to_hotel(self, admin_token):
        """POST /api/ai/travel-plan generates airport_to_hotel in the plan JSON"""
        tomorrow = (time.time() + 86400)
        start_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow))
        end_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow + 3*86400))
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/travel-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "destination": "Barcelona",
                "start_date": start_date,
                "end_date": end_date,
                "trip_type": "cultural"
            },
            timeout=60
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        plan = data.get("plan", {})
        
        # Verify airport_to_hotel structure
        assert "airport_to_hotel" in plan, "Plan should include airport_to_hotel"
        transport = plan["airport_to_hotel"]
        
        # Check best_option
        assert "best_option" in transport, "airport_to_hotel should have best_option"
        best = transport["best_option"]
        assert "mode" in best, "best_option should have mode"
        assert "duration" in best, "best_option should have duration"
        assert "cost" in best, "best_option should have cost"
        
        # Check alternative
        assert "alternative" in transport, "airport_to_hotel should have alternative"
        alt = transport["alternative"]
        assert "mode" in alt, "alternative should have mode"
        assert "duration" in alt, "alternative should have duration"
        assert "cost" in alt, "alternative should have cost"
        
        print(f"✓ airport_to_hotel.best_option: {best.get('mode')} - {best.get('duration')} - {best.get('cost')}")
        print(f"✓ airport_to_hotel.alternative: {alt.get('mode')} - {alt.get('duration')} - {alt.get('cost')}")
        if transport.get("tip"):
            print(f"✓ airport_to_hotel.tip: {transport.get('tip')[:50]}...")


class TestGeocodeSpecialPins:
    """Test that geocode-plan returns special_pins for airport and hotel"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin (ambassador) token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        return resp.json()["token"]
    
    def test_geocode_returns_airport_pin(self, admin_token):
        """POST /api/ai/geocode-plan returns special_pins.airport with lat/lng when flight_info exists"""
        plan = {
            "destination": "Paris",
            "flight_info": {
                "outbound": {
                    "flight_number": "AF1234",
                    "departure_airport": "Lisbon Portela - LIS",
                    "arrival_airport": "Paris Charles de Gaulle - CDG",
                    "departure_time": "08:00",
                    "arrival_time": "11:30"
                },
                "return": {
                    "flight_number": "AF1235",
                    "departure_airport": "Paris Charles de Gaulle - CDG",
                    "arrival_airport": "Lisbon Portela - LIS",
                    "departure_time": "18:00",
                    "arrival_time": "19:30"
                }
            },
            "itinerary": [
                {
                    "day": 1,
                    "title": "Dia 1 - Chegada",
                    "activities": ["Eiffel Tower", "Champs-Élysées"]
                }
            ]
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"plan": plan},
            timeout=60
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify special_pins structure
        assert "special_pins" in data, "Response should have special_pins"
        special_pins = data["special_pins"]
        
        # Check airport pin
        assert "airport" in special_pins, "special_pins should have airport"
        airport = special_pins["airport"]
        assert "lat" in airport, "airport should have lat"
        assert "lng" in airport, "airport should have lng"
        assert "name" in airport, "airport should have name"
        assert "type" in airport, "airport should have type"
        assert airport["type"] == "airport", "airport.type should be 'airport'"
        
        # Verify coordinates are valid for Paris CDG (lat ~49.0, lng ~2.5)
        assert 48 < airport["lat"] < 50, f"Airport lat {airport['lat']} seems wrong for Paris CDG"
        assert 1 < airport["lng"] < 4, f"Airport lng {airport['lng']} seems wrong for Paris CDG"
        
        print(f"✓ special_pins.airport: {airport['name']} at ({airport['lat']}, {airport['lng']})")
    
    def test_geocode_returns_hotel_pin(self, admin_token):
        """POST /api/ai/geocode-plan returns special_pins.hotel with lat/lng when hotel_info exists"""
        plan = {
            "destination": "Rome",
            "hotel_info": {
                "name": "Hotel Artemide",
                "address": "Via Nazionale 22, Rome",
                "area": "Centro Storico"
            },
            "itinerary": [
                {
                    "day": 1,
                    "title": "Dia 1",
                    "activities": ["Colosseum", "Roman Forum"]
                }
            ]
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"plan": plan},
            timeout=60
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify special_pins structure
        assert "special_pins" in data, "Response should have special_pins"
        special_pins = data["special_pins"]
        
        # Check hotel pin
        assert "hotel" in special_pins, "special_pins should have hotel"
        hotel = special_pins["hotel"]
        assert "lat" in hotel, "hotel should have lat"
        assert "lng" in hotel, "hotel should have lng"
        assert "name" in hotel, "hotel should have name"
        assert "type" in hotel, "hotel should have type"
        assert hotel["type"] == "hotel", "hotel.type should be 'hotel'"
        
        # Verify coordinates are valid for Rome (lat ~41.9, lng ~12.5)
        assert 41 < hotel["lat"] < 43, f"Hotel lat {hotel['lat']} seems wrong for Rome"
        assert 11 < hotel["lng"] < 14, f"Hotel lng {hotel['lng']} seems wrong for Rome"
        
        print(f"✓ special_pins.hotel: {hotel['name']} at ({hotel['lat']}, {hotel['lng']})")
    
    def test_geocode_returns_both_pins(self, admin_token):
        """POST /api/ai/geocode-plan returns both airport and hotel pins when both exist"""
        plan = {
            "destination": "Barcelona",
            "flight_info": {
                "outbound": {
                    "flight_number": "VY1234",
                    "departure_airport": "Lisbon - LIS",
                    "arrival_airport": "Barcelona El Prat - BCN",
                    "departure_time": "10:00",
                    "arrival_time": "12:30"
                },
                "return": {
                    "flight_number": "VY1235",
                    "departure_airport": "Barcelona El Prat - BCN",
                    "arrival_airport": "Lisbon - LIS",
                    "departure_time": "18:00",
                    "arrival_time": "18:30"
                }
            },
            "hotel_info": {
                "name": "Hotel Arts Barcelona",
                "address": "Carrer de la Marina 19-21, Barcelona",
                "area": "Port Olimpic"
            },
            "itinerary": [
                {
                    "day": 1,
                    "title": "Dia 1",
                    "activities": ["La Sagrada Familia", "Park Guell"]
                }
            ]
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/geocode-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"plan": plan},
            timeout=60
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        special_pins = data.get("special_pins", {})
        
        # Both should be present
        assert "airport" in special_pins, "special_pins should have airport"
        assert "hotel" in special_pins, "special_pins should have hotel"
        
        airport = special_pins["airport"]
        hotel = special_pins["hotel"]
        
        # Verify both have coordinates
        assert airport.get("lat") and airport.get("lng"), "Airport should have coordinates"
        assert hotel.get("lat") and hotel.get("lng"), "Hotel should have coordinates"
        
        print(f"✓ Both pins present: airport at ({airport['lat']}, {airport['lng']}), hotel at ({hotel['lat']}, {hotel['lng']})")


class TestRefinePreservesContext:
    """Test that refine endpoint preserves flight_info, hotel_info, airport_to_hotel"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin (ambassador) token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        return resp.json()["token"]
    
    def test_refine_preserves_flight_info(self, admin_token):
        """POST /api/ai/travel-plan/refine preserves flight_info from previous_plan"""
        tomorrow = (time.time() + 86400)
        start_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow))
        end_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow + 3*86400))
        
        previous_plan = {
            "destination": "Lisbon",
            "dates": f"{start_date} a {end_date}",
            "summary": "Cultural trip to Lisbon",
            "flight_info": {
                "outbound": {
                    "flight_number": "TAP TP1234",
                    "departure_airport": "London Heathrow - LHR",
                    "arrival_airport": "Lisbon Portela - LIS",
                    "departure_time": "09:00",
                    "arrival_time": "11:30"
                },
                "return": {
                    "flight_number": "TAP TP1235",
                    "departure_airport": "Lisbon Portela - LIS",
                    "arrival_airport": "London Heathrow - LHR",
                    "departure_time": "18:00",
                    "arrival_time": "21:30"
                }
            },
            "hotel_info": {
                "name": "Hotel Avenida Palace",
                "address": "Rua 1 de Dezembro 123, Lisbon",
                "area": "Baixa"
            },
            "airport_to_hotel": {
                "best_option": {
                    "mode": "Metro",
                    "details": "Take the red line from Aeroporto to Baixa-Chiado",
                    "duration": "25 min",
                    "cost": "1.50 EUR"
                },
                "alternative": {
                    "mode": "Taxi",
                    "details": "Direct taxi from airport",
                    "duration": "15 min",
                    "cost": "15-20 EUR"
                },
                "tip": "Metro is the best option during rush hour"
            },
            "itinerary": [
                {
                    "day": 1,
                    "title": "Dia 1 - Belem",
                    "activities": ["Torre de Belem", "Mosteiro dos Jeronimos"]
                }
            ],
            "weather": "Sunny, 20-25C",
            "packing": {"clothing": ["light clothes"], "essentials": ["sunscreen"]},
            "checklist": {"documents": ["passport"], "hygiene": ["toothbrush"], "tech": ["phone charger"]},
            "local_tips": ["Try pasteis de nata"]
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/refine",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "destination": "Lisbon",
                "start_date": start_date,
                "end_date": end_date,
                "trip_type": "cultural",
                "previous_plan": previous_plan,
                "refinement": "Add more restaurants and food experiences"
            },
            timeout=60
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        plan = data.get("plan", {})
        
        # Verify flight_info is preserved
        assert "flight_info" in plan, "Refined plan should preserve flight_info"
        assert plan["flight_info"]["outbound"]["flight_number"] == "TAP TP1234", "flight_info.outbound should be preserved"
        assert plan["flight_info"]["return"]["flight_number"] == "TAP TP1235", "flight_info.return should be preserved"
        
        print(f"✓ flight_info preserved: {plan['flight_info']['outbound']['flight_number']}")
    
    def test_refine_preserves_hotel_info(self, admin_token):
        """POST /api/ai/travel-plan/refine preserves hotel_info from previous_plan"""
        tomorrow = (time.time() + 86400)
        start_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow))
        end_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow + 3*86400))
        
        previous_plan = {
            "destination": "Madrid",
            "dates": f"{start_date} a {end_date}",
            "summary": "Cultural trip to Madrid",
            "flight_info": {
                "outbound": {"flight_number": "IB1234", "departure_airport": "LIS", "arrival_airport": "MAD", "departure_time": "10:00", "arrival_time": "11:30"},
                "return": {"flight_number": "IB1235", "departure_airport": "MAD", "arrival_airport": "LIS", "departure_time": "18:00", "arrival_time": "19:30"}
            },
            "hotel_info": {
                "name": "Hotel Ritz Madrid",
                "address": "Plaza de la Lealtad 5, Madrid",
                "area": "Retiro",
                "phone": "+34 91 701 67 67"
            },
            "airport_to_hotel": {
                "best_option": {"mode": "Metro", "details": "Line 8 to Nuevos Ministerios", "duration": "30 min", "cost": "5 EUR"},
                "alternative": {"mode": "Taxi", "details": "Direct", "duration": "20 min", "cost": "30 EUR"},
                "tip": "Buy a 10-trip metro card"
            },
            "itinerary": [{"day": 1, "title": "Dia 1", "activities": ["Prado Museum"]}],
            "weather": "Warm",
            "packing": {"clothing": ["light clothes"], "essentials": ["sunscreen"]},
            "checklist": {"documents": ["passport"], "hygiene": ["toothbrush"], "tech": ["charger"]},
            "local_tips": ["Visit El Retiro park"]
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/refine",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "destination": "Madrid",
                "start_date": start_date,
                "end_date": end_date,
                "trip_type": "cultural",
                "previous_plan": previous_plan,
                "refinement": "Make it more budget-friendly"
            },
            timeout=60
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        plan = data.get("plan", {})
        
        # Verify hotel_info is preserved
        assert "hotel_info" in plan, "Refined plan should preserve hotel_info"
        assert plan["hotel_info"]["name"] == "Hotel Ritz Madrid", "hotel_info.name should be preserved"
        assert plan["hotel_info"]["area"] == "Retiro", "hotel_info.area should be preserved"
        
        print(f"✓ hotel_info preserved: {plan['hotel_info']['name']}")
    
    def test_refine_preserves_airport_to_hotel(self, admin_token):
        """POST /api/ai/travel-plan/refine preserves airport_to_hotel from previous_plan"""
        tomorrow = (time.time() + 86400)
        start_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow))
        end_date = time.strftime("%Y-%m-%d", time.localtime(tomorrow + 3*86400))
        
        previous_plan = {
            "destination": "Amsterdam",
            "dates": f"{start_date} a {end_date}",
            "summary": "Cultural trip to Amsterdam",
            "flight_info": {
                "outbound": {"flight_number": "KL1234", "departure_airport": "LIS", "arrival_airport": "AMS", "departure_time": "08:00", "arrival_time": "12:00"},
                "return": {"flight_number": "KL1235", "departure_airport": "AMS", "arrival_airport": "LIS", "departure_time": "18:00", "arrival_time": "20:00"}
            },
            "hotel_info": {
                "name": "Hotel V Nesplein",
                "address": "Nes 49, Amsterdam",
                "area": "City Center"
            },
            "airport_to_hotel": {
                "best_option": {
                    "mode": "Train",
                    "details": "Direct train from Schiphol to Amsterdam Centraal",
                    "duration": "15 min",
                    "cost": "5.50 EUR"
                },
                "alternative": {
                    "mode": "Taxi",
                    "details": "Direct taxi from airport",
                    "duration": "25 min",
                    "cost": "45-55 EUR"
                },
                "tip": "Buy an OV-chipkaart for public transport"
            },
            "itinerary": [{"day": 1, "title": "Dia 1", "activities": ["Anne Frank House", "Van Gogh Museum"]}],
            "weather": "Cool and rainy",
            "packing": {"clothing": ["rain jacket"], "essentials": ["umbrella"]},
            "checklist": {"documents": ["passport"], "hygiene": ["toothbrush"], "tech": ["charger"]},
            "local_tips": ["Rent a bike"]
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/ai/travel-plan/refine",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "destination": "Amsterdam",
                "start_date": start_date,
                "end_date": end_date,
                "trip_type": "cultural",
                "previous_plan": previous_plan,
                "refinement": "Add more museums"
            },
            timeout=60
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        plan = data.get("plan", {})
        
        # Verify airport_to_hotel is preserved
        assert "airport_to_hotel" in plan, "Refined plan should preserve airport_to_hotel"
        assert plan["airport_to_hotel"]["best_option"]["mode"] == "Train", "airport_to_hotel.best_option should be preserved"
        assert plan["airport_to_hotel"]["alternative"]["mode"] == "Taxi", "airport_to_hotel.alternative should be preserved"
        assert plan["airport_to_hotel"]["tip"] == "Buy an OV-chipkaart for public transport", "airport_to_hotel.tip should be preserved"
        
        print(f"✓ airport_to_hotel preserved: {plan['airport_to_hotel']['best_option']['mode']} / {plan['airport_to_hotel']['alternative']['mode']}")


class TestFrontendDataTestIds:
    """Verify frontend components have correct data-testid attributes (code review)"""
    
    def test_travel_context_testids_exist(self):
        """Verify TravelContext.js has required data-testid attributes"""
        # Read the TravelContext.js file
        import subprocess
        result = subprocess.run(
            ["grep", "-c", "data-testid", "/app/frontend/src/components/TravelContext.js"],
            capture_output=True, text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        
        # Check for specific testids
        result2 = subprocess.run(
            ["grep", "-E", "data-testid=['\"]travel-context|data-testid=['\"]flight-info|data-testid=['\"]hotel-info|data-testid=['\"]transport-info",
             "/app/frontend/src/components/TravelContext.js"],
            capture_output=True, text=True
        )
        
        assert "travel-context" in result2.stdout, "TravelContext should have data-testid='travel-context'"
        assert "flight-info" in result2.stdout, "TravelContext should have data-testid='flight-info'"
        assert "hotel-info" in result2.stdout, "TravelContext should have data-testid='hotel-info'"
        assert "transport-info" in result2.stdout, "TravelContext should have data-testid='transport-info'"
        
        print(f"✓ TravelContext.js has {count} data-testid attributes")
        print(f"✓ Found: travel-context, flight-info, hotel-info, transport-info")
    
    def test_smartmap_special_pins_testids_exist(self):
        """Verify SmartMap.js has required data-testid attributes for special pins"""
        import subprocess
        result = subprocess.run(
            ["grep", "-E", "data-testid=['\"]sidebar-special-airport|data-testid=['\"]sidebar-special-hotel|data-testid=['\"]smart-map",
             "/app/frontend/src/components/SmartMap.js"],
            capture_output=True, text=True
        )
        
        assert "smart-map" in result.stdout, "SmartMap should have data-testid='smart-map'"
        assert "sidebar-special-airport" in result.stdout, "SmartMap should have data-testid='sidebar-special-airport'"
        assert "sidebar-special-hotel" in result.stdout, "SmartMap should have data-testid='sidebar-special-hotel'"
        
        print(f"✓ SmartMap.js has data-testid for smart-map, sidebar-special-airport, sidebar-special-hotel")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
