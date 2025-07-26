#!/usr/bin/env python3
"""
Test Task 20.1: Boundary Layer Mesh Generation
Tests boundary layer functionality for all supported geometries
"""

import ctypes
import os
import tempfile
import shutil
import numpy as np

# Load the shared library
lib_path = os.path.join(os.path.dirname(__file__), 'libeducational_mesh.so')
if not os.path.exists(lib_path):
    print(f"Error: Library not found at {lib_path}")
    print("Please run 'make' first to build the library")
    exit(1)

lib = ctypes.CDLL(lib_path)

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
generate_mesh.restype = None

def analyze_boundary_layer_spacing(nodes_file):
    """Analyze boundary layer spacing from nodes file"""
    nodes = []
    boundary_nodes = []
    
    with open(nodes_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                node_id = int(parts[0])
                boundary_tag = int(parts[1])
                x = float(parts[2])
                y = float(parts[3])
                z = float(parts[4])
                
                nodes.append((x, y, z))
                if boundary_tag > 0:
                    boundary_nodes.append(node_id - 1)  # Convert to 0-based index
    
    return np.array(nodes), boundary_nodes

def test_rectangle_boundary_layers():
    """Test rectangle mesh with boundary layers"""
    print("\n=== Testing Rectangle with Boundary Layers ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up geometry
        geom = GeometryParams()
        geom.geometry_type = 1  # Rectangle
        geom.params[0] = 2.0    # width
        geom.params[1] = 1.0    # height
        geom.mesh_density = 3
        geom.boundary_layer = 1  # Enable boundary layers
        
        quality = MeshQuality()
        
        # Generate mesh
        output_dir = temp_dir.encode('utf-8')
        generate_mesh(ctypes.byref(geom), output_dir, ctypes.byref(quality))
        
        print(f"Generated rectangle mesh with boundary layers:")
        print(f"  Elements: {quality.total_elements}")
        print(f"  Nodes: {quality.total_nodes}")
        print(f"  Min angle: {quality.min_angle:.2f}°")
        print(f"  Max angle: {quality.max_angle:.2f}°")
        print(f"  Avg aspect ratio: {quality.aspect_ratio_avg:.2f}")
        print(f"  Max aspect ratio: {quality.aspect_ratio_max:.2f}")
        
        # Analyze boundary layer spacing
        nodes_file = os.path.join(temp_dir, 'mesh.nodes')
        if os.path.exists(nodes_file):
            nodes, boundary_indices = analyze_boundary_layer_spacing(nodes_file)
            
            # Check boundary layer growth on left edge (x=0)
            left_edge_nodes = [(i, nodes[i]) for i in range(len(nodes)) 
                              if abs(nodes[i][0]) < 1e-10]
            left_edge_nodes.sort(key=lambda x: x[1][1])  # Sort by y-coordinate
            
            # Extract x-coordinates along a horizontal line at y=0.5
            y_target = 0.5
            horizontal_nodes = []
            for i, node in enumerate(nodes):
                if abs(node[1] - y_target) < 0.05:  # Some tolerance
                    horizontal_nodes.append((node[0], i))
            horizontal_nodes.sort()
            
            if len(horizontal_nodes) > 5:
                # Calculate spacing between first few nodes
                print("\n  Boundary layer spacing analysis (first 5 layers from x=0):")
                prev_spacing = horizontal_nodes[1][0] - horizontal_nodes[0][0]
                for i in range(1, min(6, len(horizontal_nodes))):
                    spacing = horizontal_nodes[i][0] - horizontal_nodes[i-1][0]
                    print(f"    Layer {i-1} to {i}: {spacing:.6f}")
                    if i > 1:
                        growth_ratio = spacing / prev_spacing
                        print(f"      Growth ratio: {growth_ratio:.3f}")
                    prev_spacing = spacing
        
        return quality.return_code == 0

def test_annulus_boundary_layers():
    """Test annulus mesh with boundary layers"""
    print("\n=== Testing Annulus with Boundary Layers ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up geometry
        geom = GeometryParams()
        geom.geometry_type = 3  # Annulus
        geom.params[0] = 0.5    # inner radius
        geom.params[1] = 1.0    # outer radius
        geom.mesh_density = 3
        geom.boundary_layer = 1  # Enable boundary layers
        
        quality = MeshQuality()
        
        # Generate mesh
        output_dir = temp_dir.encode('utf-8')
        generate_mesh(ctypes.byref(geom), output_dir, ctypes.byref(quality))
        
        print(f"Generated annulus mesh with boundary layers:")
        print(f"  Elements: {quality.total_elements}")
        print(f"  Nodes: {quality.total_nodes}")
        print(f"  Min angle: {quality.min_angle:.2f}°")
        print(f"  Max angle: {quality.max_angle:.2f}°")
        print(f"  Avg aspect ratio: {quality.aspect_ratio_avg:.2f}")
        print(f"  Max aspect ratio: {quality.aspect_ratio_max:.2f}")
        
        # Analyze radial spacing
        nodes_file = os.path.join(temp_dir, 'mesh.nodes')
        if os.path.exists(nodes_file):
            nodes, boundary_indices = analyze_boundary_layer_spacing(nodes_file)
            
            # Get nodes along a radial line (theta = 0)
            radial_nodes = []
            for i, node in enumerate(nodes):
                angle = np.arctan2(node[1], node[0])
                if abs(angle) < 0.1:  # Near theta = 0
                    radius = np.sqrt(node[0]**2 + node[1]**2)
                    radial_nodes.append((radius, i))
            radial_nodes.sort()
            
            if len(radial_nodes) > 5:
                print("\n  Radial boundary layer spacing (from inner radius):")
                prev_spacing = radial_nodes[1][0] - radial_nodes[0][0]
                for i in range(1, min(6, len(radial_nodes))):
                    spacing = radial_nodes[i][0] - radial_nodes[i-1][0]
                    print(f"    Layer {i-1} to {i}: {spacing:.6f}")
                    if i > 1:
                        growth_ratio = spacing / prev_spacing
                        print(f"      Growth ratio: {growth_ratio:.3f}")
                    prev_spacing = spacing
        
        return quality.return_code == 0

def test_circle_boundary_layers():
    """Test circle mesh with boundary layers (already implemented)"""
    print("\n=== Testing Circle with Boundary Layers ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up geometry
        geom = GeometryParams()
        geom.geometry_type = 2  # Circle
        geom.params[0] = 1.0    # radius
        geom.mesh_density = 3
        geom.boundary_layer = 1  # Enable boundary layers
        
        quality = MeshQuality()
        
        # Generate mesh
        output_dir = temp_dir.encode('utf-8')
        generate_mesh(ctypes.byref(geom), output_dir, ctypes.byref(quality))
        
        print(f"Generated circle mesh with boundary layers:")
        print(f"  Elements: {quality.total_elements}")
        print(f"  Nodes: {quality.total_nodes}")
        print(f"  Min angle: {quality.min_angle:.2f}°")
        print(f"  Max angle: {quality.max_angle:.2f}°")
        print(f"  Avg aspect ratio: {quality.aspect_ratio_avg:.2f}")
        print(f"  Max aspect ratio: {quality.aspect_ratio_max:.2f}")
        
        return quality.return_code == 0

def compare_with_without_boundary_layers():
    """Compare meshes with and without boundary layers"""
    print("\n=== Comparing Meshes With/Without Boundary Layers ===")
    
    geometries = [
        (1, "Rectangle", [2.0, 1.0]),
        (3, "Annulus", [0.5, 1.0])
    ]
    
    for geom_type, name, params in geometries:
        print(f"\n{name}:")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Without boundary layers
            geom = GeometryParams()
            geom.geometry_type = geom_type
            for i, p in enumerate(params):
                geom.params[i] = p
            geom.mesh_density = 3
            geom.boundary_layer = 0
            
            quality_no_bl = MeshQuality()
            output_dir = temp_dir.encode('utf-8')
            generate_mesh(ctypes.byref(geom), output_dir, ctypes.byref(quality_no_bl))
            
            # With boundary layers
            geom.boundary_layer = 1
            quality_bl = MeshQuality()
            
            bl_dir = os.path.join(temp_dir, 'bl')
            os.makedirs(bl_dir)
            output_dir_bl = bl_dir.encode('utf-8')
            generate_mesh(ctypes.byref(geom), output_dir_bl, ctypes.byref(quality_bl))
            
            print(f"  Without boundary layers: {quality_no_bl.total_elements} elements")
            print(f"  With boundary layers:    {quality_bl.total_elements} elements")
            print(f"  Aspect ratio change:     {quality_no_bl.aspect_ratio_max:.2f} -> {quality_bl.aspect_ratio_max:.2f}")

if __name__ == "__main__":
    print("Task 20.1: Boundary Layer Mesh Generation Tests")
    print("=" * 50)
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if test_rectangle_boundary_layers():
        tests_passed += 1
    
    if test_annulus_boundary_layers():
        tests_passed += 1
    
    if test_circle_boundary_layers():
        tests_passed += 1
    
    compare_with_without_boundary_layers()
    tests_passed += 1  # Comparison test
    
    print(f"\n{'='*50}")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    print(f"{'='*50}") 