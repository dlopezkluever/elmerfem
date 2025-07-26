#!/usr/bin/env python3
"""
Performance tests for Educational Mesh Generator Python wrapper

This script tests the performance of the Python wrapper to ensure it meets
the sub-50ms overhead requirement for mesh generation.
"""

import time
import statistics
import sys
from pathlib import Path
import tempfile
import shutil
from educational_mesh_generator_wrapper import (
    EducationalMeshGenerator, 
    MeshDensity,
    GeometryType
)


def measure_overhead(generator, n_runs=100):
    """Measure the Python wrapper overhead"""
    
    print("\n" + "="*60)
    print("PERFORMANCE TEST: Python Wrapper Overhead")
    print("="*60)
    
    # Test configurations
    test_cases = [
        ('Rectangle Small', 'rectangle', {'width': 1.0, 'height': 1.0}, MeshDensity.COARSE),
        ('Rectangle Medium', 'rectangle', {'width': 2.0, 'height': 1.0}, MeshDensity.MEDIUM),
        ('Rectangle Large', 'rectangle', {'width': 5.0, 'height': 5.0}, MeshDensity.FINE),
        ('Circle Small', 'circle', {'radius': 1.0}, MeshDensity.COARSE),
        ('Circle Large', 'circle', {'radius': 3.0}, MeshDensity.FINE),
        ('Annulus', 'annulus', {'inner_radius': 0.5, 'outer_radius': 1.5}, MeshDensity.MEDIUM),
        ('L-Shape', 'l_shape', {'width': 2.0, 'height': 2.0, 'cutout_width': 1.0, 'cutout_height': 1.0}, MeshDensity.MEDIUM)
    ]
    
    results = {}
    
    # Create temporary directory for all tests
    with tempfile.TemporaryDirectory() as temp_base:
        temp_base = Path(temp_base)
        
        for test_name, geom_type, params, density in test_cases:
            print(f"\nTesting: {test_name}")
            print(f"  Geometry: {geom_type}")
            print(f"  Parameters: {params}")
            print(f"  Density: {density.name}")
            
            times = []
            
            # Warm-up run
            output_dir = temp_base / "warmup"
            generator.generate_mesh(geom_type, params, output_dir, density)
            shutil.rmtree(output_dir)
            
            # Measure multiple runs
            for i in range(n_runs):
                output_dir = temp_base / f"run_{i}"
                
                start = time.perf_counter()
                success, quality = generator.generate_mesh(geom_type, params, output_dir, density)
                end = time.perf_counter()
                
                if not success:
                    print(f"  ERROR: Mesh generation failed on run {i}")
                    continue
                
                elapsed_ms = (end - start) * 1000
                times.append(elapsed_ms)
                
                # Clean up after each run
                shutil.rmtree(output_dir)
            
            if times:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                std_dev = statistics.stdev(times) if len(times) > 1 else 0
                
                results[test_name] = {
                    'avg': avg_time,
                    'min': min_time,
                    'max': max_time,
                    'std': std_dev,
                    'samples': len(times)
                }
                
                print(f"  Results ({len(times)} runs):")
                print(f"    Average: {avg_time:.2f} ms")
                print(f"    Min:     {min_time:.2f} ms")
                print(f"    Max:     {max_time:.2f} ms")
                print(f"    Std Dev: {std_dev:.2f} ms")
                
                # Check if meeting 50ms target
                if avg_time > 50:
                    print(f"    WARNING: Average time exceeds 50ms target!")
    
    return results


def measure_fortran_baseline():
    """Measure direct Fortran library call time for comparison"""
    
    print("\n" + "="*60)
    print("BASELINE TEST: Direct Fortran Library Calls")
    print("="*60)
    
    import ctypes
    from educational_mesh_generator_wrapper import GeometryParams, MeshQuality
    
    # Load library directly
    lib_path = Path(__file__).parent / "libeducational_mesh.so"
    if not lib_path.exists():
        print(f"ERROR: Library not found at {lib_path}")
        return None
    
    lib = ctypes.CDLL(str(lib_path))
    generate_mesh = lib.generate_mesh
    generate_mesh.argtypes = [
        ctypes.POINTER(GeometryParams),
        ctypes.c_char_p,
        ctypes.POINTER(MeshQuality)
    ]
    
    # Test simple rectangle
    geometry = GeometryParams()
    geometry.geometry_type = 1  # Rectangle
    geometry.params[0] = 1.0
    geometry.params[1] = 1.0
    geometry.mesh_density = 3
    geometry.boundary_layer = 0
    
    quality = MeshQuality()
    
    times = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        
        # Warm-up
        generate_mesh(
            ctypes.byref(geometry),
            str(temp_dir).encode('utf-8'),
            ctypes.byref(quality)
        )
        
        # Measure
        for i in range(100):
            start = time.perf_counter()
            generate_mesh(
                ctypes.byref(geometry),
                str(temp_dir).encode('utf-8'),
                ctypes.byref(quality)
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)
    
    avg_time = statistics.mean(times)
    print(f"Direct Fortran call average: {avg_time:.2f} ms")
    
    return avg_time


