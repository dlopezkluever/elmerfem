"""
Task 23 Implementation Verification Test
========================================

This script tests all the functionality implemented for Task 23:
- FastAPI mesh generation endpoints
- WebSocket support
- Pydantic schemas
- API documentation
- Integration with existing services
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test 1: Verify all imports work correctly"""
    print("🧪 TEST 1: Import Verification")
    print("=" * 50)
    
    try:
        # Test mesh API router import
        from app.api.v1.mesh import router as mesh_router
        print("✅ Successfully imported mesh router")
        
        # Check endpoints
        routes = [route.path for route in mesh_router.routes]
        expected_routes = ['/mesh/generate', '/mesh/preview/{mesh_id}', '/mesh/status/{mesh_id}', '/mesh/ws/{mesh_id}', '/mesh/geometries']
        
        print(f"✅ Found {len(routes)} mesh endpoints:")
        for route in routes:
            print(f"   - {route}")
        
        # Verify all expected endpoints exist
        for expected in expected_routes:
            if any(expected.replace('{mesh_id}', 'test') in route.replace('{mesh_id}', 'test') for route in routes):
                print(f"✅ Found expected endpoint: {expected}")
            else:
                print(f"❌ Missing expected endpoint: {expected}")
                return False
        
        # Test model imports
        from app.models.mesh_dtos import (
            GeometryType,
            MeshGenerationParams,
            MeshQualityMetrics
        )
        print("✅ Successfully imported mesh DTOs")
        
        # Test geometry types
        geometry_types = [g.value for g in GeometryType]
        expected_types = ['rectangle', 'circle', 'annulus', 'l_shape']
        print(f"✅ Geometry types: {geometry_types}")
        
        for expected_type in expected_types:
            if expected_type in geometry_types:
                print(f"✅ Found geometry type: {expected_type}")
            else:
                print(f"❌ Missing geometry type: {expected_type}")
                return False
        
        # Test educational mesh service
        from app.services.educational_mesh_service import EducationalMeshService
        print("✅ Successfully imported EducationalMeshService")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        traceback.print_exc()
        return False


def test_pydantic_schemas():
    """Test 2: Verify Pydantic schemas work correctly"""
    print("\n🧪 TEST 2: Pydantic Schema Validation")
    print("=" * 50)
    
    try:
        from app.api.v1.mesh import MeshGenerationRequestDTO, MeshPreviewDTO, MeshStatusDTO
        from app.services.educational_mesh_service import GeometryType
        
        # Test valid rectangle request
        valid_rectangle = {
            "geometry_type": "rectangle",
            "parameters": {"width": 10.0, "height": 5.0},
            "mesh_density": 3,
            "enable_boundary_layer": False
        }
        
        request = MeshGenerationRequestDTO(**valid_rectangle)
        print("✅ Valid rectangle request validated successfully")
        
        # Test valid circle request
        valid_circle = {
            "geometry_type": "circle",
            "parameters": {"radius": 5.0},
            "mesh_density": 4,
            "enable_boundary_layer": True
        }
        
        request = MeshGenerationRequestDTO(**valid_circle)
        print("✅ Valid circle request validated successfully")
        
        # Test validation constraints
        try:
            invalid_request = {
                "geometry_type": "rectangle",
                "parameters": {"width": -5.0, "height": 5.0},  # Invalid negative width
                "mesh_density": 3
            }
            # This should fail when we try to validate the geometry
            from app.services.educational_mesh_service import MeshGenerationRequest
            mesh_request = MeshGenerationRequest(**invalid_request)
            mesh_request.get_validated_geometry()  # This should raise an error
            print("❌ Invalid request should have failed validation")
            return False
        except Exception:
            print("✅ Invalid parameters correctly rejected")
        
        # Test mesh density validation
        try:
            invalid_density = {
                "geometry_type": "rectangle",
                "parameters": {"width": 10.0, "height": 5.0},
                "mesh_density": 10  # Invalid density > 5
            }
            MeshGenerationRequestDTO(**invalid_density)
            print("❌ Invalid mesh density should have failed")
            return False
        except Exception:
            print("✅ Invalid mesh density correctly rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema validation test failed: {e}")
        traceback.print_exc()
        return False


