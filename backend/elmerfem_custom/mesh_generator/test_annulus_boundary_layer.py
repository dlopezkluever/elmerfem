#!/usr/bin/env python3
"""
Detailed test for Task 17.3 - Boundary Layer Mesh with ratio 1.2
"""

import os
import sys
import ctypes
import math

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    """Load the shared library"""
    lib_path = os.path.join(os.path.dirname(__file__), "libeducational_mesh.so")
    if not os.path.exists(lib_path):
        print("Library not found. Building...")
        os.system("make")
    
    lib = ctypes.CDLL(lib_path)
    
    # Define function signature
    lib.generate_mesh.argtypes = [
        ctypes.POINTER(GeometryParams),
        ctypes.c_char_p,
        ctypes.POINTER(MeshQuality)
    ]
    lib.generate_mesh.restype = None
    
    return lib

def test_boundary_layer_detail():
    """Test boundary layer implementation in detail"""
    lib = load_library()
    
    # Test parameters
    inner_radius = 0.5
    outer_radius = 1.0
    density = 3
    
    output_dir = "test_boundary_layer_detail"
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Setup geometry parameters
    geometry = GeometryParams()
    geometry.geometry_type = 3  # annulus
    geometry.params[0] = inner_radius
    geometry.params[1] = outer_radius
    geometry.mesh_density = density
    geometry.boundary_layer = 1  # Enable boundary layer
    
    # Setup quality structure
    quality = MeshQuality()
    
    # Generate mesh
    lib.generate_mesh(
        ctypes.byref(geometry),
        output_dir.encode('utf-8'),
        ctypes.byref(quality)
    )
    
    print("Task 17.3 - Boundary Layer Validation")
    print("="*50)
    print(f"Inner radius: {inner_radius}")
    print(f"Outer radius: {outer_radius}")
    print(f"Mesh density: {density}")
    print(f"Expected growth ratio: 1.2")
    print()
    
    # Read nodes and extract radial layers
    nodes_file = os.path.join(output_dir, "mesh.nodes")
    if not os.path.exists(nodes_file):
        print("ERROR: mesh.nodes not found")
        return
    
    # Dictionary to store unique radii
    radii_dict = {}
    
    with open(nodes_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                x = float(parts[2])
                y = float(parts[3])
                r = math.sqrt(x*x + y*y)
                # Round to 6 decimal places to group similar radii
                r_rounded = round(r, 6)
                if r_rounded not in radii_dict:
                    radii_dict[r_rounded] = 0
                radii_dict[r_rounded] += 1
    
    # Sort unique radii
    unique_radii = sorted(radii_dict.keys())
    
    print(f"Number of radial layers found: {len(unique_radii)}")
    print(f"Expected radial layers: {5 * density + 1}")
    print()
    
    # Calculate and display spacings
    print("Radial positions and spacings:")
    print("-"*50)
    print("Layer | Radius      | Spacing    | Ratio")
    print("-"*50)
    
    spacings = []
    ratios = []
    
    for i, r in enumerate(unique_radii):
        if i == 0:
            print(f"{i:5d} | {r:11.6f} |            |")
        else:
            spacing = r - unique_radii[i-1]
            spacings.append(spacing)
            
            if i > 1:
                ratio = spacing / spacings[i-2]
                ratios.append(ratio)
                print(f"{i:5d} | {r:11.6f} | {spacing:10.6f} | {ratio:6.3f}")
            else:
                print(f"{i:5d} | {r:11.6f} | {spacing:10.6f} |")
    
    print("-"*50)
    
    # Analyze ratios
    if len(ratios) > 0:
        avg_ratio = sum(ratios) / len(ratios)
        min_ratio = min(ratios)
        max_ratio = max(ratios)
        
        print()
        print("Ratio Analysis:")
        print(f"  Average ratio: {avg_ratio:.3f}")
        print(f"  Min ratio: {min_ratio:.3f}")
        print(f"  Max ratio: {max_ratio:.3f}")
        print(f"  Expected: 1.200")
        
        # Check if ratios are close to 1.2
        tolerance = 0.05
        if all(abs(r - 1.2) < tolerance for r in ratios):
            print("\n✓ Boundary layer ratio is CORRECT (within tolerance)")
        else:
            print("\n✗ Boundary layer ratio is INCORRECT")
    
    # Verify inner and outer radii
    print()
    print("Boundary Validation:")
    print(f"  Inner radius: {unique_radii[0]:.6f} (expected: {inner_radius:.6f})")
    print(f"  Outer radius: {unique_radii[-1]:.6f} (expected: {outer_radius:.6f})")
    
    if abs(unique_radii[0] - inner_radius) < 1e-6:
        print("  ✓ Inner radius correct")
    else:
        print("  ✗ Inner radius incorrect")
        
    if abs(unique_radii[-1] - outer_radius) < 1e-6:
        print("  ✓ Outer radius correct")
    else:
        print("  ✗ Outer radius incorrect")

if __name__ == "__main__":
    test_boundary_layer_detail() 