"""
Mesh-related Data Transfer Objects
"""

from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

# Re-export geometry models from educational_mesh_service for API consistency
from ..services.educational_mesh_service import (
    GeometryType,
    RectangleGeometry,
    CircleGeometry,
    AnnulusGeometry,
    LShapeGeometry,
    MeshGenerationRequest,
    MeshQualityMetrics,
)


class MeshGenerationParams(BaseModel):
    """Parameters for mesh generation via API"""
    geometry_type: GeometryType = Field(..., description="Type of geometry to generate")
    parameters: Dict[str, float] = Field(..., description="Geometry-specific parameters")
    mesh_density: int = Field(3, ge=1, le=5, description="Mesh density level (1=coarse, 5=fine)")
    enable_boundary_layer: bool = Field(False, description="Enable boundary layer for fluid/heat transfer")
    
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
                },
                {
                    "geometry_type": "annulus",
                    "parameters": {"inner_radius": 2.0, "outer_radius": 5.0},
                    "mesh_density": 3,
                    "enable_boundary_layer": False
                },
                {
                    "geometry_type": "l_shape",
                    "parameters": {
                        "width": 10.0,
                        "height": 10.0,
                        "cutout_width": 5.0,
                        "cutout_height": 5.0
                    },
                    "mesh_density": 4,
                    "enable_boundary_layer": False
                }
            ]
        }


# Export all mesh-related models
__all__ = [
    "GeometryType",
    "RectangleGeometry",
    "CircleGeometry",
    "AnnulusGeometry",
    "LShapeGeometry",
    "MeshGenerationRequest",
    "MeshQualityMetrics",
    "MeshGenerationParams",
] 