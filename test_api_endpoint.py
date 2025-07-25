#!/usr/bin/env python3
"""
Test SIF generation through the API endpoint
Requires the backend to be running at http://localhost:8000
"""

import requests
import json
import time

def test_api_simulation():
    """Test creating a simulation through the API"""
    
    # Check if backend is running
    try:
        health = requests.get("http://localhost:8000/health", timeout=2)
        if health.status_code != 200:
            print("❌ Backend is not healthy. Status:", health.status_code)
            return False
        print("✓ Backend is running")
    except requests.exceptions.RequestException as e:
        print("❌ Cannot connect to backend at http://localhost:8000")
        print("  Make sure the backend is running with: docker-compose up")
        return False
    
    # Create a heat transfer simulation
    payload = {
        "simulation_type": "heat_transfer",
        "geometry": {
            "type": "rectangle",
            "width": 1.0,
            "height": 1.0
        },
        "material_properties": {
            "k": 50,
            "rho": 7850,
            "C": 460
        },
        "boundary_conditions": [
            {
                "surface_id": 1,
                "type": "temperature",
                "value": 300,
                "location": "left",
                "name": "Hot surface"
            },
            {
                "surface_id": 2,
                "type": "heat_flux",
                "value": 1000,
                "location": "right",
                "name": "Heat input"
            }
        ]
    }
    
    print("\n📤 Sending simulation request...")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/simulations",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"\n✓ Simulation created successfully!")
            print(f"  Job ID: {result.get('id', 'N/A')}")
            print(f"  Status: {result.get('status', 'N/A')}")
            
            # Check job status
            job_id = result.get('id')
            if job_id:
                print(f"\n📊 Checking job status...")
                time.sleep(1)
                
                status_response = requests.get(
                    f"http://localhost:8000/api/simulations/{job_id}/status",
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"  Progress: {status_data.get('progress', 0)}%")
                    print(f"  State: {status_data.get('state', 'unknown')}")
                    print(f"  Message: {status_data.get('msg', 'N/A')}")
            
            return True
        else:
            print(f"\n❌ Failed to create simulation")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error making API request: {e}")
        return False

def test_invalid_request():
    """Test that validation works through the API"""
    
    # Invalid BC type for heat transfer
    invalid_payload = {
        "simulation_type": "heat_transfer",
        "geometry": {
            "type": "rectangle",
            "width": 1.0,
            "height": 1.0
        },
        "material_properties": {
            "k": 50
        },
        "boundary_conditions": [
            {
                "surface_id": 1,
                "type": "force",  # Invalid for heat transfer!
                "value": 1000,
                "location": "left"
            }
        ]
    }
    
    print("\n📤 Testing validation with invalid boundary condition...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/simulations",
            json=invalid_payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 422 or response.status_code == 400:
            print("✓ Validation correctly rejected invalid configuration")
            print(f"  Status Code: {response.status_code}")
            print(f"  Error: {response.json().get('detail', response.text)}")
            return True
        else:
            print(f"❌ Expected validation error but got status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error making API request: {e}")
        return False

if __name__ == "__main__":
    print("API Endpoint Test for SIF Generation")
    print("=" * 60)
    
    # Run tests
    api_ok = test_api_simulation()
    
    if api_ok:
        validation_ok = test_invalid_request()
    else:
        validation_ok = False
        print("\n⚠️  Skipping validation test since API is not available")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  API Test: {'PASSED' if api_ok else 'FAILED'}")
    print(f"  Validation Test: {'PASSED' if validation_ok else 'SKIPPED' if not api_ok else 'FAILED'}")
    print(f"\nOverall: {'ALL TESTS PASSED' if api_ok and validation_ok else 'TESTS FAILED'}") 