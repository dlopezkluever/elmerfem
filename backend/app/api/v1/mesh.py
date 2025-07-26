"""
Mesh generation API endpoints
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from ...models import JobStatus
from ...services.educational_mesh_service import (
    EducationalMeshService,
    GeometryType,
    MeshGenerationRequest,
    MeshQualityMetrics,
    RectangleGeometry,
    CircleGeometry,
    AnnulusGeometry,
    LShapeGeometry,
)
from ...jobs.store import JobStore, InMemoryJobStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mesh", tags=["mesh"])


# API-specific request/response schemas
class MeshGenerationRequestDTO(BaseModel):
    """Request schema for mesh generation"""
    geometry_type: GeometryType = Field(..., description="Type of geometry to generate")
    parameters: Dict[str, float] = Field(..., description="Geometry-specific parameters")
    mesh_density: int = Field(3, ge=1, le=5, description="Mesh density level (1=coarse, 5=fine)")
    enable_boundary_layer: bool = Field(False, description="Enable boundary layer for fluid/heat transfer")
    job_id: Optional[UUID] = Field(None, description="Optional job ID to associate with mesh")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "geometry_type": "rectangle",
                    "parameters": {"width": 10.0, "height": 5.0},
                    "mesh_density": 3,
                    "enable_boundary_layer": False
                },
                {
                    "geometry_type": "circle",
                    "parameters": {"radius": 5.0},
                    "mesh_density": 4,
                    "enable_boundary_layer": True
                }
            ]
        }


class MeshGenerationResponseDTO(BaseModel):
    """Response schema for mesh generation"""
    mesh_id: UUID = Field(..., description="Unique identifier for the generated mesh")
    geometry_type: GeometryType
    parameters: Dict[str, float]
    quality_metrics: MeshQualityMetrics
    generation_time_ms: float
    mesh_files: List[str] = Field(..., description="List of generated mesh file paths")
    preview_available: bool = Field(True, description="Whether mesh preview is available")
    
    
class MeshPreviewDTO(BaseModel):
    """Simplified mesh data for visualization"""
    mesh_id: UUID
    geometry_type: GeometryType
    nodes: List[List[float]] = Field(..., description="Node coordinates [[x1,y1,z1], [x2,y2,z2], ...]")
    elements: List[List[int]] = Field(..., description="Element connectivity (0-indexed)")
    element_type: str = Field(..., description="Type of elements (e.g., 'triangle', 'quad')")
    boundaries: Dict[str, List[int]] = Field(..., description="Boundary node indices by boundary name")
    quality_metrics: MeshQualityMetrics
    bounding_box: Dict[str, float] = Field(..., description="Mesh bounding box {min_x, max_x, min_y, max_y, min_z, max_z}")


class MeshStatusDTO(BaseModel):
    """Mesh generation status"""
    mesh_id: UUID
    status: str = Field(..., description="Status: pending, generating, completed, failed")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    message: Optional[str] = None
    error: Optional[str] = None
    

# In-memory mesh storage (for demo purposes)
mesh_storage: Dict[UUID, Dict[str, Any]] = {}
mesh_generation_tasks: Dict[UUID, asyncio.Task] = {}


def get_mesh_service() -> EducationalMeshService:
    """Dependency to get mesh service instance"""
    return EducationalMeshService()


# Dependency injection function
def get_job_store() -> JobStore:
    """Get job store instance"""
    # This will be injected from the app factory
    from ...main import job_store
    return job_store


@router.post("/generate", response_model=MeshGenerationResponseDTO)
async def generate_mesh(
    request: MeshGenerationRequestDTO,
    mesh_service: EducationalMeshService = Depends(get_mesh_service)
) -> MeshGenerationResponseDTO:
    """
    Generate a new educational mesh
    
    This endpoint creates a mesh based on the specified geometry type and parameters.
    The mesh is generated using optimized algorithms for common educational geometries.
    
    **Supported Geometry Types:**
    - `rectangle`: Requires `width` and `height` parameters
    - `circle`: Requires `radius` parameter
    - `annulus`: Requires `inner_radius` and `outer_radius` parameters
    - `l_shape`: Requires `width`, `height`, `cutout_width`, and `cutout_height` parameters
    
    **Mesh Density Levels:**
    - 1: Very coarse (quick preview)
    - 2: Coarse
    - 3: Medium (default)
    - 4: Fine
    - 5: Very fine (detailed analysis)
    """
    mesh_id = uuid4()
    job_id = request.job_id or uuid4()
    
    try:
        # Create mesh generation request
        mesh_request = MeshGenerationRequest(
            geometry_type=request.geometry_type,
            parameters=request.parameters,
            mesh_density=request.mesh_density,
            enable_boundary_layer=request.enable_boundary_layer
        )
        
        # Validate geometry parameters
        validated_geometry = mesh_request.get_validated_geometry()
        
        # Generate mesh
        start_time = datetime.utcnow()
        output_dir = mesh_service._get_output_directory(str(job_id))
        
        success, quality_metrics = await mesh_service.generate_mesh(
            request.geometry_type,
            request.parameters,
            output_dir,
            request.mesh_density,
            job_id=str(job_id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Mesh generation failed"
            )
        
        generation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Get list of generated files
        mesh_files = [
            str(output_dir / "mesh.header"),
            str(output_dir / "mesh.nodes"),
            str(output_dir / "mesh.elements"),
            str(output_dir / "mesh.boundary")
        ]
        
        # Store mesh information
        mesh_data = {
            "mesh_id": mesh_id,
            "job_id": job_id,
            "geometry_type": request.geometry_type,
            "parameters": request.parameters,
            "quality_metrics": quality_metrics,
            "generation_time_ms": generation_time,
            "mesh_files": mesh_files,
            "output_dir": str(output_dir),
            "created_at": datetime.utcnow()
        }
        mesh_storage[mesh_id] = mesh_data
        
        return MeshGenerationResponseDTO(
            mesh_id=mesh_id,
            geometry_type=request.geometry_type,
            parameters=request.parameters,
            quality_metrics=quality_metrics,
            generation_time_ms=generation_time,
            mesh_files=mesh_files,
            preview_available=True
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Mesh generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate mesh"
        )


@router.get("/preview/{mesh_id}", response_model=MeshPreviewDTO)
async def get_mesh_preview(
    mesh_id: UUID,
    max_nodes: int = Query(1000, ge=100, le=10000, description="Maximum nodes to return for preview"),
    max_elements: int = Query(2000, ge=100, le=20000, description="Maximum elements to return for preview")
) -> MeshPreviewDTO:
    """
    Get simplified mesh data for visualization
    
    Returns a simplified version of the mesh suitable for frontend visualization.
    The data is downsampled if necessary to stay within the specified limits.
    """
    # Check if mesh exists
    if mesh_id not in mesh_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mesh {mesh_id} not found"
        )
    
    mesh_data = mesh_storage[mesh_id]
    output_dir = mesh_data["output_dir"]
    
    try:
        # Read mesh files
        from pathlib import Path
        mesh_dir = Path(output_dir)
        
        # Read nodes
        nodes = []
        with open(mesh_dir / "mesh.nodes", "r") as f:
            lines = f.readlines()
            for line in lines[1:]:  # Skip header
                parts = line.strip().split()
                if len(parts) >= 4:  # node_id x y z
                    nodes.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    if len(nodes) >= max_nodes:
                        break
        
        # Read elements
        elements = []
        element_type = "quad"  # Default for educational meshes
        with open(mesh_dir / "mesh.elements", "r") as f:
            lines = f.readlines()
            for line in lines[1:]:  # Skip header
                parts = line.strip().split()
                if len(parts) >= 5:  # elem_id type material nodes...
                    elem_type_code = int(parts[1])
                    # Map ElmerFEM element types to simple names
                    if elem_type_code == 303:  # Triangle
                        element_type = "triangle"
                        node_indices = [int(parts[i]) - 1 for i in range(3, 6)]  # 0-indexed
                    elif elem_type_code == 404:  # Quadrilateral
                        element_type = "quad"
                        node_indices = [int(parts[i]) - 1 for i in range(3, 7)]  # 0-indexed
                    else:
                        continue
                    
                    elements.append(node_indices)
                    if len(elements) >= max_elements:
                        break
        
        # Read boundaries
        boundaries = {}
        with open(mesh_dir / "mesh.boundary", "r") as f:
            lines = f.readlines()
            current_boundary = None
            for line in lines[1:]:  # Skip header
                parts = line.strip().split()
                if len(parts) >= 5:
                    boundary_id = int(parts[1])
                    boundary_name = f"boundary_{boundary_id}"
                    if boundary_name not in boundaries:
                        boundaries[boundary_name] = []
                    # Add boundary nodes (simplified - just first two nodes of boundary element)
                    boundaries[boundary_name].extend([int(parts[3]) - 1, int(parts[4]) - 1])
        
        # Remove duplicates from boundaries
        for name in boundaries:
            boundaries[name] = list(set(boundaries[name]))
        
        # Calculate bounding box
        if nodes:
            x_coords = [n[0] for n in nodes]
            y_coords = [n[1] for n in nodes]
            z_coords = [n[2] for n in nodes]
            bounding_box = {
                "min_x": min(x_coords),
                "max_x": max(x_coords),
                "min_y": min(y_coords),
                "max_y": max(y_coords),
                "min_z": min(z_coords),
                "max_z": max(z_coords)
            }
        else:
            bounding_box = {
                "min_x": 0, "max_x": 0,
                "min_y": 0, "max_y": 0,
                "min_z": 0, "max_z": 0
            }
        
        return MeshPreviewDTO(
            mesh_id=mesh_id,
            geometry_type=mesh_data["geometry_type"],
            nodes=nodes,
            elements=elements,
            element_type=element_type,
            boundaries=boundaries,
            quality_metrics=mesh_data["quality_metrics"],
            bounding_box=bounding_box
        )
        
    except Exception as e:
        logger.error(f"Failed to read mesh preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate mesh preview"
        )


@router.get("/status/{mesh_id}", response_model=MeshStatusDTO)
async def get_mesh_status(mesh_id: UUID) -> MeshStatusDTO:
    """
    Get the status of a mesh generation request
    
    Returns the current status and progress of a mesh generation task.
    """
    if mesh_id in mesh_storage:
        return MeshStatusDTO(
            mesh_id=mesh_id,
            status="completed",
            progress=100.0,
            message="Mesh generation completed successfully"
        )
    elif mesh_id in mesh_generation_tasks:
        # Check if task is still running
        task = mesh_generation_tasks[mesh_id]
        if task.done():
            try:
                task.result()
                return MeshStatusDTO(
                    mesh_id=mesh_id,
                    status="completed",
                    progress=100.0,
                    message="Mesh generation completed"
                )
            except Exception as e:
                return MeshStatusDTO(
                    mesh_id=mesh_id,
                    status="failed",
                    progress=0.0,
                    error=str(e)
                )
        else:
            return MeshStatusDTO(
                mesh_id=mesh_id,
                status="generating",
                progress=50.0,  # Simplified progress
                message="Mesh generation in progress"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mesh {mesh_id} not found"
        )


@router.websocket("/ws/{mesh_id}")
async def mesh_generation_websocket(
    websocket: WebSocket,
    mesh_id: UUID
):
    """
    WebSocket endpoint for real-time mesh generation status updates
    
    Connect to this endpoint to receive real-time updates about mesh generation progress.
    Messages are sent in JSON format with the following structure:
    ```json
    {
        "type": "status|progress|completed|error",
        "data": {
            "mesh_id": "uuid",
            "status": "generating",
            "progress": 75.0,
            "message": "Generating boundary elements..."
        }
    }
    ```
    """
    await websocket.accept()
    
    try:
        # Check if mesh exists or is being generated
        if mesh_id in mesh_storage:
            # Mesh already completed
            await websocket.send_json({
                "type": "completed",
                "data": {
                    "mesh_id": str(mesh_id),
                    "status": "completed",
                    "progress": 100.0,
                    "message": "Mesh generation already completed"
                }
            })
        else:
            # Simulate mesh generation progress updates
            progress_steps = [
                (10, "Initializing mesh generator..."),
                (25, "Parsing geometry parameters..."),
                (40, "Generating nodes..."),
                (60, "Creating elements..."),
                (80, "Defining boundaries..."),
                (95, "Optimizing mesh quality..."),
                (100, "Mesh generation completed!")
            ]
            
            for progress, message in progress_steps:
                await websocket.send_json({
                    "type": "progress" if progress < 100 else "completed",
                    "data": {
                        "mesh_id": str(mesh_id),
                        "status": "generating" if progress < 100 else "completed",
                        "progress": float(progress),
                        "message": message
                    }
                })
                
                if progress < 100:
                    await asyncio.sleep(0.5)  # Simulate processing time
        
        # Keep connection open for potential future updates
        while True:
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for mesh {mesh_id}")
    except Exception as e:
        logger.error(f"WebSocket error for mesh {mesh_id}: {e}")
        await websocket.send_json({
            "type": "error",
            "data": {
                "mesh_id": str(mesh_id),
                "status": "failed",
                "error": str(e)
            }
        })


@router.get("/geometries", response_model=List[Dict[str, Any]])
async def get_supported_geometries() -> List[Dict[str, Any]]:
    """
    Get list of supported geometry types with their parameter schemas
    
    Returns detailed information about each supported geometry type,
    including required parameters and validation constraints.
    """
    return [
        {
            "type": GeometryType.RECTANGLE,
            "name": "Rectangle",
            "description": "2D rectangular geometry",
            "parameters": {
                "width": {
                    "type": "float",
                    "required": True,
                    "min": 0.1,
                    "max": 100.0,
                    "description": "Rectangle width"
                },
                "height": {
                    "type": "float",
                    "required": True,
                    "min": 0.1,
                    "max": 100.0,
                    "description": "Rectangle height"
                }
            },
            "preview_image": "/static/geometries/rectangle.svg"
        },
        {
            "type": GeometryType.CIRCLE,
            "name": "Circle",
            "description": "2D circular geometry",
            "parameters": {
                "radius": {
                    "type": "float",
                    "required": True,
                    "min": 0.1,
                    "max": 50.0,
                    "description": "Circle radius"
                }
            },
            "preview_image": "/static/geometries/circle.svg"
        },
        {
            "type": GeometryType.ANNULUS,
            "name": "Annulus",
            "description": "2D ring geometry (circle with hole)",
            "parameters": {
                "inner_radius": {
                    "type": "float",
                    "required": True,
                    "min": 0.1,
                    "max": 49.0,
                    "description": "Inner radius (hole)"
                },
                "outer_radius": {
                    "type": "float",
                    "required": True,
                    "min": 0.2,
                    "max": 50.0,
                    "description": "Outer radius"
                }
            },
            "validation_rules": [
                "inner_radius < outer_radius",
                "inner_radius / outer_radius >= 0.1"
            ],
            "preview_image": "/static/geometries/annulus.svg"
        },
        {
            "type": GeometryType.L_SHAPE,
            "name": "L-Shape",
            "description": "2D L-shaped geometry",
            "parameters": {
                "width": {
                    "type": "float",
                    "required": True,
                    "min": 0.2,
                    "max": 100.0,
                    "description": "Total width"
                },
                "height": {
                    "type": "float",
                    "required": True,
                    "min": 0.2,
                    "max": 100.0,
                    "description": "Total height"
                },
                "cutout_width": {
                    "type": "float",
                    "required": True,
                    "min": 0.1,
                    "max": 99.0,
                    "description": "Width of cutout section"
                },
                "cutout_height": {
                    "type": "float",
                    "required": True,
                    "min": 0.1,
                    "max": 99.0,
                    "description": "Height of cutout section"
                }
            },
            "validation_rules": [
                "cutout_width < width",
                "cutout_height < height",
                "cutout_width >= 0.1 * width",
                "cutout_height >= 0.1 * height"
            ],
            "preview_image": "/static/geometries/l_shape.svg"
        }
    ] 