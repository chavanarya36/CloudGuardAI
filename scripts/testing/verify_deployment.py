#!/usr/bin/env python3
"""
CloudGuard AI - Deployment Verification Script
Tests all components before GitHub push
"""

import subprocess
import time
import sys
import requests
import json
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.RESET}")

def check_service(name, url, timeout=2):
    """Check if a service is running and responsive"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print_success(f"{name} is running at {url}")
            return True, response.json() if 'json' in response.headers.get('content-type', '') else None
        else:
            print_error(f"{name} returned status {response.status_code}")
            return False, None
    except requests.exceptions.ConnectionError:
        print_error(f"{name} is not running at {url}")
        return False, None
    except Exception as e:
        print_error(f"{name} check failed: {str(e)}")
        return False, None

def start_service(name, cmd, cwd):
    """Start a service in background"""
    try:
        print_info(f"Starting {name}...")
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)  # Give it time to start
        
        if process.poll() is None:
            print_success(f"{name} started (PID: {process.pid})")
            return process
        else:
            stderr = process.stderr.read().decode()
            print_error(f"{name} failed to start: {stderr}")
            return None
    except Exception as e:
        print_error(f"Failed to start {name}: {str(e)}")
        return None

def test_api_endpoints():
    """Test critical API endpoints"""
    print_header("Testing API Endpoints")
    
    endpoints = {
        "Health Check": "http://localhost:8000/health",
        "Scanner Status": "http://localhost:8000/scanners/status",
        "API Docs": "http://localhost:8000/docs"
    }
    
    passed = 0
    for name, url in endpoints.items():
        success, data = check_service(name, url)
        if success:
            passed += 1
            if data:
                print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
    
    return passed, len(endpoints)

def test_ml_service():
    """Test ML service endpoints"""
    print_header("Testing ML Service")
    
    endpoints = {
        "ML Health": "http://localhost:8001/health",
        "Model Status": "http://localhost:8001/status"
    }
    
    passed = 0
    for name, url in endpoints.items():
        success, data = check_service(name, url)
        if success:
            passed += 1
            if data:
                print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
    
    return passed, len(endpoints)

def test_frontend():
    """Test frontend accessibility"""
    print_header("Testing Frontend")
    
    try:
        response = requests.get("http://localhost:3000", timeout=2)
        if response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
            print_success("Frontend is accessible at http://localhost:3000")
            print_info(f"Page size: {len(response.content)} bytes")
            return 1, 1
        else:
            print_error(f"Frontend returned unexpected response: {response.status_code}")
            return 0, 1
    except requests.exceptions.ConnectionError:
        print_error("Frontend is not running at http://localhost:3000")
        return 0, 1
    except Exception as e:
        print_error(f"Frontend check failed: {str(e)}")
        return 0, 1

def test_file_scan():
    """Test end-to-end scan workflow"""
    print_header("Testing End-to-End Scan Workflow")
    
    # Create a test file
    test_file = Path(__file__).parent / "data" / "samples" / "iac_files" / "vulnerable_sample.tf"
    
    if not test_file.exists():
        print_warning(f"Test file not found: {test_file}")
        return 0, 1
    
    try:
        # Test scan endpoint
        print_info("Uploading test file for scanning...")
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'text/plain')}
            response = requests.post(
                "http://localhost:8000/scan",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print_success("Scan completed successfully")
            print_info(f"Total findings: {result.get('total_findings', 0)}")
            print_info(f"Risk score: {result.get('risk_score', 'N/A')}")
            print_info(f"Scanners used: {', '.join(result.get('scanners_used', []))}")
            return 1, 1
        else:
            print_error(f"Scan failed with status {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return 0, 1
    except Exception as e:
        print_error(f"Scan test failed: {str(e)}")
        return 0, 1

def check_critical_files():
    """Verify critical files exist"""
    print_header("Checking Critical Files")
    
    critical_files = [
        "api/app/main.py",
        "ml/ml_service/main.py",
        "web/src/App.jsx",
        "api/.env",
        "ml/.env",
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/presentations/INTERVIEW_GUIDE.md"
    ]
    
    passed = 0
    for file_path in critical_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print_success(f"{file_path}")
            passed += 1
        else:
            print_error(f"{file_path} - MISSING")
    
    return passed, len(critical_files)

def main():
    print_header("CloudGuard AI - Pre-Deployment Verification")
    
    all_tests = []
    
    # Check critical files first
    passed, total = check_critical_files()
    all_tests.append(("Critical Files", passed, total))
    
    # Check if services are already running
    print_header("Checking Service Status")
    
    api_running, _ = check_service("API Service", "http://localhost:8000/health")
    ml_running, _ = check_service("ML Service", "http://localhost:8001/health")
    web_running, _ = check_service("Web Frontend", "http://localhost:3000")
    
    if not api_running:
        print_warning("API service not detected. Please start it manually with:")
        print_info("  cd api && python -m uvicorn app.main:app --port 8000 --reload")
    
    if not ml_running:
        print_warning("ML service not detected. Please start it manually with:")
        print_info("  cd ml && python -m uvicorn ml_service.main:app --port 8001 --reload")
    
    if not web_running:
        print_warning("Web frontend not detected. Please start it manually with:")
        print_info("  cd web && npm run dev")
    
    # Test endpoints if services are running
    if api_running:
        passed, total = test_api_endpoints()
        all_tests.append(("API Endpoints", passed, total))
        
        # Try integration test
        if api_running:
            passed, total = test_file_scan()
            all_tests.append(("End-to-End Scan", passed, total))
    
    if ml_running:
        passed, total = test_ml_service()
        all_tests.append(("ML Service", passed, total))
    
    if web_running:
        passed, total = test_frontend()
        all_tests.append(("Frontend", passed, total))
    
    # Print summary
    print_header("Verification Summary")
    
    total_passed = 0
    total_tests = 0
    
    for name, passed, total in all_tests:
        total_passed += passed
        total_tests += total
        status = f"{passed}/{total}"
        if passed == total:
            print_success(f"{name}: {status}")
        elif passed > 0:
            print_warning(f"{name}: {status}")
        else:
            print_error(f"{name}: {status}")
    
    print()
    percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    if percentage >= 80:
        print_success(f"Overall: {total_passed}/{total_tests} ({percentage:.1f}%) - READY TO DEPLOY")
        return 0
    elif percentage >= 50:
        print_warning(f"Overall: {total_passed}/{total_tests} ({percentage:.1f}%) - NEEDS ATTENTION")
        return 1
    else:
        print_error(f"Overall: {total_passed}/{total_tests} ({percentage:.1f}%) - NOT READY")
        return 2

if __name__ == "__main__":
    sys.exit(main())
