#!/usr/bin/env python3
"""
Comprehensive diagnostic test for the simulation pipeline
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== ElmerFEM Backend Diagnostic Test ===\n")

# Test 1: Import all modules
print("1. Testing module imports...")
try:
    from app.main import app
    print("   ✓ app.main imported")
    
    from app.jobs.launcher import JobLauncher
    print("   ✓ JobLauncher imported")
    
    from app.jobs.store import InMemoryJobStore
    print("   ✓ InMemoryJobStore imported")
    
    from app.services.educational_mesh_service import EducationalMeshService
    print("   ✓ EducationalMeshService imported")
    
    from app.services.sif_generator import SIFGenerator
    print("   ✓ SIFGenerator imported")
    
    from app.services.docker_wrapper import DockerWrapper
    print("   ✓ DockerWrapper imported")
    
    from app.models import SimulationParamsDTO
    print("   ✓ SimulationParamsDTO imported")
    
    print("\n   All imports successful!\n")
except Exception as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 2: Test direct job creation
print("2. Testing direct job creation...")

async def test_job_creation():
    try:
        # Create services
        job_store = InMemoryJobStore()
        docker_wrapper = DockerWrapper()
        
        launcher = JobLauncher(
            job_store=job_store,
            docker_wrapper=docker_wrapper
        )
        
        # Create test parameters
        params = SimulationParamsDTO(
            simulation_type="heat_transfer",
            geometry={
                "type": "rectangle",
                "parameters": {
                    "width": 1.0,
                    "height": 1.0
                }
            },
            material_id="steel",
            mesh_density=3,
            boundary_conditions=[
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
        )
        
        print("   Creating job...")
        job = await launcher.launch_job(params)
        print(f"   ✓ Job created with ID: {job.id}")
        
        # Wait a bit for job to start
        await asyncio.sleep(2)
        
        # Check job status
        job_from_store = await job_store.get(job.id)
        print(f"   Job status: {job_from_store.status}")
        print(f"   Job progress: {job_from_store.progress}")
        
        # Cancel job to clean up
        await launcher.cancel_job(job.id)
        print("   ✓ Job cancelled for cleanup")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

# Run the async test
print("\nRunning async tests...")
asyncio.run(test_job_creation())

print("\n=== Diagnostic Complete ===")
print("\nTo run the server, use one of these commands from the backend directory:")
print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
print("\nOr from the project root:")
print("  python run_backend.py") 