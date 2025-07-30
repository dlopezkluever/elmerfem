"""
Simulation management endpoints with enhanced job tracking
"""

import gzip
import json
import logging
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Query, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from ...dependencies import get_job_store, get_job_launcher
from ...jobs.launcher import JobLauncher
from ...jobs.store import JobStore
from ...models import (
    SimulationJob,
    SimulationParamsDTO,
    SimulationCreateResponseDTO,
    SimulationStatusDTO,
    SimulationResultDTO,
    VTUDataDTO,
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
    
    # Get JSON result paths from metadata
    result_json = None
    result_json_compressed = None
    
    if job.metadata:
        if 'result_json' in job.metadata:
            result_json = f"/api/v1/simulations/{job_id}/result-data"
        if 'result_json_gzip' in job.metadata:
            result_json_compressed = f"/api/v1/simulations/{job_id}/result-data/compressed"
    
    return SimulationResultDTO(
        id=job.id,
        status=job.status,
        result_files=result_files,
        vtk_file=f"/api/v1/simulations/{job_id}/download/{job.vtk_file_path.name}" if job.vtk_file_path else None,
        log_file=f"/api/v1/simulations/{job_id}/logs" if job.log_file_path else None,
        result_json=result_json,
        result_json_compressed=result_json_compressed,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at or job.created_at,
        execution_time=(job.completed_at - job.started_at).total_seconds() if job.completed_at and job.started_at else 0.0
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


@router.get("/{job_id}/result-data", response_model=VTUDataDTO)
async def get_simulation_result_data(
    job_id: UUID,
    job_store: JobStore = Depends(get_job_store)
) -> VTUDataDTO:
    """
    Get simulation result data in JSON format for visualization
    
    Returns the complete mesh and result data as JSON, suitable for 3D visualization.
    Only available for completed jobs with converted VTU data.
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
    
    # Check if JSON result data exists
    if not job.metadata or 'result_json' not in job.metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result data not available. VTU file may not have been converted to JSON."
        )
    
    # Construct path to JSON file
    json_filename = job.metadata['result_json']
    json_path = job.workspace_dir / json_filename
    
    if not json_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result JSON file not found: {json_filename}"
        )
    
    try:
        # Read and return JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        # Validate the structure matches our DTO
        return VTUDataDTO(**result_data)
        
    except Exception as e:
        logger.error(f"Failed to read result JSON for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read result data: {str(e)}"
        )


@router.get("/{job_id}/result-data/compressed")
async def get_simulation_result_data_compressed(
    job_id: UUID,
    job_store: JobStore = Depends(get_job_store)
) -> StreamingResponse:
    """
    Get simulation result data as compressed stream for efficient transfer
    
    Returns gzip-compressed JSON data with appropriate headers.
    Recommended for large result datasets.
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
    
    # Check if compressed JSON result data exists
    if not job.metadata or 'result_json_gzip' not in job.metadata:
        # Fallback to uncompressed version if compressed not available
        if 'result_json' in job.metadata:
            return await _stream_uncompressed_json_as_gzip(job, job_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compressed result data not available"
            )
    
    # Use pre-compressed file
    gzip_filename = job.metadata['result_json_gzip']
    gzip_path = job.workspace_dir / gzip_filename
    
    if not gzip_path.exists():
        # Fallback to uncompressed version
        if 'result_json' in job.metadata:
            return await _stream_uncompressed_json_as_gzip(job, job_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Compressed result file not found: {gzip_filename}"
            )
    
    try:
        def generate_compressed_stream():
            """Generator for streaming compressed data"""
            with open(gzip_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    yield chunk
        
        return StreamingResponse(
            generate_compressed_stream(),
            media_type="application/json",
            headers={
                "Content-Encoding": "gzip",
                "Content-Type": "application/json",
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Disposition": f"inline; filename=result_{job_id}.json.gz"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to stream compressed result for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream compressed data: {str(e)}"
        )


async def _stream_uncompressed_json_as_gzip(job: SimulationJob, job_id: UUID) -> StreamingResponse:
    """
    Helper function to compress and stream uncompressed JSON on-the-fly
    """
    json_filename = job.metadata['result_json']
    json_path = job.workspace_dir / json_filename
    
    if not json_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result JSON file not found: {json_filename}"
        )
    
    def generate_compressed_json():
        """Generator for compressing JSON on-the-fly"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                # Read the entire file and compress it
                json_content = f.read()
                compressed_data = gzip.compress(json_content.encode('utf-8'))
                
                # Yield in chunks for streaming
                chunk_size = 8192
                for i in range(0, len(compressed_data), chunk_size):
                    yield compressed_data[i:i + chunk_size]
                    
        except Exception as e:
            logger.error(f"Error in on-the-fly compression: {e}")
            # Return error as compressed JSON
            error_json = json.dumps({"error": f"Compression failed: {str(e)}"})
            yield gzip.compress(error_json.encode('utf-8'))
    
    return StreamingResponse(
        generate_compressed_json(),
        media_type="application/json",
        headers={
            "Content-Encoding": "gzip",
            "Content-Type": "application/json",
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f"inline; filename=result_{job_id}.json.gz"
        }
    ) 