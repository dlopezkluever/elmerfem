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
from .mesh_dtos import (
    GeometryType,
    RectangleGeometry,
    CircleGeometry,
    AnnulusGeometry,
    LShapeGeometry,
    MeshGenerationRequest,
    MeshQualityMetrics,
    MeshGenerationParams,
)

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
    "GeometryType",
    "RectangleGeometry",
    "CircleGeometry",
    "AnnulusGeometry",
    "LShapeGeometry",
    "MeshGenerationRequest",
    "MeshQualityMetrics",
    "MeshGenerationParams",
] 