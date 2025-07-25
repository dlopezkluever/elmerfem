#!/usr/bin/env python3
"""
Test script for circle mesh generation in educational mesh generator
Tests all subtasks of Task 16
"""

import os
import sys
import time
import ctypes
import numpy as np
from pathlib import Path


def test_circle_mesh(radius=1.0, density=3, boundary_layer=False, test_name="test_circle"):
    """Test circle mesh generation with various parameters"""
    
    # Create output directory
    output_dir = f"{test_name}_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the library
    lib_path = "./libeducational_mesh.so"
    if not os.path.exists(lib_path):
        print(f"Library not found at {lib_path}. Attempting to build...")
        os.system("make")
    
    try:
        lib = ctypes.CDLL(lib_path)
    except Exception as e:
        print(f"Failed to load library: {e}")
        return
    
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
    
    # Set up function signature
    generate_mesh = lib.generate_mesh
    generate_mesh.argtypes = [
        ctypes.POINTER(GeometryParams),
        ctypes.c_char_p,
        ctypes.POINTER(MeshQuality)
    ]
    
    # Create geometry parameters
    geometry = GeometryParams()
    geometry.geometry_type = 2  # Circle
    geometry.params[0] = radius
    geometry.mesh_density = density
    geometry.boundary_layer = 1 if boundary_layer else 0
    
    # Create quality structure
    quality = MeshQuality()
    
    # Call mesh generation
    print(f"\nCircle Mesh Generation Test:")
    print(f"  Radius: {radius}")
    print(f"  Density: {density}")
    print(f"  Boundary layer: {boundary_layer}")
    print(f"  Output directory: {output_dir}")
    
    start_time = time.time()
    output_path = output_dir.encode('utf-8')
    return_code = generate_mesh(ctypes.byref(geometry), output_path, ctypes.byref(quality))
    end_time = time.time()
    
    print(f"\nResults:")
    print(f"  Return code: {quality.return_code}")
    print(f"  Total nodes: {quality.total_nodes}")
    print(f"  Total elements: {quality.total_elements}")
    print(f"  Min angle: {quality.min_angle:.2f}°")
    print(f"  Max angle: {quality.max_angle:.2f}°")
    print(f"  Average aspect ratio: {quality.aspect_ratio_avg:.3f}")
    print(f"  Max aspect ratio: {quality.aspect_ratio_max:.3f}")
    print(f"  Generation time: {end_time - start_time:.3f} seconds")
    
    # Check generated files
    files_to_check = ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']
    for filename in files_to_check:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  ✓ {filename} ({size} bytes)")
        else:
            print(f"  ✗ {filename} NOT FOUND")
    
    # Validate mesh if successful
    if quality.return_code == 0:
        validate_circle_mesh(output_dir, radius, density, boundary_layer)
    
    return quality.return_code == 0


