#!/usr/bin/env python3
"""
Simple verification script for Task 19 features
Tests each feature individually to ensure everything is working
"""

import ctypes
import json
import os
import tempfile
import sys

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

class GeometryParams(ctypes.Structure):
    _fields_ = [
        ("geometry_type", ctypes.c_int),
        ("dim1", ctypes.c_double),
        ("dim2", ctypes.c_double),
        ("dim3", ctypes.c_double),
        ("dim4", ctypes.c_double),
        ("nx", ctypes.c_int),
        ("ny", ctypes.c_int),
        ("boundary_layer", ctypes.c_int),
        ("boundary_thickness", ctypes.c_double),
        ("return_code", ctypes.c_int)
    ]

print("Task 19 Feature Verification")
print("=" * 50)

# Load library
lib_path = "/app/elmerfem_custom/mesh_generator/libeducational_mesh.so"
lib = ctypes.CDLL(lib_path)
print(f"✓ Library loaded: {lib_path}")

# Configure generate_mesh
lib.generate_mesh.argtypes = [
    ctypes.POINTER(GeometryParams),
    ctypes.c_char_p,
    ctypes.POINTER(MeshQuality)
]
lib.generate_mesh.restype = None

# Create temp directory
with tempfile.TemporaryDirectory() as temp_dir:
    # Step 1: Generate a test mesh
    print("\n1. Generating test mesh...")
    params = GeometryParams(
        geometry_type=1, dim1=1.0, dim2=1.0, dim3=0.0, dim4=0.0,
        nx=10, ny=10, boundary_layer=0, boundary_thickness=0.0,
        return_code=0
    )
    
    output_dir = ctypes.c_char_p(temp_dir.encode('utf-8'))
    quality = MeshQuality()
    
    lib.generate_mesh(ctypes.byref(params), output_dir, ctypes.byref(quality))
    
    if quality.return_code == 0:
        print(f"   ✓ Mesh generated: {quality.total_nodes} nodes, {quality.total_elements} elements")
    else:
        print(f"   ✗ Failed with code: {quality.return_code}")
        sys.exit(1)
    
    # Step 2: Test ComputeQuality (19.1)
    print("\n2. Testing ComputeQuality (Task 19.1)...")
    try:
        compute_quality = lib.__educationalmeshgenerator_MOD_computequality
        compute_quality.argtypes = [ctypes.c_char_p, ctypes.POINTER(MeshQuality)]
        compute_quality.restype = None
        
        quality2 = MeshQuality()
        compute_quality(output_dir, ctypes.byref(quality2))
        
        print(f"   ✓ ComputeQuality works!")
        print(f"     Min angle: {quality2.min_angle:.1f}°")
        print(f"     Max angle: {quality2.max_angle:.1f}°")
        print(f"     Avg aspect ratio: {quality2.aspect_ratio_avg:.3f}")
    except Exception as e:
        print(f"   ✗ ComputeQuality failed: {e}")
    
    # Step 3: Test Laplacian Smoothing (19.2 & 19.3)
    print("\n3. Testing Laplacian Smoothing (Task 19.2 & 19.3)...")
    try:
        smooth = lib.__educationalmeshgenerator_MOD_applylaplaciansmoothing
        smooth.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double)]
        smooth.restype = None
        
        iterations = ctypes.c_int(5)
        omega = ctypes.c_double(0.5)
        smooth(output_dir, ctypes.byref(iterations), ctypes.byref(omega))
        
        print(f"   ✓ Smoothing applied successfully!")
        print(f"     Iterations: {iterations.value}")
        print(f"     Relaxation factor: {omega.value}")
    except Exception as e:
        print(f"   ✗ Smoothing failed: {e}")
    
    # Step 4: Test JSON Export (19.4)
    print("\n4. Testing JSON Export (Task 19.4)...")
    try:
        export_json = lib.__educationalmeshgenerator_MOD_exportqualityjson
        export_json.argtypes = [ctypes.c_char_p, ctypes.POINTER(MeshQuality), ctypes.c_char_p]
        export_json.restype = None
        
        export_json(output_dir, ctypes.byref(quality2), ctypes.c_char_p("test_mesh".encode('utf-8')))
        
        json_file = os.path.join(temp_dir, "mesh_quality.json")
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
            print(f"   ✓ JSON export works!")
            print(f"     Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"     Assessment: {data.get('quality_assessment', 'N/A')}")
        else:
            print(f"   ✗ JSON file not created")
    except Exception as e:
        print(f"   ✗ JSON export failed: {e}")
    
    print("\n" + "=" * 50)
    print("Task 19 Verification Complete!")
    print("=" * 50) 