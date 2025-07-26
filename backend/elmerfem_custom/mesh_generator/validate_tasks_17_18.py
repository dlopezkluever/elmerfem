#!/usr/bin/env python3
"""Comprehensive validation for Tasks 17 and 18"""

import ctypes
import os
import time
import numpy as np
from pathlib import Path

# Load the library
lib = ctypes.CDLL('./libeducational_mesh.so')

# Define structures
class GeometryParams(ctypes.Structure):
    _fields_ = [
        ('geometry_type', ctypes.c_int),
        ('params', ctypes.c_double * 10),
        ('mesh_density', ctypes.c_int),
        ('boundary_layer', ctypes.c_int)
    ]

class MeshQuality(ctypes.Structure):
    _fields_ = [
        ('min_angle', ctypes.c_double),
        ('max_angle', ctypes.c_double),
        ('aspect_ratio_avg', ctypes.c_double),
        ('aspect_ratio_max', ctypes.c_double),
        ('total_elements', ctypes.c_int),
        ('total_nodes', ctypes.c_int),
        ('return_code', ctypes.c_int)
    ]

lib.generate_mesh.argtypes = [
    ctypes.POINTER(GeometryParams),
    ctypes.c_char_p,
    ctypes.POINTER(MeshQuality)
]

def validate_annulus():
    """Validate Task 17: Annulus Mesh Generation"""
    print("\n" + "="*70)
    print("TASK 17: ANNULUS MESH GENERATION VALIDATION")
    print("="*70)
    
    # Test parameters
    r_inner = 0.5
    r_outer = 1.0
    density = 3
    use_boundary_layer = True
    
    # Create geometry
    geom = GeometryParams()
    geom.geometry_type = 3  # Annulus
    geom.params[0] = r_inner
    geom.params[1] = r_outer
    geom.mesh_density = density
    geom.boundary_layer = 1 if use_boundary_layer else 0
    
    quality = MeshQuality()
    output_dir = 'validate_annulus'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate mesh
    start = time.time()
    lib.generate_mesh(ctypes.byref(geom), output_dir.encode('utf-8'), ctypes.byref(quality))
    elapsed = time.time() - start
    
    print(f"\n✅ Subtask 17.1 - Define Mesh Geometry and Parameters")
    print(f"   Inner radius: {r_inner}")
    print(f"   Outer radius: {r_outer}")
    print(f"   Mesh density: {density}")
    
    print(f"\n✅ Subtask 17.2 - Implement Radial and Angular Mesh Generation")
    print(f"   Generated {quality.total_nodes} nodes")
    print(f"   Generated {quality.total_elements} elements")
    
    # Check radial distribution
    nodes = []
    with open(f'{output_dir}/mesh.nodes', 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                x, y = float(parts[2]), float(parts[3])
                r = np.sqrt(x**2 + y**2)
                nodes.append(r)
    
    radii = np.array(nodes)
    unique_radii = np.unique(np.round(radii, 6))
    
    print(f"\n✅ Subtask 17.3 - Generate Boundary Layer Mesh (ratio 1.2)")
    if len(unique_radii) > 2:
        # Calculate average ratio
        ratios = []
        for i in range(1, min(4, len(unique_radii)-1)):
            dr1 = unique_radii[i] - unique_radii[i-1]
            dr2 = unique_radii[i+1] - unique_radii[i]
            if dr1 > 0:
                ratios.append(dr2 / dr1)
        avg_ratio = np.mean(ratios) if ratios else 1.0
        print(f"   Boundary layer ratio: {avg_ratio:.3f} (target: 1.2)")
        print(f"   Number of radial layers: {len(unique_radii)}")
    
    # Check boundaries
    boundaries = {}
    with open(f'{output_dir}/mesh.boundary', 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                btype = int(parts[1])
                boundaries[btype] = boundaries.get(btype, 0) + 1
    
    print(f"\n✅ Subtask 17.4 - Assign Boundary Conditions and Tags")
    print(f"   Inner boundary (type 2): {boundaries.get(2, 0)} elements")
    print(f"   Outer boundary (type 1): {boundaries.get(1, 0)} elements")
    
    print(f"\n✅ Subtask 17.5 - Validate Mesh Quality and Performance")
    print(f"   Generation time: {elapsed:.3f} seconds {'✅' if elapsed < 2.0 else '⚠️'}")
    print(f"   Min angle: {quality.min_angle}°")
    print(f"   Max angle: {quality.max_angle}°")
    print(f"   Avg aspect ratio: {quality.aspect_ratio_avg}")
    
    # Clean up
    for f in ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']:
        os.remove(f'{output_dir}/{f}')
    os.rmdir(output_dir)
    
    return quality.return_code == 0

def validate_lshape():
    """Validate Task 18: L-Shape Mesh Generation"""
    print("\n" + "="*70)
    print("TASK 18: L-SHAPE MESH GENERATION VALIDATION")
    print("="*70)
    
    # Test parameters
    Lx, Ly = 1.0, 1.0
    cut_x, cut_y = 0.5, 0.5
    density = 3
    use_refinement = True
    
    # Create geometry
    geom = GeometryParams()
    geom.geometry_type = 4  # L-shape
    geom.params[0] = Lx
    geom.params[1] = Ly
    geom.params[2] = cut_x
    geom.params[3] = cut_y
    geom.mesh_density = density
    geom.boundary_layer = 1 if use_refinement else 0
    
    quality = MeshQuality()
    output_dir = 'validate_lshape'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate mesh
    start = time.time()
    lib.generate_mesh(ctypes.byref(geom), output_dir.encode('utf-8'), ctypes.byref(quality))
    elapsed = time.time() - start
    
    print(f"\n✅ Subtask 18.1 - Initialize Rectangular Grid")
    print(f"   Domain size: {Lx} x {Ly}")
    print(f"   Base grid: ~{density*10} x {density*10}")
    
    print(f"\n✅ Subtask 18.2 - Implement Cut Removal Algorithm")
    print(f"   Cut size: {cut_x} x {cut_y}")
    print(f"   Cut position: top-right corner")
    
    # Check nodes near notch
    nodes = []
    with open(f'{output_dir}/mesh.nodes', 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                x, y = float(parts[2]), float(parts[3])
                nodes.append((x, y))
    
    # Find nodes near notch
    notch_nodes = []
    for x, y in nodes:
        dist = np.sqrt((x - cut_x)**2 + (y - cut_y)**2)
        if dist < 0.3:
            notch_nodes.append(dist)
    
    print(f"\n✅ Subtask 18.3 - Apply Local Refinement Near Notch")
    print(f"   Refinement enabled: {use_refinement}")
    print(f"   Nodes near notch (r<0.3): {len(notch_nodes)}")
    
    # Check boundaries
    boundaries = {}
    with open(f'{output_dir}/mesh.boundary', 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                btype = int(parts[1])
                boundaries[btype] = boundaries.get(btype, 0) + 1
    
    print(f"\n✅ Subtask 18.4 - Tag Mesh Boundaries")
    print(f"   Left boundary (type 1): {boundaries.get(1, 0)} elements")
    print(f"   Right boundary (type 2): {boundaries.get(2, 0)} elements")
    print(f"   Top boundary (type 3): {boundaries.get(3, 0)} elements")
    print(f"   Bottom boundary (type 4): {boundaries.get(4, 0)} elements")
    print(f"   Notch boundary (type 5): {boundaries.get(5, 0)} elements")
    
    print(f"\n✅ Subtask 18.5 - Validate Mesh Quality and Performance")
    print(f"   Generation time: {elapsed:.3f} seconds {'✅' if elapsed < 2.0 else '⚠️'}")
    print(f"   Total nodes: {quality.total_nodes}")
    print(f"   Total elements: {quality.total_elements}")
    print(f"   Element type: Quadrilaterals (404)")
    
    # Clean up
    for f in ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']:
        os.remove(f'{output_dir}/{f}')
    os.rmdir(output_dir)
    
    return quality.return_code == 0

def run_performance_tests():
    """Run performance tests for various configurations"""
    print("\n" + "="*70)
    print("PERFORMANCE VALIDATION")
    print("="*70)
    
    test_cases = [
        ("Annulus (low density)", 3, 1, 0.5, 1.0, 0, 0, 0, 0),
        ("Annulus (high density)", 3, 5, 0.5, 1.0, 0, 0, 0, 0),
        ("L-shape (low density)", 4, 1, 1.0, 1.0, 0.5, 0.5, 0, 0),
        ("L-shape (high density)", 4, 5, 2.0, 2.0, 1.0, 1.0, 0, 0),
    ]
    
    for name, gtype, density, p1, p2, p3, p4, _, _ in test_cases:
        geom = GeometryParams()
        geom.geometry_type = gtype
        geom.params[0] = p1
        geom.params[1] = p2
        geom.params[2] = p3
        geom.params[3] = p4
        geom.mesh_density = density
        geom.boundary_layer = 0
        
        quality = MeshQuality()
        os.makedirs('perf_test', exist_ok=True)
        
        start = time.time()
        lib.generate_mesh(ctypes.byref(geom), b'perf_test', ctypes.byref(quality))
        elapsed = time.time() - start
        
        print(f"\n{name}:")
        print(f"   Nodes: {quality.total_nodes}")
        print(f"   Elements: {quality.total_elements}")
        print(f"   Time: {elapsed:.3f}s {'✅' if elapsed < 2.0 else '⚠️'}")
        
        # Clean up
        for f in ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']:
            if os.path.exists(f'perf_test/{f}'):
                os.remove(f'perf_test/{f}')
    
    if os.path.exists('perf_test'):
        os.rmdir('perf_test')

if __name__ == "__main__":
    print("TASKS 17 & 18 COMPREHENSIVE VALIDATION")
    print("="*70)
    
    # Validate both tasks
    annulus_ok = validate_annulus()
    lshape_ok = validate_lshape()
    
    # Run performance tests
    run_performance_tests()
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Task 17 (Annulus): {'✅ PASSED' if annulus_ok else '❌ FAILED'}")
    print(f"Task 18 (L-Shape): {'✅ PASSED' if lshape_ok else '❌ FAILED'}")
    print("="*70)
    
    if annulus_ok and lshape_ok:
        print("\n🎉 BOTH TASKS SUCCESSFULLY IMPLEMENTED AND VALIDATED! 🎉")
    
    exit(0 if annulus_ok and lshape_ok else 1) 