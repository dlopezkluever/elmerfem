"""
Simulation management endpoints with enhanced job tracking
"""

import logging
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Query, status
from fastapi.responses import FileResponse, JSONResponse

from ...dependencies import get_job_store, get_job_launcher
from ...jobs.launcher import JobLauncher
from ...jobs.store import JobStore
from ...models import (
    SimulationJob,
    SimulationParamsDTO,
    SimulationCreateResponseDTO,
    SimulationStatusDTO,
    SimulationResultDTO,
    JobStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/", response_model=SimulationCreateResponseDTO)
async def create_simulation(
    params: SimulationParamsDTO,
    launcher: JobLauncher = Depends(get_job_launcher)
) -> SimulationCreateResponseDTO:
    """
    Create a new simulation job
    
    This endpoint validates the input parameters and launches a new simulation job.
    The job runs asynchronously and progress can be tracked using the status endpoint.
    """
    try:
        job = await launcher.launch_job(params)
        
        return SimulationCreateResponseDTO(
            id=job.id,
            status=job.status,
            created_at=job.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create simulation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create simulation"
        )


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
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
    Get the results of a completed simulation
    
    Returns information about result files and provides download links.
    Only available for completed jobs.
    """
    job = await job_store.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (status: {job.status})"
        )
    
    # Build download URLs for result files
    result_files = []
    for filename in job.result_files:
        result_files.append(f"/api/v1/simulations/{job_id}/download/{filename}")
    
    return SimulationResultDTO(
        id=job.id,
        status=job.status,
        result_files=result_files,
        output_directory=job.output_dir,
        vtk_file=f"/api/v1/simulations/{job_id}/download/vtk" if job.vtk_file_path else None,
        log_file=f"/api/v1/simulations/{job_id}/logs" if job.log_file_path else None,
        sif_file=f"/api/v1/simulations/{job_id}/download/sif" if job.sif_file_path else None
    )


@router.get("/{job_id}/download/{filename}")
async def download_result_file(
    job_id: UUID,
    filename: str,
    job_store: JobStore = Depends(get_job_store)
) -> FileResponse:
    """
    Download a specific result file from a completed simulation
    
    Use special filenames 'vtk' or 'sif' to download the VTK visualization
    file or SIF input file respectively.
    """
    job = await job_store.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (status: {job.status})"
        )
    
    # Handle special file names
    if filename == "vtk" and job.vtk_file_path:
        file_path = job.vtk_file_path
    elif filename == "sif" and job.sif_file_path:
        file_path = job.sif_file_path
    else:
        # Regular result file
        if filename not in job.result_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found in job results"
            )
        file_path = job.workspace_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {filename} not found on disk"
        )
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@router.get("/{job_id}/logs")
async def get_simulation_logs(
    job_id: UUID,
    launcher: JobLauncher = Depends(get_job_launcher)
) -> JSONResponse:
    """
    Get the execution logs for a simulation job
    
    Returns the ElmerSolver output logs if available.
    """
    logs = await launcher.get_job_logs(job_id)
    
    if logs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logs not available for this job"
        )
    
    return JSONResponse(content={"logs": logs})


@router.delete("/{job_id}")
async def cancel_simulation(
    job_id: UUID,
    launcher: JobLauncher = Depends(get_job_launcher)
) -> JSONResponse:
    """
    Cancel a running simulation job
    
    Only running jobs can be cancelled. Completed or failed jobs
    cannot be cancelled.
    """
    success = await launcher.cancel_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not running or cannot be cancelled"
        )
    
    return JSONResponse(content={"message": "Job cancelled successfully"})


@router.get("/", response_model=List[SimulationStatusDTO])
async def list_simulations(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    job_store: JobStore = Depends(get_job_store)
) -> List[SimulationStatusDTO]:
    """
    List all simulation jobs with optional filtering
    
    Returns a paginated list of simulation jobs. Use the status parameter
    to filter by job status (pending, running, completed, failed, cancelled).
    """
    jobs = await job_store.list_jobs(status=status, limit=limit, offset=offset)
    
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


@router.get("/{job_id}/mesh-quality")
async def get_mesh_quality_metrics(
    job_id: UUID,
    job_store: JobStore = Depends(get_job_store)
) -> JSONResponse:
    """
    Get mesh quality metrics for a simulation job
    
    Returns detailed mesh quality information including element count,
    node count, quality metrics, and generation performance data.
    This endpoint is only available for jobs that have successfully
    generated a mesh.
    """
    job = await job_store.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Check if mesh quality metrics exist in metadata
    mesh_quality = job.metadata.get('mesh_quality')
    
    if not mesh_quality:
        # For backward compatibility, check if job has progressed past mesh generation
        if job.progress < 30.0 and job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mesh generation not yet completed for this job"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mesh quality metrics not available for this job"
            )
    
    # Add job context to the response
    response_data = {
        "job_id": str(job_id),
        "simulation_type": job.params.simulation_type.value,
        "geometry_type": job.params.geometry.get('type', 'unknown'),
        "mesh_quality": mesh_quality,
        "mesh_generation_completed": job.progress >= 30.0 or job.status == JobStatus.COMPLETED
    }
    
    return JSONResponse(
        content=response_data,
        status_code=status.HTTP_200_OK
    ) 