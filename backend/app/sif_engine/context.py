"""
Parameter to context mapper for SIF template rendering
"""

import logging
from typing import Any, Dict, List, Optional

from ..models import (
    BoundaryCondition,
    MaterialProperties,
    SimulationParamsDTO,
    SimulationType,
)
from ..services.materials_service import materials_service
from .units import convert_temperature, convert_force

logger = logging.getLogger(__name__)


def build_context(params: SimulationParamsDTO) -> Dict[str, Any]:
    """
    Transform SimulationParamsDTO into a context dictionary for template rendering
    
    Args:
        params: Simulation parameters from API
        
    Returns:
        Dictionary with template context variables
    """
    context = {
        # Basic information
        "case_name": "case",
        "simulation_type": params.simulation_type.value,
        
        # Simulation settings
        "steady_state": params.time_settings is None or params.time_settings.get("steady_state", True),
        "max_iterations": params.solver_settings.get("max_iterations", 100) if params.solver_settings else 100,
        "time_end": params.time_settings.get("end_time", 1.0) if params.time_settings else 1.0,
        "time_step": params.time_settings.get("time_step", 0.1) if params.time_settings else 0.1,
        
        # Solver settings
        "solver_settings": _build_solver_settings(params),
        
        # Geometry
        "geometry": params.geometry,
        "mesh_density": params.mesh_density,
        
        # Material properties
        "material": _build_material_context(params),
        
        # Boundary conditions
        "boundary_conditions": _build_boundary_conditions(params),
        
        # Additional flags
        "has_custom_material": params.custom_material is not None,
        "material_id": params.material_id,
    }
    
    return context


def _build_solver_settings(params: SimulationParamsDTO) -> Dict[str, Any]:
    """Build solver-specific settings"""
    defaults = {
        "linear_solver": "Iterative",
        "linear_method": "BiCGStab",
        "linear_max_iterations": 500,
        "linear_tolerance": 1.0e-10,
        "linear_preconditioning": "ILU0",
        "nonlinear_max_iterations": 20,
        "nonlinear_tolerance": 1.0e-7,
        "steady_state_tolerance": 1.0e-5,
        "stabilize": True,
        "bubbles": False,
        "lumped_mass": False,
        "optimize_bandwidth": True,
    }
    
    # Override with user settings if provided
    if params.solver_settings:
        defaults.update(params.solver_settings)
    
    return defaults


def _build_material_context(params: SimulationParamsDTO) -> Dict[str, Any]:
    """Build material properties context"""
    
    # First, check if we have a material_id and try to load from materials service
    if params.material_id:
        logger.info(f"Loading material properties for material_id: {params.material_id}")
        try:
            material_data = materials_service.get_material_by_id(params.material_id)
            if material_data:
                logger.info(f"Found material: {material_data['name']}")
                # Build context from materials database
                material_context = {
                    "name": f"Material 1 - {material_data['name']}",
                    "from_library": True,
                    "library_id": params.material_id,
                }
                
                # Add properties based on simulation type
                if params.simulation_type == SimulationType.HEAT_TRANSFER:
                    material_context.update({
                        "thermal_conductivity": material_data["k"],
                        "density": material_data["rho"],
                        "heat_capacity": material_data.get("C", 1.0),  # C might not be in our materials.json yet
                    })
                elif params.simulation_type == SimulationType.STRUCTURAL_MECHANICS:
                    material_context.update({
                        "youngs_modulus": material_data["E"],
                        "poisson_ratio": material_data["nu"],
                        "density": material_data["rho"],
                    })
                
                return material_context
        except Exception as e:
            logger.warning(f"Failed to load material from library: {e}. Falling back to custom/default.")
    
    # Fall back to custom material or defaults
    mat_props = params.custom_material or params.material_properties or MaterialProperties()
    
    # Build context based on simulation type
    material_context = {
        "name": f"Material {params.material_id}" if params.material_id else "Custom Material",
        "from_library": False,
    }
    
    if params.simulation_type == SimulationType.HEAT_TRANSFER:
        material_context.update({
            "thermal_conductivity": mat_props.k or 1.0,
            "density": mat_props.rho or 1.0,
            "heat_capacity": mat_props.C or 1.0,
        })
    elif params.simulation_type == SimulationType.STRUCTURAL_MECHANICS:
        material_context.update({
            "youngs_modulus": mat_props.E or 210e9,
            "poisson_ratio": mat_props.nu or 0.3,
            "density": mat_props.rho or 7850,
        })
    
    return material_context


def _build_boundary_conditions(params: SimulationParamsDTO) -> List[Dict[str, Any]]:
    """Build boundary conditions list for template"""
    bc_list = []
    
    for i, bc in enumerate(params.boundary_conditions, 1):
        bc_dict = {
            "index": i,
            "name": bc.name or f"BC {i}",
            "type": bc.type,
            "value": bc.value,
            "location": bc.location,
            "surface_id": bc.surface_id or i,  # Default to index if not specified
        }
        
        # Convert units if needed
        if bc.type == "temperature":
            # Keep temperature as-is (assume Kelvin or will be converted elsewhere)
            pass
        elif bc.type == "force" and bc.component:
            bc_dict["component"] = bc.component
            bc_dict["value"] = convert_force(bc.value)
        elif bc.type == "displacement" and bc.component:
            bc_dict["component"] = bc.component
        
        bc_list.append(bc_dict)
    
    # Map location names to surface IDs if needed
    _map_locations_to_surfaces(bc_list, params.geometry)
    
    return bc_list


def _map_locations_to_surfaces(bc_list: List[Dict[str, Any]], geometry: Dict[str, Any]) -> None:
    """Map location names to surface IDs based on geometry type"""
    # Default mappings for common geometries
    location_mappings = {
        "rectangle": {
            "left": 1,
            "right": 2,
            "bottom": 3,
            "top": 4,
        },
        "box": {
            "left": 1,
            "right": 2,
            "bottom": 3,
            "top": 4,
            "front": 5,
            "back": 6,
        },
        "cylinder": {
            "bottom": 1,
            "top": 2,
            "side": 3,
        },
    }
    
    geometry_type = geometry.get("type", "").lower()
    if geometry_type in location_mappings:
        mapping = location_mappings[geometry_type]
        for bc in bc_list:
            location = bc.get("location", "").lower()
            if location in mapping and bc.get("surface_id") == bc["index"]:
                bc["surface_id"] = mapping[location] 