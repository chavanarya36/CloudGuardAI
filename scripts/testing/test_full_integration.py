"""Test full integration: Web UI → API → ML Service"""
import requests
import json

API_URL = "http://127.0.0.1:8000"

def test_api_to_ml_integration():
    print("\n" + "="*60)
    print("FULL INTEGRATION TEST: API → ML Service")
    print("="*60)
    
    # Read sample file
    with open('data/samples/iac_files/vulnerable_sample.tf', 'r') as f:
        content = f.read()
    
    print("\n📁 Uploading vulnerable_sample.tf...")
    print(f"   File size: {len(content)} bytes")
    print(f"   Content preview: {content[:100]}...")
    
    # Call API scan endpoint
    payload = {
        "file_name": "vulnerable_sample.tf",
        "file_content": content
    }
    
    print("\n🔄 Calling API /scan endpoint...")
    try:
        response = requests.post(f"{API_URL}/scan", json=payload, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ SCAN COMPLETED SUCCESSFULLY!")
            print(f"\n📊 Results Summary:")
            print(f"   Scan ID: {result['scan_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Unified Risk Score: {result['unified_risk_score']:.2f}")
            print(f"   ML Score: {result['ml_score']:.2f}")
            print(f"   Rules Score: {result['rules_score']:.2f}")
            print(f"   LLM Score: {result['llm_score']:.2f}")
            print(f"   Findings Count: {len(result['findings'])}")
            print(f"   Reasoning: {result.get('reasoning')}")
            
            # Show findings
            print(f"\n🔍 Security Findings:")
            for i, finding in enumerate(result['findings'][:3], 1):
                print(f"\n   Finding #{i}:")
                print(f"      Rule: {finding['rule_id']}")
                print(f"      Severity: {finding['severity']}")
                print(f"      Description: {finding['description']}")
                print(f"      Snippet: {finding['code_snippet'][:60]}...")
            
            if len(result['findings']) > 3:
                print(f"\n   ... and {len(result['findings']) - 3} more findings")
            
            print("\n" + "="*60)
            print("✅ INTEGRATION TEST PASSED!")
            print("="*60)
            print("\nNext step: Test this through Web UI at http://localhost:3000")
            return True
        else:
            print(f"\n❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: API service not running on port 8000")
        print("   Run: cd D:\\CloudGuardAI\\api && python test_server.py")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_api_to_ml_integration()
