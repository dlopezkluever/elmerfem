#!/usr/bin/env python3
"""
Test script that starts the server and runs tests
"""

import asyncio
import subprocess
import time
import requests
import json
import sys

def start_server():
    """Start the server and return the process"""
    print("Starting server...")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Check if server started successfully
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("Server started successfully!")
            return process
    except:
        pass
    
    # If we get here, server didn't start
    print("Server failed to start. Error output:")
    stdout, stderr = process.communicate(timeout=1)
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
    return None

def test_simulation():
    """Test creating a simulation"""
    print("\nTesting simulation creation...")
    
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
    
    try:
        response = requests.post("http://localhost:8000/api/v1/simulations/", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print("\nChecking server logs...")
            
    except Exception as e:
        print(f"Error: {e}")

def read_server_output(process):
    """Read server output to see errors"""
    print("\nServer output:")
    for i in range(10):  # Read up to 10 lines
        line = process.stderr.readline()
        if line:
            print(f"  {line.strip()}")
        line = process.stdout.readline()
        if line:
            print(f"  {line.strip()}")

if __name__ == "__main__":
    # Start server
    server_process = start_server()
    
    if server_process:
        try:
            # Test simulation
            test_simulation()
            
            # Read server output to see any errors
            read_server_output(server_process)
            
        finally:
            # Stop server
            print("\nStopping server...")
            server_process.terminate()
            server_process.wait(timeout=5)
    else:
        print("Failed to start server!") 