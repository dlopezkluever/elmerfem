#!/usr/bin/env python3
"""
Basic usage example for Educational Mesh Generator

This script demonstrates the simplest way to generate meshes for
educational finite element analysis.
"""

import sys
from pathlib import Path

# Add parent directory to path to import the wrapper
sys.path.append(str(Path(__file__).parent.parent))

from educational_mesh_generator_wrapper import (
    EducationalMeshGenerator,
    MeshDensity,
    generate_educational_mesh
)


def main():
    print("Educational Mesh Generator - Basic Usage Example")
    print("=" * 50)
    
    # Method 1: Using the convenience function (simplest approach)
    print("\n1. Using convenience function:")
    success, quality = generate_educational_mesh(
        geometry_type='rectangle',
        parameters={'width': 2.0, 'height': 1.0},
        output_dir='./output/rectangle_simple',
        mesh_density=3
    )
    
    if success:
        print(f"   ✓ Generated rectangle mesh")
        print(f"   - Elements: {quality['total_elements']}")
        print(f"   - Nodes: {quality['total_nodes']}")
        print(f"   - Min angle: {quality['min_angle']:.1f}°")
    
    # Method 2: Using the class (more control)
    print("\n2. Using EducationalMeshGenerator class:")
    generator = EducationalMeshGenerator()
    
    # Generate different geometries
    geometries = [
        ('circle', {'radius': 1.0}, MeshDensity.MEDIUM),
        ('annulus', {'inner_radius': 0.5, 'outer_radius': 1.0}, MeshDensity.FINE),
        ('l_shape', {'width': 2.0, 'height': 2.0, 'cutout_width': 1.0, 'cutout_height': 1.0}, MeshDensity.MEDIUM)
    ]
    
    for geom_type, params, density in geometries:
        output_dir = f'./output/{geom_type}_example'
        success, quality = generator.generate_mesh(
            geometry_type=geom_type,
            parameters=params,
            output_dir=output_dir,
            mesh_density=density
        )
        
        if success:
            print(f"   ✓ Generated {geom_type} mesh with {density.name} density")
            print(f"     - Elements: {quality['total_elements']}")
            print(f"     - Quality: min angle = {quality['min_angle']:.1f}°, "
                  f"avg aspect ratio = {quality['aspect_ratio_avg']:.2f}")
        else:
            print(f"   ✗ Failed to generate {geom_type} mesh")
    
    # Show performance statistics
    print("\n3. Performance Statistics:")
    stats = generator.get_performance_stats()
    print(f"   - Total generations: {stats['total_calls']}")
    print(f"   - Average time: {stats['average_time']:.1f} ms")
    print(f"   - Min/Max time: {stats['min_time']:.1f} - {stats['max_time']:.1f} ms")
    
    # Estimate mesh size before generation
    print("\n4. Mesh Size Estimation:")
    estimate = generator.estimate_mesh_size(
        geometry_type='circle',
        parameters={'radius': 2.0},
        mesh_density=MeshDensity.FINE
    )
    print(f"   Circle (radius=2.0, FINE density):")
    print(f"   - Estimated elements: {estimate['estimated_elements']}")
    print(f"   - Estimated nodes: {estimate['estimated_nodes']}")


if __name__ == "__main__":
    main() 