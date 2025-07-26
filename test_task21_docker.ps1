# PowerShell script to test Task 21 in Docker
Write-Host "==================================================================="
Write-Host "Task 21 Docker Testing - Python Wrapper for Fortran Mesh Generator"
Write-Host "==================================================================="

# Build the backend image
Write-Host "`n1. Building backend Docker image..."
docker build -t elmerfem-backend-test ./backend

# Test 1: Check library compilation
Write-Host "`n[TEST 1] Checking Fortran library compilation..."
docker run --rm elmerfem-backend-test bash -c "cd /app/elmerfem_custom/mesh_generator && ls -la libeducational_mesh.so && echo 'Library compiled successfully'"

# Test 2: Run library test
Write-Host "`n[TEST 2] Testing library loading..."
docker run --rm elmerfem-backend-test bash -c "cd /app/elmerfem_custom/mesh_generator && python test_library.py"

# Test 3: Run structure test
Write-Host "`n[TEST 3] Testing wrapper structure..."
docker run --rm elmerfem-backend-test bash -c "cd /app/elmerfem_custom/mesh_generator && python test_wrapper_structure.py"

# Test 4: Run performance test
Write-Host "`n[TEST 4] Running performance tests (this may take a minute)..."
docker run --rm elmerfem-backend-test bash -c "cd /app/elmerfem_custom/mesh_generator && python test_performance_wrapper.py"

# Test 5: Run examples
Write-Host "`n[TEST 5] Running basic usage example..."
docker run --rm elmerfem-backend-test bash -c "cd /app/elmerfem_custom/mesh_generator && python examples/basic_usage.py"

# Test 6: Test service integration
Write-Host "`n[TEST 6] Testing educational_mesh_service integration..."
$pythonCode = @'
import sys
sys.path.append("/app")
from app.services.educational_mesh_service import EducationalMeshService
from pathlib import Path
import asyncio

async def test():
    service = EducationalMeshService()
    print("Service instantiated successfully")
    
    success, quality = await service.generate_mesh(
        "rectangle",
        {"width": 1.0, "height": 1.0},
        Path("/tmp/test_mesh"),
        mesh_density=3
    )
    
    if success:
        print(f"Mesh generated successfully")
        print(f"  Elements: {quality.get('total_elements')}")
        print(f"  Nodes: {quality.get('total_nodes')}")
        print(f"  Min angle: {quality.get('min_angle')}°")
    else:
        print("Mesh generation failed")

asyncio.run(test())
'@

docker run --rm elmerfem-backend-test bash -c "cd /app && python -c '$pythonCode'"

Write-Host "`n==================================================================="
Write-Host "Task 21 Docker testing complete!"
Write-Host "====================================================================" 