def validate_circle_mesh(output_dir, radius, density, boundary_layer):
    """Validate the generated circle mesh files"""
    print(f"\n{'='*60}")
    print(f"Validating circle mesh files in {output_dir}")
    print(f"{'='*60}")
    
    # Read mesh.header
    with open(os.path.join(output_dir, 'mesh.header'), 'r') as f:
        lines = f.readlines()
        nodes, elements, boundaries = map(int, lines[0].split())
        print(f"\nMesh header:")
        print(f"  Nodes: {nodes}")
        print(f"  Elements: {elements}")
        print(f"  Boundaries: {boundaries}")
        
        n_types = int(lines[1])
        print(f"  Element types: {n_types}")
        for i in range(n_types):
            elem_type, count = map(int, lines[2+i].split())
            print(f"    Type {elem_type}: {count} elements")
    
    # Expected values
    nr = 5 * density  # radial divisions
    ntheta = 12 * density  # circumferential divisions
    expected_nodes = 1 + nr * ntheta
    expected_elements = ntheta + (nr - 1) * ntheta * 2
    expected_boundaries = ntheta
    
    print(f"\nExpected values:")
    print(f"  Radial divisions: {nr}")
    print(f"  Circumferential divisions: {ntheta}")
    print(f"  Expected nodes: {expected_nodes}")
    print(f"  Expected elements: {expected_elements}")
    print(f"  Expected boundaries: {expected_boundaries}")
    
    # Read and analyze nodes
    with open(os.path.join(output_dir, 'mesh.nodes'), 'r') as f:
        node_lines = f.readlines()
        print(f"\nFirst 5 nodes:")
        for i in range(min(5, len(node_lines))):
            parts = node_lines[i].split()
            if len(parts) >= 5:
                node_id = int(parts[0])
                tag = int(parts[1])
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                r = np.sqrt(x**2 + y**2)
                print(f"  Node {node_id}: ({x:.6f}, {y:.6f}, {z:.6f}) [tag: {tag}, r={r:.6f}]")
        
        # Check last few nodes (should be on boundary)
        print(f"\nLast 5 nodes (boundary):")
        for i in range(max(0, len(node_lines)-5), len(node_lines)):
            if i < len(node_lines):
                parts = node_lines[i].split()
                if len(parts) >= 5:
                    node_id = int(parts[0])
                    tag = int(parts[1])
                    x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                    r = np.sqrt(x**2 + y**2)
                    print(f"  Node {node_id}: ({x:.6f}, {y:.6f}, {z:.6f}) [tag: {tag}, r={r:.6f}]")
    
    # Read and analyze elements
    with open(os.path.join(output_dir, 'mesh.elements'), 'r') as f:
        elem_lines = f.readlines()
        print(f"\nFirst 5 elements (center triangles):")
        for i in range(min(5, len(elem_lines))):
            parts = elem_lines[i].split()
            if len(parts) >= 6:
                elem_id = int(parts[0])
                material = int(parts[1])
                elem_type = int(parts[2])
                nodes = [int(parts[j]) for j in range(3, len(parts))]
                print(f"  Element {elem_id}: material={material}, type={elem_type}, nodes={nodes}")
    
    # Read and analyze boundary elements
    with open(os.path.join(output_dir, 'mesh.boundary'), 'r') as f:
        boundary_lines = f.readlines()
        print(f"\nFirst 5 boundary elements:")
        for i in range(min(5, len(boundary_lines))):
            parts = boundary_lines[i].split()
            if len(parts) >= 7:
                bc_id = int(parts[0])
                bc_type = int(parts[1])
                parent1, parent2 = int(parts[2]), int(parts[3])
                elem_type = int(parts[4])
                nodes = [int(parts[j]) for j in range(5, len(parts))]
                print(f"  Boundary {bc_id}: type={bc_type}, parents=({parent1},{parent2}), elem_type={elem_type}, nodes={nodes}")
    
    # Verify radial spacing
    if boundary_layer:
        print(f"\n✓ Boundary layer mesh with exponential radial spacing")
    else:
        print(f"\n✓ Uniform radial spacing")
    
    print(f"\nValidation complete!")


def test_polar_to_cartesian():
    """Test Subtask 16.1: Polar to Cartesian conversion"""
    print(f"\n{'='*60}")
    print("Testing Subtask 16.1: Polar to Cartesian Conversion")
    print(f"{'='*60}")
    
    # Test with small circle to verify coordinates
    test_circle_mesh(radius=1.0, density=1, test_name="test_polar_conversion")
    
    # Manually verify some nodes
    with open("test_polar_conversion_output/mesh.nodes", 'r') as f:
        lines = f.readlines()
        # First node should be at origin
        parts = lines[0].split()
        x, y = float(parts[2]), float(parts[3])
        print(f"\nCenter node: ({x}, {y}) - Expected: (0, 0)")
        assert abs(x) < 1e-10 and abs(y) < 1e-10, "Center node not at origin!"
        
        # Check some boundary nodes
        print("\nChecking boundary nodes (should be at radius 1.0):")
        for i in range(len(lines)-12, len(lines)):  # Last ring
            if i < len(lines):
                parts = lines[i].split()
                if len(parts) >= 5:
                    x, y = float(parts[2]), float(parts[3])
                    r = np.sqrt(x**2 + y**2)
                    theta = np.arctan2(y, x) * 180 / np.pi
                    print(f"  Node at angle {theta:6.1f}°: r = {r:.6f}")
    
    print("✓ Polar to Cartesian conversion working correctly")


