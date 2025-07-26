#!/usr/bin/env python3
"""
Educational Mesh Generator - Python wrapper for Fortran mesh generation library

This module provides a Python interface to the high-performance Fortran mesh generator
specifically designed for educational finite element analysis workflows. The wrapper
uses ctypes for direct library calls, minimizing overhead to achieve sub-50ms
performance targets.

Author: Educational FEM Platform Team
Version: 1.0.0
"""

import ctypes
import logging
import os
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, Union, List
from enum import IntEnum
import threading
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)


class GeometryType(IntEnum):
    """Enumeration of supported geometry types"""
    RECTANGLE = 1
    CIRCLE = 2
    ANNULUS = 3
    L_SHAPE = 4


class MeshDensity(IntEnum):
    """Predefined mesh density levels for educational use"""
    COARSE = 1
    MEDIUM_COARSE = 2
    MEDIUM = 3
    MEDIUM_FINE = 4
    FINE = 5


class MeshGeneratorError(Exception):
    """Base exception for mesh generator errors"""
    pass


class GeometryValidationError(MeshGeneratorError):
    """Raised when geometry parameters are invalid"""
    pass


class MeshGenerationError(MeshGeneratorError):
    """Raised when mesh generation fails"""
    pass


class LibraryLoadError(MeshGeneratorError):
    """Raised when the Fortran library cannot be loaded"""
    pass


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


