"""
Test script for mesh API endpoints
"""

import asyncio
import json
import httpx
from datetime import datetime


async def test_mesh_api():
    """Test the mesh generation API endpoints"""
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        print("=== Testing Mesh API Endpoints ===\n")
        
        # Test 1: Get supported geometries
        print("1. Testing GET /mesh/geometries")
        response = await client.get(f"{base_url}/mesh/geometries")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            geometries = response.json()
            print(f"   Found {len(geometries)} geometry types:")
            for geom in geometries:
                print(f"   - {geom['name']} ({geom['type']})")
        print()
        
        # Test 2: Generate a rectangle mesh
        print("2. Testing POST /mesh/generate (Rectangle)")
        mesh_data = {
            "geometry_type": "rectangle",
            "parameters": {
                "width": 10.0,
                "height": 5.0
            },
            "mesh_density": 3,
            "enable_boundary_layer": False
        }
        
        try:
            response = await client.post(
                f"{base_url}/mesh/generate",
                json=mesh_data
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                mesh_id = result['mesh_id']
                print(f"   Mesh ID: {mesh_id}")
                print(f"   Generation time: {result['generation_time_ms']:.2f} ms")
                print(f"   Quality metrics:")
                metrics = result['quality_metrics']
                print(f"     - Total nodes: {metrics['total_nodes']}")
                print(f"     - Total elements: {metrics['total_elements']}")
                print(f"     - Min angle: {metrics['min_angle']:.2f}°")
                print(f"     - Max angle: {metrics['max_angle']:.2f}°")
                
                # Test 3: Get mesh status
                print(f"\n3. Testing GET /mesh/status/{mesh_id}")
                status_response = await client.get(f"{base_url}/mesh/status/{mesh_id}")
                print(f"   Status: {status_response.status_code}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   Mesh status: {status_data['status']}")
                    print(f"   Progress: {status_data['progress']}%")
                
                # Test 4: Get mesh preview
                print(f"\n4. Testing GET /mesh/preview/{mesh_id}")
                preview_response = await client.get(
                    f"{base_url}/mesh/preview/{mesh_id}",
                    params={"max_nodes": 100, "max_elements": 200}
                )
                print(f"   Status: {preview_response.status_code}")
                if preview_response.status_code == 200:
                    preview_data = preview_response.json()
                    print(f"   Preview data:")
                    print(f"     - Nodes: {len(preview_data['nodes'])}")
                    print(f"     - Elements: {len(preview_data['elements'])}")
                    print(f"     - Element type: {preview_data['element_type']}")
                    print(f"     - Boundaries: {list(preview_data['boundaries'].keys())}")
                    bbox = preview_data['bounding_box']
                    print(f"     - Bounding box: X[{bbox['min_x']}, {bbox['max_x']}], "
                          f"Y[{bbox['min_y']}, {bbox['max_y']}]")
            else:
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        print()
        
        # Test 5: Test different geometry types
        print("5. Testing other geometry types")
        
        test_geometries = [
            {
                "name": "Circle",
                "data": {
                    "geometry_type": "circle",
                    "parameters": {"radius": 5.0},
                    "mesh_density": 4
                }
            },
            {
                "name": "Annulus",
                "data": {
                    "geometry_type": "annulus",
                    "parameters": {"inner_radius": 2.0, "outer_radius": 5.0},
                    "mesh_density": 3
                }
            },
            {
                "name": "L-Shape",
                "data": {
                    "geometry_type": "l_shape",
                    "parameters": {
                        "width": 10.0,
                        "height": 10.0,
                        "cutout_width": 5.0,
                        "cutout_height": 5.0
                    },
                    "mesh_density": 3
                }
            }
        ]
        
        for geom_test in test_geometries:
            print(f"\n   Testing {geom_test['name']}:")
            try:
                response = await client.post(
                    f"{base_url}/mesh/generate",
                    json=geom_test['data']
                )
                if response.status_code == 200:
                    result = response.json()
                    print(f"     ✓ Success - {result['quality_metrics']['total_elements']} elements")
                else:
                    print(f"     ✗ Failed - Status {response.status_code}")
            except Exception as e:
                print(f"     ✗ Error: {e}")
        
        print("\n=== Testing WebSocket endpoint ===")
        print("Note: WebSocket testing requires a separate WebSocket client")
        print(f"WebSocket URL: ws://localhost:8000/api/v1/mesh/ws/{{mesh_id}}")


if __name__ == "__main__":
    asyncio.run(test_mesh_api()) 