#!/usr/bin/env python3
"""
Test script for Annulus Mesh Generation (Task 17)
Tests all subtasks:
17.1 - Define Mesh Geometry and Parameters
17.2 - Implement Radial and Angular Mesh Generation
17.3 - Generate Boundary Layer Mesh (ratio 1.2)
17.4 - Assign Boundary Conditions and Tags (inner=2, outer=1)
17.5 - Validate Mesh Quality and Performance
"""

import os
import sys
import ctypes
import tempfile
import time
import shutil
import math

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Define structures matching Fortran
class GeometryParams(ctypes.Structure):
    _fields_ = [
        ("geometry_type", ctypes.c_int),
        ("params", ctypes.c_double * 10),
        ("mesh_density", ctypes.c_int),
        ("boundary_layer", ctypes.c_int)
    ]

class MeshQuality(ctypes.Structure):
    _fields_ = [
        ("min_angle", ctypes.c_double),
        ("max_angle", ctypes.c_double),
        ("aspect_ratio_avg", ctypes.c_double),
        ("aspect_ratio_max", ctypes.c_double),
        ("total_elements", ctypes.c_int),
        ("total_nodes", ctypes.c_int),
        ("return_code", ctypes.c_int)
    ]

def load_library():
    """Load the shared library"""
    lib_path = os.path.join(os.path.dirname(__file__), "libeducational_mesh.so")
    if not os.path.exists(lib_path):
        print("Library not found. Building...")
        os.system("make")
    
    lib = ctypes.CDLL(lib_path)
    
    # Define function signature
    lib.generate_mesh.argtypes = [
        ctypes.POINTER(GeometryParams),
        ctypes.c_char_p,
        ctypes.POINTER(MeshQuality)
    ]
    lib.generate_mesh.restype = None
    
    return lib

def test_annulus_mesh(inner_radius, outer_radius, density, boundary_layer, test_name="test"):
    """Test annulus mesh generation with given parameters"""
    lib = load_library()
    
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = f"test_annulus_{test_name}"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)
        
        # Setup geometry parameters for annulus (geometry_type = 3)
        geometry = GeometryParams()
        geometry.geometry_type = 3  # annulus
        geometry.params[0] = inner_radius
        geometry.params[1] = outer_radius
        geometry.mesh_density = density
        geometry.boundary_layer = 1 if boundary_layer else 0
        
        # Setup quality structure
        quality = MeshQuality()
        
        # Measure generation time
        start_time = time.time()
        lib.generate_mesh(
            ctypes.byref(geometry),
            output_dir.encode('utf-8'),
            ctypes.byref(quality)
        )
        end_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"Annulus Mesh Generation Test: {test_name}")
        print(f"  Inner radius: {inner_radius}")
        print(f"  Outer radius: {outer_radius}")
        print(f"  Density: {density}")
        print(f"  Boundary layer: {boundary_layer}")
        print(f"  Output directory: {output_dir}")
        print(f"\nResults:")
        print(f"  Return code: {quality.return_code}")
        print(f"  Total nodes: {quality.total_nodes}")
        print(f"  Total elements: {quality.total_elements}")
        print(f"  Min angle: {quality.min_angle:.2f}°")
        print(f"  Max angle: {quality.max_angle:.2f}°")
        print(f"  Average aspect ratio: {quality.aspect_ratio_avg:.3f}")
        print(f"  Max aspect ratio: {quality.aspect_ratio_max:.3f}")
        print(f"  Generation time: {end_time - start_time:.3f} seconds")
        
        # Verify files were created
        files = ["mesh.header", "mesh.nodes", "mesh.elements", "mesh.boundary"]
        for file in files:
            filepath = os.path.join(output_dir, file)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  ✓ {file} ({size} bytes)")
            else:
                print(f"  ✗ {file} not found")
        
        # Validate mesh header
        validate_annulus_mesh(output_dir, inner_radius, outer_radius, density, boundary_layer)
        
        return quality.return_code == 0

