#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class TipSystemAPITester:
    def __init__(self, base_url="https://comeback-point.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def admin_login(self):
        """Login as admin to get token"""
        print("\n🔐 Admin Login...")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@4luis.com", "password": "Admin1"}
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"✅ Admin token obtained")
            return True
        print(f"❌ Admin login failed")
        return False

    def get_auth_headers(self):
        """Get authorization headers"""
        if self.admin_token:
            return {'Authorization': f'Bearer {self.admin_token}'}
        return {}

    def test_tip_configuration_endpoint(self):
        """Test GET /api/contributions/config for tip options"""
        success, response = self.run_test(
            "Tip Configuration Endpoint",
            "GET",
            "contributions/config",
            200
        )
        
        if success:
            # Verify tip_options structure
            if 'tip_options' in response:
                tip_options = response['tip_options']
                print(f"   Tip options found: {len(tip_options)} options")
                
                # Check for required tip values
                tip_values = [opt.get('value') for opt in tip_options]
                expected_values = [2, 5, 10, 0]
                
                if all(val in tip_values for val in expected_values):
                    print(f"   ✅ All expected tip values present: {tip_values}")
                else:
                    print(f"   ❌ Missing tip values. Expected: {expected_values}, Got: {tip_values}")
                
                # Check default tip
                default_tip = response.get('default_tip')
                if default_tip == 2:
                    print(f"   ✅ Default tip is 2€")
                else:
                    print(f"   ❌ Default tip should be 2€, got: {default_tip}")
                
                # Check for default option in tip_options
                default_options = [opt for opt in tip_options if opt.get('default', False)]
                if len(default_options) == 1 and default_options[0].get('value') == 2:
                    print(f"   ✅ Default option correctly marked in tip_options")
                else:
                    print(f"   ❌ Default option not correctly marked")
                    
            else:
                print(f"   ❌ tip_options not found in response")
                
        return success

    def test_platform_revenue_endpoint(self):
        """Test GET /api/admin/platform-revenue"""
        if not self.admin_token:
            print("❌ Admin token required for platform revenue test")
            return False
            
        success, response = self.run_test(
            "Platform Revenue Endpoint",
            "GET",
            "admin/platform-revenue",
            200,
            headers=self.get_auth_headers()
        )
        
        if success:
            # Check for expected revenue structure
            if 'summary' in response:
                summary = response['summary']
                expected_fields = ['total_platform_revenue', 'total_tips', 'tip_contributions', 'tip_conversion_rate']
                
                missing_fields = [field for field in expected_fields if field not in summary]
                if not missing_fields:
                    print(f"   ✅ All expected summary fields present")
                    print(f"   Total platform revenue: €{summary.get('total_platform_revenue', 0)}")
                    print(f"   Total tips: €{summary.get('total_tips', 0)}")
                    print(f"   Tip contributions: {summary.get('tip_contributions', 0)}")
                    print(f"   Tip conversion rate: {summary.get('tip_conversion_rate', 0)}%")
                else:
                    print(f"   ❌ Missing summary fields: {missing_fields}")
            else:
                print(f"   ❌ summary not found in response")
                
        return success

    def test_contribution_creation_with_tip(self):
        """Test creating a contribution with tip amount"""
        # First get an active journey
        success, journeys_response = self.run_test(
            "Get Active Journeys",
            "GET",
            "journeys",
            200
        )
        
        if not success or not journeys_response:
            print("❌ Cannot get journeys for contribution test")
            return False
            
        active_journeys = [j for j in journeys_response if j.get('is_active', False)]
        if not active_journeys:
            print("❌ No active journeys found for contribution test")
            return False
            
        journey_id = active_journeys[0]['journey_id']
        print(f"   Using journey: {journey_id}")
        
        # Test contribution with tip
        contribution_data = {
            "support_amount": 20,
            "tip_amount": 5,
            "payment_method": "mbway",
            "journey_id": journey_id,
            "contributor_name": "Test User",
            "contributor_email": "test@example.com"
        }
        
        success, response = self.run_test(
            "Create Contribution with Tip",
            "POST",
            "contributions/create",
            200,
            data=contribution_data
        )
        
        if success:
            # Verify response contains tip information
            if 'tip_amount' in response and response['tip_amount'] == 5:
                print(f"   ✅ Tip amount correctly set: €{response['tip_amount']}")
            else:
                print(f"   ❌ Tip amount not correctly set")
                
            if 'support_amount' in response and response['support_amount'] == 20:
                print(f"   ✅ Support amount correctly set: €{response['support_amount']}")
            else:
                print(f"   ❌ Support amount not correctly set")
                
            total_amount = response.get('amount', 0)
            expected_total = 25  # 20 + 5
            if total_amount == expected_total:
                print(f"   ✅ Total amount correctly calculated: €{total_amount}")
            else:
                print(f"   ❌ Total amount incorrect. Expected: €{expected_total}, Got: €{total_amount}")
                
        return success

    def test_tip_validation(self):
        """Test tip amount validation"""
        # Get an active journey
        success, journeys_response = self.run_test(
            "Get Journeys for Validation Test",
            "GET",
            "journeys",
            200
        )
        
        if not success or not journeys_response:
            return False
            
        active_journeys = [j for j in journeys_response if j.get('is_active', False)]
        if not active_journeys:
            return False
            
        journey_id = active_journeys[0]['journey_id']
        
        # Test invalid tip amount
        invalid_contribution_data = {
            "support_amount": 20,
            "tip_amount": 3,  # Invalid tip amount (not in [0, 2, 5, 10])
            "payment_method": "mbway",
            "journey_id": journey_id,
            "contributor_name": "Test User",
            "contributor_email": "test@example.com"
        }
        
        success, response = self.run_test(
            "Invalid Tip Amount Validation",
            "POST",
            "contributions/create",
            400,  # Should return 400 for invalid tip
            data=invalid_contribution_data
        )
        
        if success:
            print(f"   ✅ Invalid tip amount correctly rejected")
        
        return success

def main():
    print("🚀 Starting Tip System API Tests")
    print("=" * 50)
    
    tester = TipSystemAPITester()
    
    # Login as admin first
    if not tester.admin_login():
        print("❌ Cannot proceed without admin access")
        return 1
    
    # Run tip system tests
    tests = [
        tester.test_tip_configuration_endpoint,
        tester.test_platform_revenue_endpoint,
        tester.test_contribution_creation_with_tip,
        tester.test_tip_validation
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Tests completed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())