#!/usr/bin/env python3
"""
Script to run the backend server from the correct directory
"""

import os
import sys
import subprocess

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, "backend")

# Change to backend directory
os.chdir(backend_dir)

print(f"Running server from: {os.getcwd()}")

# Run uvicorn
cmd = [
    sys.executable,
    "-m",
    "uvicorn",
    "app.main:app",
    "--host", "0.0.0.0",
    "--port", "8000",
    "--reload"
]

print(f"Running command: {' '.join(cmd)}")

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\nServer stopped.") 