#!/usr/bin/env python3
"""
Quality Assurance Tests for Rectangle Mesh Generator
Tests mesh correctness, performance, and quality metrics
"""

import ctypes
import os
import time
import shutil
from pathlib import Path

# Define the C-compatible structures
class GeometryParams(ctypes.Structure):
    _fields_ = [
        ("geometry_type", ctypes.c_int32),
        ("params", ctypes.c_double * 10),
        ("mesh_density", ctypes.c_int32),
        ("boundary_layer", ctypes.c_int32)
    ]

class MeshQuality(ctypes.Structure):
    _fields_ = [
        ("min_angle", ctypes.c_double),
        ("max_angle", ctypes.c_double),
        ("aspect_ratio_avg", ctypes.c_double),
        ("aspect_ratio_max", ctypes.c_double),
        ("total_elements", ctypes.c_int32),
        ("total_nodes", ctypes.c_int32),
        ("return_code", ctypes.c_int32)
    ]

def load_library():
    """Load the educational mesh generator library"""
    lib_path = Path("./libeducational_mesh.so")
    if not lib_path.exists():
        raise FileNotFoundError(f"Library not found: {lib_path}")
    
    lib = ctypes.CDLL(str(lib_path.absolute()))
    
    # Define the function prototype
    lib.generate_mesh.argtypes = [
        ctypes.POINTER(GeometryParams),
        ctypes.c_char_p,
        ctypes.POINTER(MeshQuality)
    ]
    lib.generate_mesh.restype = None
    
    return lib

def verify_mesh_files(output_dir):
    """Verify that all required mesh files exist and have content"""
    required_files = ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']
    results = {}
    
    for filename in required_files:
        filepath = Path(output_dir) / filename
        if filepath.exists():
            size = filepath.stat().st_size
            results[filename] = (True, size)
        else:
            results[filename] = (False, 0)
    
    return results

def parse_mesh_header(filepath):
    """Parse mesh.header file and return mesh information"""
    with open(filepath, 'r') as f:
        # First line: nodes elements boundaries
        line1 = f.readline().strip().split()
        nodes = int(line1[0])
        elements = int(line1[1])
        boundaries = int(line1[2])
        
        # Number of element types
        num_types = int(f.readline().strip())
        
        # Element type information
        types = []
        for _ in range(num_types):
            type_info = f.readline().strip().split()
            types.append((int(type_info[0]), int(type_info[1])))
    
    return nodes, elements, boundaries, types

def verify_node_coordinates(filepath, expected_nodes, width, height):
    """Verify node coordinates are within expected bounds"""
    errors = []
    with open(filepath, 'r') as f:
        node_count = 0
        for line in f:
            node_count += 1
            parts = line.strip().split()
            if len(parts) < 5:
                errors.append(f"Line {node_count}: Invalid format")
                continue
            
            node_id = int(parts[0])
            x = float(parts[2])
            y = float(parts[3])
            z = float(parts[4])
            
            if node_id != node_count:
                errors.append(f"Node {node_count}: ID mismatch (expected {node_count}, got {node_id})")
            
            if x < -0.0001 or x > width + 0.0001:
                errors.append(f"Node {node_id}: X coordinate {x} out of bounds [0, {width}]")
            
            if y < -0.0001 or y > height + 0.0001:
                errors.append(f"Node {node_id}: Y coordinate {y} out of bounds [0, {height}]")
            
            if abs(z) > 0.0001:
                errors.append(f"Node {node_id}: Z coordinate {z} should be 0")
    
    if node_count != expected_nodes:
        errors.append(f"Node count mismatch: expected {expected_nodes}, found {node_count}")
    
    return errors

def verify_element_connectivity(filepath, expected_elements, expected_nodes):
    """Verify element connectivity references valid nodes"""
    errors = []
    with open(filepath, 'r') as f:
        elem_count = 0
        for line in f:
            elem_count += 1
            parts = line.strip().split()
            if len(parts) < 7:  # elem_id material type n1 n2 n3 n4
                errors.append(f"Element {elem_count}: Invalid format")
                continue
            
            elem_id = int(parts[0])
            elem_type = int(parts[2])
            
            if elem_type != 404:
                errors.append(f"Element {elem_id}: Invalid type {elem_type}, expected 404")
            
            # Check node references
            nodes = [int(parts[i]) for i in range(3, 7)]
            for node in nodes:
                if node < 1 or node > expected_nodes:
                    errors.append(f"Element {elem_id}: Invalid node reference {node}")
    
    if elem_count != expected_elements:
        errors.append(f"Element count mismatch: expected {expected_elements}, found {elem_count}")
    
    return errors

