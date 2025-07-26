#!/usr/bin/env python3
"""
Backend Integration Example for Educational Mesh Generator

This script demonstrates how to integrate the mesh generator with
the existing backend service architecture, including:
- FastAPI integration
- Docker workflow
- Job execution pipeline
- Error handling and logging
"""

import asyncio
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the wrapper (adjust path as needed in production)
import sys
sys.path.append(str(Path(__file__).parent.parent))

from educational_mesh_generator_wrapper import (
    EducationalMeshGenerator,
    MeshDensity,
    GeometryValidationError,
    MeshGenerationError
)


class EnhancedEducationalMeshService:
    """
    Enhanced version of EducationalMeshService using the new wrapper.
    
    This demonstrates how to replace or enhance the existing service
    with the optimized wrapper implementation.
    """
    
    def __init__(self):
        """Initialize the enhanced mesh service"""
        self.generator = EducationalMeshGenerator()
        logger.info("Enhanced Educational Mesh Service initialized")
    
    async def generate_mesh(
        self,
        geometry_type: str,
        parameters: Dict[str, float],
        output_dir: Path,
        mesh_density: int = 3,
        enable_boundary_layer: bool = False
    ) -> tuple[bool, Dict[str, any]]:
        """
        Async wrapper for mesh generation compatible with existing service interface.
        
        This maintains backward compatibility while using the new wrapper.
        """
        try:
            # The new wrapper is synchronous, so we run it in an executor
            loop = asyncio.get_event_loop()
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate mesh using the wrapper
            success, quality = await loop.run_in_executor(
                None,
                self.generator.generate_mesh,
                geometry_type,
                parameters,
                output_dir,
                mesh_density,
                enable_boundary_layer
            )
            
            # Log performance metrics
            if success:
                logger.info(
                    f"Generated {geometry_type} mesh: "
                    f"{quality['total_elements']} elements in "
                    f"{quality['generation_time_ms']:.1f}ms"
                )
            
            return success, quality
            
        except GeometryValidationError as e:
            logger.error(f"Geometry validation failed: {e}")
            return False, {"error": str(e), "error_type": "validation"}
        except MeshGenerationError as e:
            logger.error(f"Mesh generation failed: {e}")
            return False, {"error": str(e), "error_type": "generation"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False, {"error": str(e), "error_type": "unexpected"}


class SimulationJobExecutor:
    """
    Example job executor showing mesh generation integration.
    
    This simulates how the mesh generator integrates with the
    job execution pipeline.
    """
    
    def __init__(self):
        self.mesh_service = EnhancedEducationalMeshService()
        self.job_counter = 0
    
    async def execute_simulation_job(self, job_params: Dict) -> Dict:
        """Execute a complete simulation job with mesh generation"""
        
        job_id = f"job_{self.job_counter:04d}"
        self.job_counter += 1
        
        logger.info(f"Starting job {job_id}")
        job_start = datetime.now()
        
        # Create job workspace
        workspace = Path(f"/tmp/simulations/{job_id}")
        workspace.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: Generate mesh
            mesh_dir = workspace / "mesh"
            mesh_start = datetime.now()
            
            mesh_success, mesh_quality = await self.mesh_service.generate_mesh(
                geometry_type=job_params.get('geometry_type', 'rectangle'),
                parameters=job_params.get('geometry_parameters', {'width': 1.0, 'height': 1.0}),
                output_dir=mesh_dir,
                mesh_density=job_params.get('mesh_density', 3),
                enable_boundary_layer=job_params.get('enable_boundary_layer', False)
            )
            
            mesh_time = (datetime.now() - mesh_start).total_seconds() * 1000
            
            if not mesh_success:
                raise Exception(f"Mesh generation failed: {mesh_quality.get('error')}")
            
            # Step 2: Generate SIF file (simulation input)
            sif_content = self._generate_sif_file(job_params, mesh_dir)
            sif_path = workspace / "simulation.sif"
            
            with open(sif_path, 'w') as f:
                f.write(sif_content)
            
            # Step 3: Run simulation (mocked here)
            sim_start = datetime.now()
            sim_result = await self._run_simulation(workspace, sif_path)
            sim_time = (datetime.now() - sim_start).total_seconds() * 1000
            
            # Step 4: Process results
            total_time = (datetime.now() - job_start).total_seconds() * 1000
            
            result = {
                'job_id': job_id,
                'status': 'completed',
                'mesh_generation': {
                    'success': mesh_success,
                    'time_ms': mesh_time,
                    'quality': mesh_quality
                },
                'simulation': {
                    'success': sim_result['success'],
                    'time_ms': sim_time,
                    'result': sim_result
                },
                'total_time_ms': total_time,
                'workspace': str(workspace)
            }
            
            # Save job metadata
            with open(workspace / 'job_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"Job {job_id} completed in {total_time:.1f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            return {
                'job_id': job_id,
                'status': 'failed',
                'error': str(e),
                'workspace': str(workspace)
            }
    
    def _generate_sif_file(self, job_params: Dict, mesh_dir: Path) -> str:
        """Generate a simple SIF file for the simulation"""
        
        sim_type = job_params.get('simulation_type', 'heat_transfer')
        
        if sim_type == 'heat_transfer':
            return f"""
Header
  CHECK KEYWORDS Warn
  Mesh DB "{mesh_dir}" "."
  Include Path ""
  Results Directory "results"
End

Simulation
  Max Output Level = 5
  Coordinate System = Cartesian
  Coordinate Mapping(3) = 1 2 3
  Simulation Type = Steady state
  Steady State Max Iterations = 1
  Output Intervals = 1
  Timestepping Method = BDF
  BDF Order = 1
  Solver Input File = case.sif
  Post File = case.vtu
End

Body 1
  Target Bodies(1) = 1
  Name = "Body 1"
  Equation = 1
  Material = 1
End

Solver 1
  Equation = Heat Equation
  Procedure = "HeatSolve" "HeatSolver"
  Variable = Temperature
  Exec Solver = Always
  Stabilize = True
  Bubbles = False
  Lumped Mass Matrix = False
  Optimize Bandwidth = True
  Steady State Convergence Tolerance = 1.0e-5
  Linear System Solver = Iterative
  Linear System Iterative Method = BiCGStab
  Linear System Max Iterations = 500
  Linear System Convergence Tolerance = 1.0e-10
  Linear System Preconditioning = ILU0
  Linear System ILUT Tolerance = 1.0e-3
  Linear System Abort Not Converged = False
  Linear System Residual Output = 20
  Linear System Precondition Recompute = 1
End

Material 1
  Name = "Material 1"
  Heat Conductivity = 1
  Density = 1
End

Equation 1
  Name = "Equation 1"
  Active Solvers(1) = 1
End
"""
        else:
            # Add other simulation types as needed
            return ""
    
    async def _run_simulation(self, workspace: Path, sif_path: Path) -> Dict:
        """Mock simulation execution"""
        # In real implementation, this would call ElmerSolver
        await asyncio.sleep(0.1)  # Simulate computation time
        
        return {
            'success': True,
            'max_temperature': 100.0,
            'min_temperature': 20.0,
            'convergence_iterations': 15
        }


# FastAPI Integration Example
from pydantic import BaseModel, Field


class MeshGenerationRequest(BaseModel):
    """Request model for mesh generation endpoint"""
    geometry_type: str = Field(..., description="Type of geometry: rectangle, circle, annulus, l_shape")
    parameters: Dict[str, float] = Field(..., description="Geometry-specific parameters")
    mesh_density: int = Field(3, ge=1, le=5, description="Mesh density level")
    enable_boundary_layer: bool = Field(False, description="Enable boundary layer generation")


class SimulationRequest(BaseModel):
    """Request model for full simulation"""
    simulation_type: str = Field("heat_transfer", description="Type of simulation")
    geometry_type: str = Field(..., description="Geometry type")
    geometry_parameters: Dict[str, float] = Field(..., description="Geometry parameters")
    mesh_density: int = Field(3, ge=1, le=5)
    enable_boundary_layer: bool = Field(False)
    material_properties: Dict[str, float] = Field(default_factory=dict)
    boundary_conditions: Dict[str, any] = Field(default_factory=dict)


# Example FastAPI app integration
async def create_fastapi_app():
    """Create FastAPI app with mesh generation endpoints"""
    
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.responses import FileResponse
    import uvicorn
    
    app = FastAPI(title="Educational FEM API")
    mesh_service = EnhancedEducationalMeshService()
    job_executor = SimulationJobExecutor()
    
    @app.post("/api/mesh/generate")
    async def generate_mesh_endpoint(request: MeshGenerationRequest):
        """Generate a mesh and return quality metrics"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            success, quality = await mesh_service.generate_mesh(
                geometry_type=request.geometry_type,
                parameters=request.parameters,
                output_dir=temp_path,
                mesh_density=request.mesh_density,
                enable_boundary_layer=request.enable_boundary_layer
            )
            
            if not success:
                raise HTTPException(
                    status_code=400,
                    detail=quality.get('error', 'Mesh generation failed')
                )
            
            # In production, you might store files and return URLs
            return {
                "success": True,
                "quality": quality,
                "message": "Mesh generated successfully"
            }
    
    @app.post("/api/simulation/submit")
    async def submit_simulation(
        request: SimulationRequest,
        background_tasks: BackgroundTasks
    ):
        """Submit a simulation job"""
        
        # Convert request to job parameters
        job_params = {
            'simulation_type': request.simulation_type,
            'geometry_type': request.geometry_type,
            'geometry_parameters': request.geometry_parameters,
            'mesh_density': request.mesh_density,
            'enable_boundary_layer': request.enable_boundary_layer,
            'material_properties': request.material_properties,
            'boundary_conditions': request.boundary_conditions
        }
        
        # Execute job in background
        background_tasks.add_task(
            job_executor.execute_simulation_job,
            job_params
        )
        
        return {
            "message": "Simulation job submitted",
            "job_id": f"job_{job_executor.job_counter:04d}"
        }
    
    @app.get("/api/mesh/estimate")
    async def estimate_mesh_size(
        geometry_type: str,
        parameters: str,  # JSON string
        mesh_density: int = 3
    ):
        """Estimate mesh size without generation"""
        
        import json
        
        try:
            params = json.loads(parameters)
            estimate = mesh_service.generator.estimate_mesh_size(
                geometry_type,
                params,
                mesh_density
            )
            return {
                "success": True,
                "estimate": estimate
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        stats = mesh_service.generator.get_performance_stats()
        return {
            "status": "healthy",
            "mesh_generator": {
                "total_generations": stats['total_calls'],
                "average_time_ms": stats['average_time']
            }
        }
    
    return app


async def demonstrate_integration():
    """Demonstrate the complete integration"""
    
    print("Educational Mesh Generator - Backend Integration Demo")
    print("=" * 60)
    
    # Test job executor
    executor = SimulationJobExecutor()
    
    # Example job parameters
    job_params = {
        'simulation_type': 'heat_transfer',
        'geometry_type': 'rectangle',
        'geometry_parameters': {'width': 2.0, 'height': 1.0},
        'mesh_density': 3,
        'enable_boundary_layer': False
    }
    
    print("\nExecuting sample simulation job...")
    result = await executor.execute_simulation_job(job_params)
    
    print(f"\nJob Result:")
    print(f"  Status: {result['status']}")
    print(f"  Mesh generation time: {result['mesh_generation']['time_ms']:.1f}ms")
    print(f"  Total time: {result['total_time_ms']:.1f}ms")
    
    if result['status'] == 'completed':
        mesh_quality = result['mesh_generation']['quality']
        print(f"  Mesh elements: {mesh_quality['total_elements']}")
        print(f"  Mesh quality: {mesh_quality['min_angle']:.1f}° - {mesh_quality['max_angle']:.1f}°")
    
    # Clean up
    if 'workspace' in result:
        shutil.rmtree(result['workspace'], ignore_errors=True)


def main():
    """Run the integration demonstration"""
    
    # Run the async demonstration
    asyncio.run(demonstrate_integration())
    
    print("\n" + "="*60)
    print("Integration demonstration completed!")
    print("\nTo run the FastAPI server:")
    print("  1. Create the app: app = await create_fastapi_app()")
    print("  2. Run with: uvicorn app:app --reload")


if __name__ == "__main__":
    main() 