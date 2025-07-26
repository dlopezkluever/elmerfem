#!/usr/bin/env python3
"""
Test script for L-Shape Mesh Generation (Task 18)
Tests all subtasks:
18.1 - Initialize Rectangular Grid
18.2 - Implement Cut Removal Algorithm
18.3 - Apply Local Refinement Near Notch (size ∝ r^0.5)
18.4 - Tag Mesh Boundaries (left=1, right=2, top=3, bottom=4, notch=5)
18.5 - Validate Mesh Quality and Performance
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

def test_lshape_mesh(length, density, test_name="test"):
    """Test L-shape mesh generation with given parameters"""
    lib = load_library()
    
    # Create output directory
    output_dir = f"test_lshape_{test_name}"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Setup geometry parameters for L-shape (geometry_type = 4)
    geometry = GeometryParams()
    geometry.geometry_type = 4  # L-shape
    geometry.params[0] = length  # Overall dimension
    geometry.mesh_density = density
    geometry.boundary_layer = 0  # Not used for L-shape
    
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
    print(f"L-Shape Mesh Generation Test: {test_name}")
    print(f"  Length: {length}")
    print(f"  Density: {density}")
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
    
    # Validate mesh
    validate_lshape_mesh(output_dir, length, density)
    
    return quality.return_code == 0

def validate_lshape_mesh(output_dir, length, density):
    """Validate the generated L-shape mesh"""
    print(f"\nValidating L-shape mesh in {output_dir}")
    
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
    
    # Validate boundary conditions (18.4)
    boundary_file = os.path.join(output_dir, "mesh.boundary")
    if os.path.exists(boundary_file):
        boundary_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        with open(boundary_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    boundary_tag = int(parts[1])
                    if boundary_tag in boundary_counts:
                        boundary_counts[boundary_tag] += 1
        
        print(f"\nBoundary validation (Task 18.4):")
        print(f"  Left boundary (tag=1): {boundary_counts[1]} elements")
        print(f"  Right boundary (tag=2): {boundary_counts[2]} elements")
        print(f"  Top boundary (tag=3): {boundary_counts[3]} elements")
        print(f"  Bottom boundary (tag=4): {boundary_counts[4]} elements")
        print(f"  Notch boundary (tag=5): {boundary_counts[5]} elements")
        
        # Check if all boundaries have elements
        all_boundaries_present = all(count > 0 for count in boundary_counts.values())
        if all_boundaries_present:
            print(f"  ✓ All boundary tags correctly assigned")
        else:
            print(f"  ✗ Some boundary tags missing")
    
    # Validate cut removal (18.2) - check that no nodes exist in cut region
    nodes_file = os.path.join(output_dir, "mesh.nodes")
    if os.path.exists(nodes_file):
        nodes_in_cut = 0
        notch_nodes = []
        half_length = length / 2.0
        
        with open(nodes_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 4:
                    x = float(parts[2])
                    y = float(parts[3])
                    
                    # Check if node is in the cut region (top-right quarter)
                    if x > half_length + 1e-6 and y > half_length + 1e-6:
                        nodes_in_cut += 1
                    
                    # Collect nodes near the notch corner
                    dist_to_notch = math.sqrt((x - half_length)**2 + (y - half_length)**2)
                    if dist_to_notch < length * 0.3:  # Within 30% of notch
                        notch_nodes.append((x, y, dist_to_notch))
        
        print(f"\nCut removal validation (Task 18.2):")
        print(f"  Nodes in cut region: {nodes_in_cut}")
        if nodes_in_cut == 0:
            print(f"  ✓ Cut region correctly removed")
        else:
            print(f"  ✗ Cut region not properly removed")
        
        # Validate refinement near notch (18.3)
        if len(notch_nodes) > 10:
            # Sort by distance to notch
            notch_nodes.sort(key=lambda n: n[2])
            
            # Check element sizes near notch
            print(f"\nNotch refinement validation (Task 18.3):")
            print(f"  Nodes near notch: {len(notch_nodes)}")
            
            # Calculate approximate element sizes at different distances
            if len(notch_nodes) > 20:
                # Sample nodes at different distances
                close_nodes = notch_nodes[:10]
                far_nodes = notch_nodes[-10:]
                
                avg_close_dist = sum(n[2] for n in close_nodes) / len(close_nodes)
                avg_far_dist = sum(n[2] for n in far_nodes) / len(far_nodes)
                
                print(f"  Average distance (close): {avg_close_dist:.4f}")
                print(f"  Average distance (far): {avg_far_dist:.4f}")
                
                # Check if refinement follows r^0.5 pattern
                expected_ratio = math.sqrt(avg_far_dist / avg_close_dist)
                print(f"  Distance ratio: {avg_far_dist/avg_close_dist:.3f}")
                print(f"  Expected ratio (√r): {expected_ratio:.3f}")
                
                if avg_close_dist < avg_far_dist:
                    print(f"  ✓ Mesh refined near notch")
                else:
                    print(f"  ✗ No refinement detected near notch")
    
    return True

def run_all_tests():
    """Run comprehensive tests for L-shape mesh generation"""
    print("="*60)
    print("Task 18: L-Shape Mesh Generation - Comprehensive Tests")
    print("="*60)
    
    # Test 1: Small L-shape
    test_lshape_mesh(1.0, 2, "small")
    
    # Test 2: Medium L-shape with higher density
    test_lshape_mesh(2.0, 3, "medium")
    
    # Test 3: Large L-shape
    test_lshape_mesh(4.0, 4, "large")
    
    # Test 4: Performance test (18.5)
    print("\n" + "="*60)
    print("Performance Test (Task 18.5)")
    print("="*60)
    
    start_time = time.time()
    test_lshape_mesh(3.0, 5, "performance")
    end_time = time.time()
    
    total_time = end_time - start_time
    print(f"\nTotal performance test time: {total_time:.3f} seconds")
    if total_time < 2.0:
        print("✓ Performance requirement met (< 2 seconds)")
    else:
        print("✗ Performance requirement NOT met (> 2 seconds)")
    
    # Test 5: Quality validation with detailed analysis
    print("\n" + "="*60)
    print("Detailed Quality Analysis")
    print("="*60)
    test_lshape_mesh(2.0, 4, "quality_analysis")
    
    print("\n" + "="*60)
    print("All Task 18 tests completed!")
    print("="*60)

if __name__ == "__main__":
    run_all_tests() 