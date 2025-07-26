#!/usr/bin/env python3
"""
Test Task 20.5: Performance Benchmarking and Optimization
Benchmarks mesh generation performance for different geometries and configurations
"""

import ctypes
import os
import tempfile
import time
import numpy as np
import matplotlib.pyplot as plt

# Load the shared library
lib_path = os.path.join(os.path.dirname(__file__), 'libeducational_mesh.so')
if not os.path.exists(lib_path):
    print(f"Error: Library not found at {lib_path}")
    print("Please run 'make' first to build the library")
    exit(1)

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

# Set up function signatures
generate_mesh = lib.generate_mesh
generate_mesh.argtypes = [
    ctypes.POINTER(GeometryParams),
    ctypes.c_char_p,
    ctypes.POINTER(MeshQuality)
]
generate_mesh.restype = None

# Try to load benchmark function if available
try:
    benchmark_mesh = lib.BenchmarkMeshGeneration
    benchmark_mesh.argtypes = [ctypes.c_char_p]
    benchmark_mesh.restype = None
    has_benchmark = True
except:
    has_benchmark = False
    print("Note: BenchmarkMeshGeneration not found in library")

def benchmark_geometry(geom_type, geom_name, params, densities):
    """Benchmark a single geometry type with various densities"""
    results = {
        'densities': [],
        'elements': [],
        'nodes': [],
        'times': [],
        'elements_per_sec': []
    }
    
    print(f"\nBenchmarking {geom_name}:")
    print("-" * 50)
    print("Density | Elements |   Nodes  |  Time(s) | Elem/s")
    print("-" * 50)
    
    for density in densities:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up geometry
            geom = GeometryParams()
            geom.geometry_type = geom_type
            for i, p in enumerate(params):
                geom.params[i] = p
            geom.mesh_density = density
            geom.boundary_layer = 0  # No boundary layers for base benchmark
            
            quality = MeshQuality()
            
            # Time the mesh generation
            start_time = time.time()
            output_dir = temp_dir.encode('utf-8')
            generate_mesh(ctypes.byref(geom), output_dir, ctypes.byref(quality))
            end_time = time.time()
            
            elapsed = end_time - start_time
            
            if quality.return_code == 0:
                elem_per_sec = quality.total_elements / elapsed
                
                print(f"   {density:2d}   | {quality.total_elements:8d} | {quality.total_nodes:8d} | {elapsed:8.4f} | {elem_per_sec:7.0f}")
                
                results['densities'].append(density)
                results['elements'].append(quality.total_elements)
                results['nodes'].append(quality.total_nodes)
                results['times'].append(elapsed)
                results['elements_per_sec'].append(elem_per_sec)
            else:
                print(f"   {density:2d}   |  FAILED  |")
    
    return results

def benchmark_boundary_layers():
    """Compare performance with and without boundary layers"""
    print("\n\nBoundary Layer Performance Comparison:")
    print("=" * 60)
    
    geometries = [
        (1, "Rectangle", [2.0, 1.0]),
        (2, "Circle", [1.0]),
        (3, "Annulus", [0.5, 1.0])
    ]
    
    density = 3
    results = []
    
    print("Geometry   | Type |  Elements  |   Time(s)  | Overhead")
    print("-" * 60)
    
    for geom_type, name, params in geometries:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Without boundary layers
            geom = GeometryParams()
            geom.geometry_type = geom_type
            for i, p in enumerate(params):
                geom.params[i] = p
            geom.mesh_density = density
            geom.boundary_layer = 0
            
            quality_no_bl = MeshQuality()
            
            start_time = time.time()
            output_dir = temp_dir.encode('utf-8')
            generate_mesh(ctypes.byref(geom), output_dir, ctypes.byref(quality_no_bl))
            time_no_bl = time.time() - start_time
            
            # With boundary layers
            geom.boundary_layer = 1
            quality_bl = MeshQuality()
            
            bl_dir = os.path.join(temp_dir, 'bl')
            os.makedirs(bl_dir)
            
            start_time = time.time()
            output_dir_bl = bl_dir.encode('utf-8')
            generate_mesh(ctypes.byref(geom), output_dir_bl, ctypes.byref(quality_bl))
            time_bl = time.time() - start_time
            
            overhead = (time_bl - time_no_bl) / time_no_bl * 100
            
            print(f"{name:10s} | No BL | {quality_no_bl.total_elements:10d} | {time_no_bl:10.4f} |")
            print(f"{' ':10s} | BL    | {quality_bl.total_elements:10d} | {time_bl:10.4f} | {overhead:+6.1f}%")
            
            results.append({
                'geometry': name,
                'time_no_bl': time_no_bl,
                'time_bl': time_bl,
                'elements_no_bl': quality_no_bl.total_elements,
                'elements_bl': quality_bl.total_elements
            })
    
    return results

