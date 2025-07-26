"""
Educational Mesh Service - Python wrapper for Fortran mesh generator

This service provides a streamlined interface for generating educational meshes
using the custom Fortran library. It includes comprehensive validation, error
handling, and quality metrics tracking.
"""

import asyncio
import ctypes
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

from pydantic import BaseModel, Field, field_validator, model_validator

# Configure structured logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GeometryType(str, Enum):
    """Supported geometry types for educational meshes"""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    ANNULUS = "annulus"
    L_SHAPE = "l_shape"


class RectangleGeometry(BaseModel):
    """Rectangle geometry parameters with validation"""
    width: float = Field(..., gt=0, le=100, description="Rectangle width")
    height: float = Field(..., gt=0, le=100, description="Rectangle height")
    
    @field_validator('width', 'height')
    @classmethod
    def validate_dimensions(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Dimensions must be positive")
        if v > 100:
            raise ValueError("Dimensions must be <= 100 for educational meshes")
        return v


class CircleGeometry(BaseModel):
    """Circle geometry parameters with validation"""
    radius: float = Field(..., gt=0, le=50, description="Circle radius")
    
    @field_validator('radius')
    @classmethod
    def validate_radius(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Radius must be positive")
        if v > 50:
            raise ValueError("Radius must be <= 50 for educational meshes")
        return v


class AnnulusGeometry(BaseModel):
    """Annulus geometry parameters with validation"""
    inner_radius: float = Field(..., gt=0, description="Inner radius")
    outer_radius: float = Field(..., gt=0, description="Outer radius")
    
    @model_validator(mode='after')
    def validate_radii(self) -> 'AnnulusGeometry':
        if self.inner_radius >= self.outer_radius:
            raise ValueError("Inner radius must be less than outer radius")
        if self.outer_radius > 50:
            raise ValueError("Outer radius must be <= 50 for educational meshes")
        if self.inner_radius / self.outer_radius < 0.1:
            raise ValueError("Inner/outer radius ratio must be >= 0.1 for mesh quality")
        return self


class LShapeGeometry(BaseModel):
    """L-shape geometry parameters with validation"""
    width: float = Field(..., gt=0, le=100, description="Total width")
    height: float = Field(..., gt=0, le=100, description="Total height")
    cutout_width: float = Field(..., gt=0, description="Cutout width")
    cutout_height: float = Field(..., gt=0, description="Cutout height")
    
    @model_validator(mode='after')
    def validate_cutout(self) -> 'LShapeGeometry':
        if self.cutout_width >= self.width:
            raise ValueError("Cutout width must be less than total width")
        if self.cutout_height >= self.height:
            raise ValueError("Cutout height must be less than total height")
        if self.cutout_width < 0.1 * self.width:
            raise ValueError("Cutout width must be at least 10% of total width")
        if self.cutout_height < 0.1 * self.height:
            raise ValueError("Cutout height must be at least 10% of total height")
        return self


class MeshGenerationRequest(BaseModel):
    """Validated mesh generation request"""
    geometry_type: GeometryType
    parameters: Dict[str, float]
    mesh_density: int = Field(3, ge=1, le=5, description="Mesh density level")
    enable_boundary_layer: bool = Field(False, description="Enable boundary layer mesh")
    
    @field_validator('mesh_density')
    @classmethod
    def validate_density(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Mesh density must be between 1 and 5")
        return v
    
    def get_validated_geometry(self) -> BaseModel:
        """Get validated geometry object based on type"""
        if self.geometry_type == GeometryType.RECTANGLE:
            return RectangleGeometry(**self.parameters)
        elif self.geometry_type == GeometryType.CIRCLE:
            return CircleGeometry(**self.parameters)
        elif self.geometry_type == GeometryType.ANNULUS:
            return AnnulusGeometry(**self.parameters)
        elif self.geometry_type == GeometryType.L_SHAPE:
            return LShapeGeometry(**self.parameters)
        else:
            raise ValueError(f"Unknown geometry type: {self.geometry_type}")


class MeshQualityMetrics(BaseModel):
    """Mesh quality metrics for database storage"""
    total_nodes: int = Field(..., ge=0)
    total_elements: int = Field(..., ge=0)
    min_angle: float = Field(..., ge=0, le=180)
    max_angle: float = Field(..., ge=0, le=180)
    aspect_ratio_avg: float = Field(..., ge=1)
    aspect_ratio_max: float = Field(..., ge=1)
    generation_time_ms: int = Field(..., ge=0)
    mesh_density_level: int = Field(..., ge=1, le=5)
    geometry_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GeometryParams(ctypes.Structure):
    """C-compatible structure for geometry parameters"""
    _fields_ = [
        ("geometry_type", ctypes.c_int32),
        ("params", ctypes.c_double * 10),
        ("mesh_density", ctypes.c_int32),
        ("boundary_layer", ctypes.c_int32)
    ]


class MeshQuality(ctypes.Structure):
    """C-compatible structure for mesh quality metrics"""
    _fields_ = [
        ("min_angle", ctypes.c_double),
        ("max_angle", ctypes.c_double),
        ("aspect_ratio_avg", ctypes.c_double),
        ("aspect_ratio_max", ctypes.c_double),
        ("total_elements", ctypes.c_int32),
        ("total_nodes", ctypes.c_int32),
        ("return_code", ctypes.c_int32)
    ]


class EducationalMeshService:
    """Service for generating educational meshes using Fortran library"""
    
    def __init__(self):
        """Initialize the mesh service and load the Fortran library"""
        self._lib = None
        self._lib_path = None
        self._initialize_library()
    
    def _initialize_library(self):
        """Initialize the Fortran library with comprehensive error handling"""
        try:
            # Find the library path
            lib_path = Path(__file__).parent.parent.parent / "elmerfem_custom" / "mesh_generator" / "libeducational_mesh.so"
            
            if not lib_path.exists():
                # Try alternative paths
                alt_paths = [
                    Path(__file__).parent.parent.parent / "elmerfem_custom" / "mesh_generator" / "libeducational_mesh.dll",
                    Path(__file__).parent.parent.parent / "elmerfem_custom" / "mesh_generator" / "educational_mesh.so",
                ]
                
                for alt_path in alt_paths:
                    if alt_path.exists():
                        lib_path = alt_path
                        break
                else:
                    raise FileNotFoundError(
                        f"Educational mesh library not found. Searched paths:\n"
                        f"  - {lib_path}\n" +
                        "\n  - ".join(str(p) for p in alt_paths)
                    )
            
            # Load the shared library
            self._lib = ctypes.CDLL(str(lib_path))
            self._lib_path = lib_path
            
            # Set up the function signature
            self._lib.generate_mesh.argtypes = [
                ctypes.POINTER(GeometryParams),
                ctypes.c_char_p,
                ctypes.POINTER(MeshQuality)
            ]
            self._lib.generate_mesh.restype = None
            
            logger.info(
                "Educational mesh library initialized",
                extra={
                    "library_path": str(lib_path),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to initialize educational mesh library",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.utcnow().isoformat()
                },
                exc_info=True
            )
            # Don't raise - allow service to continue without library
            # This enables API testing on Windows even without the compiled Fortran library
            self._lib = None
            self._lib_path = None
            logger.warning("Educational mesh service running without Fortran library - API endpoints will return simulation mode responses")
    
    async def generate_mesh(
        self, 
        request: MeshGenerationRequest,
        output_dir: Path,
        job_id: Optional[str] = None
    ) -> Tuple[bool, MeshQualityMetrics]:
        """
        Generate mesh for educational geometry with validation and quality metrics
        
        Args:
            request: Validated mesh generation request
            output_dir: Directory to save mesh files
            job_id: Optional job ID for tracking
            
        Returns:
            Tuple of (success, quality_metrics)
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "Starting mesh generation",
            extra={
                "job_id": job_id,
                "geometry_type": request.geometry_type.value,
                "mesh_density": request.mesh_density,
                "output_dir": str(output_dir),
                "timestamp": start_time.isoformat()
            }
        )
        
        try:
            # Validate geometry parameters
            geometry = request.get_validated_geometry()
            
            # Map geometry type to integer
            geometry_map = {
                GeometryType.RECTANGLE: 1,
                GeometryType.CIRCLE: 2,
                GeometryType.ANNULUS: 3,
                GeometryType.L_SHAPE: 4
            }
            
            # Create geometry parameters structure
            geom_params = GeometryParams()
            geom_params.geometry_type = geometry_map[request.geometry_type]
            geom_params.mesh_density = request.mesh_density
            geom_params.boundary_layer = 1 if request.enable_boundary_layer else 0
            
            # Fill in parameters based on validated geometry
            if isinstance(geometry, RectangleGeometry):
                geom_params.params[0] = geometry.width
                geom_params.params[1] = geometry.height
            elif isinstance(geometry, CircleGeometry):
                geom_params.params[0] = geometry.radius
            elif isinstance(geometry, AnnulusGeometry):
                geom_params.params[0] = geometry.inner_radius
                geom_params.params[1] = geometry.outer_radius
            elif isinstance(geometry, LShapeGeometry):
                geom_params.params[0] = geometry.width
                geom_params.params[1] = geometry.height
                geom_params.params[2] = geometry.cutout_width
                geom_params.params[3] = geometry.cutout_height
            
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create quality structure
            quality = MeshQuality()
            
            # Call the Fortran mesh generator in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._lib.generate_mesh,
                ctypes.byref(geom_params),
                str(output_dir).encode('utf-8'),
                ctypes.byref(quality)
            )
            
            # Check return code
            if quality.return_code != 0:
                error_msg = self._get_error_message(quality.return_code)
                logger.error(
                    "Mesh generation failed",
                    extra={
                        "job_id": job_id,
                        "return_code": quality.return_code,
                        "error_message": error_msg,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                raise RuntimeError(f"Mesh generation failed: {error_msg}")
            
            # Verify mesh files exist
            mesh_files = self._verify_mesh_files(output_dir)
            
            # Calculate generation time
            generation_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Create quality metrics object
            metrics = MeshQualityMetrics(
                total_nodes=quality.total_nodes,
                total_elements=quality.total_elements,
                min_angle=quality.min_angle,
                max_angle=quality.max_angle,
                aspect_ratio_avg=quality.aspect_ratio_avg,
                aspect_ratio_max=quality.aspect_ratio_max,
                generation_time_ms=generation_time_ms,
                mesh_density_level=request.mesh_density,
                geometry_type=request.geometry_type.value
            )
            
            # Log success with structured data
            logger.info(
                "Mesh generation completed successfully",
                extra={
                    "job_id": job_id,
                    "metrics": metrics.dict(),
                    "mesh_files": mesh_files,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return True, metrics
            
        except Exception as e:
            logger.error(
                "Mesh generation error",
                extra={
                    "job_id": job_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "geometry_type": request.geometry_type.value,
                    "timestamp": datetime.utcnow().isoformat()
                },
                exc_info=True
            )
            
            # Create error metrics
            error_metrics = MeshQualityMetrics(
                total_nodes=0,
                total_elements=0,
                min_angle=0,
                max_angle=0,
                aspect_ratio_avg=1.0,  # Changed from 0 to 1.0
                aspect_ratio_max=1.0,  # Changed from 0 to 1.0
                generation_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                mesh_density_level=request.mesh_density,
                geometry_type=request.geometry_type.value
            )
            
            return False, error_metrics
    
    def _verify_mesh_files(self, output_dir: Path) -> Dict[str, str]:
        """Verify that all required mesh files exist"""
        required_files = {
            'header': 'mesh.header',
            'nodes': 'mesh.nodes',
            'elements': 'mesh.elements',
            'boundary': 'mesh.boundary'
        }
        
        mesh_files = {}
        missing_files = []
        
        for file_type, filename in required_files.items():
            file_path = output_dir / filename
            if file_path.exists():
                mesh_files[file_type] = str(file_path)
            else:
                missing_files.append(filename)
        
        if missing_files:
            raise FileNotFoundError(
                f"Missing mesh files: {', '.join(missing_files)} in {output_dir}"
            )
        
        return mesh_files
    
    def _get_error_message(self, return_code: int) -> str:
        """Get human-readable error message for return code"""
        error_messages = {
            -1: "Invalid geometry type",
            -2: "Invalid parameters",
            -3: "Memory allocation error",
            -4: "File I/O error",
            -5: "Mesh generation algorithm failure",
            -6: "Invalid mesh density level",
            -7: "Geometry validation failed",
            -8: "Mesh quality check failed"
        }
        return error_messages.get(return_code, f"Unknown error (code: {return_code})")
    
    async def save_quality_metrics(
        self,
        job_id: str,
        metrics: MeshQualityMetrics,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save mesh quality metrics to job metadata
        
        This method should be called by the job launcher after successful mesh generation
        to persist quality metrics in the database.
        
        Args:
            job_id: Job ID to associate metrics with
            metrics: Quality metrics to save
            metadata: Additional metadata to merge
        """
        logger.info(
            "Saving mesh quality metrics",
            extra={
                "job_id": job_id,
                "metrics": metrics.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # In a real implementation, this would update the job's metadata in the database
        # For now, we'll just log it
        # The job launcher should handle the actual database update
        pass 