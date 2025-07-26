"""
Job store interface and implementations
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ..models import SimulationJob, JobStatus

logger = logging.getLogger(__name__)


class JobStore(ABC):
    """Abstract base class for job storage"""
    
    @abstractmethod
    async def create(self, job: SimulationJob) -> SimulationJob:
        """Create a new job"""
        pass
    
    @abstractmethod
    async def get(self, job_id: UUID) -> Optional[SimulationJob]:
        """Get a job by ID"""
        pass
    
    @abstractmethod
    async def update(self, job: SimulationJob) -> SimulationJob:
        """Update an existing job"""
        pass
    
    @abstractmethod
    async def delete(self, job_id: UUID) -> bool:
        """Delete a job"""
        pass
    
    @abstractmethod
    async def list_jobs(
        self, 
        status: Optional[JobStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SimulationJob]:
        """List jobs with optional filtering"""
        pass
    
    @abstractmethod
    async def get_active_job_count(self) -> int:
        """Get count of currently running jobs"""
        pass


class InMemoryJobStore(JobStore):
    """In-memory implementation of job store"""
    
    def __init__(self):
        self._jobs: Dict[UUID, SimulationJob] = {}
    
    async def create(self, job: SimulationJob) -> SimulationJob:
        """Create a new job"""
        if job.id in self._jobs:
            raise ValueError(f"Job with ID {job.id} already exists")
        self._jobs[job.id] = job
        return job
    
    async def get(self, job_id: UUID) -> Optional[SimulationJob]:
        """Get a job by ID"""
        return self._jobs.get(job_id)
    
    async def update(self, job: SimulationJob) -> SimulationJob:
        """Update an existing job"""
        if job.id not in self._jobs:
            raise ValueError(f"Job with ID {job.id} not found")
        self._jobs[job.id] = job
        return job
    
    async def delete(self, job_id: UUID) -> bool:
        """Delete a job"""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False
    
    async def list_jobs(
        self, 
        status: Optional[JobStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SimulationJob]:
        """List jobs with optional filtering"""
        jobs = list(self._jobs.values())
        
        # Filter by status if provided
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        # Apply pagination
        return jobs[offset:offset + limit]
    
    async def get_active_job_count(self) -> int:
        """Get count of currently running jobs"""
        return sum(
            1 for job in self._jobs.values() 
            if job.status == JobStatus.RUNNING
        )
    
    async def update_job_progress(
        self, 
        job_id: UUID, 
        progress: float,
        current_step: Optional[str] = None
    ) -> Optional[SimulationJob]:
        """Update job progress"""
        job = await self.get(job_id)
        if job:
            job.progress = progress
            if current_step:
                job.current_step = current_step
            await self.update(job)
        return job
    
    async def mark_job_started(self, job_id: UUID) -> Optional[SimulationJob]:
        """Mark a job as started"""
        job = await self.get(job_id)
        if job:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            await self.update(job)
        return job
    
    async def mark_job_completed(
        self, 
        job_id: UUID,
        result_files: Optional[List[str]] = None
    ) -> Optional[SimulationJob]:
        """Mark a job as completed"""
        job = await self.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress = 100.0
            if result_files:
                job.result_files = result_files
            await self.update(job)
        return job
    
    async def mark_job_failed(
        self, 
        job_id: UUID,
        error_message: str
    ) -> Optional[SimulationJob]:
        """Mark a job as failed"""
        job = await self.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = error_message
            await self.update(job)
        return job


class RedisJobStore(JobStore):
    """Redis-based job storage implementation"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize Redis job store
        
        Args:
            redis_url: Redis connection URL
        """
        # Note: This is a placeholder implementation
        # Full Redis support would require aioredis and proper serialization
        # For MVP, we'll use the in-memory store
        logger.warning("RedisJobStore not fully implemented, using InMemoryJobStore as fallback")
        self._fallback_store = InMemoryJobStore()
    
    async def create(self, job: SimulationJob) -> SimulationJob:
        """Create a new job"""
        return await self._fallback_store.create(job)
    
    async def get(self, job_id: UUID) -> Optional[SimulationJob]:
        """Get a job by ID"""
        return await self._fallback_store.get(job_id)
    
    async def update(self, job: SimulationJob) -> SimulationJob:
        """Update an existing job"""
        return await self._fallback_store.update(job)
    
    async def delete(self, job_id: UUID) -> bool:
        """Delete a job"""
        return await self._fallback_store.delete(job_id)
    
    async def list_jobs(
        self, status: Optional[JobStatus] = None, limit: int = 100, offset: int = 0
    ) -> List[SimulationJob]:
        """List jobs with optional filtering"""
        return await self._fallback_store.list_jobs(status, limit, offset)
    
    async def update_job_progress(
        self, job_id: UUID, progress: float, message: Optional[str] = None,
        current_step: Optional[str] = None
    ) -> Optional[SimulationJob]:
        """Update job progress"""
        return await self._fallback_store.update_job_progress(job_id, progress, message, current_step)
    
    async def mark_job_started(self, job_id: UUID) -> Optional[SimulationJob]:
        """Mark job as started"""
        return await self._fallback_store.mark_job_started(job_id)
    
    async def mark_job_completed(
        self, job_id: UUID, result_files: Optional[List[str]] = None
    ) -> Optional[SimulationJob]:
        """Mark job as completed"""
        return await self._fallback_store.mark_job_completed(job_id, result_files)
    
    async def mark_job_failed(self, job_id: UUID, error: str) -> Optional[SimulationJob]:
        """Mark job as failed"""
        return await self._fallback_store.mark_job_failed(job_id, error)
    
    async def get_active_job_count(self) -> int:
        """Get count of currently running jobs"""
        return await self._fallback_store.get_active_job_count()


# Global job store instance getter
def get_job_store() -> JobStore:
    """
    Get the job store instance
    
    This function is used for dependency injection in FastAPI endpoints.
    It returns the global job store instance from the main application.
    """
    from ..main import job_store
    return job_store 