def run_quality_test(lib, width, height, density, test_name):
    """Run a single quality test"""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"{'='*60}")
    
    # Create output directory
    output_dir = f"qa_test_{test_name.replace(' ', '_').lower()}"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Set up parameters
    params = GeometryParams()
    params.geometry_type = 1  # Rectangle
    params.params[0] = width
    params.params[1] = height
    params.mesh_density = density
    params.boundary_layer = 0
    
    quality = MeshQuality()
    
    # Generate mesh and measure time
    start_time = time.time()
    lib.generate_mesh(
        ctypes.byref(params),
        output_dir.encode('utf-8'),
        ctypes.byref(quality)
    )
    generation_time = time.time() - start_time
    
    print(f"Dimensions: {width} x {height}")
    print(f"Density: {density}")
    print(f"Generation time: {generation_time:.3f} seconds")
    print(f"Return code: {quality.return_code}")
    
    if quality.return_code != 0:
        print(f"ERROR: Mesh generation failed!")
        return False
    
    print(f"Total nodes: {quality.total_nodes}")
    print(f"Total elements: {quality.total_elements}")
    print(f"Min angle: {quality.min_angle:.2f}°")
    print(f"Max angle: {quality.max_angle:.2f}°")
    print(f"Average aspect ratio: {quality.aspect_ratio_avg:.3f}")
    print(f"Max aspect ratio: {quality.aspect_ratio_max:.3f}")
    
    # Verify files exist
    print("\nFile verification:")
    file_results = verify_mesh_files(output_dir)
    all_files_ok = True
    for filename, (exists, size) in file_results.items():
        if exists:
            print(f"  ✓ {filename} ({size} bytes)")
        else:
            print(f"  ✗ {filename} (missing)")
            all_files_ok = False
    
    if not all_files_ok:
        return False
    
    # Parse and verify mesh header
    print("\nMesh header verification:")
    header_path = Path(output_dir) / "mesh.header"
    nodes, elements, boundaries, types = parse_mesh_header(header_path)
    
    print(f"  Nodes: {nodes} (expected: {quality.total_nodes})")
    print(f"  Elements: {elements} (expected: {quality.total_elements})")
    print(f"  Boundaries: {boundaries}")
    print(f"  Element types: {types}")
    
    header_ok = (nodes == quality.total_nodes and elements == quality.total_elements)
    
    # Verify node coordinates
    print("\nNode coordinate verification:")
    nodes_path = Path(output_dir) / "mesh.nodes"
    node_errors = verify_node_coordinates(nodes_path, nodes, width, height)
    if node_errors:
        print(f"  ✗ Found {len(node_errors)} errors:")
        for error in node_errors[:5]:  # Show first 5 errors
            print(f"    - {error}")
        if len(node_errors) > 5:
            print(f"    ... and {len(node_errors) - 5} more errors")
    else:
        print(f"  ✓ All {nodes} nodes have valid coordinates")
    
    # Verify element connectivity
    print("\nElement connectivity verification:")
    elements_path = Path(output_dir) / "mesh.elements"
    elem_errors = verify_element_connectivity(elements_path, elements, nodes)
    if elem_errors:
        print(f"  ✗ Found {len(elem_errors)} errors:")
        for error in elem_errors[:5]:  # Show first 5 errors
            print(f"    - {error}")
        if len(elem_errors) > 5:
            print(f"    ... and {len(elem_errors) - 5} more errors")
    else:
        print(f"  ✓ All {elements} elements have valid connectivity")
    
    # Quality checks
    print("\nQuality checks:")
    quality_ok = True
    
    # Angle check (should be 90° for rectangles)
    if abs(quality.min_angle - 90.0) > 0.01 or abs(quality.max_angle - 90.0) > 0.01:
        print(f"  ✗ Angles should be 90° for rectangles")
        quality_ok = False
    else:
        print(f"  ✓ All angles are 90°")
    
    # Aspect ratio check
    if quality.aspect_ratio_max > 2.0:
        print(f"  ✗ Maximum aspect ratio {quality.aspect_ratio_max:.3f} exceeds 2.0")
        quality_ok = False
    else:
        print(f"  ✓ Aspect ratios are acceptable")
    
    # Performance check
    if generation_time > 2.0 and density <= 40:  # 400x400 should be under 2s
        print(f"  ✗ Generation time {generation_time:.3f}s exceeds 2.0s for density {density}")
        quality_ok = False
    else:
        print(f"  ✓ Performance is acceptable")
    
    overall_ok = all_files_ok and header_ok and len(node_errors) == 0 and len(elem_errors) == 0 and quality_ok
    
    print(f"\nOverall result: {'PASS' if overall_ok else 'FAIL'}")
    
    return overall_ok

def main():
    """Run comprehensive quality assurance tests"""
    print("Educational Mesh Generator - Quality Assurance Tests")
    print("====================================================\n")
    
    # Load library
    try:
        lib = load_library()
        print("✓ Library loaded successfully\n")
    except Exception as e:
        print(f"✗ Failed to load library: {e}")
        return 1
    
    # Test cases
    test_cases = [
        # (width, height, density, test_name)
        (1.0, 1.0, 1, "Small square"),
        (2.0, 1.0, 2, "Rectangle 2:1 ratio"),
        (4.0, 1.0, 2, "Rectangle 4:1 ratio"), 
        (1.0, 1.0, 10, "Dense square"),
        (4.0, 4.0, 10, "Large square (400 elements)"),
        (8.0, 8.0, 5, "Very large square (1600 elements)"),
        (0.1, 0.1, 10, "Tiny square"),
        (10.0, 10.0, 4, "Large domain (1600 elements)"),
    ]
    
    passed = 0
    failed = 0
    
    for width, height, density, test_name in test_cases:
        if run_quality_test(lib, width, height, density, test_name):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main()) 