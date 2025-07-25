#!/usr/bin/env python3
"""Test program for the educational rectangle mesh generator"""

import ctypes
import os
import shutil
import time
from pathlib import Path

# Define the C-compatible structures
class GeometryParams(ctypes.Structure):
    _fields_ = [
        ("geometry_type", ctypes.c_int32),
        ("params", ctypes.c_double * 10),
        ("mesh_density", ctypes.c_int32),
        ("boundary_layer", ctypes.c_int32)
    ]

class MeshQuality(ctypes.Structure):
    _fields_ = [
        ("min_angle", ctypes.c_double),
        ("max_angle", ctypes.c_double),
        ("aspect_ratio_avg", ctypes.c_double),
        ("aspect_ratio_max", ctypes.c_double),
        ("total_elements", ctypes.c_int32),
        ("total_nodes", ctypes.c_int32),
        ("return_code", ctypes.c_int32)
    ]

def test_rectangle_mesh(width, height, density, output_dir):
    """Test rectangle mesh generation"""
    
    # Load the shared library
    lib_path = Path(__file__).parent / "libeducational_mesh.so"
    if not lib_path.exists():
        print(f"Error: Library not found at {lib_path}")
        print("Please run 'make' to build the library first")
        return False
    
    lib = ctypes.CDLL(str(lib_path))
    
    # Get the generate_mesh function
    generate_mesh = lib.generate_mesh
    generate_mesh.argtypes = [
        ctypes.POINTER(GeometryParams),
        ctypes.c_char_p,
        ctypes.POINTER(MeshQuality)
    ]
    generate_mesh.restype = None
    
    # Create geometry parameters
    geometry = GeometryParams()
    geometry.geometry_type = 1  # Rectangle
    geometry.params[0] = width
    geometry.params[1] = height
    geometry.mesh_density = density
    geometry.boundary_layer = 0
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create quality structure
    quality = MeshQuality()
    
    # Call the mesh generator and measure time
    start_time = time.time()
    generate_mesh(
        ctypes.byref(geometry),
        output_dir.encode('utf-8'),
        ctypes.byref(quality)
    )
    elapsed_time = time.time() - start_time
    
    # Print results
    print(f"\nRectangle Mesh Generation Test:")
    print(f"  Dimensions: {width} x {height}")
    print(f"  Density: {density}")
    print(f"  Output directory: {output_dir}")
    print(f"\nResults:")
    print(f"  Return code: {quality.return_code}")
    print(f"  Total nodes: {quality.total_nodes}")
    print(f"  Total elements: {quality.total_elements}")
    print(f"  Min angle: {quality.min_angle:.2f}°")
    print(f"  Max angle: {quality.max_angle:.2f}°")
    print(f"  Average aspect ratio: {quality.aspect_ratio_avg:.3f}")
    print(f"  Max aspect ratio: {quality.aspect_ratio_max:.3f}")
    print(f"  Generation time: {elapsed_time:.3f} seconds")
    
    # Verify files exist
    expected_files = ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']
    all_files_exist = True
    for filename in expected_files:
        filepath = Path(output_dir) / filename
        if filepath.exists():
            print(f"  ✓ {filename} ({filepath.stat().st_size} bytes)")
        else:
            print(f"  ✗ {filename} missing")
            all_files_exist = False
    
    # Validate mesh.header
    if all_files_exist:
        with open(Path(output_dir) / 'mesh.header', 'r') as f:
            header_line = f.readline().strip()
            nodes, elements, boundaries = map(int, header_line.split())
            print(f"\nMesh header validation:")
            print(f"  Nodes: {nodes} (expected: {quality.total_nodes})")
            print(f"  Elements: {elements} (expected: {quality.total_elements})")
            print(f"  Boundaries: {boundaries}")
            
            if nodes != quality.total_nodes or elements != quality.total_elements:
                print("  ERROR: Header counts don't match quality report!")
                return False
    
    return quality.return_code == 0 and all_files_exist

