"""SIF Engine package for ElmerFEM Educational Platform"""

from .env import get_env
from .context import build_context
from .units import to_SI, convert_length, convert_temperature
from .renderer import render_sif, validate_geometry_physics_compatibility

__all__ = [
    "get_env",
    "build_context",
    "to_SI",
    "convert_length",
    "convert_temperature",
    "render_sif",
    "validate_geometry_physics_compatibility",
] 