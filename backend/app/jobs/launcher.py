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
from ..services.educational_mesh_service import EducationalMeshService
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
        job = await self.job_store.create(params)
        logger.info(f"Created job {job.id} for {params.simulation_type.value} simulation")
        
        # Start execution task
        task = asyncio.create_task(self._execute_job(job.id))
        self._running_tasks[job.id] = task
        
        # Clean up task when done
        task.add_done_callback(lambda t: self._running_tasks.pop(job.id, None))
        
        return job
    
    async def _execute_job(self, job_id: UUID) -> None:
        """
        Execute a simulation job
        
        Args:
            job_id: ID of the job to execute
        """
        logger.info(f"Starting execution of job {job_id}")
        
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
            
            # Generate mesh files using EducationalMeshService
            # The educational mesh generator provides fast, reliable mesh generation
            # for standard educational geometries (rectangle, circle, annulus, L-shape)
            logger.info(f"Generating mesh for job {job_id}")
            try:
                mesh_quality = await asyncio.to_thread(
                    self.educational_mesh_service.generate_mesh,
                    job.params.geometry,
                    str(job.workspace_dir),
                    job.params.mesh_density
                )
                mesh_success = mesh_quality.return_code == 0
                
                if mesh_success:
                    logger.info(f"Mesh generated successfully: {mesh_quality.total_elements} elements, "
                               f"{mesh_quality.total_nodes} nodes")
                else:
                    logger.error(f"Mesh generation failed with code {mesh_quality.return_code}")
            except Exception as e:
                logger.error(f"Mesh generation error: {e}")
                mesh_success = False
            
            if not mesh_success:
                await self.job_store.mark_job_failed(
                    job_id, f"Mesh generation failed"
                )
                return
            
            # Update progress
            await self.job_store.update_job_progress(
                job_id, 30.0, "Mesh generated"
            )
            
            # Execute ElmerSolver
            logger.info(f"Executing ElmerSolver for job {job_id}")
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
                logger.info(f"Job {job_id} completed successfully")
                
                # Find result files
                result_files = list(job.workspace_dir.glob("*.vtu"))
                result_files.extend(job.workspace_dir.glob("*.vtk"))
                result_files.extend(job.workspace_dir.glob("*.result*"))
                
                job.result_files = [str(f.relative_to(job.workspace_dir)) for f in result_files]
                if result_files:
                    job.vtk_file_path = result_files[0]  # Use first VTK/VTU file
                
                await self.job_store.mark_job_completed(
                    job_id,
                    result_files=job.result_files
                )
            else:
                # Failure
                error_msg = f"ElmerSolver failed with return code {returncode}"
                if stderr:
                    error_msg += f": {stderr[:500]}"  # First 500 chars of error
                
                logger.error(f"Job {job_id} failed: {error_msg}")
                await self.job_store.mark_job_failed(job_id, error_msg)
                
        except Exception as e:
            logger.exception(f"Error executing job {job_id}")
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
            logger.info(f"Cancelling job {job_id}")
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