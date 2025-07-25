#!/usr/bin/env python3
"""
Test script that generates mesh files and displays their contents
"""

import ctypes
import os
import tempfile
from pathlib import Path


def test_and_display():
    """Test mesh generation and display the generated files"""
    
    # Load the library
    lib_path = Path(__file__).parent / "libeducational_mesh.so"
    lib = ctypes.CDLL(str(lib_path))
    
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
    generate_mesh.restype = None
    
    # Create parameters for a small rectangle
    geometry = GeometryParams()
    geometry.geometry_type = 1  # Rectangle
    geometry.params[0] = 2.0    # Width
    geometry.params[1] = 1.0    # Height  
    geometry.mesh_density = 1   # Low density for readable output
    geometry.boundary_layer = 0
    
    quality = MeshQuality()
    
    # Use a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Generating mesh in: {tmpdir}")
        
        # Generate mesh
        generate_mesh(
            ctypes.byref(geometry),
            tmpdir.encode('utf-8'),
            ctypes.byref(quality)
        )
        
        print(f"\nMesh generation completed:")
        print(f"  Return code: {quality.return_code}")
        print(f"  Elements: {quality.total_elements}")
        print(f"  Nodes: {quality.total_nodes}")
        
        # Display mesh.header
        header_file = Path(tmpdir) / "mesh.header"
        if header_file.exists():
            print("\n=== mesh.header ===")
            print(header_file.read_text())
        
        # Display mesh.nodes
        nodes_file = Path(tmpdir) / "mesh.nodes"
        if nodes_file.exists():
            print("\n=== mesh.nodes ===")
            print(nodes_file.read_text())
        
        # Check for other expected files
        print("\n=== Files created ===")
        for f in Path(tmpdir).iterdir():
            print(f"  {f.name}")


if __name__ == "__main__":
    test_and_display()
