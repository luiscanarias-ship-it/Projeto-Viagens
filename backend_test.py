import requests
import sys
import json
from datetime import datetime

class FourLuisAPITester:
    def __init__(self, base_url="https://build-project-51.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f" - {response.text[:100]}"
            
            self.log_test(name, success, details)
            
            if success and response.content:
                try:
                    return response.json()
                except:
                    return response.text
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        print("\n🔍 Testing Basic Endpoints...")
        
        # Test root endpoint
        self.run_test("API Root", "GET", "", 200)
        
        # Test journeys endpoint
        journeys = self.run_test("Get Journeys", "GET", "journeys", 200)
        
        # Test seed journeys
        self.run_test("Seed Journeys", "POST", "seed-journeys", 200)
        
        # Test payment info
        self.run_test("Get Payment Info", "GET", "payment-info", 200)
        
        return journeys

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔍 Testing Authentication...")
        
        # Test user registration
        timestamp = datetime.now().strftime('%H%M%S')
        test_user = {
            "email": f"test_user_{timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test",
            "surname": "User"
        }
        
        register_result = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200, 
            test_user
        )
        
        if register_result and 'token' in register_result:
            self.token = register_result['token']
            print(f"   User token obtained: {self.token[:20]}...")
        
        # Test user login
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        login_result = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            login_data
        )
        
        # Test admin registration (using Admin1 password)
        admin_user = {
            "email": f"admin_{timestamp}@test.com",
            "password": "Admin1",
            "name": "Admin",
            "surname": "User"
        }
        
        admin_register_result = self.run_test(
            "Admin Registration",
            "POST",
            "auth/register",
            200,
            admin_user
        )
        
        if admin_register_result and 'token' in admin_register_result:
            self.admin_token = admin_register_result['token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
        
        # Test /auth/me endpoint
        if self.token:
            auth_headers = {"Authorization": f"Bearer {self.token}"}
            self.run_test("Get Current User", "GET", "auth/me", 200, headers=auth_headers)

    def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        print("\n🔍 Testing Admin Endpoints...")
        
        if not self.admin_token:
            print("❌ No admin token available, skipping admin tests")
            return
        
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test admin stats
        self.run_test("Admin Stats", "GET", "admin/stats", 200, headers=admin_headers)
        
        # Test get all journeys (admin)
        journeys = self.run_test("Admin Get All Journeys", "GET", "admin/journeys", 200, headers=admin_headers)
        
        # Test create journey
        new_journey = {
            "name": "Test Journey",
            "poetic_name": "Where Dreams Begin",
            "description": "A test journey for API testing",
            "emotional_message": "Every test is a step towards perfection",
            "impact_description": "Help us test the platform",
            "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4",
            "goal_amount": 1000.0
        }
        
        created_journey = self.run_test(
            "Create Journey",
            "POST",
            "admin/journeys",
            200,
            new_journey,
            headers=admin_headers
        )
        
        if created_journey and 'journey_id' in created_journey:
            journey_id = created_journey['journey_id']
            
            # Test update journey
            update_data = {
                "goal_amount": 1500.0,
                "is_active": True
            }
            
            self.run_test(
                "Update Journey",
                "PUT",
                f"admin/journeys/{journey_id}",
                200,
                update_data,
                headers=admin_headers
            )
            
            # Test delete journey
            self.run_test(
                "Delete Journey",
                "DELETE",
                f"admin/journeys/{journey_id}",
                200,
                headers=admin_headers
            )

    def test_journey_endpoints(self):
        """Test journey-related endpoints"""
        print("\n🔍 Testing Journey Endpoints...")
        
        # Get journeys to test with
        journeys = self.run_test("Get Journeys for Testing", "GET", "journeys", 200)
        
        if journeys and len(journeys) > 0:
            journey_id = journeys[0]['journey_id']
            
            # Test get specific journey
            self.run_test(
                "Get Specific Journey",
                "GET",
                f"journeys/{journey_id}",
                200
            )
        else:
            print("❌ No journeys available for testing")

    def test_payment_endpoints(self):
        """Test payment-related endpoints"""
        print("\n🔍 Testing Payment Endpoints...")
        
        # Get journeys for payment testing
        journeys = self.run_test("Get Journeys for Payment", "GET", "journeys", 200)
        
        if journeys and len(journeys) > 0:
            journey_id = journeys[0]['journey_id']
            
            # Test create checkout session
            checkout_data = {
                "amount_key": "10",
                "journey_id": journey_id,
                "origin_url": "https://test.com",
                "sponsor_code": None
            }
            
            # This might fail due to Stripe configuration, but we test the endpoint
            self.run_test(
                "Create Stripe Checkout",
                "POST",
                "contributions/create-checkout",
                200,
                checkout_data
            )

    def test_translation_endpoint(self):
        """Test translation endpoint"""
        print("\n🔍 Testing Translation...")
        
        translation_data = {
            "texts": {
                "hello": "Hello",
                "world": "World"
            },
            "target_language": "Portuguese"
        }
        
        self.run_test(
            "Translation Service",
            "POST",
            "translate",
            200,
            translation_data
        )

    def test_new_features(self):
        """Test new features: dreamers stats, settings, contributions management, raffle"""
        print("\n🔍 Testing New Features...")
        
        # Test dreamers stats endpoint
        dreamers_stats = self.run_test(
            "Get Dreamers Stats",
            "GET",
            "dreamers-stats",
            200
        )
        
        if dreamers_stats:
            print(f"   Dreamers stats: {dreamers_stats}")
        
        # Test site settings endpoint
        settings = self.run_test(
            "Get Site Settings",
            "GET",
            "settings",
            200
        )
        
        if settings:
            print(f"   Site settings: {settings}")
        
        # Test admin settings endpoints
        if self.admin_token:
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test get admin settings
            admin_settings = self.run_test(
                "Get Admin Settings",
                "GET",
                "admin/settings",
                200,
                headers=admin_headers
            )
            
            # Test update admin settings
            new_settings = {
                "contact_email": "test@4luis.com",
                "contact_message": "Test message for contact section"
            }
            
            self.run_test(
                "Update Admin Settings",
                "PUT",
                "admin/settings",
                200,
                new_settings,
                headers=admin_headers
            )
            
            # Test admin contributions endpoint
            contributions = self.run_test(
                "Get Admin Contributions",
                "GET",
                "admin/contributions",
                200,
                headers=admin_headers
            )
            
            if contributions:
                print(f"   Found {len(contributions)} contributions")
            
            # Test manual contribution creation
            manual_contrib_data = {
                "journey_id": "journey_china001",  # Using seeded journey
                "amount_key": "10",
                "payment_method": "MBWay",
                "is_crypto": False,
                "name": "Test User",
                "email": "testcontrib@test.com"
            }
            
            manual_contrib = self.run_test(
                "Create Manual Contribution",
                "POST",
                "contributions/manual",
                200,
                manual_contrib_data
            )
            
            if manual_contrib and 'contribution_id' in manual_contrib:
                contrib_id = manual_contrib['contribution_id']
                print(f"   Created manual contribution: {contrib_id}")
                
                # Test confirm contribution
                self.run_test(
                    "Confirm Manual Contribution",
                    "PUT",
                    f"admin/contributions/{contrib_id}/confirm",
                    200,
                    {},
                    headers=admin_headers
                )
            
            # Test raffle endpoints (get tickets for a journey)
            self.run_test(
                "Get Raffle Tickets",
                "GET",
                "admin/raffle/journey_china001",
                200,
                headers=admin_headers
            )

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting 4Luis API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Run test suites
        self.test_basic_endpoints()
        self.test_auth_endpoints()
        self.test_admin_endpoints()
        self.test_journey_endpoints()
        self.test_payment_endpoints()
        self.test_translation_endpoint()
        self.test_new_features()
        
        # Print summary
        print(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed")
            return 1

def main():
    tester = FourLuisAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())