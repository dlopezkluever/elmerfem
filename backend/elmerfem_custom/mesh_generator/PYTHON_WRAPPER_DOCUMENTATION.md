# Educational Mesh Generator Python Wrapper Documentation

## Overview

The Educational Mesh Generator Python wrapper provides a high-performance interface to the Fortran mesh generation library specifically designed for educational finite element analysis workflows. This wrapper enables seamless integration of mesh generation capabilities into Python-based applications while maintaining sub-50ms performance targets.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [API Reference](#api-reference)
4. [Usage Examples](#usage-examples)
5. [Performance Considerations](#performance-considerations)
6. [Error Handling](#error-handling)
7. [Integration Guide](#integration-guide)
8. [Troubleshooting](#troubleshooting)

## Installation

### Requirements

- Python 3.7 or higher
- gfortran compiler
- make utility
- ctypes (included with Python)

### Building the Library

```bash
cd backend/elmerfem_custom/mesh_generator
make clean
make
```

This will create `libeducational_mesh.so` in the same directory.

### Docker Integration

The library is automatically built when creating the Docker image:

```dockerfile
RUN cd elmerfem_custom/mesh_generator && make
```

## Quick Start

```python
from educational_mesh_generator_wrapper import EducationalMeshGenerator, MeshDensity

# Initialize the generator
generator = EducationalMeshGenerator()

# Generate a simple rectangle mesh
success, quality = generator.generate_mesh(
    geometry_type='rectangle',
    parameters={'width': 2.0, 'height': 1.0},
    output_dir='/tmp/my_mesh',
    mesh_density=MeshDensity.MEDIUM
)

if success:
    print(f"Generated mesh with {quality['total_elements']} elements")
    print(f"Mesh quality - Min angle: {quality['min_angle']:.1f}°")
```

## API Reference

### EducationalMeshGenerator Class

The main class for mesh generation operations.

#### Constructor

```python
EducationalMeshGenerator(library_path: Optional[Path] = None)
```

**Parameters:**
- `library_path`: Optional path to the Fortran library. If not provided, searches in standard locations.

**Raises:**
- `LibraryLoadError`: If the Fortran library cannot be loaded.

#### Methods

##### generate_mesh

```python
generate_mesh(
    geometry_type: Union[str, GeometryType],
    parameters: Dict[str, float],
    output_dir: Union[str, Path],
    mesh_density: Union[int, MeshDensity] = MeshDensity.MEDIUM,
    enable_boundary_layer: bool = False
) -> Tuple[bool, Dict[str, any]]
```

Generate a finite element mesh for the specified geometry.

**Parameters:**
- `geometry_type`: Type of geometry ('rectangle', 'circle', 'annulus', 'l_shape')
- `parameters`: Geometry-specific parameters (see table below)
- `output_dir`: Directory where mesh files will be saved
- `mesh_density`: Mesh density level (1-5 or MeshDensity enum)
- `enable_boundary_layer`: Whether to generate boundary layer elements

**Geometry Parameters:**

| Geometry | Required Parameters |
|----------|-------------------|
| rectangle | width, height |
| circle | radius |
| annulus | inner_radius, outer_radius |
| l_shape | width, height, cutout_width, cutout_height |

**Returns:**
- Tuple of (success: bool, quality_metrics: dict)

**Quality Metrics Dictionary:**
```python
{
    'total_nodes': int,          # Number of nodes in the mesh
    'total_elements': int,       # Number of elements in the mesh
    'min_angle': float,          # Minimum angle in degrees
    'max_angle': float,          # Maximum angle in degrees
    'aspect_ratio_avg': float,   # Average element aspect ratio
    'aspect_ratio_max': float,   # Maximum element aspect ratio
    'geometry_type': str,        # Type of geometry
    'mesh_density': int,         # Density level used
    'boundary_layer': bool,      # Whether boundary layer was enabled
    'generation_time_ms': float  # Average generation time in milliseconds
}
```

##### estimate_mesh_size

```python
estimate_mesh_size(
    geometry_type: Union[str, GeometryType],
    parameters: Dict[str, float],
    mesh_density: Union[int, MeshDensity] = MeshDensity.MEDIUM
) -> Dict[str, int]
```

Estimate the number of elements and nodes without generating the mesh.

**Returns:**
```python
{
    'estimated_elements': int,
    'estimated_nodes': int
}
```

##### get_performance_stats

```python
get_performance_stats() -> Dict[str, float]
```

Get performance statistics for mesh generation.

**Returns:**
```python
{
    'total_calls': int,        # Number of mesh generations performed
    'total_time': float,       # Total time spent in mesh generation (ms)
    'average_time': float,     # Average time per mesh generation (ms)
    'min_time': float,         # Fastest mesh generation time (ms)
    'max_time': float          # Slowest mesh generation time (ms)
}
```

##### cleanup_mesh_files

```python
cleanup_mesh_files(directory: Union[str, Path]) -> bool
```

Remove mesh files from a directory.

### Enumerations

#### GeometryType

```python
class GeometryType(IntEnum):
    RECTANGLE = 1
    CIRCLE = 2
    ANNULUS = 3
    L_SHAPE = 4
```

#### MeshDensity

```python
class MeshDensity(IntEnum):
    COARSE = 1
    MEDIUM_COARSE = 2
    MEDIUM = 3
    MEDIUM_FINE = 4
    FINE = 5
```

### Exceptions

- `MeshGeneratorError`: Base exception for all mesh generator errors
- `GeometryValidationError`: Raised when geometry parameters are invalid
- `MeshGenerationError`: Raised when mesh generation fails
- `LibraryLoadError`: Raised when the Fortran library cannot be loaded

## Usage Examples

### Basic Rectangle Mesh

```python
from educational_mesh_generator_wrapper import EducationalMeshGenerator, MeshDensity

generator = EducationalMeshGenerator()

# Generate a 2x1 rectangle with medium density
success, quality = generator.generate_mesh(
    geometry_type='rectangle',
    parameters={'width': 2.0, 'height': 1.0},
    output_dir='./meshes/rectangle',
    mesh_density=MeshDensity.MEDIUM
)

if success:
    print(f"Elements: {quality['total_elements']}")
    print(f"Nodes: {quality['total_nodes']}")
    print(f"Min angle: {quality['min_angle']:.1f}°")
```

### Circle with Fine Mesh

```python
# Generate a circle with radius 1.5 and fine mesh
success, quality = generator.generate_mesh(
    geometry_type='circle',
    parameters={'radius': 1.5},
    output_dir='./meshes/circle',
    mesh_density=MeshDensity.FINE
)
```

### Annulus for Heat Transfer

```python
# Generate an annulus (pipe cross-section) with boundary layers
success, quality = generator.generate_mesh(
    geometry_type='annulus',
    parameters={
        'inner_radius': 0.5,
        'outer_radius': 1.0
    },
    output_dir='./meshes/pipe',
    mesh_density=MeshDensity.MEDIUM_FINE,
    enable_boundary_layer=True  # For better heat transfer resolution
)
```

### L-Shape for Structural Analysis

```python
# Generate L-shaped domain for stress concentration study
success, quality = generator.generate_mesh(
    geometry_type='l_shape',
    parameters={
        'width': 3.0,
        'height': 3.0,
        'cutout_width': 1.5,
        'cutout_height': 1.5
    },
    output_dir='./meshes/l_shape',
    mesh_density=MeshDensity.MEDIUM_FINE
)
```

### Using Convenience Function

```python
from educational_mesh_generator_wrapper import generate_educational_mesh

# One-liner mesh generation
success, quality = generate_educational_mesh(
    'rectangle',
    {'width': 1.0, 'height': 1.0},
    '/tmp/quick_mesh',
    mesh_density=3
)
```

### Estimating Mesh Size

```python
# Estimate before generating
estimate = generator.estimate_mesh_size(
    'circle',
    {'radius': 2.0},
    MeshDensity.FINE
)

print(f"Estimated elements: {estimate['estimated_elements']}")
print(f"Estimated nodes: {estimate['estimated_nodes']}")

# Generate if estimate is acceptable
if estimate['estimated_elements'] < 10000:
    success, quality = generator.generate_mesh(
        'circle',
        {'radius': 2.0},
        './meshes/circle',
        MeshDensity.FINE
    )
```

### Error Handling Example

```python
from educational_mesh_generator_wrapper import (
    EducationalMeshGenerator,
    GeometryValidationError,
    MeshGenerationError
)

generator = EducationalMeshGenerator()

try:
    success, quality = generator.generate_mesh(
        geometry_type='annulus',
        parameters={
            'inner_radius': 1.0,
            'outer_radius': 0.5  # Invalid: outer < inner
        },
        output_dir='./invalid_mesh'
    )
except GeometryValidationError as e:
    print(f"Invalid geometry: {e}")
except MeshGenerationError as e:
    print(f"Mesh generation failed: {e}")
```

### Performance Monitoring

```python
import time

generator = EducationalMeshGenerator()

# Generate multiple meshes
for i in range(10):
    generator.generate_mesh(
        'rectangle',
        {'width': 1.0, 'height': 1.0},
        f'/tmp/mesh_{i}',
        MeshDensity.MEDIUM
    )

# Check performance
stats = generator.get_performance_stats()
print(f"Average generation time: {stats['average_time']:.1f} ms")
print(f"Min/Max times: {stats['min_time']:.1f} - {stats['max_time']:.1f} ms")

if stats['average_time'] > 50:
    print("WARNING: Performance below target!")
```

## Performance Considerations

### Target Performance

The wrapper is designed to maintain sub-50ms overhead for mesh generation. This includes:
- Parameter validation
- Library function call
- Result processing
- File verification

### Performance Tips

1. **Reuse Generator Instance**: Create one instance and reuse it for multiple generations
   ```python
   generator = EducationalMeshGenerator()  # Create once
   for geometry in geometries:
       generator.generate_mesh(...)  # Reuse many times
   ```

2. **Use Appropriate Density**: Higher density levels significantly increase generation time
   ```python
   # Fast: COARSE or MEDIUM_COARSE for prototyping
   # Balanced: MEDIUM for most educational uses
   # Slow: FINE or MEDIUM_FINE for detailed analysis
   ```

3. **Batch Operations**: Generate multiple meshes in sequence to amortize initialization costs

4. **Avoid Repeated File I/O**: Use different output directories to avoid file system conflicts

### Thread Safety

The mesh generator uses thread-local storage and file-based output, making it safe for concurrent use from multiple threads as long as different output directories are used.

```python
import concurrent.futures
from pathlib import Path

def generate_in_thread(thread_id):
    generator = EducationalMeshGenerator()
    output_dir = Path(f'/tmp/mesh_thread_{thread_id}')
    return generator.generate_mesh(
        'rectangle',
        {'width': 1.0, 'height': 1.0},
        output_dir
    )

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(generate_in_thread, i) for i in range(4)]
    results = [f.result() for f in futures]
```

## Error Handling

### Exception Hierarchy

```
MeshGeneratorError (base)
├── LibraryLoadError
├── GeometryValidationError
└── MeshGenerationError
```

### Common Error Scenarios

1. **Library Not Found**
   ```python
   try:
       generator = EducationalMeshGenerator()
   except LibraryLoadError as e:
       print(f"Could not load library: {e}")
       # Ensure library is built: cd mesh_generator && make
   ```

2. **Invalid Parameters**
   ```python
   try:
       generator.generate_mesh('rectangle', {'width': -1}, '/tmp/mesh')
   except GeometryValidationError as e:
       print(f"Invalid parameters: {e}")
   ```

3. **File System Issues**
   ```python
   try:
       generator.generate_mesh(
           'circle', 
           {'radius': 1.0}, 
           '/read/only/directory'
       )
   except MeshGenerationError as e:
       print(f"Generation failed: {e}")
   ```

### Return Codes

The Fortran library uses these return codes:
- `0`: Success
- `-1`: Invalid geometry type
- `-2`: Invalid mesh density
- `-3`: Invalid geometry parameters
- `-4`: File I/O error
- `-5`: Memory allocation error

## Integration Guide

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from educational_mesh_generator_wrapper import EducationalMeshGenerator
import tempfile
import shutil

app = FastAPI()
generator = EducationalMeshGenerator()

class MeshRequest(BaseModel):
    geometry_type: str
    parameters: dict
    mesh_density: int = 3

@app.post("/generate_mesh")
async def generate_mesh(request: MeshRequest):
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            success, quality = generator.generate_mesh(
                request.geometry_type,
                request.parameters,
                temp_dir,
                request.mesh_density
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Mesh generation failed")
            
            # Read mesh files and return
            # ... file reading logic ...
            
            return {
                "success": True,
                "quality": quality,
                "mesh_data": mesh_data
            }
            
        except GeometryValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
```

### Celery Task Integration

```python
from celery import Celery
from educational_mesh_generator_wrapper import EducationalMeshGenerator

app = Celery('mesh_tasks')
generator = EducationalMeshGenerator()

@app.task
def generate_mesh_task(geometry_type, parameters, output_dir, density=3):
    success, quality = generator.generate_mesh(
        geometry_type,
        parameters,
        output_dir,
        density
    )
    return {"success": success, "quality": quality}
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gfortran \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy and build mesh generator
COPY elmerfem_custom/mesh_generator /app/mesh_generator
WORKDIR /app/mesh_generator
RUN make

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["python", "app.py"]
```

## Troubleshooting

### Library Loading Issues

**Problem**: `LibraryLoadError: Could not find libeducational_mesh.so`

**Solutions**:
1. Ensure the library is built: `cd mesh_generator && make`
2. Check library path permissions
3. Verify gfortran is installed: `gfortran --version`
4. Set explicit library path:
   ```python
   generator = EducationalMeshGenerator(
       library_path="/absolute/path/to/libeducational_mesh.so"
   )
   ```

### Performance Issues

**Problem**: Mesh generation exceeds 50ms

**Solutions**:
1. Check mesh density level (use COARSE or MEDIUM for testing)
2. Verify no file system bottlenecks (use local SSD)
3. Profile Python overhead:
   ```python
   import cProfile
   cProfile.run('generator.generate_mesh(...)')
   ```
4. Use performance stats to identify slow operations

### Memory Issues

**Problem**: Large meshes cause memory errors

**Solutions**:
1. Use lower mesh density
2. Generate meshes in batches
3. Monitor memory usage:
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

### File Permission Issues

**Problem**: Cannot write mesh files

**Solutions**:
1. Ensure output directory exists and is writable
2. Use temporary directories for testing:
   ```python
   import tempfile
   with tempfile.TemporaryDirectory() as temp_dir:
       generator.generate_mesh(..., output_dir=temp_dir, ...)
   ```
3. Check Docker volume permissions if running in container

## Best Practices

1. **Always validate parameters** before calling generate_mesh
2. **Use appropriate mesh density** for your use case
3. **Handle exceptions gracefully** in production code
4. **Monitor performance** in production environments
5. **Clean up mesh files** when no longer needed
6. **Use type hints** for better IDE support
7. **Log operations** for debugging and monitoring

## Advanced Topics

### Custom Geometry Validation

```python
def validate_custom_geometry(params):
    """Add custom validation logic"""
    if params['width'] / params['height'] > 10:
        raise GeometryValidationError("Aspect ratio too large")

# Use before mesh generation
validate_custom_geometry(my_params)
generator.generate_mesh(...)
```

### Mesh Post-Processing

```python
def read_mesh_nodes(mesh_dir):
    """Read node coordinates from mesh files"""
    nodes = []
    with open(f"{mesh_dir}/mesh.nodes", 'r') as f:
        # Skip header
        n_nodes = int(f.readline().split()[0])
        for _ in range(n_nodes):
            parts = f.readline().split()
            node_id = int(parts[0])
            x, y = float(parts[2]), float(parts[3])
            nodes.append((node_id, x, y))
    return nodes
```

### Performance Profiling

```python
import time
import matplotlib.pyplot as plt

def profile_density_performance():
    """Profile performance across density levels"""
    generator = EducationalMeshGenerator()
    densities = [1, 2, 3, 4, 5]
    times = []
    
    for density in densities:
        start = time.perf_counter()
        generator.generate_mesh(
            'rectangle',
            {'width': 1.0, 'height': 1.0},
            f'/tmp/profile_{density}',
            density
        )
        times.append((time.perf_counter() - start) * 1000)
    
    plt.plot(densities, times, 'o-')
    plt.xlabel('Mesh Density')
    plt.ylabel('Generation Time (ms)')
    plt.axhline(y=50, color='r', linestyle='--', label='50ms target')
    plt.legend()
    plt.show()
```

This comprehensive documentation provides everything needed to effectively use the Educational Mesh Generator Python wrapper in various applications and environments. 