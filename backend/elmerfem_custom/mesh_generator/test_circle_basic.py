#!/usr/bin/env python3
"""Basic test for circle mesh generation"""

import os
import ctypes
import time

# Create output directory
output_dir = "test_circle_basic_output"
os.makedirs(output_dir, exist_ok=True)

# Load the library
lib_path = "./libeducational_mesh.so"
if not os.path.exists(lib_path):
    print(f"Library not found. Building...")
    os.system("make")

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

# Set up function
generate_mesh = lib.generate_mesh
generate_mesh.argtypes = [
    ctypes.POINTER(GeometryParams),
    ctypes.c_char_p,
    ctypes.POINTER(MeshQuality)
]

# Create circle parameters
geometry = GeometryParams()
geometry.geometry_type = 2  # Circle
geometry.params[0] = 1.0   # radius
geometry.mesh_density = 3
geometry.boundary_layer = 0

quality = MeshQuality()

# Generate mesh
print("Generating circle mesh...")
start = time.time()
generate_mesh(ctypes.byref(geometry), output_dir.encode('utf-8'), ctypes.byref(quality))
elapsed = time.time() - start

print(f"\nResults:")
print(f"  Return code: {quality.return_code}")
print(f"  Nodes: {quality.total_nodes}")
print(f"  Elements: {quality.total_elements}")
print(f"  Time: {elapsed:.3f}s")
print(f"  Min angle: {quality.min_angle:.1f}°")
print(f"  Max angle: {quality.max_angle:.1f}°")

# Check files
for fname in ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']:
    path = os.path.join(output_dir, fname)
    if os.path.exists(path):
        print(f"  ✓ {fname} ({os.path.getsize(path)} bytes)")
    else:
        print(f"  ✗ {fname} NOT FOUND")

if quality.return_code == 0:
    print("\n✓ Circle mesh generation successful!")
else:
    print("\n✗ Circle mesh generation failed!") 