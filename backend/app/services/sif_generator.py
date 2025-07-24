"""
SIF file generator for ElmerSolver simulations
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import BoundaryCondition, MaterialProperties, SimulationParamsDTO, SimulationType
from ..sif_engine import render_sif, validate_geometry_physics_compatibility

logger = logging.getLogger(__name__)


class SIFGenerator:
    """Generates SIF (Solver Input File) content for ElmerSolver"""
    
    def generate(self, params: SimulationParamsDTO, case_name: str = "case") -> str:
        """
        Generate SIF file content based on simulation parameters
        
        Args:
            params: Simulation parameters
            case_name: Name for the case (default: "case")
            
        Returns:
            SIF file content as string
        """
        # Validate geometry-physics compatibility
        validate_geometry_physics_compatibility(params)
        
        # Use template-based rendering (but return content only for backward compatibility)
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(mode='w', suffix='.sif', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            content = render_sif(params, tmp_path)
            return content
        finally:
            # Clean up temp file
            if tmp_path.exists():
                tmp_path.unlink()

    
    async def write_sif_file(
        self, params: SimulationParamsDTO, output_path: Path, case_name: str = "case"
    ) -> Path:
        """
        Generate and write SIF file to disk
        
        Args:
            params: Simulation parameters
            output_path: Directory to write the file
            case_name: Name for the case (default: "case")
            
        Returns:
            Path to the written SIF file
        """
        # Validate geometry-physics compatibility
        validate_geometry_physics_compatibility(params)
        
        # Ensure directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate SIF file path
        sif_file = output_path / f"{case_name}.sif"
        
        # Use new template-based rendering
        render_sif(params, sif_file)
        logger.info(f"Generated SIF file: {sif_file}")
        
        return sif_file 