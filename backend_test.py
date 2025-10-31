import requests
import sys
import json
from datetime import datetime
import time

class ScamShieldAPITester:
    def __init__(self, base_url="https://scamshield-27.preview.cloud.example.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.scan_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, expected_content=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                try:
                    response_data = response.json()
                    if expected_content:
                        for key, expected_value in expected_content.items():
                            if key not in response_data:
                                print(f"⚠️  Warning: Expected key '{key}' not found in response")
                            elif expected_value is not None and response_data[key] != expected_value:
                                print(f"⚠️  Warning: Expected {key}={expected_value}, got {response_data[key]}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")

            return success, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        if success and response:
            print(f"   ML Model Loaded: {response.get('ml_model_loaded', 'Unknown')}")
        return success

    def test_scan_safe_content(self):
        """Test scanning safe content"""
        safe_tests = [
            {
                "content": "Hi, this is a reminder about your appointment tomorrow at 2 PM.",
                "expected_label": "🟢 Safe",
                "max_score": 30
            },
            {
                "content": "Your order has been shipped and will arrive in 2-3 business days.",
                "expected_label": "🟢 Safe", 
                "max_score": 30
            },
            {
                "content": "555-1234",
                "expected_label": "🟢 Safe",
                "max_score": 30
            },
            {
                "content": "https://google.com",
                "expected_label": "🟢 Safe",
                "max_score": 30
            }
        ]
        
        all_passed = True
        for i, test_case in enumerate(safe_tests):
            success, response = self.run_test(
                f"Safe Content Test {i+1}",
                "POST",
                "scan",
                200,
                data={"content": test_case["content"]}
            )
            
            if success and response:
                self.scan_results.append(response)
                score = response.get('risk_score', 0)
                label = response.get('label', '')
                
                print(f"   Content: {test_case['content']}")
                print(f"   Score: {score}/100")
                print(f"   Label: {label}")
                print(f"   Triggers: {response.get('triggers', [])}")
                
                if score > test_case['max_score']:
                    print(f"⚠️  Warning: Score {score} higher than expected max {test_case['max_score']}")
                    all_passed = False
                    
                if test_case['expected_label'] not in label:
                    print(f"⚠️  Warning: Expected label containing '{test_case['expected_label']}', got '{label}'")
                    all_passed = False
            else:
                all_passed = False
                
        return all_passed

    def test_scan_suspicious_content(self):
        """Test scanning suspicious content"""
        suspicious_tests = [
            {
                "content": "Your account expires soon. Please verify within 24 hours.",
                "expected_label": "🟡 Suspicious",
                "min_score": 31,
                "max_score": 70
            },
            {
                "content": "Click here to claim your reward: bit.ly/reward123",
                "expected_label": "🟡 Suspicious",
                "min_score": 31,
                "max_score": 70
            }
        ]
        
        all_passed = True
        for i, test_case in enumerate(suspicious_tests):
            success, response = self.run_test(
                f"Suspicious Content Test {i+1}",
                "POST",
                "scan",
                200,
                data={"content": test_case["content"]}
            )
            
            if success and response:
                self.scan_results.append(response)
                score = response.get('risk_score', 0)
                label = response.get('label', '')
                
                print(f"   Content: {test_case['content']}")
                print(f"   Score: {score}/100")
                print(f"   Label: {label}")
                print(f"   Triggers: {response.get('triggers', [])}")
                
                if score < test_case['min_score'] or score > test_case['max_score']:
                    print(f"⚠️  Warning: Score {score} outside expected range {test_case['min_score']}-{test_case['max_score']}")
                    all_passed = False
                    
                if test_case['expected_label'] not in label:
                    print(f"⚠️  Warning: Expected label containing '{test_case['expected_label']}', got '{label}'")
                    all_passed = False
            else:
                all_passed = False
                
        return all_passed

    def test_scan_dangerous_content(self):
        """Test scanning dangerous content"""
        dangerous_tests = [
            {
                "content": "URGENT: Your account will be suspended in 24 hours. Click here to verify immediately!",
                "expected_label": "🔴 Dangerous",
                "min_score": 71
            },
            {
                "content": "Congratulations! You've won $1,000,000 in our lottery. Claim your prize now!",
                "expected_label": "🔴 Dangerous",
                "min_score": 71
            },
            {
                "content": "IRS Notice: You owe back taxes. Pay immediately to avoid arrest.",
                "expected_label": "🔴 Dangerous",
                "min_score": 71
            }
        ]
        
        all_passed = True
        for i, test_case in enumerate(dangerous_tests):
            success, response = self.run_test(
                f"Dangerous Content Test {i+1}",
                "POST",
                "scan",
                200,
                data={"content": test_case["content"]}
            )
            
            if success and response:
                self.scan_results.append(response)
                score = response.get('risk_score', 0)
                label = response.get('label', '')
                
                print(f"   Content: {test_case['content']}")
                print(f"   Score: {score}/100")
                print(f"   Label: {label}")
                print(f"   Triggers: {response.get('triggers', [])}")
                
                if score < test_case['min_score']:
                    print(f"⚠️  Warning: Score {score} lower than expected minimum {test_case['min_score']}")
                    all_passed = False
                    
                if test_case['expected_label'] not in label:
                    print(f"⚠️  Warning: Expected label containing '{test_case['expected_label']}', got '{label}'")
                    all_passed = False
            else:
                all_passed = False
                
        return all_passed

    def test_scan_validation(self):
        """Test scan input validation"""
        success, response = self.run_test(
            "Empty Content Validation",
            "POST",
            "scan",
            400,
            data={"content": ""}
        )
        return success

    def test_history_endpoint(self):
        """Test history endpoint"""
        success, response = self.run_test(
            "Get Scan History",
            "GET",
            "history",
            200
        )
        
        if success and response:
            print(f"   History items returned: {len(response)}")
            if len(response) > 0:
                print(f"   Sample item keys: {list(response[0].keys())}")
                required_fields = ['id', 'content', 'scan_type', 'risk_score', 'label', 'guidance', 'triggers', 'timestamp']
                for field in required_fields:
                    if field not in response[0]:
                        print(f"⚠️  Warning: Required field '{field}' missing from history item")
                        return False
        
        return success

    def test_stats_endpoint(self):
        """Test stats endpoint"""
        success, response = self.run_test(
            "Get Statistics",
            "GET",
            "stats",
            200
        )
        
        if success and response:
            print(f"   Total scans: {response.get('total_scans', 0)}")
            print(f"   Safe scans: {response.get('safe_scans', 0)}")
            print(f"   Suspicious scans: {response.get('suspicious_scans', 0)}")
            print(f"   Dangerous scans: {response.get('dangerous_scans', 0)}")
            
            required_fields = ['total_scans', 'safe_scans', 'suspicious_scans', 'dangerous_scans']
            for field in required_fields:
                if field not in response:
                    print(f"⚠️  Warning: Required field '{field}' missing from stats")
                    return False
        
        return success

    def test_detection_layers(self):
        """Test that all detection layers are working"""
        print(f"\n🔍 Analyzing Detection Layer Triggers...")
        
        rule_triggers = []
        blacklist_triggers = []
        ai_triggers = []
        
        for result in self.scan_results:
            for trigger in result.get('triggers', []):
                if trigger.startswith('Rule:'):
                    rule_triggers.append(trigger)
                elif trigger.startswith('Blacklist:'):
                    blacklist_triggers.append(trigger)
                elif trigger.startswith('AI:'):
                    ai_triggers.append(trigger)
        
        print(f"   Rule layer triggers found: {len(set(rule_triggers))}")
        print(f"   Blacklist layer triggers found: {len(set(blacklist_triggers))}")
        print(f"   AI layer triggers found: {len(set(ai_triggers))}")
        
        if len(set(rule_triggers)) > 0:
            print("✅ Rule layer is working")
        else:
            print("⚠️  Rule layer may not be working properly")
            
        if len(set(ai_triggers)) > 0:
            print("✅ AI layer is working")
        else:
            print("⚠️  AI layer may not be working properly")
            
        print("ℹ️  Blacklist layer requires specific blacklisted content to trigger")
        
        return True

def main():
    print("🛡️  ScamShield API Testing Suite")
    print("=" * 50)
    
    tester = ScamShieldAPITester()
    
    tests = [
        ("Health Check", tester.test_health_check),
        ("Safe Content Scanning", tester.test_scan_safe_content),
        ("Suspicious Content Scanning", tester.test_scan_suspicious_content),
        ("Dangerous Content Scanning", tester.test_scan_dangerous_content),
        ("Input Validation", tester.test_scan_validation),
        ("History Endpoint", tester.test_history_endpoint),
        ("Stats Endpoint", tester.test_stats_endpoint),
        ("Detection Layers", tester.test_detection_layers),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            tester.tests_run += 1
    
    print(f"\n{'='*50}")
    print(f"📊 Final Results:")
    print(f"   Tests Run: {tester.tests_run}")
    print(f"   Tests Passed: {tester.tests_passed}")
    print(f"   Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

