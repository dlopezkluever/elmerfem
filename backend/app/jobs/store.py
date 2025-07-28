"""
Job store interface and implementations
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

import redis.asyncio as redis
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
    
    @abstractmethod
    async def update_job_progress(
        self, 
        job_id: UUID, 
        progress: float,
        current_step: Optional[str] = None
    ) -> Optional[SimulationJob]:
        """Update job progress"""
        pass
    
    @abstractmethod
    async def mark_job_started(self, job_id: UUID) -> Optional[SimulationJob]:
        """Mark a job as started"""
        pass
    
    @abstractmethod
    async def mark_job_completed(
        self, 
        job_id: UUID,
        result_files: Optional[List[str]] = None
    ) -> Optional[SimulationJob]:
        """Mark a job as completed"""
        pass
    
    @abstractmethod
    async def mark_job_failed(
        self, 
        job_id: UUID,
        error_message: str
    ) -> Optional[SimulationJob]:
        """Mark a job as failed"""
        pass
    
    @abstractmethod
    async def set_stage(self, job_id: UUID, stage: str, percentage: int = 0) -> None:
        """Set the current stage of a job with optional percentage"""
        pass
    
    @abstractmethod
    async def publish_progress_event(self, job_id: UUID, event_data: Dict[str, Any]) -> None:
        """Publish a progress event for WebSocket consumption"""
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
    
    async def set_stage(self, job_id: UUID, stage: str, percentage: int = 0) -> None:
        """Set the current stage of a job"""
        job = await self.get(job_id)
        if job:
            job.current_step = stage
            job.progress = percentage
            await self.update(job)
    
    async def publish_progress_event(self, job_id: UUID, event_data: Dict[str, Any]) -> None:
        """Publish a progress event (no-op for in-memory store)"""
        logger.debug(f"Progress event for job {job_id}: {event_data}")


class AsyncRedisJobStore(JobStore):
    """Async Redis-based job storage implementation"""
    
    def __init__(self, connection_pool: redis.ConnectionPool):
        """
        Initialize Redis job store with connection pool
        
        Args:
            connection_pool: Redis connection pool for async operations
        """
        self.pool = connection_pool
        self._key_prefix = "job:"
        self._event_channel_prefix = "jobs:"
    
    def _get_key(self, job_id: UUID) -> str:
        """Get Redis key for a job"""
        return f"{self._key_prefix}{job_id}"
    
    def _get_event_channel(self, job_id: UUID) -> str:
        """Get Redis pubsub channel for job events"""
        return f"{self._event_channel_prefix}{job_id}:events"
    
    def _serialize_job(self, job: SimulationJob) -> Dict[str, str]:
        """Serialize job to Redis hash format"""
        data = {
            "id": str(job.id),
            "params": job.params.model_dump_json(),
            "status": job.status.value,
            "progress": str(job.progress),
            "created_at": job.created_at.isoformat(),
            "current_step": job.current_step or "",
            "metadata": json.dumps(job.metadata)
        }
        
        # Optional fields
        if job.started_at:
            data["started_at"] = job.started_at.isoformat()
        if job.completed_at:
            data["completed_at"] = job.completed_at.isoformat()
        if job.workspace_dir:
            data["workspace_dir"] = str(job.workspace_dir)
        if job.sif_file_path:
            data["sif_file_path"] = str(job.sif_file_path)
        if job.log_file_path:
            data["log_file_path"] = str(job.log_file_path)
        if job.error_message:
            data["error_message"] = job.error_message
        if job.result_files:
            data["result_files"] = json.dumps(job.result_files)
        if job.vtk_file_path:
            data["vtk_file_path"] = str(job.vtk_file_path)
            
        return data
    
    def _deserialize_job(self, data: Dict[bytes, bytes]) -> SimulationJob:
        """Deserialize job from Redis hash data"""
        from pathlib import Path
        from ..models import SimulationParamsDTO
        
        # Redis data is already decoded due to decode_responses=True
        str_data = {k: v for k, v in data.items()}
        
        # Parse required fields
        job_data = {
            "id": UUID(str_data["id"]),
            "params": SimulationParamsDTO.model_validate_json(str_data["params"]),
            "status": JobStatus(str_data["status"]),
            "progress": float(str_data["progress"]),
            "created_at": datetime.fromisoformat(str_data["created_at"]),
            "metadata": json.loads(str_data.get("metadata", "{}"))
        }
        
        # Parse optional fields
        if str_data.get("started_at"):
            job_data["started_at"] = datetime.fromisoformat(str_data["started_at"])
        if str_data.get("completed_at"):
            job_data["completed_at"] = datetime.fromisoformat(str_data["completed_at"])
        if str_data.get("workspace_dir"):
            job_data["workspace_dir"] = Path(str_data["workspace_dir"])
        if str_data.get("sif_file_path"):
            job_data["sif_file_path"] = Path(str_data["sif_file_path"])
        if str_data.get("log_file_path"):
            job_data["log_file_path"] = Path(str_data["log_file_path"])
        if str_data.get("error_message"):
            job_data["error_message"] = str_data["error_message"]
        if str_data.get("result_files"):
            job_data["result_files"] = json.loads(str_data["result_files"])
        if str_data.get("vtk_file_path"):
            job_data["vtk_file_path"] = Path(str_data["vtk_file_path"])
        if str_data.get("current_step"):
            job_data["current_step"] = str_data["current_step"]
            
        return SimulationJob(**job_data)
    
    async def create(self, job: SimulationJob) -> SimulationJob:
        """Create a new job in Redis"""
        async with redis.Redis(connection_pool=self.pool) as client:
            key = self._get_key(job.id)
            
            # Check if job exists
            exists = await client.exists(key)
            if exists:
                raise ValueError(f"Job with ID {job.id} already exists")
            
            # Store job data
            await client.hset(key, mapping=self._serialize_job(job))
            
            # Publish creation event
            await self.publish_progress_event(job.id, {
                "event": "job_created",
                "status": job.status.value,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        return job
    
    async def get(self, job_id: UUID) -> Optional[SimulationJob]:
        """Get a job from Redis"""
        async with redis.Redis(connection_pool=self.pool) as client:
            key = self._get_key(job_id)
            data = await client.hgetall(key)
            
            if not data:
                return None
                
            return self._deserialize_job(data)
    
    async def update(self, job: SimulationJob) -> SimulationJob:
        """Update a job in Redis"""
        async with redis.Redis(connection_pool=self.pool) as client:
            key = self._get_key(job.id)
            
            # Check if job exists
            exists = await client.exists(key)
            if not exists:
                raise ValueError(f"Job with ID {job.id} not found")
            
            # Update job data
            await client.hset(key, mapping=self._serialize_job(job))
            
        return job
    
    async def delete(self, job_id: UUID) -> bool:
        """Delete a job from Redis"""
        async with redis.Redis(connection_pool=self.pool) as client:
            key = self._get_key(job_id)
            deleted = await client.delete(key)
            return deleted > 0
    
    async def list_jobs(
        self, 
        status: Optional[JobStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SimulationJob]:
        """List jobs with optional filtering"""
        async with redis.Redis(connection_pool=self.pool) as client:
            # Get all job keys
            pattern = f"{self._key_prefix}*"
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            
            # Get all jobs
            jobs = []
            for key in keys:
                data = await client.hgetall(key)
                if data:
                    job = self._deserialize_job(data)
                    if status is None or job.status == status:
                        jobs.append(job)
            
            # Sort by creation time (newest first)
            jobs.sort(key=lambda j: j.created_at, reverse=True)
            
            # Apply pagination
            return jobs[offset:offset + limit]
    
    async def get_active_job_count(self) -> int:
        """Get count of currently running jobs"""
        jobs = await self.list_jobs(status=JobStatus.RUNNING)
        return len(jobs)
    
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
            
            # Publish progress event
            await self.publish_progress_event(job_id, {
                "event": "progress_update",
                "progress": progress,
                "step": current_step,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        return job
    
    async def mark_job_started(self, job_id: UUID) -> Optional[SimulationJob]:
        """Mark a job as started"""
        job = await self.get(job_id)
        if job:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            await self.update(job)
            
            # Publish start event
            await self.publish_progress_event(job_id, {
                "event": "job_started",
                "timestamp": job.started_at.isoformat()
            })
            
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
            
            # Publish completion event
            await self.publish_progress_event(job_id, {
                "event": "job_completed",
                "result_files": result_files,
                "timestamp": job.completed_at.isoformat()
            })
            
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
            
            # Publish failure event
            await self.publish_progress_event(job_id, {
                "event": "job_failed",
                "error": error_message,
                "timestamp": job.completed_at.isoformat()
            })
            
        return job
    
    async def set_stage(self, job_id: UUID, stage: str, percentage: int = 0) -> None:
        """Set the current stage of a job with percentage"""
        async with redis.Redis(connection_pool=self.pool) as client:
            key = self._get_key(job_id)
            
            # Update stage and percentage
            await client.hset(key, mapping={
                "current_step": stage,
                "progress": str(percentage)
            })
            
            # Publish stage event
            await self.publish_progress_event(job_id, {
                "event": "stage_change",
                "stage": stage,
                "percentage": percentage,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def publish_progress_event(self, job_id: UUID, event_data: Dict[str, Any]) -> None:
        """Publish a progress event for WebSocket consumption"""
        async with redis.Redis(connection_pool=self.pool) as client:
            channel = self._get_event_channel(job_id)
            event_data["job_id"] = str(job_id)
            await client.publish(channel, json.dumps(event_data))
            
            logger.debug(f"Published event to {channel}: {event_data}") 