def validate_annulus_mesh(output_dir, inner_radius, outer_radius, density, boundary_layer):
    """Validate the generated annulus mesh"""
    print(f"\nValidating annulus mesh in {output_dir}")
    
    # Read mesh header
    header_file = os.path.join(output_dir, "mesh.header")
    if not os.path.exists(header_file):
        print("  ✗ mesh.header not found")
        return False
    
    with open(header_file, 'r') as f:
        header_line = f.readline().strip().split()
        nnodes = int(header_line[0])
        nelems = int(header_line[1])
        nbounds = int(header_line[2])
        
    print(f"  Nodes: {nnodes}")
    print(f"  Elements: {nelems}")
    print(f"  Boundaries: {nbounds}")
    
    # Validate boundary conditions (17.4 - inner=2, outer=1)
    boundary_file = os.path.join(output_dir, "mesh.boundary")
    if os.path.exists(boundary_file):
        inner_count = 0
        outer_count = 0
        with open(boundary_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    boundary_tag = int(parts[1])
                    if boundary_tag == 2:
                        inner_count += 1
                    elif boundary_tag == 1:
                        outer_count += 1
        
        print(f"\nBoundary validation (Task 17.4):")
        print(f"  Inner boundary (tag=2): {inner_count} elements")
        print(f"  Outer boundary (tag=1): {outer_count} elements")
        
        # Check if boundary counts are reasonable
        if inner_count > 0 and outer_count > 0:
            print(f"  ✓ Boundary tags correctly assigned")
        else:
            print(f"  ✗ Boundary tags incorrect")
    
    # Validate nodes for radial spacing (17.3 - boundary layer with ratio 1.2)
    if boundary_layer:
        nodes_file = os.path.join(output_dir, "mesh.nodes")
        if os.path.exists(nodes_file):
            radii = []
            with open(nodes_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        x = float(parts[2])
                        y = float(parts[3])
                        r = math.sqrt(x*x + y*y)
                        if r > 0:
                            radii.append(r)
            
            # Sort unique radii
            unique_radii = sorted(list(set(radii)))
            if len(unique_radii) > 2:
                # Check boundary layer ratio
                dr1 = unique_radii[1] - unique_radii[0]
                dr2 = unique_radii[2] - unique_radii[1]
                ratio = dr2 / dr1 if dr1 > 0 else 0
                
                print(f"\nBoundary layer validation (Task 17.3):")
                print(f"  First spacing: {dr1:.6f}")
                print(f"  Second spacing: {dr2:.6f}")
                print(f"  Growth ratio: {ratio:.3f} (expected ~1.2)")
                
                if 1.15 <= ratio <= 1.25:
                    print(f"  ✓ Boundary layer ratio correct")
                else:
                    print(f"  ✗ Boundary layer ratio incorrect")
    
    return True

def run_all_tests():
    """Run comprehensive tests for annulus mesh generation"""
    print("="*60)
    print("Task 17: Annulus Mesh Generation - Comprehensive Tests")
    print("="*60)
    
    # Test 1: Basic annulus without boundary layer
    test_annulus_mesh(0.5, 1.0, 2, False, "basic")
    
    # Test 2: Annulus with boundary layer (17.3)
    test_annulus_mesh(0.5, 1.0, 3, True, "boundary_layer")
    
    # Test 3: Thin annulus
    test_annulus_mesh(0.8, 1.0, 3, True, "thin")
    
    # Test 4: Large annulus with high density
    test_annulus_mesh(1.0, 5.0, 4, True, "large")
    
    # Test 5: Performance test (17.5)
    print("\n" + "="*60)
    print("Performance Test (Task 17.5)")
    print("="*60)
    
    start_time = time.time()
    test_annulus_mesh(0.5, 2.0, 5, True, "performance")
    end_time = time.time()
    
    total_time = end_time - start_time
    print(f"\nTotal performance test time: {total_time:.3f} seconds")
    if total_time < 2.0:
        print("✓ Performance requirement met (< 2 seconds)")
    else:
        print("✗ Performance requirement NOT met (> 2 seconds)")
    
    print("\n" + "="*60)
    print("All Task 17 tests completed!")
    print("="*60)

if __name__ == "__main__":
    run_all_tests() 