#!/usr/bin/env python3
"""Quick test for port 8001"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

print("Testing backend on port 8001...")

# Test health
try:
    start = time.time()
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    elapsed = time.time() - start
    
    print(f"Health endpoint: {response.status_code} (took {elapsed:.2f}s)")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Health endpoint error: {e}")

# Test materials
try:
    start = time.time()
    response = requests.get(f"{BASE_URL}/api/materials", timeout=5)
    elapsed = time.time() - start
    
    print(f"\nMaterials endpoint: {response.status_code} (took {elapsed:.2f}s)")
    if response.status_code == 200:
        data = response.json()
        print(f"Materials count: {data.get('count', 0)}")
except Exception as e:
    print(f"Materials endpoint error: {e}") 