#!/usr/bin/env python3
"""
Test script to verify backend health and materials endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("1. Testing health endpoint...")
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        elapsed = time.time() - start
        
        print(f"   Status: {response.status_code}")
        print(f"   Response time: {elapsed:.2f}s")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ERROR: {e}")
        return False

def test_materials():
    """Test the materials endpoint"""
    print("\n2. Testing materials endpoint...")
    try:
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/materials", timeout=5)
        elapsed = time.time() - start
        
        print(f"   Status: {response.status_code}")
        print(f"   Response time: {elapsed:.2f}s")
        if response.status_code == 200:
            data = response.json()
            print(f"   Materials count: {data.get('count', 0)}")
            if data.get('materials'):
                print(f"   First material: {data['materials'][0]['name']}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ERROR: {e}")
        return False

def test_cors():
    """Test CORS headers"""
    print("\n3. Testing CORS configuration...")
    try:
        # Simulate browser request with Origin header
        headers = {
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'GET'
        }
        response = requests.options(f"{BASE_URL}/api/materials", headers=headers, timeout=5)
        
        print(f"   Status: {response.status_code}")
        print("   CORS Headers:")
        for header, value in response.headers.items():
            if header.lower().startswith('access-control'):
                print(f"     {header}: {value}")
        
        return 'access-control-allow-origin' in response.headers
    except requests.exceptions.RequestException as e:
        print(f"   ERROR: {e}")
        return False

if __name__ == "__main__":
    print("ElmerFEM Backend Health Check")
    print("=============================")
    print(f"Testing backend at: {BASE_URL}")
    print()
    
    # Check if backend is running
    health_ok = test_health()
    materials_ok = test_materials()
    cors_ok = test_cors()
    
    print("\n\nSummary:")
    print("--------")
    print(f"Health endpoint: {'✓ OK' if health_ok else '✗ FAILED'}")
    print(f"Materials endpoint: {'✓ OK' if materials_ok else '✗ FAILED'}")
    print(f"CORS configuration: {'✓ OK' if cors_ok else '✗ FAILED'}")
    
    if not all([health_ok, materials_ok, cors_ok]):
        print("\n⚠️  Some tests failed. Please check:")
        print("   1. Is the backend running? (cd backend && python -m uvicorn app.main:app --reload)")
        print("   2. Are there any startup errors in the backend logs?")
        print("   3. Is Redis running if configured?") 