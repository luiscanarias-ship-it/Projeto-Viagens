#!/usr/bin/env python3
"""
Frontend Stripe Integration Test

This test simulates the exact user flow described in the review request:
1. Go to homepage
2. Scroll to China journey 
3. Click "Contribuir para este Sonho"
4. Select €10
5. Select "Cartão" as payment method
6. Check if Stripe form appears or "Network error" occurs
"""

import requests
import json
import time

class FrontendStripeTest:
    def __init__(self):
        self.frontend_url = "https://journey-tracker-125.preview.emergentagent.com"
        self.api_url = f"{self.frontend_url}/api"
        self.session = requests.Session()
        
    def test_homepage_api_calls(self):
        """Test all API calls made by homepage to load China journey"""
        print("🔍 Testing Homepage API Calls...")
        
        endpoints_to_test = [
            "/seed-journeys",
            "/homepage/main-journey", 
            "/homepage/ambassador-journeys",
            "/homepage/realized-journeys",
            "/homepage/curated-dreams",
            "/dreamers-stats"
        ]
        
        all_success = True
        for endpoint in endpoints_to_test:
            try:
                if endpoint == "/seed-journeys":
                    response = self.session.post(f"{self.api_url}{endpoint}", timeout=10)
                else:
                    response = self.session.get(f"{self.api_url}{endpoint}", timeout=10)
                    
                if response.status_code == 200:
                    print(f"   ✅ {endpoint}")
                    if endpoint == "/homepage/main-journey":
                        data = response.json()
                        if data and 'journey' in data:
                            journey_name = data['journey'].get('name', 'Unknown')
                            print(f"      Main journey: {journey_name}")
                else:
                    print(f"   ❌ {endpoint} - Status: {response.status_code}")
                    all_success = False
                    
            except Exception as e:
                print(f"   ❌ {endpoint} - Error: {e}")
                all_success = False
        
        return all_success
    
    def test_journey_detail_api_calls(self):
        """Test API calls made when user clicks on China journey"""
        print("\n🔍 Testing Journey Detail API Calls...")
        
        journey_id = "journey_china001"  # China journey from tests
        
        endpoints_to_test = [
            f"/journeys/{journey_id}",
            f"/contributions/payment-info", 
            f"/journey/{journey_id}/travel-resources",
            f"/journeys/{journey_id}/progress",
            f"/journeys/{journey_id}/contributions"
        ]
        
        all_success = True
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{self.api_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ {endpoint}")
                else:
                    print(f"   ❌ {endpoint} - Status: {response.status_code}")
                    all_success = False
                    
            except Exception as e:
                print(f"   ❌ {endpoint} - Error: {e}")
                all_success = False
        
        return all_success
    
    def test_payment_modal_flow(self):
        """Test the specific payment modal flow that causes the Network error"""
        print("\n🔍 Testing Payment Modal Flow...")
        
        journey_id = "journey_china001"
        
        # Step 1: Get Stripe config (this happens when payment modal opens)
        print("   Step 1: Getting Stripe config...")
        try:
            stripe_response = self.session.get(f"{self.api_url}/stripe/config", timeout=10)
            if stripe_response.status_code == 200:
                stripe_config = stripe_response.json()
                print(f"   ✅ Stripe config loaded: {stripe_config.get('publishable_key', 'No key')[:20]}...")
            else:
                print(f"   ❌ Stripe config failed - Status: {stripe_response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Stripe config error: {e}")
            return False
        
        # Step 2: Create contribution (this happens when user selects €10 and clicks "Cartão")
        print("   Step 2: Creating Stripe contribution...")
        contribution_data = {
            "amount": 10,
            "payment_method": "stripe", 
            "journey_id": journey_id,
            "contributor_name": "Test User",
            "contributor_email": "test@test.com", 
            "public_message": "Testing Stripe flow",
            "show_name": True
        }
        
        try:
            # Use exact headers that React app would send
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': self.frontend_url,
                'Referer': f'{self.frontend_url}/journey/{journey_id}?pay=true'
            }
            
            contrib_response = self.session.post(
                f"{self.api_url}/contributions/create",
                json=contribution_data,
                headers=headers,
                timeout=15
            )
            
            print(f"   Response status: {contrib_response.status_code}")
            print(f"   Response time: {contrib_response.elapsed.total_seconds():.2f}s")
            
            if contrib_response.status_code == 200:
                result = contrib_response.json()
                client_secret = result.get('client_secret')
                if client_secret:
                    print(f"   ✅ Contribution created with client_secret: {client_secret[:20]}...")
                    return True
                else:
                    print(f"   ❌ No client_secret in response: {result}")
                    return False
            else:
                print(f"   ❌ Contribution creation failed")
                print(f"   Response: {contrib_response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT - This could be the source of 'Network error'!")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ CONNECTION ERROR - This could be the source of 'Network error': {e}")
            return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False
    
    def test_concurrent_requests(self):
        """Test if concurrent requests cause issues"""
        print("\n🔍 Testing Concurrent Request Handling...")
        
        import threading
        import concurrent.futures
        
        def make_stripe_config_request():
            try:
                response = self.session.get(f"{self.api_url}/stripe/config", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        # Make 5 concurrent requests to simulate user interactions
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_stripe_config_request) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        success_rate = sum(results) / len(results)
        print(f"   Concurrent request success rate: {success_rate:.1%}")
        
        return success_rate > 0.8  # 80% success rate threshold
    
    def test_network_connectivity_issues(self):
        """Test for potential network connectivity issues"""
        print("\n🔍 Testing Network Connectivity Issues...")
        
        # Test with different timeout values
        timeouts = [5, 10, 15, 30]
        
        for timeout in timeouts:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.api_url}/stripe/config", timeout=timeout)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time = end_time - start_time
                    print(f"   ✅ Timeout {timeout}s: Success in {response_time:.2f}s")
                    if response_time > 5:
                        print(f"      ⚠️  Slow response could cause frontend timeout")
                else:
                    print(f"   ❌ Timeout {timeout}s: Failed with status {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"   ❌ Timeout {timeout}s: Request timed out")
            except Exception as e:
                print(f"   ❌ Timeout {timeout}s: Error - {e}")
    
    def run_comprehensive_test(self):
        """Run all frontend simulation tests"""
        print("🚀 Frontend Stripe Integration Test")
        print(f"Testing: {self.frontend_url}")
        print("-" * 70)
        
        test_results = []
        
        # Test 1: Homepage API calls
        test_results.append(self.test_homepage_api_calls())
        
        # Test 2: Journey detail API calls  
        test_results.append(self.test_journey_detail_api_calls())
        
        # Test 3: Payment modal flow (critical test)
        test_results.append(self.test_payment_modal_flow())
        
        # Test 4: Concurrent requests
        test_results.append(self.test_concurrent_requests())
        
        # Test 5: Network connectivity
        self.test_network_connectivity_issues()
        
        # Summary
        print(f"\n{'='*70}")
        print("📊 FRONTEND TEST SUMMARY") 
        print("="*70)
        
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        
        print(f"Tests passed: {passed_tests}/{total_tests}")
        
        if all(test_results):
            print("🎉 All frontend tests passed!")
            print("💡 The Stripe payment flow should work correctly.")
            print("💡 If users still see 'Network error', check:")
            print("   - Browser console for JavaScript errors")
            print("   - Network tab for failed requests")
            print("   - Browser extensions blocking requests")
        else:
            print("⚠️  Some tests failed - potential issues found:")
            for i, result in enumerate(test_results, 1):
                if not result:
                    test_names = [
                        "Homepage API calls",
                        "Journey detail API calls", 
                        "Payment modal flow",
                        "Concurrent requests"
                    ]
                    print(f"   ❌ {test_names[i-1]}")
        
        return all(test_results)

def main():
    tester = FrontendStripeTest()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())