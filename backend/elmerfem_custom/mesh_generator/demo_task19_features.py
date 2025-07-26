#!/usr/bin/env python3
"""
Demonstration of Task 19: Mesh Quality & Optimization Features
Shows all implemented functionality: quality analysis, smoothing, JSON export
"""

import ctypes
import json
import os
import tempfile
import shutil
from pathlib import Path

class MeshQuality(ctypes.Structure):
    """Mesh quality metrics structure"""
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
    """Geometry parameters structure"""
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

def load_library():
    """Load the educational mesh generator library"""
    lib_path = "/app/elmerfem_custom/mesh_generator/libeducational_mesh.so"
    lib = ctypes.CDLL(lib_path)
    
    # Configure function signatures
    lib.generate_mesh.argtypes = [
        ctypes.POINTER(GeometryParams),
        ctypes.c_char_p,
        ctypes.POINTER(MeshQuality)
    ]
    lib.generate_mesh.restype = None
    
    # Task 19.1: ComputeQuality
    lib.__educationalmeshgenerator_MOD_computequality.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(MeshQuality)
    ]
    lib.__educationalmeshgenerator_MOD_computequality.restype = None
    
    # Task 19.2: ApplyLaplacianSmoothing
    lib.__educationalmeshgenerator_MOD_applylaplaciansmoothing.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_double)
    ]
    lib.__educationalmeshgenerator_MOD_applylaplaciansmoothing.restype = None
    
    # Task 19.4: ExportQualityJSON
    lib.__educationalmeshgenerator_MOD_exportqualityjson.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(MeshQuality),
        ctypes.c_char_p
    ]
    lib.__educationalmeshgenerator_MOD_exportqualityjson.restype = None
    
    return lib

def demonstrate_task_19():
    """Demonstrate all Task 19 features"""
    print("=" * 70)
    print("Task 19: Mesh Quality & Optimization - Feature Demonstration")
    print("=" * 70)
    
    lib = load_library()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\nWorking directory: {temp_dir}")
        
        # Step 1: Generate a test mesh (rectangle with aspect ratio issues)
        print("\n1. Generating test mesh with aspect ratio issues...")
        params = GeometryParams(
            geometry_type=1,  # Rectangle
            dim1=2.0,         # Width
            dim2=1.0,         # Height  
            dim3=0.0, dim4=0.0,
            nx=20,            # More divisions in X
            ny=5,             # Fewer in Y (creates aspect ratio issues)
            boundary_layer=0,
            boundary_thickness=0.0,
            return_code=0
        )
        
        output_dir = ctypes.c_char_p(temp_dir.encode('utf-8'))
        initial_quality = MeshQuality()
        
        lib.generate_mesh(ctypes.byref(params), output_dir, ctypes.byref(initial_quality))
        
        if initial_quality.return_code == 0:
            print(f"   ✓ Generated mesh: {initial_quality.total_nodes} nodes, {initial_quality.total_elements} elements")
        
        # Step 2: Task 19.1 - Compute initial quality
        print("\n2. Task 19.1 - Computing initial mesh quality...")
        quality_before = MeshQuality()
        lib.__educationalmeshgenerator_MOD_computequality(output_dir, ctypes.byref(quality_before))
        
        print(f"   Initial quality metrics:")
        print(f"   - Min angle: {quality_before.min_angle:.1f}°")
        print(f"   - Max angle: {quality_before.max_angle:.1f}°")
        print(f"   - Average aspect ratio: {quality_before.aspect_ratio_avg:.3f}")
        print(f"   - Max aspect ratio: {quality_before.aspect_ratio_max:.3f}")
        
        # Step 3: Task 19.2 & 19.3 - Apply Laplacian smoothing with boundary constraints
        print("\n3. Task 19.2/19.3 - Applying Laplacian smoothing...")
        print("   (Interior nodes will be optimized, boundary nodes remain fixed)")
        
        iterations = ctypes.c_int(20)
        omega = ctypes.c_double(0.5)
        lib.__educationalmeshgenerator_MOD_applylaplaciansmoothing(output_dir, ctypes.byref(iterations), ctypes.byref(omega))
        print(f"   ✓ Applied {iterations.value} smoothing iterations with ω={omega.value}")
        
        # Step 4: Compute quality after smoothing
        print("\n4. Computing quality after smoothing...")
        quality_after = MeshQuality()
        lib.__educationalmeshgenerator_MOD_computequality(output_dir, ctypes.byref(quality_after))
        
        print(f"   Improved quality metrics:")
        print(f"   - Min angle: {quality_after.min_angle:.1f}° (was {quality_before.min_angle:.1f}°)")
        print(f"   - Max angle: {quality_after.max_angle:.1f}° (was {quality_before.max_angle:.1f}°)")
        print(f"   - Average aspect ratio: {quality_after.aspect_ratio_avg:.3f} (was {quality_before.aspect_ratio_avg:.3f})")
        print(f"   - Max aspect ratio: {quality_after.aspect_ratio_max:.3f} (was {quality_before.aspect_ratio_max:.3f})")
        
        # Step 5: Task 19.4 - Export quality to JSON
        print("\n5. Task 19.4 - Exporting quality metrics to JSON...")
        json_file = os.path.join(temp_dir, "mesh_quality.json")
        lib.__educationalmeshgenerator_MOD_exportqualityjson(
            output_dir,
            ctypes.byref(quality_after),
            ctypes.c_char_p("optimized_mesh".encode('utf-8'))
        )
        
        # Read and display JSON content
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                quality_data = json.load(f)
            
            print("   JSON export content:")
            print(json.dumps(quality_data, indent=4))
            print(f"   ✓ Quality data exported to: {json_file}")
        
        # Step 6: Demonstrate different geometry types
        print("\n6. Testing quality analysis on different geometries...")
        
        geometries = [
            ("Circle", 2, 1.0, 0, 0, 0, 10, 24),
            ("Annulus", 3, 0.5, 1.0, 0, 0, 8, 16),
            ("L-Shape", 4, 2.0, 2.0, 0.5, 0.5, 15, 15)
        ]
        
        for name, geom_type, d1, d2, d3, d4, nx, ny in geometries:
            params = GeometryParams(
                geometry_type=geom_type,
                dim1=d1, dim2=d2, dim3=d3, dim4=d4,
                nx=nx, ny=ny,
                boundary_layer=0,
                boundary_thickness=0.0,
                return_code=0
            )
            
            quality = MeshQuality()
            lib.generate_mesh(ctypes.byref(params), output_dir, ctypes.byref(quality))
            
            if quality.return_code == 0:
                lib.__educationalmeshgenerator_MOD_computequality(output_dir, ctypes.byref(quality))
                print(f"\n   {name} mesh quality:")
                print(f"   - Elements: {quality.total_elements}, Nodes: {quality.total_nodes}")
                print(f"   - Angles: [{quality.min_angle:.1f}°, {quality.max_angle:.1f}°]")
                print(f"   - Aspect ratio: avg={quality.aspect_ratio_avg:.2f}, max={quality.aspect_ratio_max:.2f}")
        
        print("\n" + "=" * 70)
        print("✓ All Task 19 features demonstrated successfully!")
        print("=" * 70)

if __name__ == "__main__":
    demonstrate_task_19() 