class EducationalMeshGenerator:
    """
    High-performance Python interface to the educational mesh generator.
    
    This class provides a streamlined interface for generating finite element
    meshes for common educational geometries. It is optimized for speed and
    ease of use, with comprehensive parameter validation and error handling.
    
    Attributes:
        library_path (Path): Path to the compiled Fortran library
        performance_stats (Dict): Performance statistics for monitoring
    
    Example:
        >>> generator = EducationalMeshGenerator()
        >>> success, quality = generator.generate_mesh(
        ...     geometry_type='rectangle',
        ...     parameters={'width': 1.0, 'height': 1.0},
        ...     output_dir='/tmp/mesh',
        ...     mesh_density=MeshDensity.MEDIUM
        ... )
    """
    
    # Class-level library instance for performance
    _lib = None
    _lib_lock = threading.Lock()
    
    def __init__(self, library_path: Optional[Path] = None):
        """
        Initialize the mesh generator.
        
        Args:
            library_path: Optional path to the Fortran library. If not provided,
                         searches in standard locations.
        
        Raises:
            LibraryLoadError: If the Fortran library cannot be loaded
        """
        self.performance_stats = {
            'total_calls': 0,
            'total_time': 0.0,
            'average_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0
        }
        
        # Load the library (shared across instances for performance)
        self._load_library(library_path)
        
        logger.info("EducationalMeshGenerator initialized successfully")
    
    def _load_library(self, library_path: Optional[Path] = None):
        """Load the Fortran shared library using ctypes."""
        with self._lib_lock:
            if self._lib is not None:
                return  # Library already loaded
            
            # Determine library path
            if library_path is None:
                # Search in standard locations
                search_paths = [
                    Path(__file__).parent / "libeducational_mesh.so",
                    Path("/app/elmerfem_custom/mesh_generator/libeducational_mesh.so"),
                    Path.cwd() / "libeducational_mesh.so"
                ]
                
                for path in search_paths:
                    if path.exists():
                        library_path = path
                        break
                else:
                    raise LibraryLoadError(
                        f"Could not find libeducational_mesh.so in any of: {search_paths}"
                    )
            
            try:
                # Load the library
                self.__class__._lib = ctypes.CDLL(str(library_path))
                
                # Configure function signatures
                self._lib.generate_mesh.argtypes = [
                    ctypes.POINTER(GeometryParams),
                    ctypes.c_char_p,
                    ctypes.POINTER(MeshQuality)
                ]
                self._lib.generate_mesh.restype = None
                
                logger.info(f"Loaded Fortran library from {library_path}")
                
            except Exception as e:
                raise LibraryLoadError(f"Failed to load library: {e}")
    
    def _validate_parameters(self, geometry_type: str, parameters: Dict[str, float]):
        """
        Validate geometry parameters.
        
        Args:
            geometry_type: Type of geometry to validate
            parameters: Dictionary of geometry parameters
        
        Raises:
            GeometryValidationError: If parameters are invalid
        """
        # Define required parameters for each geometry
        required_params = {
            'rectangle': {'width', 'height'},
            'circle': {'radius'},
            'annulus': {'inner_radius', 'outer_radius'},
            'l_shape': {'width', 'height', 'cutout_width', 'cutout_height'}
        }
        
        # Define validation rules
        validation_rules = {
            'rectangle': [
                ('width', lambda x: x > 0, "Width must be positive"),
                ('height', lambda x: x > 0, "Height must be positive")
            ],
            'circle': [
                ('radius', lambda x: x > 0, "Radius must be positive")
            ],
            'annulus': [
                ('inner_radius', lambda x: x > 0, "Inner radius must be positive"),
                ('outer_radius', lambda x: x > 0, "Outer radius must be positive"),
                ('outer_radius', lambda x: x > parameters.get('inner_radius', 0), 
                 "Outer radius must be greater than inner radius")
            ],
            'l_shape': [
                ('width', lambda x: x > 0, "Width must be positive"),
                ('height', lambda x: x > 0, "Height must be positive"),
                ('cutout_width', lambda x: x > 0, "Cutout width must be positive"),
                ('cutout_height', lambda x: x > 0, "Cutout height must be positive"),
                ('cutout_width', lambda x: x < parameters.get('width', float('inf')), 
                 "Cutout width must be less than total width"),
                ('cutout_height', lambda x: x < parameters.get('height', float('inf')), 
                 "Cutout height must be less than total height")
            ]
        }
        
        if geometry_type not in required_params:
            raise GeometryValidationError(f"Unknown geometry type: {geometry_type}")
        
        # Check required parameters
        missing = required_params[geometry_type] - set(parameters.keys())
        if missing:
            raise GeometryValidationError(f"Missing required parameters: {missing}")
        
        # Validate parameter values
        for param_name, validator, error_msg in validation_rules.get(geometry_type, []):
            value = parameters.get(param_name)
            if value is not None and not validator(value):
                raise GeometryValidationError(f"{param_name}: {error_msg}")
    
    @contextmanager
    def _performance_timer(self):
        """Context manager for performance measurement."""
        start_time = time.perf_counter()
        yield
        elapsed = (time.perf_counter() - start_time) * 1000  # Convert to ms
        
        # Update statistics
        self.performance_stats['total_calls'] += 1
        self.performance_stats['total_time'] += elapsed
        self.performance_stats['average_time'] = (
            self.performance_stats['total_time'] / self.performance_stats['total_calls']
        )
        self.performance_stats['min_time'] = min(self.performance_stats['min_time'], elapsed)
        self.performance_stats['max_time'] = max(self.performance_stats['max_time'], elapsed)
        
        # Log warning if exceeding 50ms threshold
        if elapsed > 50:
            logger.warning(f"Mesh generation took {elapsed:.1f}ms, exceeding 50ms target")
    
    def generate_mesh(
        self,
        geometry_type: Union[str, GeometryType],
        parameters: Dict[str, float],
        output_dir: Union[str, Path],
        mesh_density: Union[int, MeshDensity] = MeshDensity.MEDIUM,
        enable_boundary_layer: bool = False
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Generate a finite element mesh for the specified geometry.
        
        This is the main entry point for mesh generation. The method validates
        parameters, calls the Fortran library, and returns quality metrics.
        
        Args:
            geometry_type: Type of geometry ('rectangle', 'circle', 'annulus', 'l_shape')
            parameters: Geometry-specific parameters (e.g., width, height, radius)
            output_dir: Directory where mesh files will be saved
            mesh_density: Mesh density level (1-5 or MeshDensity enum)
            enable_boundary_layer: Whether to generate boundary layer elements
        
        Returns:
            Tuple of (success, quality_metrics) where:
                - success: Boolean indicating if mesh generation succeeded
                - quality_metrics: Dictionary containing mesh quality information
        
        Raises:
            GeometryValidationError: If parameters are invalid
            MeshGenerationError: If mesh generation fails
        
        Example:
            >>> generator = EducationalMeshGenerator()
            >>> success, quality = generator.generate_mesh(
            ...     geometry_type='rectangle',
            ...     parameters={'width': 2.0, 'height': 1.0},
            ...     output_dir='/tmp/my_mesh',
            ...     mesh_density=MeshDensity.FINE
            ... )
            >>> if success:
            ...     print(f"Generated mesh with {quality['total_elements']} elements")
        """
        # Normalize geometry type
        if isinstance(geometry_type, GeometryType):
            geometry_name = geometry_type.name.lower()
            geometry_value = geometry_type.value
        else:
            geometry_name = geometry_type.lower()
            geometry_map = {
                'rectangle': GeometryType.RECTANGLE,
                'circle': GeometryType.CIRCLE,
                'annulus': GeometryType.ANNULUS,
                'l_shape': GeometryType.L_SHAPE
            }
            if geometry_name not in geometry_map:
                raise GeometryValidationError(
                    f"Unknown geometry type: {geometry_type}. "
                    f"Valid types are: {list(geometry_map.keys())}"
                )
            geometry_value = geometry_map[geometry_name].value
        
        # Validate parameters
        self._validate_parameters(geometry_name, parameters)
        
        # Ensure output directory exists
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare geometry parameters
        geometry = GeometryParams()
        geometry.geometry_type = geometry_value
        geometry.mesh_density = int(mesh_density)
        geometry.boundary_layer = 1 if enable_boundary_layer else 0
        
        # Fill parameter array based on geometry type
        if geometry_name == 'rectangle':
            geometry.params[0] = parameters['width']
            geometry.params[1] = parameters['height']
        elif geometry_name == 'circle':
            geometry.params[0] = parameters['radius']
        elif geometry_name == 'annulus':
            geometry.params[0] = parameters['inner_radius']
            geometry.params[1] = parameters['outer_radius']
        elif geometry_name == 'l_shape':
            geometry.params[0] = parameters['width']
            geometry.params[1] = parameters['height']
            geometry.params[2] = parameters['cutout_width']
            geometry.params[3] = parameters['cutout_height']
        
        # Prepare quality structure
        quality = MeshQuality()
        
        # Call Fortran library with performance timing
        try:
            with self._performance_timer():
                self._lib.generate_mesh(
                    ctypes.byref(geometry),
                    str(output_dir).encode('utf-8'),
                    ctypes.byref(quality)
                )
        except Exception as e:
            raise MeshGenerationError(f"Fortran library call failed: {e}")
        
        # Check return code
        if quality.return_code != 0:
            error_messages = {
                -1: "Invalid geometry type",
                -2: "Invalid mesh density",
                -3: "Invalid geometry parameters",
                -4: "File I/O error",
                -5: "Memory allocation error"
            }
            error_msg = error_messages.get(
                quality.return_code, 
                f"Unknown error code: {quality.return_code}"
            )
            raise MeshGenerationError(f"Mesh generation failed: {error_msg}")
        
        # Verify output files exist
        expected_files = ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']
        missing_files = []
        for filename in expected_files:
            if not (output_dir / filename).exists():
                missing_files.append(filename)
        
        if missing_files:
            raise MeshGenerationError(
                f"Mesh generation completed but files are missing: {missing_files}"
            )
        
        # Prepare quality metrics dictionary
        quality_dict = {
            'total_nodes': quality.total_nodes,
            'total_elements': quality.total_elements,
            'min_angle': quality.min_angle,
            'max_angle': quality.max_angle,
            'aspect_ratio_avg': quality.aspect_ratio_avg,
            'aspect_ratio_max': quality.aspect_ratio_max,
            'geometry_type': geometry_name,
            'mesh_density': int(mesh_density),
            'boundary_layer': enable_boundary_layer,
            'generation_time_ms': self.performance_stats['average_time']
        }
        
        logger.info(
            f"Generated {geometry_name} mesh: "
            f"{quality.total_elements} elements, {quality.total_nodes} nodes, "
            f"time: {self.performance_stats['average_time']:.1f}ms"
        )
        
        return True, quality_dict
    
    def get_performance_stats(self) -> Dict[str, float]:
        """
        Get performance statistics for mesh generation.
        
        Returns:
            Dictionary containing:
                - total_calls: Number of mesh generations performed
                - total_time: Total time spent in mesh generation (ms)
                - average_time: Average time per mesh generation (ms)
                - min_time: Fastest mesh generation time (ms)
                - max_time: Slowest mesh generation time (ms)
        """
        return self.performance_stats.copy()
    
    def estimate_mesh_size(
        self, 
        geometry_type: Union[str, GeometryType],
        parameters: Dict[str, float],
        mesh_density: Union[int, MeshDensity] = MeshDensity.MEDIUM
    ) -> Dict[str, int]:
        """
        Estimate the number of elements and nodes without generating the mesh.
        
        This method provides a quick estimate of mesh size for UI feedback
        and resource planning.
        
        Args:
            geometry_type: Type of geometry
            parameters: Geometry parameters
            mesh_density: Desired mesh density
        
        Returns:
            Dictionary with 'estimated_elements' and 'estimated_nodes'
        """
        # Normalize inputs
        if isinstance(geometry_type, str):
            geometry_type = geometry_type.lower()
        else:
            geometry_type = geometry_type.name.lower()
        
        density = int(mesh_density)
        
        # Base element counts for density level 3 (medium)
        base_counts = {
            'rectangle': lambda p: p.get('width', 1) * p.get('height', 1) * 100,
            'circle': lambda p: 3.14159 * p.get('radius', 1)**2 * 100,
            'annulus': lambda p: 3.14159 * (p.get('outer_radius', 1)**2 - 
                                          p.get('inner_radius', 0.5)**2) * 120,
            'l_shape': lambda p: (p.get('width', 2) * p.get('height', 2) - 
                                p.get('cutout_width', 1) * p.get('cutout_height', 1)) * 110
        }
        
        # Density multipliers
        density_factors = {1: 0.25, 2: 0.5, 3: 1.0, 4: 2.0, 5: 4.0}
        
        if geometry_type not in base_counts:
            raise GeometryValidationError(f"Unknown geometry type: {geometry_type}")
        
        base_elements = base_counts[geometry_type](parameters)
        estimated_elements = int(base_elements * density_factors.get(density, 1.0))
        estimated_nodes = int(estimated_elements * 0.55)  # Approximate node/element ratio
        
        return {
            'estimated_elements': estimated_elements,
            'estimated_nodes': estimated_nodes
        }
    
    def cleanup_mesh_files(self, directory: Union[str, Path]) -> bool:
        """
        Remove mesh files from a directory.
        
        Args:
            directory: Directory containing mesh files
        
        Returns:
            True if all files were removed successfully
        """
        directory = Path(directory)
        mesh_files = ['mesh.header', 'mesh.nodes', 'mesh.elements', 'mesh.boundary']
        
        success = True
        for filename in mesh_files:
            filepath = directory / filename
            if filepath.exists():
                try:
                    filepath.unlink()
                except Exception as e:
                    logger.error(f"Failed to remove {filepath}: {e}")
                    success = False
        
        return success


# Convenience function for quick mesh generation
def generate_educational_mesh(
    geometry_type: str,
    parameters: Dict[str, float],
    output_dir: Union[str, Path],
    mesh_density: int = 3
) -> Tuple[bool, Dict[str, any]]:
    """
    Convenience function for generating educational meshes.
    
    This function creates a mesh generator instance and generates a mesh
    in a single call. Useful for one-off mesh generation.
    
    Args:
        geometry_type: Type of geometry ('rectangle', 'circle', 'annulus', 'l_shape')
        parameters: Geometry-specific parameters
        output_dir: Directory for mesh files
        mesh_density: Mesh density level (1-5)
    
    Returns:
        Tuple of (success, quality_metrics)
    
    Example:
        >>> success, quality = generate_educational_mesh(
        ...     'circle',
        ...     {'radius': 1.0},
        ...     '/tmp/circle_mesh',
        ...     mesh_density=4
        ... )
    """
    generator = EducationalMeshGenerator()
    return generator.generate_mesh(geometry_type, parameters, output_dir, mesh_density) 