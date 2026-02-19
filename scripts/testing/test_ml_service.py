"""Test ML service endpoints"""
import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_health():
    print("\n=== Testing /health ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_predict():
    print("\n=== Testing /predict ===")
    
    # Read sample file
    with open('data/samples/iac_files/vulnerable_sample.tf', 'r') as f:
        content = f.read()
    
    payload = {
        "file_path": "test.tf",
        "file_content": content
    }
    
    try:
        response = requests.post(f"{BASE_URL}/predict", json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_rules_scan():
    print("\n=== Testing /rules-scan ===")
    
    with open('data/samples/iac_files/vulnerable_sample.tf', 'r') as f:
        content = f.read()
    
    payload = {
        "file_path": "test.tf",
        "file_content": content
    }
    
    try:
        response = requests.post(f"{BASE_URL}/rules-scan", json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Found {len(result.get('findings', []))} findings")
        if result.get('findings'):
            print(f"First finding: {result['findings'][0]}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_aggregate():
    print("\n=== Testing /aggregate ===")
    
    with open('data/samples/iac_files/vulnerable_sample.tf', 'r') as f:
        content = f.read()
    
    payload = {
        "file_path": "test.tf",
        "file_content": content,
        "ml_score": 0.75,
        "rules_findings": [
            {"severity": "HIGH", "description": "Public S3 bucket"},
            {"severity": "MEDIUM", "description": "No versioning"}
        ],
        "llm_insights": [
            {"confidence": 0.8, "explanation": "Critical security issue"}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/aggregate", json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing ML Service Endpoints")
    print("=" * 50)
    
    results = {
        "health": test_health(),
        "predict": test_predict(),
        "rules_scan": test_rules_scan(),
        "aggregate": test_aggregate()
    }
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for endpoint, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {endpoint}: {status}")
