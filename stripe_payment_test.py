#!/usr/bin/env python3
"""
Comprehensive Stripe Payment Flow Test for 4Luis Application

This test specifically targets the reported "Network error" issue when clicking "Cartão" (Card)
on the China journey page.
"""
import requests
import json
import sys
import time
from datetime import datetime

class StripePaymentTester:
    def __init__(self):
        # Use the correct frontend URL from the review request
        self.frontend_url = "https://travel-celebrate.preview.emergentagent.com"
        self.api_url = f"{self.frontend_url}/api"
        self.session = requests.Session()
        
        # Test results tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}")
            if details:
                print(f"   Error: {details}")
            self.failed_tests.append({
                "test": test_name,
                "error": details
            })
        
    def test_api_connectivity(self):
        """Test basic API connectivity using the correct URL"""
        print("\n🔍 Testing API Connectivity...")
        
        try:
            response = self.session.get(f"{self.api_url}/", timeout=10)
            self.log_result(
                "API Root Endpoint", 
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            return response.status_code == 200
        except Exception as e:
            self.log_result("API Root Endpoint", False, str(e))
            return False
    
    def test_stripe_config_endpoint(self):
        """Test GET /api/stripe/config endpoint"""
        print("\n🔍 Testing Stripe Configuration...")
        
        try:
            response = self.session.get(f"{self.api_url}/stripe/config", timeout=10)
            
            if response.status_code == 200:
                config = response.json()
                print(f"   Response: {config}")
                
                # Check if publishable_key exists
                has_key = 'publishable_key' in config and config['publishable_key']
                self.log_result(
                    "GET /api/stripe/config returns publishable_key",
                    has_key,
                    "Missing publishable_key" if not has_key else f"Key: {config['publishable_key'][:20]}..."
                )
                return config if has_key else None
            else:
                self.log_result(
                    "GET /api/stripe/config",
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:100]}"
                )
                return None
                
        except Exception as e:
            self.log_result("GET /api/stripe/config", False, str(e))
            return None
    
    def test_china_journey_access(self):
        """Test access to China journey specifically"""
        print("\n🔍 Testing China Journey Access...")
        
        # First, get all journeys to see what's available
        try:
            response = self.session.get(f"{self.api_url}/journeys", timeout=10)
            if response.status_code == 200:
                journeys = response.json()
                print(f"   Found {len(journeys)} journeys")
                
                # Look for China journey
                china_journey = None
                for journey in journeys:
                    if "china" in journey.get("name", "").lower() or "china" in journey.get("journey_id", "").lower():
                        china_journey = journey
                        break
                
                if china_journey:
                    journey_id = china_journey['journey_id']
                    print(f"   Found China journey: {journey_id}")
                    
                    # Test specific journey endpoint
                    journey_response = self.session.get(f"{self.api_url}/journeys/{journey_id}", timeout=10)
                    self.log_result(
                        f"GET /api/journeys/{journey_id}",
                        journey_response.status_code == 200,
                        f"Status: {journey_response.status_code}"
                    )
                    
                    return journey_id
                else:
                    # Try hardcoded journey_id from tests
                    journey_id = "journey_china001"
                    journey_response = self.session.get(f"{self.api_url}/journeys/{journey_id}", timeout=10)
                    
                    success = journey_response.status_code == 200
                    self.log_result(
                        f"GET /api/journeys/{journey_id} (hardcoded)",
                        success,
                        f"Status: {journey_response.status_code}"
                    )
                    
                    return journey_id if success else None
            else:
                self.log_result(
                    "GET /api/journeys", 
                    False, 
                    f"Status: {response.status_code}"
                )
                return None
                
        except Exception as e:
            self.log_result("China Journey Access", False, str(e))
            return None
    
    def test_contribution_creation_flow(self, journey_id):
        """Test the complete contribution creation flow that triggers the issue"""
        print("\n🔍 Testing Contribution Creation Flow...")
        
        # Test data that mimics real user interaction
        contribution_data = {
            "amount": 10,  # €10 as mentioned in review request
            "payment_method": "stripe",
            "journey_id": journey_id,
            "contributor_name": "Test User",
            "contributor_email": "test@test.com",
            "public_message": "Testing payment flow",
            "show_name": True
        }
        
        try:
            # This is the exact call that should trigger when user clicks "Cartão"
            print(f"   Creating contribution: {contribution_data}")
            response = self.session.post(
                f"{self.api_url}/contributions/create", 
                json=contribution_data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            print(f"   Response status: {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Response data: {result}")
                
                # Check for required Stripe Payment Element fields
                required_fields = ['client_secret', 'contribution_id', 'payment_intent_id']
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    self.log_result(
                        "POST /api/contributions/create returns all required fields",
                        True
                    )
                    
                    # Test if client_secret is valid format
                    client_secret = result['client_secret']
                    valid_format = client_secret.startswith('pi_') and '_secret_' in client_secret
                    self.log_result(
                        "client_secret has valid format",
                        valid_format,
                        f"client_secret: {client_secret}" if not valid_format else ""
                    )
                    
                    return result
                else:
                    self.log_result(
                        "POST /api/contributions/create returns all required fields",
                        False,
                        f"Missing fields: {missing_fields}"
                    )
            else:
                # This is likely the "Network error" source
                self.log_result(
                    "POST /api/contributions/create",
                    False,
                    f"Status: {response.status_code}, Body: {response.text[:200]}"
                )
                
        except requests.exceptions.Timeout:
            self.log_result("POST /api/contributions/create", False, "Request timeout - this could cause 'Network error' in frontend")
        except requests.exceptions.ConnectionError as e:
            self.log_result("POST /api/contributions/create", False, f"Connection error: {e}")
        except Exception as e:
            self.log_result("POST /api/contributions/create", False, f"Exception: {e}")
        
        return None
    
    def test_cors_headers(self):
        """Test CORS headers that could cause network errors"""
        print("\n🔍 Testing CORS Configuration...")
        
        # Test preflight request (OPTIONS)
        try:
            headers = {
                'Origin': self.frontend_url,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(
                f"{self.api_url}/contributions/create",
                headers=headers,
                timeout=10
            )
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            print(f"   CORS headers: {cors_headers}")
            
            self.log_result(
                "OPTIONS /api/contributions/create (CORS preflight)",
                response.status_code in [200, 204],
                f"Status: {response.status_code}, Headers: {cors_headers}"
            )
            
        except Exception as e:
            self.log_result("CORS preflight check", False, str(e))
    
    def test_payment_info_endpoint(self):
        """Test payment info endpoint"""
        print("\n🔍 Testing Payment Info Endpoint...")
        
        try:
            response = self.session.get(f"{self.api_url}/contributions/payment-info", timeout=10)
            self.log_result(
                "GET /api/contributions/payment-info",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                payment_info = response.json()
                print(f"   Payment methods available: {list(payment_info.keys())}")
                
        except Exception as e:
            self.log_result("GET /api/contributions/payment-info", False, str(e))
    
    def test_network_timing(self):
        """Test response timing that could cause timeout issues"""
        print("\n🔍 Testing Network Timing...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.api_url}/stripe/config", timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Consider responses slower than 5 seconds as potentially problematic
            fast_enough = response_time < 5.0
            
            self.log_result(
                f"API response time ({response_time:.2f}s)",
                fast_enough,
                f"Too slow: {response_time:.2f}s" if not fast_enough else ""
            )
            
        except Exception as e:
            self.log_result("Network timing test", False, str(e))
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Stripe Payment Flow Test")
        print(f"Frontend URL: {self.frontend_url}")
        print(f"API URL: {self.api_url}")
        print("-" * 80)
        
        # Test 1: Basic connectivity
        if not self.test_api_connectivity():
            print("\n❌ API not accessible, stopping tests")
            return False
        
        # Test 2: Stripe configuration
        stripe_config = self.test_stripe_config_endpoint()
        
        # Test 3: China journey access
        journey_id = self.test_china_journey_access()
        
        # Test 4: Payment info endpoint
        self.test_payment_info_endpoint()
        
        # Test 5: CORS configuration
        self.test_cors_headers()
        
        # Test 6: Network timing
        self.test_network_timing()
        
        # Test 7: Contribution creation (main test)
        if journey_id:
            contribution_result = self.test_contribution_creation_flow(journey_id)
        else:
            print("\n⚠️  No journey_id available, skipping contribution creation test")
        
        # Print comprehensive summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"{i}. {failure['test']}")
                if failure['error']:
                    print(f"   → {failure['error']}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All tests passed! Stripe payment flow should work correctly.")
            return True
        else:
            print(f"\n⚠️  {len(self.failed_tests)} test(s) failed. These may be causing the 'Network error'.")
            return False

def main():
    tester = StripePaymentTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())