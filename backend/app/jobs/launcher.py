"""
Job launcher and execution management
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID

from ..config.settings import settings
from ..models import SimulationJob, SimulationParamsDTO, JobStatus
from ..services.docker_wrapper import DockerWrapper
from ..services.educational_mesh_service import (
    EducationalMeshService, 
    MeshGenerationRequest,
    GeometryType,
    MeshQualityMetrics
)
from ..services.sif_generator import SIFGenerator
from .store import JobStore

logger = logging.getLogger(__name__)


class JobLauncher:
    """Manages the execution of simulation jobs"""
    
    def __init__(self, job_store: JobStore, docker_wrapper: DockerWrapper):
        self.job_store = job_store
        self.docker = docker_wrapper
        self.educational_mesh_service = EducationalMeshService()
        self.sif_generator = SIFGenerator()
        self._running_tasks: Dict[UUID, asyncio.Task] = {}
    
    async def launch_job(self, params: SimulationParamsDTO) -> SimulationJob:
        """
        Launch a new simulation job
        
        Args:
            params: Simulation parameters
            
        Returns:
            Job details
        """
        # Create job
        from ..models.job import SimulationJob
        job = SimulationJob(params=params)
        job = await self.job_store.create(job)
        logger.info(f"Created job {job.id} for {params.simulation_type.value} simulation")
        
        # Start execution task
        task = asyncio.create_task(self._execute_job(job.id))
        self._running_tasks[job.id] = task
        
        # Clean up task when done
        task.add_done_callback(lambda t: self._running_tasks.pop(job.id, None))
        
        return job
    
    async def _execute_job(self, job_id: UUID) -> None:
        """
        Execute a simulation job with enhanced error handling and quality metrics
        
        Args:
            job_id: ID of the job to execute
        """
        logger.info(
            "Starting job execution",
            extra={
                "job_id": str(job_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        try:
            # Get job from store
            job = await self.job_store.get(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # Mark job as started
            await self.job_store.mark_job_started(job_id)
            
            # Generate SIF file
            sif_file_path = await self.sif_generator.write_sif_file(
                job.params, job.workspace_dir, "case"
            )
            job.sif_file_path = sif_file_path
            await self.job_store.update(job)
            
            # Update progress
            await self.job_store.update_job_progress(
                job_id, 10.0, "SIF file generated"
            )
            
            # Generate mesh using enhanced EducationalMeshService
            logger.info(
                "Generating educational mesh",
                extra={
                    "job_id": str(job_id),
                    "geometry": job.params.geometry,
                    "mesh_density": job.params.mesh_density
                }
            )
            
            try:
                # Create validated mesh generation request
                # Extract geometry type from params
                geometry_type_str = job.params.geometry.get('type', 'rectangle').lower()
                
                # Map to GeometryType enum
                geometry_type_map = {
                    'rectangle': GeometryType.RECTANGLE,
                    'circle': GeometryType.CIRCLE,
                    'annulus': GeometryType.ANNULUS,
                    'l_shape': GeometryType.L_SHAPE,
                    'l-shape': GeometryType.L_SHAPE
                }
                
                geometry_type = geometry_type_map.get(geometry_type_str, GeometryType.RECTANGLE)
                
                # Create mesh generation request with validation
                mesh_request = MeshGenerationRequest(
                    geometry_type=geometry_type,
                    parameters=job.params.geometry,
                    mesh_density=int(job.params.mesh_density),
                    enable_boundary_layer=job.params.solver_settings.get('enable_boundary_layer', False) 
                        if job.params.solver_settings else False
                )
                
                # Generate mesh with quality metrics
                success, quality_metrics = await self.educational_mesh_service.generate_mesh(
                    request=mesh_request,
                    output_dir=job.workspace_dir,
                    job_id=str(job_id)
                )
                
                if success:
                    # Store mesh quality metrics in job metadata
                    job.metadata['mesh_quality'] = quality_metrics.dict()
                    await self.job_store.update(job)
                    
                    logger.info(
                        "Mesh generated successfully",
                        extra={
                            "job_id": str(job_id),
                            "total_elements": quality_metrics.total_elements,
                            "total_nodes": quality_metrics.total_nodes,
                            "generation_time_ms": quality_metrics.generation_time_ms,
                            "min_angle": quality_metrics.min_angle,
                            "aspect_ratio_avg": quality_metrics.aspect_ratio_avg
                        }
                    )
                else:
                    raise RuntimeError("Mesh generation failed")
                    
            except Exception as e:
                logger.error(
                    "Mesh generation error",
                    extra={
                        "job_id": str(job_id),
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                await self.job_store.mark_job_failed(
                    job_id, f"Mesh generation failed: {str(e)}"
                )
                return
            
            # Update progress
            await self.job_store.update_job_progress(
                job_id, 30.0, "Mesh generated"
            )
            
            # Execute ElmerSolver
            logger.info(
                "Executing ElmerSolver",
                extra={
                    "job_id": str(job_id),
                    "sif_file": sif_file_path.name,
                    "workspace": str(job.workspace_dir)
                }
            )
            
            returncode, stdout, stderr = await self.docker.execute_solver(
                sif_file_path.name,
                job.workspace_dir,
                timeout=settings.job_timeout_seconds
            )
            
            # Log output
            log_file = job.workspace_dir / "elmer.log"
            with open(log_file, "w") as f:
                f.write("=== STDOUT ===\n")
                f.write(stdout)
                f.write("\n\n=== STDERR ===\n")
                f.write(stderr)
            
            job.log_file_path = log_file
            
            if returncode == 0:
                # Success
                logger.info(
                    "Job completed successfully",
                    extra={
                        "job_id": str(job_id),
                        "execution_time": (datetime.utcnow() - job.started_at).total_seconds()
                    }
                )
                
                # Find result files
                result_files = list(job.workspace_dir.glob("*.vtu"))
                result_files.extend(job.workspace_dir.glob("*.vtk"))
                result_files.extend(job.workspace_dir.glob("*.result*"))
                
                job.result_files = [str(f.relative_to(job.workspace_dir)) for f in result_files]
                if result_files:
                    job.vtk_file_path = result_files[0]  # Use first VTK/VTU file
                
                # Update job metadata with completion info
                job.metadata['solver_execution'] = {
                    'return_code': returncode,
                    'result_files_count': len(result_files),
                    'execution_completed': datetime.utcnow().isoformat()
                }
                
                await self.job_store.mark_job_completed(
                    job_id,
                    result_files=job.result_files
                )
            else:
                # Failure
                error_msg = f"ElmerSolver failed with return code {returncode}"
                if stderr:
                    error_msg += f": {stderr[:500]}"  # First 500 chars of error
                
                logger.error(
                    "Job failed",
                    extra={
                        "job_id": str(job_id),
                        "return_code": returncode,
                        "error_msg": error_msg
                    }
                )
                await self.job_store.mark_job_failed(job_id, error_msg)
                
        except Exception as e:
            logger.exception(
                "Unexpected error executing job",
                extra={
                    "job_id": str(job_id),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            await self.job_store.mark_job_failed(job_id, str(e))

    
    async def cancel_job(self, job_id: UUID) -> bool:
        """
        Cancel a running job
        
        Args:
            job_id: ID of job to cancel
            
        Returns:
            True if job was cancelled, False otherwise
        """
        # Check if job is running
        task = self._running_tasks.get(job_id)
        if task and not task.done():
            logger.info(
                "Cancelling job",
                extra={
                    "job_id": str(job_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            task.cancel()
            
            # Update job status
            job = await self.job_store.get(job_id)
            if job:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow()
                await self.job_store.update(job)
            
            return True
        
        return False
    
    async def get_job_logs(self, job_id: UUID) -> Optional[str]:
        """
        Get logs for a job
        
        Args:
            job_id: ID of the job
            
        Returns:
            Log content or None if not available
        """
        job = await self.job_store.get(job_id)
        if job and job.log_file_path and job.log_file_path.exists():
            return job.log_file_path.read_text()
        return None 