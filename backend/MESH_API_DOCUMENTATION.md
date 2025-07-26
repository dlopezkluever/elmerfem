# Mesh Generation API Documentation

## Overview

The Mesh Generation API provides endpoints for creating, previewing, and managing educational finite element meshes. It supports four basic geometry types optimized for educational use: Rectangle, Circle, Annulus, and L-Shape.

## Base URL

```
http://localhost:8000/api/v1/mesh
```

## Endpoints

### 1. Generate Mesh

**POST** `/generate`

Creates a new mesh based on the specified geometry type and parameters.

#### Request Body

```json
{
  "geometry_type": "rectangle|circle|annulus|l_shape",
  "parameters": {
    // Geometry-specific parameters
  },
  "mesh_density": 3,  // 1-5, where 1=coarse, 5=fine
  "enable_boundary_layer": false,
  "job_id": "optional-uuid"  // Optional: associate with existing job
}
```

#### Geometry Parameters

**Rectangle:**
```json
{
  "width": 10.0,   // 0.1 - 100.0
  "height": 5.0    // 0.1 - 100.0
}
```

**Circle:**
```json
{
  "radius": 5.0    // 0.1 - 50.0
}
```

**Annulus:**
```json
{
  "inner_radius": 2.0,  // 0.1 - 49.0
  "outer_radius": 5.0   // 0.2 - 50.0
}
// Constraint: inner_radius < outer_radius
// Constraint: inner_radius / outer_radius >= 0.1
```

**L-Shape:**
```json
{
  "width": 10.0,         // 0.2 - 100.0
  "height": 10.0,        // 0.2 - 100.0
  "cutout_width": 5.0,   // 0.1 - 99.0
  "cutout_height": 5.0   // 0.1 - 99.0
}
// Constraint: cutout_width < width
// Constraint: cutout_height < height
// Constraint: cutout_width >= 0.1 * width
// Constraint: cutout_height >= 0.1 * height
```

#### Response

```json
{
  "mesh_id": "550e8400-e29b-41d4-a716-446655440000",
  "geometry_type": "rectangle",
  "parameters": {
    "width": 10.0,
    "height": 5.0
  },
  "quality_metrics": {
    "total_nodes": 1234,
    "total_elements": 2345,
    "min_angle": 45.2,
    "max_angle": 89.8,
    "aspect_ratio_avg": 1.2,
    "aspect_ratio_max": 1.8,
    "generation_time_ms": 123.45,
    "mesh_density_level": 3,
    "geometry_type": "rectangle",
    "timestamp": "2024-01-26T12:00:00Z"
  },
  "generation_time_ms": 123.45,
  "mesh_files": [
    "/workspace/job_id/mesh.header",
    "/workspace/job_id/mesh.nodes",
    "/workspace/job_id/mesh.elements",
    "/workspace/job_id/mesh.boundary"
  ],
  "preview_available": true
}
```

### 2. Get Mesh Preview

**GET** `/preview/{mesh_id}`

Returns simplified mesh data suitable for frontend visualization.

#### Query Parameters

- `max_nodes` (optional): Maximum nodes to return (default: 1000, range: 100-10000)
- `max_elements` (optional): Maximum elements to return (default: 2000, range: 100-20000)

#### Response

```json
{
  "mesh_id": "550e8400-e29b-41d4-a716-446655440000",
  "geometry_type": "rectangle",
  "nodes": [
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [1.0, 1.0, 0.0],
    // ... more nodes
  ],
  "elements": [
    [0, 1, 2, 3],  // 0-indexed node references
    [1, 4, 5, 2],
    // ... more elements
  ],
  "element_type": "quad",  // or "triangle"
  "boundaries": {
    "boundary_1": [0, 1, 4, 5],  // Node indices on boundary
    "boundary_2": [2, 3, 6, 7]
  },
  "quality_metrics": { /* same as generation response */ },
  "bounding_box": {
    "min_x": 0.0,
    "max_x": 10.0,
    "min_y": 0.0,
    "max_y": 5.0,
    "min_z": 0.0,
    "max_z": 0.0
  }
}
```