def performance_test():
    """Test performance for various mesh sizes"""
    print("\n" + "="*60)
    print("Performance Test for Rectangle Mesh Generation")
    print("="*60)
    
    test_cases = [
        # (width, height, density, description)
        (1.0, 1.0, 1, "Small square (10x10)"),
        (2.0, 1.0, 2, "Rectangle (40x20)"),
        (1.0, 1.0, 5, "Dense square (50x50)"),
        (4.0, 4.0, 5, "Large square (200x200)"),
        (8.0, 8.0, 5, "Very large square (400x400)"),
    ]
    
    for width, height, density, description in test_cases:
        output_dir = f"test_output_{int(width*10)}x{int(height*10)}_d{density}"
        
        # Clean up existing directory
        if Path(output_dir).exists():
            shutil.rmtree(output_dir)
        
        print(f"\nTest: {description}")
        success = test_rectangle_mesh(width, height, density, output_dir)
        
        if success:
            # Calculate expected elements
            nx = max(2, int(10 * density * width))
            ny = max(2, int(10 * density * height))
            expected_elements = nx * ny
            print(f"  Expected elements: {expected_elements} ({nx}x{ny})")
        
        # Clean up
        if Path(output_dir).exists():
            shutil.rmtree(output_dir)

def validate_mesh_files(output_dir):
    """Validate the contents of mesh files"""
    print(f"\n{'='*60}")
    print(f"Validating mesh files in {output_dir}")
    print(f"{'='*60}")
    
    # Read mesh.header
    with open(Path(output_dir) / 'mesh.header', 'r') as f:
        lines = f.readlines()
        nodes, elements, boundaries = map(int, lines[0].split())
        num_types = int(lines[1])
        print(f"\nMesh header:")
        print(f"  Nodes: {nodes}")
        print(f"  Elements: {elements}")
        print(f"  Boundaries: {boundaries}")
        print(f"  Element types: {num_types}")
        
        for i in range(num_types):
            elem_type, count = map(int, lines[2+i].split())
            print(f"    Type {elem_type}: {count} elements")
    
    # Sample first few nodes
    print(f"\nFirst 5 nodes:")
    with open(Path(output_dir) / 'mesh.nodes', 'r') as f:
        for i in range(min(5, nodes)):
            line = f.readline().strip()
            parts = line.split()
            node_id = int(parts[0])
            boundary_tag = int(parts[1])
            x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
            print(f"  Node {node_id}: ({x:.6f}, {y:.6f}, {z:.6f}) [tag: {boundary_tag}]")
    
    # Sample first few elements
    print(f"\nFirst 5 elements:")
    with open(Path(output_dir) / 'mesh.elements', 'r') as f:
        for i in range(min(5, elements)):
            line = f.readline().strip()
            parts = line.split()
            elem_id = int(parts[0])
            material = int(parts[1])
            elem_type = int(parts[2])
            nodes = [int(parts[j]) for j in range(3, len(parts))]
            print(f"  Element {elem_id}: material={material}, type={elem_type}, nodes={nodes}")
    
    # Sample boundary elements
    print(f"\nFirst 5 boundary elements:")
    with open(Path(output_dir) / 'mesh.boundary', 'r') as f:
        for i in range(min(5, boundaries)):
            line = f.readline().strip()
            parts = line.split()
            bc_id = int(parts[0])
            bc_type = int(parts[1])
            parent1 = int(parts[2])
            parent2 = int(parts[3])
            elem_type = int(parts[4])
            nodes = [int(parts[j]) for j in range(5, len(parts))]
            print(f"  Boundary {bc_id}: type={bc_type}, parents=({parent1},{parent2}), " + 
                  f"elem_type={elem_type}, nodes={nodes}")

if __name__ == "__main__":
    # First compile the library if needed
    if not Path("libeducational_mesh.so").exists():
        print("Library not found. Building...")
        os.system("make")
    
    # Run a basic test
    print("Running basic rectangle mesh test...")
    test_dir = "test_rectangle_output"
    if Path(test_dir).exists():
        shutil.rmtree(test_dir)
    
    success = test_rectangle_mesh(2.0, 1.0, 3, test_dir)
    
    if success:
        validate_mesh_files(test_dir)
    
    # Run performance tests
    performance_test()
    
    # Clean up test directory
    if Path(test_dir).exists():
        shutil.rmtree(test_dir)
    
    print("\nAll tests completed!") 