"""
Data Transfer Objects (DTOs) for the API
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class SimulationType(str, Enum):
    """Supported simulation types"""
    HEAT_TRANSFER = "heat_transfer"
    STRUCTURAL_MECHANICS = "structural_mechanics"
    # Future: Add more physics types
    # FLUID_DYNAMICS = "fluid_dynamics"
    # ELECTROMAGNETICS = "electromagnetics"


class MaterialProperties(BaseModel):
    """Material properties for custom materials"""
    E: Optional[float] = Field(None, description="Young's Modulus (Pa)")
    nu: Optional[float] = Field(None, description="Poisson's Ratio")
    rho: Optional[float] = Field(None, description="Density (kg/m³)")
    k: Optional[float] = Field(None, description="Thermal Conductivity (W/mK)")
    C: Optional[float] = Field(None, description="Heat Capacity (J/kgK)")


class BoundaryCondition(BaseModel):
    """Boundary condition definition"""
    type: str = Field(..., description="Type of BC (temperature, heat_flux, displacement, force, etc.)")
    value: float = Field(..., description="BC value")
    location: str = Field(..., description="Location (left, right, top, bottom, etc.)")
    component: Optional[str] = Field(None, description="Component for vector BCs (x, y, z)")
    name: Optional[str] = None
    surface_id: Optional[int] = None
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate boundary condition type"""
        valid_types = ["temperature", "heat_flux", "displacement", "force", "pressure", "fixed"]
        if v not in valid_types:
            raise ValueError(f"Invalid BC type: {v}. Must be one of {valid_types}")
        return v


class SimulationParamsDTO(BaseModel):
    """Input parameters for creating a simulation"""
    simulation_type: SimulationType
    type: Optional[SimulationType] = Field(None, description="Alias for simulation_type")
    geometry: Dict[str, Any] = Field(..., description="Geometry parameters")
    material_id: Optional[str] = Field(None, description="Material library ID")
    custom_material: Optional[MaterialProperties] = None
    material_properties: Optional[MaterialProperties] = Field(None, description="Alias for custom_material")
    boundary_conditions: List[BoundaryCondition] = Field(default_factory=list)
    mesh_density: float = Field(1.0, description="Mesh density factor", gt=0, le=10)
    time_settings: Optional[Dict[str, Any]] = None
    solver_settings: Optional[Dict[str, Any]] = None
    
    @model_validator(mode='after')
    def validate_material_and_aliases(self):
        """Handle aliases and ensure material is provided"""
        # Handle type alias
        if self.type is not None and self.simulation_type is None:
            self.simulation_type = self.type
        elif self.simulation_type is not None and self.type is None:
            self.type = self.simulation_type
            
        # Handle material_properties alias
        if self.material_properties is not None and self.custom_material is None:
            self.custom_material = self.material_properties
        elif self.custom_material is not None and self.material_properties is None:
            self.material_properties = self.custom_material
            
        # Ensure either material_id or custom_material is provided
        if self.custom_material is None and self.material_id is None:
            raise ValueError("Either material_id or custom_material must be provided")
            
        return self
    
    @field_validator('mesh_density')
    @classmethod 
    def validate_mesh_density(cls, v: float) -> float:
        """Validate mesh density"""
        # Allow string values like "medium", "fine", etc. by converting to float
        if isinstance(v, str):
            density_map = {
                "coarse": 0.5,
                "medium": 1.0,
                "fine": 2.0,
                "very_fine": 3.0
            }
            if v.lower() in density_map:
                return density_map[v.lower()]
            else:
                raise ValueError(f"Invalid mesh density: {v}. Must be a number or one of {list(density_map.keys())}")
        return v


class JobStatus(str, Enum):
    """Simulation job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationStatusDTO(BaseModel):
    """Status information for a running simulation"""
    id: UUID
    status: JobStatus
    progress: float = Field(0.0, ge=0, le=100)
    message: Optional[str] = None
    current_step: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SimulationResultDTO(BaseModel):
    """Result information for a completed simulation"""
    id: UUID
    status: JobStatus
    result_files: List[str] = Field(default_factory=list)
    vtk_file: Optional[str] = None
    log_file: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: datetime
    execution_time: float = Field(..., description="Execution time in seconds")


class SimulationCreateResponseDTO(BaseModel):
    """Response for simulation creation"""
    id: UUID
    status: JobStatus
    message: str = "Simulation job created successfully" 