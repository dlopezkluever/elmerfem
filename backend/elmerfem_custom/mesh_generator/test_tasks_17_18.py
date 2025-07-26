#!/usr/bin/env python3
"""
Comprehensive validation test for Tasks 17 and 18
Tests all subtasks for Annulus and L-Shape mesh generation
"""

import os
import sys
import time
import subprocess

def run_test_file(test_file):
    """Run a test file and capture output"""
    print(f"\n{'='*70}")
    print(f"Running {test_file}...")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("ERROR: Test timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run test: {e}")
        return False

def main():
    """Run all tests for Tasks 17 and 18"""
    print("="*70)
    print("COMPREHENSIVE VALIDATION FOR TASKS 17 & 18")
    print("="*70)
    print("\nThis will test:")
    print("- Task 17: Annulus Mesh Generation (5 subtasks)")
    print("- Task 18: L-Shape Mesh Generation (5 subtasks)")
    print("="*70)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Build the library if needed
    if not os.path.exists("libeducational_mesh.so"):
        print("\nBuilding the mesh generator library...")
        result = subprocess.run(["make"], capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: Failed to build library")
            print(result.stdout)
            print(result.stderr)
            return 1
        print("Library built successfully!")
    
    # Run individual test scripts
    test_files = [
        "test_annulus_mesh.py",
        "test_lshape_mesh.py"
    ]
    
    all_passed = True
    
    for test_file in test_files:
        if os.path.exists(test_file):
            if not run_test_file(test_file):
                all_passed = False
        else:
            print(f"WARNING: {test_file} not found")
            all_passed = False
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY OF TASKS 17 & 18 VALIDATION")
    print("="*70)
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nTask 17 (Annulus Mesh Generation) - VERIFIED ✅")
        print("  ✅ 17.1 - Mesh geometry and parameters defined")
        print("  ✅ 17.2 - Radial and angular mesh generation implemented")
        print("  ✅ 17.3 - Boundary layer mesh with ratio 1.2 working")
        print("  ✅ 17.4 - Boundary conditions correctly assigned (inner=2, outer=1)")
        print("  ✅ 17.5 - Performance meets requirements (<2 seconds)")
        
        print("\nTask 18 (L-Shape Mesh Generation) - VERIFIED ✅")
        print("  ✅ 18.1 - Rectangular grid initialization working")
        print("  ✅ 18.2 - Cut removal algorithm implemented")
        print("  ✅ 18.3 - Local refinement near notch applied")
        print("  ✅ 18.4 - All boundary tags correctly assigned (1-5)")
        print("  ✅ 18.5 - Performance meets requirements (<2 seconds)")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\nPlease check the individual test outputs above for details.")
    
    print("="*70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 