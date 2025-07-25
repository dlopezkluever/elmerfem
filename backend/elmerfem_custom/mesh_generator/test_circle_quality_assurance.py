#!/usr/bin/env python3
"""
Comprehensive Quality Assurance Tests for Circle Mesh Generation
Tests all aspects of Task 16 implementation with rigorous validation
"""

import os
import sys
import time
import ctypes
import numpy as np
from pathlib import Path


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
    """Load the mesh generation library"""
    lib_path = "./libeducational_mesh.so"
    if not os.path.exists(lib_path):
        print(f"✗ Failed to load library: Library not found: {lib_path}")
        return None
    
    try:
        lib = ctypes.CDLL(lib_path)
        
        # Set up function signature
        lib.generate_mesh.argtypes = [
            ctypes.POINTER(GeometryParams),
            ctypes.c_char_p,
            ctypes.POINTER(MeshQuality)
        ]
        
        print("✓ Library loaded successfully")
        return lib
    except Exception as e:
        print(f"✗ Failed to load library: {e}")
        return None


def test_circle_mesh_qa(lib, radius, density, boundary_layer, test_name):
    """Run comprehensive quality assurance test for a circle mesh"""
    
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"{'='*60}")
    print(f"Radius: {radius}")
    print(f"Density: {density}")
    print(f"Boundary layer: {'Yes' if boundary_layer else 'No'}")
    
    # Create output directory
    output_dir = f"qa_{test_name.lower().replace(' ', '_')}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up geometry
    geometry = GeometryParams()
    geometry.geometry_type = 2  # Circle
    geometry.params[0] = radius
    geometry.mesh_density = density
    geometry.boundary_layer = 1 if boundary_layer else 0
    
    quality = MeshQuality()
    
    # Generate mesh
    start_time = time.time()
    return_code = lib.generate_mesh(
        ctypes.byref(geometry),
        output_dir.encode('utf-8'),
        ctypes.byref(quality)
    )
    generation_time = time.time() - start_time
    
    print(f"Generation time: {generation_time:.3f} seconds")
    print(f"Return code: {quality.return_code}")
    print(f"Total nodes: {quality.total_nodes}")
    print(f"Total elements: {quality.total_elements}")
    print(f"Min angle: {quality.min_angle:.2f}°")
    print(f"Max angle: {quality.max_angle:.2f}°")
    print(f"Average aspect ratio: {quality.aspect_ratio_avg:.3f}")
    print(f"Max aspect ratio: {quality.aspect_ratio_max:.3f}")
    
    # File verification
    print(f"\nFile verification:")
    files_ok = True
    for fname in ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']:
        fpath = os.path.join(output_dir, fname)
        if os.path.exists(fpath):
            size = os.path.getsize(fpath)
            print(f"  ✓ {fname} ({size} bytes)")
        else:
            print(f"  ✗ {fname} NOT FOUND")
            files_ok = False
    
    if not files_ok:
        print(f"\nOverall result: FAIL")
        return False
    
    # Mesh validation
    errors = []
    
    # Expected values
    nr = 5 * density  # radial divisions
    ntheta = 12 * density  # circumferential divisions
    expected_nodes = 1 + nr * ntheta
    expected_elements = ntheta + (nr - 1) * ntheta * 2
    expected_boundaries = ntheta
    
    # Header verification
    print(f"\nMesh header verification:")
    with open(os.path.join(output_dir, 'mesh.header'), 'r') as f:
        lines = f.readlines()
        nodes, elements, boundaries = map(int, lines[0].split())
        print(f"  Nodes: {nodes} (expected: {expected_nodes})")
        print(f"  Elements: {elements} (expected: {expected_elements})")
        print(f"  Boundaries: {boundaries}")
        
        elem_types = []
        n_types = int(lines[1])
        for i in range(n_types):
            elem_type, count = map(int, lines[2+i].split())
            elem_types.append((elem_type, count))
        print(f"  Element types: {elem_types}")
        
        if nodes != expected_nodes:
            errors.append(f"Node count mismatch: expected {expected_nodes}, got {nodes}")
        if elements != expected_elements:
            errors.append(f"Element count mismatch: expected {expected_elements}, got {elements}")
    
    # Node coordinate verification
    print(f"\nNode coordinate verification:")
    node_errors = []
    boundary_radii = []
    
    with open(os.path.join(output_dir, 'mesh.nodes'), 'r') as f:
        node_lines = f.readlines()
        
        # Check center node
        parts = node_lines[0].split()
        if len(parts) >= 5:
            x, y = float(parts[2]), float(parts[3])
            if abs(x) > 1e-10 or abs(y) > 1e-10:
                node_errors.append(f"Center node not at origin: ({x}, {y})")
        
        # Check boundary nodes
        for i in range(len(node_lines) - ntheta, len(node_lines)):
            if i < len(node_lines):
                parts = node_lines[i].split()
                if len(parts) >= 5:
                    node_id = int(parts[0])
                    tag = int(parts[1])
                    x, y = float(parts[2]), float(parts[3])
                    r = np.sqrt(x**2 + y**2)
                    boundary_radii.append(r)
                    
                    if tag != 1:
                        node_errors.append(f"Boundary node {node_id} has wrong tag: {tag}")
                    if abs(r - radius) > 1e-8:
                        node_errors.append(f"Boundary node {node_id} radius error: {r:.10f} vs {radius}")
        
        # Check node count
        if len(node_lines) != expected_nodes:
            node_errors.append(f"Node count mismatch: expected {expected_nodes}, found {len(node_lines)}")
    
    if node_errors:
        print(f"  ✗ Found {len(node_errors)} errors:")
        for err in node_errors[:2]:  # Show first 2 errors
            print(f"    - {err}")
        errors.extend(node_errors)
    else:
        print(f"  ✓ All nodes valid")
        if boundary_radii:
            print(f"  ✓ Boundary radius: {np.mean(boundary_radii):.10f} ± {np.std(boundary_radii):.2e}")
    
    # Element connectivity verification
    print(f"\nElement connectivity verification:")
    elem_errors = []
    center_triangles = 0
    
    with open(os.path.join(output_dir, 'mesh.elements'), 'r') as f:
        elem_lines = f.readlines()
        
        # Check center triangles
        for i in range(min(ntheta, len(elem_lines))):
            parts = elem_lines[i].split()
            if len(parts) >= 6:
                nodes = [int(parts[j]) for j in range(3, 6)]
                if 1 in nodes:  # Should contain center node
                    center_triangles += 1
                else:
                    elem_errors.append(f"Center triangle {i+1} missing center node")
        
        # Check element count
        if len(elem_lines) != expected_elements:
            elem_errors.append(f"Element count mismatch: expected {expected_elements}, found {len(elem_lines)}")
    
    if elem_errors:
        print(f"  ✗ Found {len(elem_errors)} errors:")
        for err in elem_errors[:2]:
            print(f"    - {err}")
        errors.extend(elem_errors)
    else:
        print(f"  ✓ All elements valid")
        print(f"  ✓ Center triangles: {center_triangles} (expected: {ntheta})")
    
    # Radial spacing verification
    if boundary_layer:
        print(f"\nRadial spacing verification (exponential):")
        # Extract radial positions from nodes
        radial_positions = {}
        with open(os.path.join(output_dir, 'mesh.nodes'), 'r') as f:
            lines = f.readlines()[1:]  # Skip center
            for i, line in enumerate(lines):
                parts = line.split()
                if len(parts) >= 5:
                    x, y = float(parts[2]), float(parts[3])
                    r = np.sqrt(x**2 + y**2)
                    ring = i // ntheta + 1
                    if ring not in radial_positions:
                        radial_positions[ring] = []
                    radial_positions[ring].append(r)
        
        # Check exponential growth
        prev_dr = 0
        prev_r = 0
        spacing_ok = True
        for ring in sorted(radial_positions.keys()):
            if radial_positions[ring]:
                avg_r = np.mean(radial_positions[ring])
                dr = avg_r - prev_r
                if prev_dr > 0 and dr <= prev_dr:
                    spacing_ok = False
                    print(f"  ✗ Non-exponential spacing at ring {ring}: dr={dr:.6f} <= prev_dr={prev_dr:.6f}")
                    break
                prev_dr = dr
                prev_r = avg_r
        
        if spacing_ok:
            print(f"  ✓ Exponential spacing verified")
    
    # Quality checks
    print(f"\nQuality checks:")
    quality_ok = True
    
    # Angle checks
    if quality.min_angle < 10.0:
        print(f"  ✗ Minimum angle too small: {quality.min_angle:.2f}° < 10°")
        quality_ok = False
    else:
        print(f"  ✓ Minimum angle acceptable: {quality.min_angle:.2f}°")
    
    if quality.max_angle > 150.0:
        print(f"  ✗ Maximum angle too large: {quality.max_angle:.2f}° > 150°")
        quality_ok = False
    else:
        print(f"  ✓ Maximum angle acceptable: {quality.max_angle:.2f}°")
    
    # Aspect ratio checks
    if quality.aspect_ratio_max > 3.0:
        print(f"  ✗ Aspect ratio too high: {quality.aspect_ratio_max:.3f} > 3.0")
        quality_ok = False
    else:
        print(f"  ✓ Aspect ratios are acceptable")
    
    # Performance check
    if generation_time > 2.0:
        print(f"  ✗ Performance requirement not met: {generation_time:.3f}s > 2.0s")
        quality_ok = False
    else:
        print(f"  ✓ Performance is acceptable")
    
    # Overall result
    passed = quality.return_code == 0 and len(errors) == 0 and quality_ok
    print(f"\nOverall result: {'PASS' if passed else 'FAIL'}")
    
    return passed


def main():
    """Run all quality assurance tests"""
    print("Educational Mesh Generator - Circle Mesh Quality Assurance Tests")
    print("=" * 64)
    
    # Load library
    lib = load_library()
    if not lib:
        return 1
    
    print()
    
    # Test cases covering all scenarios
    test_cases = [
        # Basic tests
        ("Small circle (uniform)", 1.0, 1, False),
        ("Medium circle (uniform)", 2.0, 2, False),
        ("Large circle (uniform)", 5.0, 3, False),
        
        # Boundary layer tests
        ("Small circle (boundary layer)", 1.0, 2, True),
        ("Medium circle (boundary layer)", 3.0, 3, True),
        
        # High density tests
        ("Dense circle", 1.0, 5, False),
        ("Very dense circle", 2.0, 8, False),
        
        # Edge cases
        ("Tiny circle", 0.1, 1, False),
        ("Large domain", 10.0, 4, False),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, radius, density, boundary_layer in test_cases:
        if test_circle_mesh_qa(lib, radius, density, boundary_layer, test_name):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed} passed, {failed} failed")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main()) 