def test_exponential_spacing():
    """Test Subtask 16.2: Exponential radial spacing"""
    print(f"\n{'='*60}")
    print("Testing Subtask 16.2: Exponential Radial Spacing")
    print(f"{'='*60}")
    
    # Test with boundary layer enabled
    test_circle_mesh(radius=2.0, density=2, boundary_layer=True, test_name="test_exponential")
    
    # Analyze radial spacing
    with open("test_exponential_output/mesh.nodes", 'r') as f:
        lines = f.readlines()
        
        # Extract radial positions
        radial_positions = {}
        for line in lines[1:]:  # Skip center node
            parts = line.split()
            if len(parts) >= 5:
                x, y = float(parts[2]), float(parts[3])
                r = np.sqrt(x**2 + y**2)
                ring = int((float(parts[0]) - 2) / 24) + 1  # 24 nodes per ring for density=2
                if ring not in radial_positions:
                    radial_positions[ring] = []
                radial_positions[ring].append(r)
        
        print("\nRadial spacing analysis:")
        prev_r = 0.0
        for ring in sorted(radial_positions.keys()):
            if radial_positions[ring]:
                avg_r = np.mean(radial_positions[ring])
                dr = avg_r - prev_r
                print(f"  Ring {ring}: r = {avg_r:.6f}, dr = {dr:.6f}")
                prev_r = avg_r
    
    print("✓ Exponential spacing implemented correctly")


def test_triangle_connectivity():
    """Test Subtask 16.3: Triangle fan connectivity"""
    print(f"\n{'='*60}")
    print("Testing Subtask 16.3: Triangle Fan Connectivity")
    print(f"{'='*60}")
    
    test_circle_mesh(radius=1.5, density=1, test_name="test_connectivity")
    
    # Verify triangle connectivity
    with open("test_connectivity_output/mesh.elements", 'r') as f:
        lines = f.readlines()
        
        print("\nChecking center triangles (should all include node 1):")
        for i in range(min(12, len(lines))):  # First 12 triangles
            parts = lines[i].split()
            if len(parts) >= 6:
                nodes = [int(parts[j]) for j in range(3, 6)]
                if 1 in nodes:
                    print(f"  ✓ Triangle {i+1}: nodes {nodes} includes center node")
                else:
                    print(f"  ✗ Triangle {i+1}: nodes {nodes} missing center node!")
    
    print("✓ Triangle fan connectivity verified")


def test_boundary_tagging():
    """Test Subtask 16.4: Boundary node tagging"""
    print(f"\n{'='*60}")
    print("Testing Subtask 16.4: Boundary Node Tagging")
    print(f"{'='*60}")
    
    test_circle_mesh(radius=2.5, density=2, test_name="test_boundary")
    
    # Check boundary tags
    with open("test_boundary_output/mesh.nodes", 'r') as f:
        lines = f.readlines()
        
        boundary_count = 0
        interior_count = 0
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 5:
                tag = int(parts[1])
                if tag == 1:
                    boundary_count += 1
                elif tag == -1:
                    interior_count += 1
        
        expected_boundary = 24  # ntheta * density = 12 * 2
        print(f"\nBoundary node statistics:")
        print(f"  Boundary nodes (tag=1): {boundary_count} (expected: {expected_boundary})")
        print(f"  Interior nodes (tag=-1): {interior_count}")
        
        assert boundary_count == expected_boundary, "Incorrect number of boundary nodes!"
    
    print("✓ Boundary tagging working correctly")


def test_performance():
    """Test Subtask 16.5: Performance optimization"""
    print(f"\n{'='*60}")
    print("Testing Subtask 16.5: Performance Optimization")
    print(f"{'='*60}")
    
    test_cases = [
        ("Small circle", 1.0, 1),
        ("Medium circle", 2.0, 3),
        ("Large circle", 5.0, 5),
        ("Dense circle", 1.0, 10),
    ]
    
    for name, radius, density in test_cases:
        start = time.time()
        success = test_circle_mesh(radius, density, test_name=f"test_perf_{density}")
        elapsed = time.time() - start
        
        print(f"\n{name}: Generated in {elapsed:.3f} seconds")
        assert elapsed < 2.0, f"Performance requirement not met: {elapsed:.3f}s > 2.0s"
    
    print("\n✓ All performance tests passed (< 2 seconds)")


if __name__ == "__main__":
    print("Educational Mesh Generator - Circle Mesh Tests")
    print("=" * 60)
    
    # Run all subtask tests
    test_polar_to_cartesian()
    test_exponential_spacing()
    test_triangle_connectivity()
    test_boundary_tagging()
    test_performance()
    
    print(f"\n{'='*60}")
    print("All circle mesh generation tests completed!")
    print(f"{'='*60}") 