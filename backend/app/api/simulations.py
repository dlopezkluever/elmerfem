"""
Legacy simulation endpoints for backward compatibility
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse

from ..dependencies import get_job_store, get_job_launcher
from ..jobs.launcher import JobLauncher
from ..jobs.store import JobStore
from ..models import (
    JobStatus,
    SimulationCreateResponseDTO,
    SimulationParamsDTO,
    SimulationResultDTO,
    SimulationStatusDTO,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/simulations", tags=["simulations-legacy"])


@router.post("", response_model=SimulationCreateResponseDTO, status_code=201)
async def create_simulation(
    params: SimulationParamsDTO,
    job_store: JobStore = Depends(get_job_store),
    job_launcher: JobLauncher = Depends(get_job_launcher)
) -> SimulationCreateResponseDTO:
    """
    Create a new simulation job
    
    This endpoint accepts simulation parameters and launches a new job
    that will be executed asynchronously in the background.
    """
    try:
        # Launch the job
        job = await job_launcher.launch_job(params)
        
        # Return response
        return SimulationCreateResponseDTO(
            id=job.id,
            status=job.status,
            created_at=job.created_at
        )
    except RuntimeError as e:
        # Maximum concurrent jobs reached
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Error creating simulation")
        raise HTTPException(status_code=500, detail="Failed to create simulation")


@router.get("/{job_id}/status", response_model=SimulationStatusDTO)
async def get_simulation_status(
    job_id: UUID,
    job_store: JobStore = Depends(get_job_store)
) -> SimulationStatusDTO:
    """
    Get the current status of a simulation job
    
    Returns detailed status information including progress percentage,
    current step, and any error messages.
    """
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return SimulationStatusDTO(
        id=job.id,
        status=job.status,
        progress=job.progress,
        message=job.current_step,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        current_step=job.current_step,
        total_steps=job.total_steps
    )


@router.get("/{job_id}/result", response_model=SimulationResultDTO)
async def get_simulation_result(
    job_id: UUID,
    job_store: JobStore = Depends(get_job_store)
) -> SimulationResultDTO:
    """
    Get simulation results
    
    Returns information about result files and paths.
    Actual file downloads are handled by separate endpoints.
    """
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return SimulationResultDTO(
        id=job.id,
        status=job.status,
        result_files=job.result_files,
        output_directory=job.output_dir,
        vtk_file=str(job.vtk_file_path) if job.vtk_file_path else None,
        log_file=str(job.log_file_path) if job.log_file_path else None,
        sif_file=str(job.sif_file_path) if job.sif_file_path else None
    )


@router.get("/{job_id}/logs")
async def get_simulation_logs(
    job_id: UUID,
    job_launcher: JobLauncher = Depends(get_job_launcher)
) -> FileResponse:
    """
    Get simulation log file
    
    Returns the raw log output from ElmerSolver execution.
    """
    logs = await job_launcher.get_job_logs(job_id)
    if logs is None:
        raise HTTPException(status_code=404, detail="Logs not found")
    
    return FileResponse(
        content=logs,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"inline; filename=simulation_{job_id}.log"
        }
    )


@router.get("/{job_id}/files/{filename}")
async def download_result_file(
    job_id: UUID,
    filename: str,
    job_store: JobStore = Depends(get_job_store)
) -> FileResponse:
    """
    Download a specific result file
    
    This endpoint allows downloading individual result files
    such as VTK files, result data, or the SIF file.
    """
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not job.workspace_dir:
        raise HTTPException(status_code=404, detail="Workspace directory not found")
    
    # Construct file path safely
    file_path = job.workspace_dir / filename
    
    # Ensure file is within workspace (prevent directory traversal)
    try:
        file_path = file_path.resolve()
        job.workspace_dir.resolve()
        file_path.relative_to(job.workspace_dir)
    except (ValueError, RuntimeError):
        raise HTTPException(status_code=403, detail="Invalid file path")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine content type
    content_type = "application/octet-stream"
    if file_path.suffix == ".vtu":
        content_type = "application/xml"
    elif file_path.suffix == ".vtk":
        content_type = "application/x-vtk"
    elif file_path.suffix == ".sif":
        content_type = "text/plain"
    
    return FileResponse(
        content=file_path.open("rb"),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.delete("/{job_id}")
async def cancel_simulation(
    job_id: UUID,
    job_launcher: JobLauncher = Depends(get_job_launcher)
) -> dict:
    """
    Cancel a running simulation
    
    Attempts to cancel a simulation that is currently running.
    Returns success status.
    """
    cancelled = await job_launcher.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Job is not running or already completed"
        )
    
    return {"message": "Simulation cancelled successfully"}


@router.get("")
async def list_simulations(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    job_store: JobStore = Depends(get_job_store)
) -> list[SimulationStatusDTO]:
    """
    List all simulations with optional filtering
    
    Query parameters:
    - status: Filter by job status (pending, running, completed, failed, cancelled)
    - limit: Maximum number of results (default: 50, max: 100)
    - offset: Pagination offset (default: 0)
    """
    # Validate limit
    limit = min(limit, 100)
    
    # Convert status string to enum if provided
    status_filter = None
    if status:
        try:
            from ..models import JobStatus
            status_filter = JobStatus(status.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Valid values are: pending, running, completed, failed, cancelled"
            )
    
    # Get jobs from store
    jobs = await job_store.list_jobs(
        status=status_filter,
        limit=limit,
        offset=offset
    )
    
    # Convert to DTOs
    return [
        SimulationStatusDTO(
            id=job.id,
            status=job.status,
            progress=job.progress,
            message=job.current_step,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            current_step=job.current_step,
            total_steps=job.total_steps
        )
        for job in jobs
    ] 