def plot_performance_results(all_results):
    """Create performance visualization plots"""
    
    # Plot 1: Elements vs Time for different geometries
    plt.figure(figsize=(12, 8))
    
    colors = ['blue', 'red', 'green', 'orange']
    markers = ['o', 's', '^', 'D']
    
    for i, (geom_name, results) in enumerate(all_results.items()):
        plt.scatter(results['elements'], results['times'], 
                   color=colors[i], marker=markers[i], s=100, label=geom_name)
        
        # Fit power law
        if len(results['elements']) > 2:
            log_elem = np.log(results['elements'])
            log_time = np.log(results['times'])
            coeffs = np.polyfit(log_elem, log_time, 1)
            
            # Plot fit line
            elem_fit = np.linspace(min(results['elements']), max(results['elements']), 100)
            time_fit = np.exp(coeffs[1]) * elem_fit ** coeffs[0]
            plt.plot(elem_fit, time_fit, color=colors[i], linestyle='--', alpha=0.5)
            
            print(f"\n{geom_name}: Time ∝ Elements^{coeffs[0]:.2f}")
    
    plt.xlabel('Number of Elements')
    plt.ylabel('Generation Time (seconds)')
    plt.title('Mesh Generation Performance')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xscale('log')
    plt.yscale('log')
    
    plt.savefig('performance_scaling.png', dpi=150, bbox_inches='tight')
    print("\nSaved plot: performance_scaling.png")
    
    # Plot 2: Elements per second vs density
    plt.figure(figsize=(12, 8))
    
    for i, (geom_name, results) in enumerate(all_results.items()):
        plt.plot(results['densities'], results['elements_per_sec'], 
                color=colors[i], marker=markers[i], markersize=10, 
                linewidth=2, label=geom_name)
    
    plt.xlabel('Mesh Density')
    plt.ylabel('Elements per Second')
    plt.title('Mesh Generation Throughput')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig('performance_throughput.png', dpi=150, bbox_inches='tight')
    print("Saved plot: performance_throughput.png")

def analyze_memory_efficiency():
    """Analyze memory usage patterns"""
    print("\n\nMemory Efficiency Analysis:")
    print("=" * 50)
    
    # Test large meshes
    large_mesh_results = []
    
    for density in [5, 10, 15]:
        with tempfile.TemporaryDirectory() as temp_dir:
            geom = GeometryParams()
            geom.geometry_type = 1  # Rectangle
            geom.params[0] = 1.0
            geom.params[1] = 1.0
            geom.mesh_density = density
            geom.boundary_layer = 0
            
            quality = MeshQuality()
            
            output_dir = temp_dir.encode('utf-8')
            generate_mesh(ctypes.byref(geom), output_dir, ctypes.byref(quality))
            
            if quality.return_code == 0:
                # Check file sizes
                header_size = os.path.getsize(os.path.join(temp_dir, 'mesh.header'))
                nodes_size = os.path.getsize(os.path.join(temp_dir, 'mesh.nodes'))
                elements_size = os.path.getsize(os.path.join(temp_dir, 'mesh.elements'))
                boundary_size = os.path.getsize(os.path.join(temp_dir, 'mesh.boundary'))
                
                total_size = header_size + nodes_size + elements_size + boundary_size
                bytes_per_node = nodes_size / quality.total_nodes
                bytes_per_elem = elements_size / quality.total_elements
                
                print(f"\nDensity {density}:")
                print(f"  Total file size: {total_size / 1024:.1f} KB")
                print(f"  Bytes per node: {bytes_per_node:.1f}")
                print(f"  Bytes per element: {bytes_per_elem:.1f}")
                print(f"  Storage efficiency: {total_size / (quality.total_nodes + quality.total_elements):.1f} bytes/entity")

def main():
    """Run all performance benchmarks"""
    print("Task 20.5: Performance Benchmarking")
    print("=" * 70)
    
    # Define test configurations
    densities = [1, 2, 3, 4, 5]
    
    geometries = [
        (1, "Rectangle", [2.0, 1.0]),
        (2, "Circle", [1.0]),
        (3, "Annulus", [0.5, 1.0]),
        (4, "L-shape", [1.0, 1.0, 0.5, 0.5])
    ]
    
    # Run benchmarks
    all_results = {}
    
    for geom_type, geom_name, params in geometries:
        results = benchmark_geometry(geom_type, geom_name, params, densities)
        all_results[geom_name] = results
    
    # Boundary layer comparison
    bl_results = benchmark_boundary_layers()
    
    # Memory efficiency
    analyze_memory_efficiency()
    
    # Create visualizations
    plot_performance_results(all_results)
    
    # Call Fortran benchmark function if available
    if has_benchmark:
        print("\n\nRunning Fortran benchmark routine...")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = temp_dir.encode('utf-8')
            benchmark_mesh(output_dir)
            
            # Check if benchmark file was created
            bench_file = os.path.join(temp_dir, 'benchmark_results.txt')
            if os.path.exists(bench_file):
                print("\nFortran benchmark results:")
                with open(bench_file, 'r') as f:
                    print(f.read())
    
    # Summary statistics
    print("\n\nPerformance Summary:")
    print("=" * 50)
    
    total_elements = 0
    total_time = 0
    
    for geom_name, results in all_results.items():
        max_density_idx = -1  # Last density
        elem = results['elements'][max_density_idx]
        t = results['times'][max_density_idx]
        total_elements += elem
        total_time += t
        
        print(f"{geom_name:10s}: {elem:8d} elements in {t:6.3f}s ({elem/t:7.0f} elem/s)")
    
    print("-" * 50)
    print(f"Average throughput: {total_elements/total_time:7.0f} elements/second")
    
    # Target check
    target_elements = 5000
    target_time = 2.0  # seconds
    estimated_time = target_elements / (total_elements/total_time)
    
    print(f"\nTarget: {target_elements} elements in {target_time} seconds")
    print(f"Estimated time for target: {estimated_time:.3f} seconds")
    print(f"Target achieved: {'YES' if estimated_time <= target_time else 'NO'}")

if __name__ == "__main__":
    main() 