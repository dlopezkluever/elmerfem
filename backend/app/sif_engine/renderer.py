"""
SIF rendering function with I/O handling
"""

import logging
from pathlib import Path
from typing import Union

from jinja2 import TemplateNotFound

from ..models import SimulationParamsDTO, SimulationType
from .context import build_context
from .env import get_env

logger = logging.getLogger(__name__)

# Map simulation types to template names
TEMPLATE_MAPPING = {
    SimulationType.HEAT_TRANSFER: "heat_transfer.sif.j2",
    SimulationType.STRUCTURAL_MECHANICS: "structural_mechanics.sif.j2",
    # Future additions
    # SimulationType.FLUID_DYNAMICS: "fluid_dynamics.sif.j2",
    # SimulationType.ELECTROMAGNETICS: "electromagnetics.sif.j2",
}


def render_sif(params: SimulationParamsDTO, output_path: Union[str, Path]) -> str:
    """
    Render SIF file from parameters and write to disk
    
    Args:
        params: Simulation parameters
        output_path: Path where the SIF file should be written
        
    Returns:
        The rendered SIF content as a string
        
    Raises:
        ValueError: If simulation type is not supported
        TemplateNotFound: If template file is missing
        IOError: If unable to write output file
    """
    # Get template name
    template_name = TEMPLATE_MAPPING.get(params.simulation_type)
    if not template_name:
        raise ValueError(
            f"Unsupported simulation type: {params.simulation_type}. "
            f"Supported types: {list(TEMPLATE_MAPPING.keys())}"
        )
    
    # Build context
    logger.info(f"Building context for {params.simulation_type.value} simulation")
    context = build_context(params)
    
    # Get Jinja2 environment and template
    env = get_env()
    try:
        template = env.get_template(template_name)
    except TemplateNotFound:
        logger.error(f"Template not found: {template_name}")
        raise TemplateNotFound(
            f"SIF template '{template_name}' not found. "
            "Please ensure template files are properly installed."
        )
    
    # Render template
    logger.info(f"Rendering SIF template: {template_name}")
    rendered_content = template.render(**context)
    
    # Write to file
    output_path = Path(output_path)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered_content, encoding='utf-8')
        logger.info(f"SIF file written to: {output_path}")
    except IOError as e:
        logger.error(f"Failed to write SIF file: {e}")
        raise IOError(f"Unable to write SIF file to {output_path}: {e}")
    
    return rendered_content


def validate_geometry_physics_compatibility(params: SimulationParamsDTO) -> None:
    """
    Validate that the geometry is compatible with the physics type
    
    Args:
        params: Simulation parameters to validate
        
    Raises:
        ValueError: If geometry and physics are incompatible
    """
    geometry_type = params.geometry.get("type", "").lower()
    simulation_type = params.simulation_type
    
    # Define valid combinations
    valid_combinations = {
        SimulationType.HEAT_TRANSFER: ["rectangle", "box", "cylinder", "sphere"],
        SimulationType.STRUCTURAL_MECHANICS: ["rectangle", "box", "beam", "cylinder"],
    }
    
    valid_geometries = valid_combinations.get(simulation_type, [])
    
    if geometry_type not in valid_geometries:
        raise ValueError(
            f"Geometry type '{geometry_type}' is not compatible with "
            f"{simulation_type.value} simulation. Valid geometries: {valid_geometries}"
        )
    
    # Additional validation for specific combinations
    if simulation_type == SimulationType.STRUCTURAL_MECHANICS:
        # Ensure at least one displacement BC exists
        has_displacement_bc = any(
            bc.type in ["displacement", "fixed"] 
            for bc in params.boundary_conditions
        )
        if not has_displacement_bc:
            raise ValueError(
                "Structural mechanics simulation requires at least one "
                "displacement or fixed boundary condition"
            ) 