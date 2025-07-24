"""
Job model for storing simulation job data
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .dtos import JobStatus, SimulationParamsDTO


class SimulationJob(BaseModel):
    """Model representing a simulation job"""
    id: UUID = Field(default_factory=uuid4)
    params: SimulationParamsDTO
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Job execution details
    workspace_dir: Optional[Path] = None
    sif_file_path: Optional[Path] = None
    output_dir: Optional[Path] = None
    log_file_path: Optional[Path] = None
    
    # Process information
    process_id: Optional[int] = None
    
    # Results and errors
    error_message: Optional[str] = None
    result_files: list[str] = Field(default_factory=list)
    vtk_file_path: Optional[Path] = None
    
    # Progress tracking
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True 