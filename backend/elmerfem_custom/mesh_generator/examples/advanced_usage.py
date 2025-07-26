#!/usr/bin/env python3
"""
Advanced usage example for Educational Mesh Generator

This script demonstrates advanced features including:
- Error handling
- Performance optimization
- Batch processing
- Integration with simulation workflows
"""

import sys
import time
import asyncio
import json
from pathlib import Path
from typing import List, Dict
import concurrent.futures

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from educational_mesh_generator_wrapper import (
    EducationalMeshGenerator,
    MeshDensity,
    GeometryType,
    GeometryValidationError,
    MeshGenerationError,
    LibraryLoadError
)


class SimulationWorkflow:
    """Example of integrating mesh generator into a simulation workflow"""
    
    def __init__(self):
        try:
            self.generator = EducationalMeshGenerator()
            print("✓ Mesh generator initialized")
        except LibraryLoadError as e:
            print(f"✗ Failed to initialize: {e}")
            raise
    
    def validate_and_generate(self, config: Dict) -> Dict:
        """Generate mesh with comprehensive validation"""
        
        # Extract configuration
        geom_type = config.get('geometry_type')
        params = config.get('parameters', {})
        density = config.get('mesh_density', MeshDensity.MEDIUM)
        output_base = config.get('output_dir', './output')
        
        # Create unique output directory
        timestamp = int(time.time() * 1000)
        output_dir = Path(output_base) / f"{geom_type}_{timestamp}"
        
        try:
            # Validate before generation
            print(f"\nProcessing {geom_type}...")
            
            # Check if parameters are reasonable
            if geom_type == 'rectangle':
                aspect_ratio = params['width'] / params['height']
                if aspect_ratio > 10 or aspect_ratio < 0.1:
                    print(f"  ⚠ Warning: Extreme aspect ratio ({aspect_ratio:.1f})")
            
            # Estimate mesh size
            estimate = self.generator.estimate_mesh_size(geom_type, params, density)
            print(f"  Estimated: {estimate['estimated_elements']} elements")
            
            # Warn if mesh might be too large
            if estimate['estimated_elements'] > 10000:
                print(f"  ⚠ Large mesh warning: {estimate['estimated_elements']} elements")
            
            # Generate mesh
            start_time = time.perf_counter()
            success, quality = self.generator.generate_mesh(
                geometry_type=geom_type,
                parameters=params,
                output_dir=output_dir,
                mesh_density=density,
                enable_boundary_layer=config.get('boundary_layer', False)
            )
            generation_time = (time.perf_counter() - start_time) * 1000
            
            if success:
                print(f"  ✓ Generated in {generation_time:.1f} ms")
                print(f"    Elements: {quality['total_elements']}")
                print(f"    Quality: {quality['min_angle']:.1f}° - {quality['max_angle']:.1f}°")
                
                # Add workflow metadata
                result = {
                    'status': 'success',
                    'config': config,
                    'output_dir': str(output_dir),
                    'quality': quality,
                    'generation_time_ms': generation_time,
                    'timestamp': timestamp
                }
                
                # Save metadata
                with open(output_dir / 'mesh_metadata.json', 'w') as f:
                    json.dump(result, f, indent=2)
                
                return result
            else:
                return {
                    'status': 'failed',
                    'config': config,
                    'error': 'Unknown generation failure'
                }
                
        except GeometryValidationError as e:
            print(f"  ✗ Invalid geometry: {e}")
            return {
                'status': 'validation_error',
                'config': config,
                'error': str(e)
            }
        except MeshGenerationError as e:
            print(f"  ✗ Generation failed: {e}")
            return {
                'status': 'generation_error',
                'config': config,
                'error': str(e)
            }
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            return {
                'status': 'unexpected_error',
                'config': config,
                'error': str(e)
            }


def demonstrate_error_handling():
    """Show proper error handling patterns"""
    
    print("\n" + "="*50)
    print("ERROR HANDLING DEMONSTRATION")
    print("="*50)
    
    generator = EducationalMeshGenerator()
    
    # Test cases that should fail
    error_cases = [
        {
            'name': 'Invalid geometry type',
            'geometry_type': 'hexagon',  # Not supported
            'parameters': {},
            'expected_error': GeometryValidationError
        },
        {
            'name': 'Missing parameters',
            'geometry_type': 'circle',
            'parameters': {},  # Missing radius
            'expected_error': GeometryValidationError
        },
        {
            'name': 'Invalid parameter values',
            'geometry_type': 'rectangle',
            'parameters': {'width': -1, 'height': 1},
            'expected_error': GeometryValidationError
        },
        {
            'name': 'Invalid annulus (inner > outer)',
            'geometry_type': 'annulus',
            'parameters': {'inner_radius': 2.0, 'outer_radius': 1.0},
            'expected_error': GeometryValidationError
        }
    ]
    
    for case in error_cases:
        print(f"\nTesting: {case['name']}")
        try:
            generator.generate_mesh(
                case['geometry_type'],
                case['parameters'],
                '/tmp/error_test'
            )
            print("  ✗ Should have failed but didn't!")
        except case['expected_error'] as e:
            print(f"  ✓ Caught expected error: {type(e).__name__}")
            print(f"    Message: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error type: {type(e).__name__}")