def test_api_structure():
    """Test 3: Verify API structure and documentation"""
    print("\n🧪 TEST 3: API Structure and Documentation")
    print("=" * 50)
    
    try:
        from app.api.v1.mesh import router as mesh_router
        
        # Check that endpoints have proper documentation
        for route in mesh_router.routes:
            if hasattr(route, 'endpoint') and route.endpoint:
                func = route.endpoint
                if hasattr(func, '__doc__') and func.__doc__:
                    print(f"✅ {route.path} has documentation")
                else:
                    print(f"⚠️  {route.path} missing documentation")
        
        # Check that proper HTTP methods are used
        method_check = {
            '/mesh/generate': 'POST',
            '/mesh/preview/{mesh_id}': 'GET',
            '/mesh/status/{mesh_id}': 'GET',
            '/mesh/geometries': 'GET'
        }
        
        for route in mesh_router.routes:
            if route.path in method_check:
                expected_method = method_check[route.path]
                if expected_method in route.methods:
                    print(f"✅ {route.path} uses correct method: {expected_method}")
                else:
                    print(f"❌ {route.path} missing method: {expected_method}")
                    return False
        
        # Check WebSocket endpoint
        websocket_found = any('ws' in route.path for route in mesh_router.routes)
        if websocket_found:
            print("✅ WebSocket endpoint found")
        else:
            print("❌ WebSocket endpoint missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        traceback.print_exc()
        return False


def test_integration():
    """Test 4: Verify integration with existing services"""
    print("\n🧪 TEST 4: Service Integration")
    print("=" * 50)
    
    try:
        # Test that dependency injection functions exist
        from app.jobs.store import get_job_store
        from app.services.docker_wrapper import get_docker_wrapper
        print("✅ Dependency injection functions available")
        
        # Test that mesh service can be instantiated
        from app.services.educational_mesh_service import EducationalMeshService
        service = EducationalMeshService()
        print("✅ EducationalMeshService can be instantiated")
        
        # Test output directory creation
        output_dir = service._get_output_directory("test-job-id")
        print(f"✅ Output directory method works: {output_dir}")
        
        # Test that main app integration exists
        try:
            from app.main import app
            print("✅ Main FastAPI app can be imported")
        except Exception as e:
            print(f"⚠️  Main app import issue (may be normal): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False


def test_file_structure():
    """Test 5: Verify all required files exist"""
    print("\n🧪 TEST 5: File Structure Verification")
    print("=" * 50)
    
    required_files = [
        "app/api/v1/mesh.py",
        "app/api/v1/__init__.py", 
        "app/models/mesh_dtos.py",
        "test_mesh_api.py",
        "MESH_API_DOCUMENTATION.md",
        "TASK_23_IMPLEMENTATION_SUMMARY.md"
    ]
    
    all_files_exist = True
    
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_files_exist = False
    
    return all_files_exist


def main():
    """Run all tests"""
    print("🚀 Task 23 Implementation Verification")
    print("=" * 60)
    print("Testing all Task 23 subtasks:")
    print("23.1 - FastAPI Endpoint for Mesh Generation")
    print("23.2 - WebSocket Endpoint for Real-Time Status Updates")
    print("23.3 - Mesh Preview Endpoint")
    print("23.4 - Pydantic Schemas for Geometry Parameters")
    print("23.5 - OpenAPI Documentation Integration")
    print("=" * 60)
    
    tests = [
        ("Import Verification", test_imports),
        ("Pydantic Schema Validation", test_pydantic_schemas),
        ("API Structure and Documentation", test_api_structure),
        ("Service Integration", test_integration),
        ("File Structure", test_file_structure)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Task 23 implementation is working correctly.")
        print("\n📝 Next steps to test with a running server:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Visit http://localhost:8000/docs to see the API documentation")
        print("3. Run the mesh API test: python test_mesh_api.py")
        print("4. Test WebSocket connections with a WebSocket client")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 