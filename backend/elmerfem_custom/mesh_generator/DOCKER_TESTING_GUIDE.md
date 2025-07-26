# Task 21 Docker Testing Guide

This guide explains how to fully test the Python wrapper implementation in a Docker environment where the Fortran library can be compiled and run.

## Prerequisites

- Docker Desktop installed and running
- Git Bash or WSL (recommended for Windows users)
- Project cloned to local machine

## Step 1: Build the Docker Image

From the project root directory:

```bash
# Build the backend image with mesh generator
docker-compose build backend

# Or build just the backend service
cd backend
docker build -t elmerfem-backend .
```

## Step 2: Run Performance Tests

### Option A: Using docker-compose

```bash
# Start the services
docker-compose up -d

# Execute tests in the running container
docker-compose exec backend bash -c "cd /app/elmerfem_custom/mesh_generator && python test_performance_wrapper.py"
```

### Option B: Using docker run

```bash
# Run a temporary container
docker run --rm -it elmerfem-backend bash

# Inside the container
cd /app/elmerfem_custom/mesh_generator
python test_performance_wrapper.py
```

## Step 3: Verify Library Loading

Test that the library loads correctly:

```bash
# In the container
cd /app/elmerfem_custom/mesh_generator
python test_library.py
```

Expected output:
```
✓ Successfully loaded library: /app/elmerfem_custom/mesh_generator/libeducational_mesh.so
✓ Successfully retrieved 'generate_mesh' function
✓ Function call completed with return code: 0
  Total elements: XXX
  Total nodes: XXX
✓ All tests passed!
```

## Step 4: Run Usage Examples

### Basic Usage
```bash
python examples/basic_usage.py
```

This should generate several meshes and show performance statistics.

### Advanced Usage
```bash
python examples/advanced_usage.py
```

This demonstrates error handling, batch processing, and async integration.

### Backend Integration
```bash
python examples/backend_integration.py
```

Shows how the wrapper integrates with FastAPI and job execution.

## Step 5: Performance Verification

The performance test should show results like:

```
PERFORMANCE TEST: Python Wrapper Overhead
Testing: Rectangle Small
  Results (50 runs):
    Average: 12.34 ms
    Min:     10.12 ms
    Max:     15.67 ms
    Std Dev: 1.23 ms
```

**Success Criteria:**
- Average time < 50ms ✓
- Consistent performance across geometries
- No memory leaks with repeated calls

## Step 6: Integration Testing

Test the wrapper with the existing service:

```bash
# In the container
cd /app
python -c "
from app.services.educational_mesh_service import EducationalMeshService
import asyncio

async def test():
    service = EducationalMeshService()
    success, quality = await service.generate_mesh(
        'rectangle',
        {'width': 1.0, 'height': 1.0},
        Path('/tmp/test_mesh'),
        mesh_density=3
    )
    print(f'Success: {success}')
    print(f'Elements: {quality.get(\"total_elements\")}')

asyncio.run(test())
"
```

## Common Issues and Solutions

### Issue: Library not found
```
LibraryLoadError: Could not find libeducational_mesh.so
```
**Solution:** Ensure the library is built:
```bash
cd /app/elmerfem_custom/mesh_generator
make clean
make
```

### Issue: Performance exceeds 50ms
**Solution:** Check system resources and ensure no other heavy processes are running in the container.

### Issue: Import errors
**Solution:** Verify Python path includes the mesh generator directory:
```python
import sys
sys.path.append('/app/elmerfem_custom/mesh_generator')
```

## Summary Checklist

- [ ] Docker image builds successfully
- [ ] Library compiles without errors
- [ ] test_library.py passes
- [ ] test_performance_wrapper.py shows <50ms average
- [ ] All example scripts run without errors
- [ ] Integration with educational_mesh_service works

## Next Steps

Once all tests pass:

1. **Task 22**: Integrate wrapper with job launcher
2. **Task 23**: Create frontend geometry components
3. **Task 24**: Implement mesh visualization
4. **Task 27**: End-to-end testing

The Python wrapper is now ready for full integration into the educational FEM platform! 