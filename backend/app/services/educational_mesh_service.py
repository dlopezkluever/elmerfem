"""
Educational Mesh Service - Python wrapper for Fortran mesh generator
"""

import ctypes
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


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
        # Find the library path
        lib_path = Path(__file__).parent.parent.parent / "elmerfem_custom" / "mesh_generator" / "libeducational_mesh.so"
        
        if not lib_path.exists():
            raise FileNotFoundError(f"Educational mesh library not found at {lib_path}")
        
        # Load the shared library
        self.lib = ctypes.CDLL(str(lib_path))
        
        # Set up the function signature
        self.generate_mesh = self.lib.generate_mesh
        self.generate_mesh.argtypes = [
            ctypes.POINTER(GeometryParams),
            ctypes.c_char_p,
            ctypes.POINTER(MeshQuality)
        ]
        self.generate_mesh.restype = None
        
        logger.info(f"Loaded educational mesh library from {lib_path}")
    
    async def generate_mesh(
        self, 
        geometry_type: str,
        parameters: Dict[str, float],
        output_dir: Path,
        mesh_density: int = 3
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Generate mesh for educational geometry
        
        Args:
            geometry_type: Type of geometry ('rectangle', 'circle', 'annulus', 'l_shape')
            parameters: Geometry-specific parameters
            output_dir: Directory to save mesh files
            mesh_density: Mesh density level (1-5)
            
        Returns:
            Tuple of (success, quality_metrics)
        """
        # Map geometry type to integer
        geometry_map = {
            'rectangle': 1,
            'circle': 2,
            'annulus': 3,
            'l_shape': 4
        }
        
        if geometry_type not in geometry_map:
            logger.error(f"Unknown geometry type: {geometry_type}")
            return False, {"error": f"Unknown geometry type: {geometry_type}"}
        
        # Create geometry parameters
        geometry = GeometryParams()
        geometry.geometry_type = geometry_map[geometry_type]
        geometry.mesh_density = max(1, min(5, mesh_density))
        geometry.boundary_layer = 0
        
        # Fill in parameters based on geometry type
        if geometry_type == 'rectangle':
            geometry.params[0] = parameters.get('width', 1.0)
            geometry.params[1] = parameters.get('height', 1.0)
        elif geometry_type == 'circle':
            geometry.params[0] = parameters.get('radius', 1.0)
        elif geometry_type == 'annulus':
            geometry.params[0] = parameters.get('inner_radius', 0.5)
            geometry.params[1] = parameters.get('outer_radius', 1.0)
        elif geometry_type == 'l_shape':
            geometry.params[0] = parameters.get('width', 2.0)
            geometry.params[1] = parameters.get('height', 2.0)
            geometry.params[2] = parameters.get('cutout_width', 1.0)
            geometry.params[3] = parameters.get('cutout_height', 1.0)
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create quality structure
        quality = MeshQuality()
        
        # Call the Fortran mesh generator
        try:
            self.generate_mesh(
                ctypes.byref(geometry),
                str(output_dir).encode('utf-8'),
                ctypes.byref(quality)
            )
        except Exception as e:
            logger.error(f"Error calling mesh generator: {e}")
            return False, {"error": str(e)}
        
        # Check return code
        if quality.return_code != 0:
            logger.error(f"Mesh generation failed with code {quality.return_code}")
            return False, {"error": f"Mesh generation failed with code {quality.return_code}"}
        
        # Verify mesh files exist
        expected_files = ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']
        for filename in expected_files:
            if not (output_dir / filename).exists():
                logger.error(f"Expected mesh file {filename} not found")
                return False, {"error": f"Expected mesh file {filename} not found"}
        
        # Return quality metrics
        quality_dict = {
            "total_nodes": quality.total_nodes,
            "total_elements": quality.total_elements,
            "min_angle": quality.min_angle,
            "max_angle": quality.max_angle,
            "aspect_ratio_avg": quality.aspect_ratio_avg,
            "aspect_ratio_max": quality.aspect_ratio_max
        }
        
        logger.info(f"Successfully generated {geometry_type} mesh with {quality.total_elements} elements")
        return True, quality_dict 