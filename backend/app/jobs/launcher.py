"""
Job launcher and execution management
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
from uuid import UUID

import meshio

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
    """Manages the execution of simulation jobs with stage-based progress tracking"""
    
    # Stage definitions with progress ranges
    STAGES = {
        "validate": (0, 5),      # 0-5%
        "mesh": (5, 30),         # 5-30%
        "write_sif": (30, 35),   # 30-35%
        "solve": (35, 90),       # 35-90%
        "post": (90, 100)        # 90-100%
    }
    
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
    
    async def _send_progress_update(self, job_id: UUID, progress: float, message: str) -> None:
        """Send progress update via WebSocket"""
        try:
            # Update job progress in store
            job = await self.job_store.get(job_id)
            if job:
                job.progress = progress
                job.current_step = message
                await self.job_store.update(job)
            
            # Publish progress event
            await self.job_store.publish_progress_event(job_id, {
                "job_id": str(job_id),
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")
    
    async def _send_status_update(self, job_id: UUID, status: JobStatus) -> None:
        """Send status update via WebSocket"""
        try:
            # Update job status in store
            job = await self.job_store.get(job_id)
            if job:
                job.status = status
                if status == JobStatus.COMPLETED:
                    job.completed_at = datetime.utcnow()
                await self.job_store.update(job)
            
            # Publish status event
            await self.job_store.publish_progress_event(job_id, {
                "job_id": str(job_id),
                "status": status.value,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
    
    async def _execute_job(self, job_id: UUID) -> None:
        """
        Execute a simulation job with enhanced error handling and stage-based progress
        
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
            # Stage 1: Validate and Initialize
            await self.job_store.set_stage(job_id, "validate", 0)
            
            # Get job from store
            job = await self.job_store.get(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # Create workspace directory for this job
            workspace_dir = settings.workspace_path / str(job_id)
            workspace_dir.mkdir(parents=True, exist_ok=True)
            job.workspace_dir = workspace_dir
            
            logger.info(
                "Created job workspace",
                extra={
                    "job_id": str(job_id),
                    "workspace_dir": str(workspace_dir)
                }
            )
            
            # Update job with workspace directory
            await self.job_store.update(job)
            
            # Mark job as started
            await self.job_store.mark_job_started(job_id)
            await self._send_status_update(job_id, JobStatus.RUNNING)
            await self._send_progress_update(job_id, 5, "Validation complete")
            
            # Stage 2: Write SIF File
            await self._send_progress_update(job_id, 10, "Writing SIF file...")
            
            sif_file_path = await self.sif_generator.write_sif_file(
                job.params, job.workspace_dir, "case"
            )
            job.sif_file_path = sif_file_path
            await self.job_store.update(job)
            
            await self._send_progress_update(job_id, 15, "SIF file created")
            
            # Stage 3: Generate Mesh
            await self._send_progress_update(job_id, 20, "Starting mesh generation...")
            
            logger.info(
                "Generating educational mesh",
                extra={
                    "job_id": str(job_id),
                    "geometry": job.params.geometry,
                    "mesh_density": job.params.mesh_density
                }
            )
            
            try:
                mesh_request = self._create_mesh_request(job.params)
                success, mesh_metrics = await self.educational_mesh_service.generate_mesh(
                    mesh_request, 
                    workspace_dir,
                    str(job_id)
                )
                
                if not success:
                    raise RuntimeError("Mesh generation failed")
                
                logger.info(
                    "Mesh generation completed",
                    extra={
                        "job_id": str(job_id),
                        "elements": mesh_metrics.total_elements,
                        "nodes": mesh_metrics.total_nodes,
                        "min_angle": mesh_metrics.min_angle,
                        "aspect_ratio": mesh_metrics.aspect_ratio_avg
                    }
                )
                
                # Store mesh metrics
                job.metadata = job.metadata or {}
                job.metadata['mesh_quality'] = json.loads(mesh_metrics.json())
                await self.job_store.update(job)
                
                await self._send_progress_update(job_id, 30, f"Mesh generated: {mesh_metrics.total_elements} elements")
                    
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
                await self._send_status_update(job_id, JobStatus.FAILED)
                return
            
            # Stage 4: Execute ElmerSolver
            await self._send_progress_update(job_id, 35, "Starting ElmerSolver...")
            
            logger.info(
                "Executing ElmerSolver",
                extra={
                    "job_id": str(job_id),
                    "sif_file": sif_file_path.name,
                    "workspace": str(job.workspace_dir)
                }
            )
            
            # Track solver progress
            solver_progress = 35
            
            async def on_solver_line(line: str):
                """Process solver output lines for progress updates"""
                nonlocal solver_progress
                
                # Look for progress indicators in solver output
                if "MAIN:" in line or "Iteration" in line:
                    # Increment progress within solve stage range
                    solver_progress = min(solver_progress + 2, 85)
                    await self._send_progress_update(job_id, solver_progress, f"Solving: {line.strip()[:50]}...")
                
                # Log significant lines
                if any(keyword in line for keyword in ["WARNING", "ERROR", "CONVERGED"]):
                    logger.info(f"Solver [{job_id}]: {line.strip()}")
            
            returncode, stdout, stderr = await self.docker.execute_solver(
                sif_file_path.name,
                job.workspace_dir,
                timeout=settings.job_timeout_seconds,
                on_line_callback=on_solver_line
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
                await self._send_progress_update(job_id, 90, "Solver completed successfully")
                
                # Stage 5: Post-processing
                await self._send_progress_update(job_id, 92, "Post-processing results...")
                
                # Find result files
                result_files = list(job.workspace_dir.glob("*.vtu"))
                result_files.extend(job.workspace_dir.glob("*.vtk"))
                result_files.extend(job.workspace_dir.glob("*.result*"))
                
                job.result_files = [str(f.relative_to(job.workspace_dir)) for f in result_files]
                
                # Process VTU files to JSON if found
                vtu_files = list(job.workspace_dir.glob("*.vtu"))
                if vtu_files:
                    job.vtk_file_path = vtu_files[0]
                    
                    try:
                        # Convert VTU to JSON
                        json_path = await self._convert_vtu_to_json(vtu_files[0], job.workspace_dir)
                        job.metadata['result_json'] = str(json_path.relative_to(job.workspace_dir))
                        
                        logger.info(
                            "Converted VTU to JSON",
                            extra={
                                "job_id": str(job_id),
                                "vtu_file": vtu_files[0].name,
                                "json_file": json_path.name
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to convert VTU to JSON: {e}")
                
                await self._send_progress_update(job_id, 95, "Finalizing results...")
                
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
                
                await self._send_progress_update(job_id, 100, "Simulation completed successfully")
                await self._send_status_update(job_id, JobStatus.COMPLETED)
                
                logger.info(
                    "Job completed successfully",
                    extra={
                        "job_id": str(job_id),
                        "execution_time": (datetime.utcnow() - job.started_at).total_seconds() if job.started_at else 0
                    }
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
                await self._send_status_update(job_id, JobStatus.FAILED)
                
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
            await self._send_status_update(job_id, JobStatus.FAILED)
    
    async def _convert_vtu_to_json(self, vtu_path: Path, output_dir: Path) -> Path:
        """
        Convert VTU file to JSON format using meshio
        
        Args:
            vtu_path: Path to VTU file
            output_dir: Directory to save JSON file
            
        Returns:
            Path to created JSON file
        """
        # Read VTU file
        mesh = meshio.read(vtu_path)
        
        # Create JSON-serializable structure
        mesh_data = {
            "points": mesh.points.tolist(),
            "cells": {},
            "point_data": {},
            "cell_data": {},
            "field_data": mesh.field_data if hasattr(mesh, 'field_data') else {}
        }
        
        # Convert cells
        for cell_type in mesh.cells:
            if hasattr(cell_type, 'type') and hasattr(cell_type, 'data'):
                mesh_data["cells"][cell_type.type] = cell_type.data.tolist()
            elif isinstance(cell_type, tuple) and len(cell_type) == 2:
                mesh_data["cells"][cell_type[0]] = cell_type[1].tolist()
        
        # Convert point data
        for key, data in mesh.point_data.items():
            mesh_data["point_data"][key] = data.tolist()
        
        # Convert cell data
        for key, data_dict in mesh.cell_data.items():
            mesh_data["cell_data"][key] = {}
            for cell_type, data in data_dict.items():
                mesh_data["cell_data"][key][cell_type] = data.tolist()
        
        # Save to JSON
        json_path = output_dir / f"{vtu_path.stem}.json"
        with open(json_path, 'w') as f:
            json.dump(mesh_data, f, indent=2)
        
        return json_path
    
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
    
    def _create_mesh_request(self, params: SimulationParamsDTO) -> MeshGenerationRequest:
        """Create mesh generation request from simulation parameters"""
        # Map simulation geometry type to mesh geometry type
        geometry_map = {
            "box": GeometryType.RECTANGLE,
            "rectangle": GeometryType.RECTANGLE,
            "cylinder": GeometryType.CIRCLE,
            "circle": GeometryType.CIRCLE,
            "annulus": GeometryType.ANNULUS,
            "lshape": GeometryType.L_SHAPE,
            "l-shape": GeometryType.L_SHAPE,
            "l_shape": GeometryType.L_SHAPE
        }
        
        geometry_type = geometry_map.get(
            params.geometry_type.lower() if hasattr(params, 'geometry_type') else params.geometry.get('type', 'rectangle').lower(), 
            GeometryType.RECTANGLE
        )
        
        # Get dimensions from geometry
        dimensions = params.dimensions if hasattr(params, 'dimensions') else params.geometry.get('parameters', {})
        
        # Build geometry-specific parameters
        parameters = {}
        if geometry_type == GeometryType.RECTANGLE:
            parameters = {
                "width": dimensions.get("width", dimensions.get("length", 1.0)),
                "height": dimensions.get("height", dimensions.get("width", 1.0))
            }
        elif geometry_type == GeometryType.CIRCLE:
            parameters = {
                "radius": dimensions.get("radius", 0.5)
            }
        elif geometry_type == GeometryType.ANNULUS:
            parameters = {
                "inner_radius": dimensions.get("inner_radius", 0.25),
                "outer_radius": dimensions.get("outer_radius", 0.5)
            }
        elif geometry_type == GeometryType.L_SHAPE:
            parameters = {
                "length": dimensions.get("length", 1.0),
                "width": dimensions.get("width", 1.0),
                "notch_size": dimensions.get("notch_size", 0.5)
            }
        
        # Build mesh request
        return MeshGenerationRequest(
            geometry_type=geometry_type,
            parameters=parameters,
            mesh_density=int(params.mesh_density)
        ) 