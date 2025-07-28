#!/usr/bin/env python3
"""
Simple test script to verify the simulation pipeline is working
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_create_simulation():
    """Test creating a simulation"""
    print("\n2. Creating a test simulation...")
    
    payload = {
        "simulation_type": "heat_transfer",
        "geometry": {
            "type": "rectangle",
            "parameters": {
                "width": 1.0,
                "height": 1.0
            }
        },
        "material_id": "steel",  # Use a material from the library
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
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/simulations/", json=payload)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Job ID: {data.get('job_id')}")
            print(f"   Status: {data.get('status')}")
            return data.get('job_id')
        else:
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"   ERROR: {e}")
        return None

def test_check_status(job_id):
    """Check simulation status"""
    print(f"\n3. Checking status for job {job_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/simulations/{job_id}/status")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Progress: {data.get('progress', 0)}%")
            print(f"   Stage: {data.get('current_stage', 'unknown')}")
            return data
        else:
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"   ERROR: {e}")
        return None

def main():
    """Run all tests"""
    print("=== Testing ElmerFEM Simulation Pipeline ===\n")
    
    # Test health
    if not test_health():
        print("\nERROR: Server is not responding. Make sure it's running on port 8000")
        sys.exit(1)
    
    # Create simulation
    job_id = test_create_simulation()
    if not job_id:
        print("\nERROR: Failed to create simulation")
        sys.exit(1)
    
    # Check status a few times
    print("\n4. Monitoring progress...")
    for i in range(5):
        time.sleep(2)
        status_data = test_check_status(job_id)
        if status_data and status_data.get('status') == 'completed':
            print("\n✓ Simulation completed successfully!")
            break
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main() 