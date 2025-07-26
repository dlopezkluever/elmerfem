#!/usr/bin/env python3
"""
Test small rectangle mesh with boundary layers to check nodes file generation
"""

import ctypes
import os
import tempfile

# Load the shared library
lib_path = os.path.join(os.path.dirname(__file__), 'libeducational_mesh.so')
lib = ctypes.CDLL(lib_path)

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

# Configure function
lib.generate_mesh.argtypes = [ctypes.POINTER(GeometryParams), 
                               ctypes.c_char_p,
                               ctypes.POINTER(MeshQuality)]

# Test small rectangle with boundary layers
with tempfile.TemporaryDirectory() as temp_dir:
    geometry = GeometryParams()
    geometry.geometry_type = 1  # Rectangle
    geometry.params[0] = 1.0    # width
    geometry.params[1] = 0.5    # height
    geometry.mesh_density = 10  # Small mesh
    geometry.boundary_layer = 1  # Enable boundary layers
    
    quality = MeshQuality()
    lib.generate_mesh(ctypes.byref(geometry), 
                     temp_dir.encode('utf-8'),
                     ctypes.byref(quality))
    
    print(f"Mesh generation result: {quality.return_code}")
    print(f"Elements: {quality.total_elements}")
    print(f"Nodes: {quality.total_nodes}")
    
    # Check files
    files = os.listdir(temp_dir)
    print(f"\nFiles created: {files}")
    
    for file in files:
        path = os.path.join(temp_dir, file)
        size = os.path.getsize(path)
        print(f"  {file}: {size} bytes")
        
        # Check first few lines of nodes file
        if file == "mesh.nodes" and size > 0:
            with open(path, 'r') as f:
                print(f"\n  First 5 lines of {file}:")
                for i in range(5):
                    line = f.readline().strip()
                    if line:
                        print(f"    {line}") 