def test_error_handling():
    """Test error handling performance"""
    
    print("\n" + "="*60)
    print("ERROR HANDLING TEST")
    print("="*60)
    
    generator = EducationalMeshGenerator()
    
    # Test invalid geometry type
    print("\nTesting invalid geometry type...")
    start = time.perf_counter()
    try:
        generator.generate_mesh('invalid_shape', {}, '/tmp/test')
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  Exception raised in {elapsed:.2f} ms: {type(e).__name__}")
    
    # Test invalid parameters
    print("\nTesting invalid parameters...")
    start = time.perf_counter()
    try:
        generator.generate_mesh('rectangle', {'width': -1, 'height': 1}, '/tmp/test')
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  Exception raised in {elapsed:.2f} ms: {type(e).__name__}")
    
    # Test missing parameters
    print("\nTesting missing parameters...")
    start = time.perf_counter()
    try:
        generator.generate_mesh('circle', {}, '/tmp/test')
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  Exception raised in {elapsed:.2f} ms: {type(e).__name__}")


def test_concurrent_generation():
    """Test concurrent mesh generation performance"""
    
    print("\n" + "="*60)
    print("CONCURRENCY TEST")
    print("="*60)
    
    import threading
    import concurrent.futures
    
    generator = EducationalMeshGenerator()
    
    def generate_mesh_thread(thread_id, output_dir):
        """Generate a mesh in a thread"""
        start = time.perf_counter()
        success, quality = generator.generate_mesh(
            'rectangle',
            {'width': 1.0, 'height': 1.0},
            output_dir,
            MeshDensity.MEDIUM
        )
        elapsed = (time.perf_counter() - start) * 1000
        return thread_id, success, elapsed
    
    # Test with multiple threads
    n_threads = 4
    with tempfile.TemporaryDirectory() as temp_base:
        temp_base = Path(temp_base)
        
        print(f"\nRunning {n_threads} concurrent mesh generations...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = []
            for i in range(n_threads):
                output_dir = temp_base / f"thread_{i}"
                future = executor.submit(generate_mesh_thread, i, output_dir)
                futures.append(future)
            
            results = [future.result() for future in futures]
        
        for thread_id, success, elapsed in results:
            print(f"  Thread {thread_id}: {'Success' if success else 'Failed'} in {elapsed:.2f} ms")


def main():
    """Run all performance tests"""
    
    print("Educational Mesh Generator - Performance Test Suite")
    print("Testing Python wrapper overhead and performance characteristics")
    
    # Initialize generator
    try:
        generator = EducationalMeshGenerator()
    except Exception as e:
        print(f"ERROR: Failed to initialize generator: {e}")
        return 1
    
    # Run tests
    try:
        # Baseline test
        baseline_time = measure_fortran_baseline()
        
        # Wrapper overhead test
        results = measure_overhead(generator, n_runs=50)
        
        # Error handling test
        test_error_handling()
        
        # Concurrency test
        test_concurrent_generation()
        
        # Summary
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        
        if baseline_time:
            print(f"\nDirect Fortran baseline: {baseline_time:.2f} ms")
        
        print("\nPython wrapper times:")
        all_passed = True
        for test_name, stats in results.items():
            status = "PASS" if stats['avg'] < 50 else "FAIL"
            if stats['avg'] >= 50:
                all_passed = False
            print(f"  {test_name}: {stats['avg']:.2f} ms [{status}]")
        
        if baseline_time and results:
            # Calculate average overhead
            wrapper_avg = statistics.mean([s['avg'] for s in results.values()])
            overhead = wrapper_avg - baseline_time
            print(f"\nAverage Python overhead: {overhead:.2f} ms")
        
        # Get generator's own stats
        perf_stats = generator.get_performance_stats()
        print(f"\nGenerator statistics:")
        print(f"  Total calls: {perf_stats['total_calls']}")
        print(f"  Average time: {perf_stats['average_time']:.2f} ms")
        print(f"  Min time: {perf_stats['min_time']:.2f} ms")
        print(f"  Max time: {perf_stats['max_time']:.2f} ms")
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\nERROR: Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 