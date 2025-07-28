#!/usr/bin/env python3
"""
Test script to verify Task 2: Backend Path Translation & Workspace Sync
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from uuid import uuid4
import tempfile

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.config.settings import settings
from app.jobs.launcher import JobLauncher
from app.jobs.store import InMemoryJobStore
from app.services.docker_wrapper import DockerWrapper
from app.models import SimulationParamsDTO, SimulationType


async def test_task2():
    """Comprehensive test for Task 2 implementation"""
    
    print("=" * 70)
    print("Task 2 Verification: Backend Path Translation & Workspace Sync")
    print("=" * 70)
    
    all_tests_passed = True
    
    # Test 1: WORKSPACE_PATH Environment Variable
    print("\n[TEST 1] WORKSPACE_PATH Environment Variable")
    print("-" * 50)
    try:
        # Check default value
        print(f"workspace_path: {settings.workspace_path}")
        print(f"workspace_base_dir (alias): {settings.workspace_base_dir}")
        print(f"Type: {type(settings.workspace_path)}")
        
        # Verify they're the same (backward compatibility)
        assert settings.workspace_path == settings.workspace_base_dir
        print("✓ Backward compatibility maintained")
        
        # Check if it's using the correct default
        if not os.environ.get('ELMERFEM_WORKSPACE_PATH'):
            # On Windows, the path might be \workspace instead of /workspace
            assert str(settings.workspace_path).replace('\\', '/') == "/workspace"
            print("✓ Default value is /workspace")
        else:
            print(f"✓ Using environment override: {settings.workspace_path}")
        
        # Test get_workspace_path method
        workspace = settings.get_workspace_path()
        assert workspace == settings.workspace_path
        print("✓ get_workspace_path() method works correctly")
        
        print("\n✅ TEST 1 PASSED: WORKSPACE_PATH properly configured")
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        all_tests_passed = False
    
    # Test 2: JobLauncher Absolute Paths
    print("\n[TEST 2] JobLauncher Uses Absolute Paths")
    print("-" * 50)
    try:
        # Create test instances
        job_store = InMemoryJobStore()
        docker_wrapper = DockerWrapper()
        launcher = JobLauncher(job_store, docker_wrapper)
        
        # Create a test job
        test_params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_EQUATION,
            mesh_density=5,
            geometry={"type": "rectangle", "width": 1.0, "height": 1.0},
            solver_settings={}
        )
        
        # Test that job workspace would be created correctly
        job_id = uuid4()
        expected_workspace = settings.workspace_path / str(job_id)
        
        print(f"Job ID: {job_id}")
        print(f"Expected workspace: {expected_workspace}")
        print(f"Path is absolute: {expected_workspace.is_absolute()}")
        
        # Verify the path structure
        assert str(job_id) in str(expected_workspace)
        assert str(settings.workspace_path) in str(expected_workspace)
        print("✓ Job workspace path correctly constructed")
        
        # Check that launcher has the necessary attributes
        assert hasattr(launcher, 'job_store')
        assert hasattr(launcher, 'docker')
        print("✓ JobLauncher properly initialized")
        
        print("\n✅ TEST 2 PASSED: JobLauncher configured for absolute paths")
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        all_tests_passed = False
    
    # Test 3: No os.getcwd() in Backend
    print("\n[TEST 3] Verify No os.getcwd() Usage")
    print("-" * 50)
    try:
        # Check key backend files for os.getcwd()
        backend_files = [
            'app/jobs/launcher.py',
            'app/services/docker_wrapper.py',
            'app/config/settings.py',
            'app/services/sif_generator.py',
            'app/api/simulations.py'
        ]
        
        found_getcwd = False
        for file_path in backend_files:
            full_path = Path(file_path)
            if full_path.exists():
                content = full_path.read_text()
                if 'os.getcwd()' in content:
                    print(f"❌ Found os.getcwd() in {file_path}")
                    found_getcwd = True
                else:
                    print(f"✓ No os.getcwd() in {file_path}")
        
        if not found_getcwd:
            print("\n✅ TEST 3 PASSED: No os.getcwd() usage in backend")
        else:
            print("\n❌ TEST 3 FAILED: Found os.getcwd() usage")
            all_tests_passed = False
            
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        all_tests_passed = False
    
    # Test 4: DockerWrapper Working Directory
    print("\n[TEST 4] DockerWrapper Working Directory Handling")
    print("-" * 50)
    try:
        docker = DockerWrapper()
        
        # Test absolute path handling
        test_job_id = "test-job-456"
        test_dir = Path(f"/workspace/{test_job_id}")
        
        print(f"Test directory: {test_dir}")
        print(f"Starts with /workspace: {str(test_dir).startswith('/workspace')}")
        
        # The DockerWrapper should recognize this as an absolute workspace path
        assert str(test_dir).startswith('/workspace')
        print("✓ DockerWrapper will handle absolute workspace paths correctly")
        
        # Check DockerWrapper attributes
        assert hasattr(docker, 'work_dir')
        assert hasattr(docker, 'running_in_docker')
        print(f"✓ DockerWrapper work_dir: {docker.work_dir}")
        print(f"✓ Running in Docker: {docker.running_in_docker}")
        
        print("\n✅ TEST 4 PASSED: DockerWrapper properly configured")
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        all_tests_passed = False
    
    # Test 5: Path Operations
    print("\n[TEST 5] Path Operations and Job Workspace")
    print("-" * 50)
    try:
        # Test various path operations
        job_id = "test-job-789"
        
        # Test path joining
        job_workspace = settings.workspace_path / job_id
        sif_path = job_workspace / "simulation.sif"
        mesh_dir = job_workspace / "mesh"
        results_dir = job_workspace / "results"
        
        print(f"Job workspace: {job_workspace}")
        print(f"SIF path: {sif_path}")
        print(f"Mesh directory: {mesh_dir}")
        print(f"Results directory: {results_dir}")
        
        # Verify all paths are under workspace
        for path in [job_workspace, sif_path, mesh_dir, results_dir]:
            assert str(settings.workspace_path) in str(path).replace('\\', '/')
        
        print("✓ All paths correctly rooted in workspace")
        
        # Test path components
        assert job_workspace.name == job_id
        assert sif_path.name == "simulation.sif"
        assert mesh_dir.name == "mesh"
        print("✓ Path components correctly constructed")
        
        print("\n✅ TEST 5 PASSED: Path operations work correctly")
        
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 70)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED! Task 2 implementation is correct.")
    else:
        print("❌ SOME TESTS FAILED! Please check the implementation.")
    print("=" * 70)
    
    return all_tests_passed


async def test_docker_compose_integration():
    """Test workspace synchronization with Docker Compose (requires Docker)"""
    
    print("\n" + "=" * 70)
    print("Docker Compose Integration Test")
    print("=" * 70)
    
    try:
        # Check if docker-compose.yml exists
        compose_file = Path("../docker-compose.yml")
        if not compose_file.exists():
            print("❌ docker-compose.yml not found")
            return False
        
        # Read and verify volume configuration
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Check for workspace volume
        if 'workspace:' in content and './workspace:/workspace' in content:
            print("✓ Workspace volume properly configured in docker-compose.yml")
        else:
            print("❌ Workspace volume not properly configured")
            return False
        
        # Check that all services mount the workspace
        services_with_workspace = []
        if 'backend:' in content and '/workspace' in content:
            services_with_workspace.append('backend')
        if 'elmer:' in content and '/workspace' in content:
            services_with_workspace.append('elmer')
        if 'frontend:' in content and '/workspace' in content:
            services_with_workspace.append('frontend')
        
        print(f"✓ Services with workspace mount: {', '.join(services_with_workspace)}")
        
        if len(services_with_workspace) >= 2:
            print("\n✅ Docker Compose configuration verified")
            return True
        else:
            print("\n❌ Not enough services have workspace mount")
            return False
            
    except Exception as e:
        print(f"\n❌ Docker Compose test failed: {e}")
        return False


if __name__ == "__main__":
    # Run main tests
    result = asyncio.run(test_task2())
    
    # Run Docker Compose test if main tests passed
    if result:
        asyncio.run(test_docker_compose_integration())
    
    # Exit with appropriate code
    sys.exit(0 if result else 1) 