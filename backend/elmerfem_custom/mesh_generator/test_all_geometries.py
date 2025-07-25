#!/usr/bin/env python3
"""
Test all geometry types in the educational mesh generator
"""

import ctypes
from pathlib import Path


def test_all_geometries():
    """Test mesh generation for all supported geometry types"""
    
    # Load library
    lib = ctypes.CDLL(str(Path(__file__).parent / "libeducational_mesh.so"))
    
    # Define structures
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
    
    # Set up function
    generate_mesh = lib.generate_mesh
    generate_mesh.argtypes = [
        ctypes.POINTER(GeometryParams),
        ctypes.c_char_p,
        ctypes.POINTER(MeshQuality)
    ]
    
    # Test configurations
    test_cases = [
        {
            "name": "Rectangle",
            "type": 1,
            "params": [2.0, 1.0],  # width, height
            "expected_elements": 200
        },
        {
            "name": "Circle", 
            "type": 2,
            "params": [1.0],  # radius
            "expected_elements": 100
        },
        {
            "name": "Annulus",
            "type": 3,
            "params": [0.5, 1.0],  # inner radius, outer radius
            "expected_elements": 200
        },
        {
            "name": "L-Shape",
            "type": 4,
            "params": [2.0, 2.0, 1.0, 1.0],  # outer width/height, cutout width/height
            "expected_elements": 150
        }
    ]
    
    print("Testing all geometry types:")
    print("=" * 50)
    
    all_passed = True
    
    for test in test_cases:
        geometry = GeometryParams()
        geometry.geometry_type = test["type"]
        geometry.mesh_density = 1
        geometry.boundary_layer = 0
        
        # Set parameters
        for i, param in enumerate(test["params"]):
            geometry.params[i] = param
        
        quality = MeshQuality()
        
        # Generate mesh
        generate_mesh(
            ctypes.byref(geometry),
            b"/tmp/test",
            ctypes.byref(quality)
        )
        
        # Check results
        passed = quality.return_code == 0
        all_passed &= passed
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"\n{test['name']:15} {status}")
        print(f"  Return code: {quality.return_code}")
        print(f"  Elements: {quality.total_elements}")
        print(f"  Nodes: {quality.total_nodes}")
        
        if quality.return_code != 0:
            print(f"  ERROR: Mesh generation failed!")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All geometry types passed!")
    else:
        print("✗ Some tests failed!")
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = test_all_geometries()
    sys.exit(0 if success else 1)
