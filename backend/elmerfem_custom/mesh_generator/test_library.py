#!/usr/bin/env python3
"""
Test script to verify the educational mesh generator library can be loaded and called
"""

import ctypes
import os
import sys
from pathlib import Path


def test_library_loading():
    """Test that the shared library can be loaded and the function can be called"""
    
    # Get the library path
    lib_path = Path(__file__).parent / "libeducational_mesh.so"
    
    if not lib_path.exists():
        print(f"ERROR: Library not found at {lib_path}")
        print("Please run 'make' to build the library first")
        return False
    
    try:
        # Load the shared library
        lib = ctypes.CDLL(str(lib_path))
        print(f"✓ Successfully loaded library: {lib_path}")
        
        # Define the structures matching Fortran types
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
        
        # Get the function
        generate_mesh = lib.generate_mesh
        generate_mesh.argtypes = [
            ctypes.POINTER(GeometryParams),
            ctypes.c_char_p,
            ctypes.POINTER(MeshQuality)
        ]
        generate_mesh.restype = None
        
        print("✓ Successfully retrieved 'generate_mesh' function")
        
        # Create test parameters
        geometry = GeometryParams()
        geometry.geometry_type = 1  # Rectangle
        geometry.params[0] = 1.0    # Width
        geometry.params[1] = 1.0    # Height
        geometry.mesh_density = 3   # Medium density
        geometry.boundary_layer = 0 # No boundary layer
        
        # Create output structure
        quality = MeshQuality()
        
        # Create test output directory
        test_dir = Path("/tmp/test_mesh")
        test_dir.mkdir(exist_ok=True)
        
        # Call the function
        print("\nCalling generate_mesh with rectangle geometry...")
        generate_mesh(
            ctypes.byref(geometry),
            str(test_dir).encode('utf-8'),
            ctypes.byref(quality)
        )
        
        # Check results
        print(f"\n✓ Function call completed with return code: {quality.return_code}")
        print(f"  Total elements: {quality.total_elements}")
        print(f"  Total nodes: {quality.total_nodes}")
        print(f"  Min angle: {quality.min_angle}")
        print(f"  Max angle: {quality.max_angle}")
        print(f"  Avg aspect ratio: {quality.aspect_ratio_avg}")
        print(f"  Max aspect ratio: {quality.aspect_ratio_max}")
        
        # Check if mesh files were created
        if quality.return_code == 0:
            mesh_header = test_dir / "mesh.header"
            mesh_nodes = test_dir / "mesh.nodes"
            
            if mesh_header.exists():
                print(f"\n✓ Created mesh.header file")
            if mesh_nodes.exists():
                print(f"✓ Created mesh.nodes file")
        
        return quality.return_code == 0
        
    except Exception as e:
        print(f"ERROR: Failed to load or call library: {e}")
        return False


if __name__ == "__main__":
    print("Educational Mesh Generator Library Test")
    print("=" * 40)
    
    success = test_library_loading()
    
    if success:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Tests failed!")
        sys.exit(1)
