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


class JobStatus(str, Enum):
    """Job status states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MaterialProperties(BaseModel):
    """Material properties for simulation"""
    E: Optional[float] = Field(None, description="Young's Modulus (Pa)", gt=0)
    nu: Optional[float] = Field(None, description="Poisson's Ratio", ge=0, le=0.5)
    rho: Optional[float] = Field(None, description="Density (kg/m³)", gt=0)
    k: Optional[float] = Field(None, description="Thermal Conductivity (W/mK)", gt=0)
    C: Optional[float] = Field(None, description="Heat Capacity (J/kgK)", gt=0)


class BoundaryCondition(BaseModel):
    """Boundary condition specification"""
    type: str = Field(..., description="Type of boundary condition")
    value: float = Field(..., description="Value of the boundary condition")
    location: str = Field(..., description="Location identifier")
    surface_id: Optional[int] = Field(None, description="Surface ID for mesh boundary")
    component: Optional[int] = Field(None, description="Component (1, 2, or 3) for vector BC")
    name: Optional[str] = Field(None, description="Optional name for the boundary condition")


class SimulationParamsDTO(BaseModel):
    """Input parameters for creating a simulation"""
    simulation_type: SimulationType
    type: Optional[SimulationType] = Field(None, description="Alias for simulation_type")
    geometry: Dict[str, Any] = Field(..., description="Geometry parameters")
    material_id: Optional[int] = Field(None, description="Material library ID")
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


class SimulationCreateResponseDTO(BaseModel):
    """Response after creating a simulation"""
    id: UUID
    status: JobStatus
    created_at: datetime
    message: str = "Simulation job created successfully"


class SimulationStatusDTO(BaseModel):
    """Current status of a simulation"""
    id: UUID
    status: JobStatus
    progress: float = Field(0.0, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    current_step: Optional[str] = None
    total_steps: Optional[int] = None


class SimulationResultDTO(BaseModel):
    """Simulation result information"""
    id: UUID
    status: JobStatus
    result_files: List[str] = Field(default_factory=list)
    output_directory: Optional[Path] = None
    summary: Optional[Dict[str, Any]] = None
    vtk_file: Optional[str] = None
    log_file: Optional[str] = None
    sif_file: Optional[str] = None 