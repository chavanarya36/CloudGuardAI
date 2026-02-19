#!/usr/bin/env python3
"""
CloudGuard AI - Full System Test
Tests all components: API, ML Service, Frontend integration
"""

import subprocess
import time
import sys
import os
import requests
from pathlib import Path
import json
import signal

os.chdir(Path(__file__).parent)

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def p(text, color=Colors.RESET): 
    try:
        print(f"{color}{text}{Colors.RESET}")
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode())

def ok(text): p(f"[OK] {text}", Colors.GREEN)
def warn(text): p(f"[WARN] {text}", Colors.YELLOW)
def err(text): p(f"[ERR] {text}", Colors.RED)
def info(text): p(f"[INFO] {text}", Colors.CYAN)

processes = []

def cleanup():
    """Kill background processes"""
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            try: proc.kill()
            except: pass

def start_service(name, cwd, port, command):
    """Start a service and wait for it to be ready"""
    info(f"Starting {name} on port {port}...")
    
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).parent)
    
    proc = subprocess.Popen(
        command,
        cwd=str(cwd),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env
    )
    processes.append(proc)
    
    # Wait for service to start
    for attempt in range(30):  # 30 seconds timeout
        time.sleep(1)
        try:
            resp = requests.get(f"http://localhost:{port}/health", timeout=2)
            if resp.status_code == 200:
                ok(f"{name} started successfully on port {port}")
                return proc
        except:
            pass
        
        # Check if process died
        if proc.poll() is not None:
            output = proc.stdout.read().decode() if proc.stdout else ""
            err(f"{name} failed to start")
            if output:
                print(f"Error output:\n{output[:500]}")
            return None
    
    err(f"{name} timed out")
    return None

def test_api():
    """Test API endpoints"""
    p("\n" + "="*60, Colors.CYAN)
    p("Testing API Endpoints", Colors.CYAN)
    p("="*60, Colors.CYAN)
    
    tests = [
        ("Health Check", "GET", "http://localhost:8000/health"),
        ("Scanners Status", "GET", "http://localhost:8000/scanners/status"),
        ("API Root", "GET", "http://localhost:8000/"),
    ]
    
    passed = 0
    for name, method, url in tests:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                ok(f"{name}: {resp.status_code}")
                passed += 1
            else:
                err(f"{name}: {resp.status_code}")
        except Exception as e:
            err(f"{name}: {str(e)}")
    
    return passed, len(tests)

def test_ml_service():
    """Test ML Service endpoints"""
    p("\n" + "="*60, Colors.CYAN)
    p("Testing ML Service", Colors.CYAN)
    p("="*60, Colors.CYAN)
    
    tests = [
        ("Health Check", "http://localhost:8001/health"),
        ("Status", "http://localhost:8001/status"),
    ]
    
    passed = 0
    for name, url in tests:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                ok(f"{name}: {resp.status_code}")
                passed += 1
            else:
                warn(f"{name}: {resp.status_code} (ML service may have issues)")
        except Exception as e:
            err(f"{name}: {str(e)}")
    
    return passed, len(tests)

def test_scan_workflow():
    """Test end-to-end scan workflow"""
    p("\n" + "="*60, Colors.CYAN)
    p("Testing Scan Workflow", Colors.CYAN)
    p("="*60, Colors.CYAN)
    
    # Find a test file
    test_file = Path("data/samples/iac_files/vulnerable_sample.tf")
    if not test_file.exists():
        warn(f"Test file not found: {test_file}")
        return 0, 1
    
    try:
        info(f"Scanning test file: {test_file}")
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'text/plain')}
            resp = requests.post(
                "http://localhost:8000/scan",
                files=files,
                timeout=60
            )
        
        if resp.status_code == 200:
            result = resp.json()
            ok(f"Scan completed!")
            info(f"  Total findings: {result.get('total_findings', 0)}")
            info(f"  Risk score: {result.get('risk_score', 'N/A')}")
            info(f"  Scanners used: {', '.join(result.get('scanners_used', []))}")
            return 1, 1
        else:
            err(f"Scan failed: {resp.status_code}")
            err(f"Response: {resp.text[:200]}")
            return 0, 1
    except Exception as e:
        err(f"Scan test failed: {str(e)}")
        return 0, 1

def test_frontend():
    """Test frontend accessibility"""
    p("\n" + "="*60, Colors.CYAN)
    p("Testing Frontend", Colors.CYAN)
    p("="*60, Colors.CYAN)
    
    try:
        resp = requests.get("http://localhost:3000", timeout=5)
        if resp.status_code == 200:
            ok("Frontend accessible at http://localhost:3000")
            info(f"Page size: {len(resp.content)} bytes")
            return 1, 1
        else:
            err(f"Frontend returned {resp.status_code}")
            return 0, 1
    except requests.exceptions.ConnectionError:
        warn("Frontend not running (optional - UI not started)")
        return 0, 1
    except Exception as e:
        err(f"Frontend check failed: {str(e)}")
        return 0, 1

def main():
    p("\n" + "="*60, Colors.CYAN + Colors.BOLD)
    p("CloudGuard AI - Full System Test", Colors.CYAN + Colors.BOLD)
    p("="*60, Colors.CYAN + Colors.BOLD)
    
    try:
        # Start services
        root = Path(__file__).parent
        
        api_proc = start_service(
            "API Service", 
            root / "api",
            8000,
            "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
        )
        
        ml_proc = start_service(
            "ML Service",
            root / "ml", 
            8001,
            "python -m uvicorn ml_service.main:app --host 0.0.0.0 --port 8001"
        )
        
        all_tests = []
        
        # Run tests
        if api_proc:
            passed, total = test_api()
            all_tests.append(("API Endpoints", passed, total))
            
            passed, total = test_scan_workflow()
            all_tests.append(("Scan Workflow", passed, total))
        else:
            all_tests.append(("API Service", 0, 1))
        
        if ml_proc:
            passed, total = test_ml_service()
            all_tests.append(("ML Service", passed, total))
        else:
            all_tests.append(("ML Service", 0, 1))
        
        # Test frontend (if running externally)
        passed, total = test_frontend()
        all_tests.append(("Frontend", passed, total))
        
        # Summary
        p("\n" + "="*60, Colors.CYAN + Colors.BOLD)
        p("Test Summary", Colors.CYAN + Colors.BOLD)
        p("="*60, Colors.CYAN + Colors.BOLD)
        
        total_passed = 0
        total_tests = 0
        
        for name, passed, total in all_tests:
            total_passed += passed
            total_tests += total
            status = f"{passed}/{total}"
            if passed == total:
                ok(f"{name}: {status}")
            elif passed > 0:
                warn(f"{name}: {status}")
            else:
                err(f"{name}: {status}")
        
        print()
        pct = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        if pct >= 70:
            ok(f"Overall: {total_passed}/{total_tests} ({pct:.0f}%) - READY TO PUSH")
            return 0
        elif pct >= 50:
            warn(f"Overall: {total_passed}/{total_tests} ({pct:.0f}%) - NEEDS ATTENTION")
            return 1
        else:
            err(f"Overall: {total_passed}/{total_tests} ({pct:.0f}%) - NOT READY")
            return 2
            
    finally:
        info("\nCleaning up services...")
        cleanup()
        ok("Done")

if __name__ == "__main__":
    sys.exit(main())