### 3. Get Mesh Status

**GET** `/status/{mesh_id}`

Returns the current status of a mesh generation request.

#### Response

```json
{
  "mesh_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",  // pending, generating, completed, failed
  "progress": 100.0,      // 0-100
  "message": "Mesh generation completed successfully",
  "error": null
}
```

### 4. Get Supported Geometries

**GET** `/geometries`

Returns detailed information about all supported geometry types.

#### Response

```json
[
  {
    "type": "rectangle",
    "name": "Rectangle",
    "description": "2D rectangular geometry",
    "parameters": {
      "width": {
        "type": "float",
        "required": true,
        "min": 0.1,
        "max": 100.0,
        "description": "Rectangle width"
      },
      "height": {
        "type": "float",
        "required": true,
        "min": 0.1,
        "max": 100.0,
        "description": "Rectangle height"
      }
    },
    "preview_image": "/static/geometries/rectangle.svg"
  },
  // ... other geometries
]
```

### 5. WebSocket Status Updates

**WebSocket** `/ws/{mesh_id}`

Connect to receive real-time updates during mesh generation.

#### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/mesh/ws/550e8400-e29b-41d4-a716-446655440000');
```

#### Message Format

```json
{
  "type": "status|progress|completed|error",
  "data": {
    "mesh_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "generating",
    "progress": 75.0,
    "message": "Generating boundary elements..."
  }
}
```

## Error Responses

All endpoints return standard HTTP error codes with detailed error messages:

```json
{
  "detail": "Validation error: Inner radius must be less than outer radius"
}
```

Common error codes:
- `400`: Bad Request (validation errors)
- `404`: Not Found (mesh not found)
- `500`: Internal Server Error (mesh generation failed)

## Integration with Simulations

The mesh generation can be integrated with simulation jobs by:

1. Including a `job_id` in the mesh generation request
2. The mesh will be automatically associated with the simulation job
3. Mesh quality metrics will be stored in the job metadata

## Performance Considerations

- Mesh generation typically completes in < 2 seconds for educational geometries
- Higher mesh densities (4-5) may take slightly longer
- The preview endpoint downsamples large meshes for efficient visualization
- WebSocket connections timeout after 5 minutes of inactivity

## Examples

### Generate a Rectangle Mesh with cURL

```bash
curl -X POST http://localhost:8000/api/v1/mesh/generate \
  -H "Content-Type: application/json" \
  -d '{
    "geometry_type": "rectangle",
    "parameters": {"width": 10.0, "height": 5.0},
    "mesh_density": 3
  }'
```

### Python Example

```python
import httpx
import asyncio

async def generate_mesh():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/mesh/generate",
            json={
                "geometry_type": "circle",
                "parameters": {"radius": 5.0},
                "mesh_density": 4,
                "enable_boundary_layer": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Mesh ID: {result['mesh_id']}")
            print(f"Total elements: {result['quality_metrics']['total_elements']}")
            
            # Get preview
            preview = await client.get(
                f"http://localhost:8000/api/v1/mesh/preview/{result['mesh_id']}"
            )
            preview_data = preview.json()
            print(f"Preview nodes: {len(preview_data['nodes'])}")

asyncio.run(generate_mesh())
```

### JavaScript WebSocket Example

```javascript
function connectToMeshStatus(meshId) {
  const ws = new WebSocket(`ws://localhost:8000/api/v1/mesh/ws/${meshId}`);
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log(`${message.type}: ${message.data.message}`);
    
    if (message.type === 'completed') {
      console.log('Mesh generation completed!');
      ws.close();
    } else if (message.type === 'error') {
      console.error('Mesh generation failed:', message.data.error);
      ws.close();
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
}
``` 