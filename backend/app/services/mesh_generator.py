"""
Mesh generation service for ElmerFEM simulations
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

from ..config.settings import settings

logger = logging.getLogger(__name__)


class MeshGenerator:
    """Generates mesh files using ElmerGrid for basic geometries"""
    
    def __init__(self):
        self.compose_project = settings.docker_compose_project
        self.elmer_container = settings.elmer_container_name
        self.compose_file = "/docker-compose.yml"
    
    async def generate_mesh(self, geometry: Dict[str, Any], working_directory: Path, mesh_density: float = 1.0) -> bool:
        """
        Generate mesh files for the given geometry
        
        Args:
            geometry: Geometry parameters (type, dimensions, etc.)
            working_directory: Directory where mesh files should be created
            mesh_density: Mesh density factor (higher = finer mesh)
            
        Returns:
            True if mesh generation successful, False otherwise
        """
        try:
            geometry_type = geometry.get("type", "rectangle").lower()
            
            if geometry_type == "rectangle":
                return await self._generate_rectangle_mesh(geometry, working_directory, mesh_density)
            else:
                logger.error(f"Unsupported geometry type: {geometry_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating mesh: {e}")
            return False
    
    async def _generate_rectangle_mesh(self, geometry: Dict[str, Any], working_directory: Path, mesh_density: float) -> bool:
        """Generate mesh for a rectangle geometry using ElmerGrid"""
        
        # Get rectangle dimensions
        width = geometry.get("width", 1.0)
        height = geometry.get("height", 1.0)
        
        # Calculate number of elements based on mesh density
        # Base resolution: 10 elements per unit length
        base_resolution = 10
        nx = max(2, int(width * base_resolution * mesh_density))
        ny = max(2, int(height * base_resolution * mesh_density))
        
        logger.info(f"Generating {nx}x{ny} rectangle mesh (size: {width}x{height})")
        
        # Convert to relative path inside container
        relative_path = working_directory.relative_to(settings.workspace_base_dir)
        container_work_dir = Path("/usr/src/elmerfem/work") / relative_path
        
        # Create ElmerGrid command for rectangle mesh
        # Format: ElmerGrid 1 2 test -out mesh -2d -autoclean
        # This creates a simple rectangular mesh and converts it to Elmer format
        cmd = [
            "docker", "compose",
            "-f", self.compose_file,
            "-p", self.compose_project,
            "exec",
            "-T",  # Disable pseudo-TTY
            "-w", str(container_work_dir),  # Working directory
            self.elmer_container,
            "ElmerGrid", "1", "2", "rectangle",
            "-out", "mesh",
            "-2d",
            f"-relh", str(1.0 / mesh_density),  # Relative mesh density
            "-autoclean"
        ]
        
        logger.info(f"Executing mesh generation command: {' '.join(cmd)}")
        
        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(working_directory)
        )
        
        # Wait for completion
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"ElmerGrid failed with return code {process.returncode}")
            logger.error(f"STDOUT: {stdout.decode()}")
            logger.error(f"STDERR: {stderr.decode()}")
            return False
        
        logger.info("Mesh generation completed successfully")
        logger.debug(f"ElmerGrid output: {stdout.decode()}")
        
        return True 