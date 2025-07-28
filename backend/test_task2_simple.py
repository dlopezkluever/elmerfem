#!/usr/bin/env python3
"""
Simple test script to verify Task 2 implementation without dependencies
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))


def test_settings_changes():
    """Test settings.py changes"""
    print("\n[TEST] Checking settings.py changes...")
    
    try:
        from app.config.settings import settings
        
        # Test 1: workspace_path exists
        assert hasattr(settings, 'workspace_path'), "settings.workspace_path not found"
        print("✓ workspace_path attribute exists")
        
        # Test 2: workspace_base_dir is a property
        assert hasattr(settings.__class__.workspace_base_dir, 'fget'), "workspace_base_dir is not a property"
        print("✓ workspace_base_dir is a property (backward compatibility)")
        
        # Test 3: Both return the same value
        assert settings.workspace_path == settings.workspace_base_dir
        print("✓ workspace_path == workspace_base_dir")
        
        # Test 4: Default value
        if not os.environ.get('ELMERFEM_WORKSPACE_PATH'):
            assert str(settings.workspace_path).replace('\\', '/') == "/workspace"
            print("✓ Default value is /workspace")
        
        return True
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False


def test_launcher_changes():
    """Test JobLauncher changes"""
    print("\n[TEST] Checking JobLauncher changes...")
    
    try:
        # Read the launcher file
        launcher_file = Path('app/jobs/launcher.py')
        content = launcher_file.read_text()
        
        # Check for workspace directory creation
        checks = [
            ('workspace_dir = settings.workspace_path / str(job_id)', 'Workspace directory creation'),
            ('workspace_dir.mkdir(parents=True, exist_ok=True)', 'Directory creation with parents'),
            ('job.workspace_dir = workspace_dir', 'Workspace directory assignment'),
            ('await self.job_store.update(job)', 'Job update after workspace assignment')
        ]
        
        all_found = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✓ Found: {description}")
            else:
                print(f"❌ Missing: {description}")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ JobLauncher test failed: {e}")
        return False


def test_docker_wrapper_changes():
    """Test DockerWrapper changes"""
    print("\n[TEST] Checking DockerWrapper changes...")
    
    try:
        # Read the docker wrapper file
        wrapper_file = Path('app/services/docker_wrapper.py')
        content = wrapper_file.read_text()
        
        # Check for workspace path handling
        checks = [
            ('if str(working_directory).startswith("/workspace"):', 'Absolute workspace path check'),
            ('container_work_dir = working_directory', 'Direct workspace path usage'),
            ('# Legacy behavior: convert relative path', 'Legacy path handling comment')
        ]
        
        all_found = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✓ Found: {description}")
            else:
                print(f"❌ Missing: {description}")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ DockerWrapper test failed: {e}")
        return False


def test_no_getcwd():
    """Test that os.getcwd() is not used"""
    print("\n[TEST] Checking for os.getcwd() usage...")
    
    try:
        backend_files = [
            'app/jobs/launcher.py',
            'app/services/docker_wrapper.py',
            'app/config/settings.py',
            'app/api/simulations.py',
            'app/main.py'
        ]
        
        found_getcwd = False
        for file_path in backend_files:
            full_path = Path(file_path)
            if full_path.exists():
                content = full_path.read_text()
                if 'os.getcwd()' in content:
                    print(f"❌ Found os.getcwd() in {file_path}")
                    found_getcwd = True
        
        if not found_getcwd:
            print("✓ No os.getcwd() usage found in backend files")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ getcwd test failed: {e}")
        return False


def main():
    """Run all simple tests"""
    print("=" * 60)
    print("Task 2 Simple Verification Tests")
    print("=" * 60)
    
    tests = [
        test_settings_changes,
        test_launcher_changes,
        test_docker_wrapper_changes,
        test_no_getcwd
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED!")
        print("\nNext steps to fully verify:")
        print("1. Run: python test_task2_implementation.py")
        print("2. Start Docker Compose and test a real simulation")
        print("3. Check that files appear in ./workspace/{job_id}/")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 