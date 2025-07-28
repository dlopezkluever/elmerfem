#!/usr/bin/env python3
"""
Detailed test for simulation creation showing exact error
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=== Detailed Simulation Test ===\n")

# 1. Test health endpoint
print("1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ERROR: {e}")
    print("\nERROR: Server is not responding. Make sure it's running on port 8000")
    exit(1)

# 2. Test materials endpoint to verify API is working
print("\n2. Testing materials endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/materials", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Materials count: {data.get('count', 0)}")
        if data.get('materials'):
            print(f"   Available materials: {[m['name'] for m in data['materials']]}")
except Exception as e:
    print(f"   ERROR: {e}")

# 3. Create a simulation with detailed error reporting
print("\n3. Creating a test simulation...")
payload = {
    "simulation_type": "heat_transfer",
    "geometry": {
        "type": "rectangle",
        "parameters": {
            "width": 1.0,
            "height": 1.0
        }
    },
    "material_id": "steel",
    "mesh_density": 3,
    "boundary_conditions": [
        {
            "location": "left",
            "type": "temperature",
            "value": 100.0
        },
        {
            "location": "right",
            "type": "temperature",
            "value": 0.0
        }
    ]
}

print(f"   Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/simulations/", 
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n   Status Code: {response.status_code}")
    print(f"   Status Text: {response.reason}")
    
    # Show response headers
    print("\n   Response Headers:")
    for key, value in response.headers.items():
        print(f"     {key}: {value}")
    
    # Show response body
    print("\n   Response Body:")
    try:
        # Try to parse as JSON
        response_json = response.json()
        print(f"     {json.dumps(response_json, indent=2)}")
    except:
        # If not JSON, show raw text
        print(f"     {response.text}")
    
    # If error, try to get more details
    if response.status_code >= 400:
        print("\n   ERROR DETAILS:")
        if response.status_code == 422:
            print("   Validation error - check the payload format")
        elif response.status_code == 500:
            print("   Internal server error - check backend logs for details")
            print("   Common causes:")
            print("   - Missing dependencies")
            print("   - File permission issues")
            print("   - Invalid configuration")
            
except Exception as e:
    print(f"   REQUEST ERROR: {e}")
    print(f"   Type: {type(e).__name__}")

print("\n=== Test Complete ===") 