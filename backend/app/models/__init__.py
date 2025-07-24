"""Models package for ElmerFEM Educational Platform"""

from .dtos import (
    BoundaryCondition,
    JobStatus,
    MaterialProperties,
    SimulationCreateResponseDTO,
    SimulationParamsDTO,
    SimulationResultDTO,
    SimulationStatusDTO,
    SimulationType,
)
from .job import SimulationJob

__all__ = [
    "BoundaryCondition",
    "JobStatus",
    "MaterialProperties",
    "SimulationCreateResponseDTO",
    "SimulationJob",
    "SimulationParamsDTO",
    "SimulationResultDTO",
    "SimulationStatusDTO",
    "SimulationType",
] 