def demonstrate_batch_processing():
    """Show efficient batch processing"""
    
    print("\n" + "="*50)
    print("BATCH PROCESSING DEMONSTRATION")
    print("="*50)
    
    # Define batch of meshes to generate
    batch_configs = [
        {
            'geometry_type': 'rectangle',
            'parameters': {'width': 1.0, 'height': 1.0},
            'mesh_density': MeshDensity.COARSE
        },
        {
            'geometry_type': 'rectangle',
            'parameters': {'width': 2.0, 'height': 1.0},
            'mesh_density': MeshDensity.MEDIUM
        },
        {
            'geometry_type': 'circle',
            'parameters': {'radius': 0.5},
            'mesh_density': MeshDensity.FINE
        },
        {
            'geometry_type': 'annulus',
            'parameters': {'inner_radius': 0.3, 'outer_radius': 0.8},
            'mesh_density': MeshDensity.MEDIUM
        }
    ]
    
    workflow = SimulationWorkflow()
    
    # Sequential processing
    print("\nSequential Processing:")
    start_time = time.perf_counter()
    sequential_results = []
    
    for config in batch_configs:
        result = workflow.validate_and_generate(config)
        sequential_results.append(result)
    
    sequential_time = (time.perf_counter() - start_time) * 1000
    print(f"\nTotal sequential time: {sequential_time:.1f} ms")
    
    # Parallel processing using ThreadPoolExecutor
    print("\nParallel Processing (ThreadPool):")
    start_time = time.perf_counter()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        parallel_results = list(executor.map(workflow.validate_and_generate, batch_configs))
    
    parallel_time = (time.perf_counter() - start_time) * 1000
    print(f"\nTotal parallel time: {parallel_time:.1f} ms")
    print(f"Speedup: {sequential_time/parallel_time:.2f}x")


def demonstrate_performance_optimization():
    """Show performance optimization techniques"""
    
    print("\n" + "="*50)
    print("PERFORMANCE OPTIMIZATION DEMONSTRATION")
    print("="*50)
    
    generator = EducationalMeshGenerator()
    
    # Technique 1: Reuse generator instance
    print("\n1. Instance Reuse Comparison:")
    
    # Bad: Create new instance each time
    start = time.perf_counter()
    for i in range(5):
        new_gen = EducationalMeshGenerator()
        new_gen.generate_mesh(
            'rectangle',
            {'width': 1.0, 'height': 1.0},
            f'/tmp/perf_test_bad_{i}',
            MeshDensity.COARSE
        )
    bad_time = (time.perf_counter() - start) * 1000
    
    # Good: Reuse instance
    start = time.perf_counter()
    for i in range(5):
        generator.generate_mesh(
            'rectangle',
            {'width': 1.0, 'height': 1.0},
            f'/tmp/perf_test_good_{i}',
            MeshDensity.COARSE
        )
    good_time = (time.perf_counter() - start) * 1000
    
    print(f"  New instance each time: {bad_time:.1f} ms")
    print(f"  Reused instance: {good_time:.1f} ms")
    print(f"  Improvement: {((bad_time - good_time) / bad_time * 100):.1f}%")
    
    # Technique 2: Appropriate density selection
    print("\n2. Density Impact on Performance:")
    
    for density in [MeshDensity.COARSE, MeshDensity.MEDIUM, MeshDensity.FINE]:
        start = time.perf_counter()
        success, quality = generator.generate_mesh(
            'circle',
            {'radius': 1.0},
            f'/tmp/density_test_{density}',
            density
        )
        elapsed = (time.perf_counter() - start) * 1000
        
        if success:
            print(f"  {density.name}: {elapsed:.1f} ms "
                  f"({quality['total_elements']} elements)")


async def demonstrate_async_integration():
    """Show how to integrate with async frameworks"""
    
    print("\n" + "="*50)
    print("ASYNC INTEGRATION DEMONSTRATION")
    print("="*50)
    
    # Since the Fortran library is synchronous, we use run_in_executor
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    generator = EducationalMeshGenerator()
    executor = ThreadPoolExecutor(max_workers=4)
    
    async def generate_mesh_async(geom_type, params, output_dir):
        """Async wrapper for mesh generation"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            generator.generate_mesh,
            geom_type,
            params,
            output_dir,
            MeshDensity.MEDIUM
        )
    
    # Create multiple async tasks
    tasks = []
    for i in range(4):
        task = generate_mesh_async(
            'rectangle',
            {'width': 1.0 + i * 0.5, 'height': 1.0},
            f'/tmp/async_test_{i}'
        )
        tasks.append(task)
    
    # Wait for all to complete
    start = time.perf_counter()
    results = await asyncio.gather(*tasks)
    elapsed = (time.perf_counter() - start) * 1000
    
    print(f"\nGenerated {len(results)} meshes asynchronously in {elapsed:.1f} ms")
    for i, (success, quality) in enumerate(results):
        if success:
            print(f"  Mesh {i}: {quality['total_elements']} elements")


def main():
    """Run all demonstrations"""
    
    print("Educational Mesh Generator - Advanced Usage Examples")
    print("=" * 60)
    
    # Run demonstrations
    demonstrate_error_handling()
    demonstrate_batch_processing()
    demonstrate_performance_optimization()
    
    # Run async demonstration
    print("\nRunning async demonstration...")
    asyncio.run(demonstrate_async_integration())
    
    print("\n" + "="*60)
    print("All demonstrations completed!")


if __name__ == "__main__":
    main() 