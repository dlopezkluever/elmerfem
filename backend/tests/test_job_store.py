"""
Tests for job store
"""

import pytest

from app.models import JobStatus


@pytest.mark.asyncio
class TestInMemoryJobStore:
    """Test InMemoryJobStore implementation"""
    
    async def test_create_job(self, job_store, sample_job):
        """Test creating a job"""
        # Job was created in fixture
        retrieved = await job_store.get(sample_job.id)
        assert retrieved is not None
        assert retrieved.id == sample_job.id
        assert retrieved.params == sample_job.params
    
    async def test_create_duplicate_job_fails(self, job_store, sample_job):
        """Test that creating duplicate job ID fails"""
        with pytest.raises(ValueError, match="already exists"):
            await job_store.create(sample_job)
    
    async def test_get_nonexistent_job(self, job_store):
        """Test getting non-existent job returns None"""
        from uuid import uuid4
        job = await job_store.get(uuid4())
        assert job is None
    
    async def test_update_job(self, job_store, sample_job):
        """Test updating a job"""
        # Update job status
        sample_job.status = JobStatus.RUNNING
        sample_job.progress = 50.0
        
        updated = await job_store.update(sample_job)
        assert updated.status == JobStatus.RUNNING
        assert updated.progress == 50.0
        
        # Verify update persisted
        retrieved = await job_store.get(sample_job.id)
        assert retrieved.status == JobStatus.RUNNING
        assert retrieved.progress == 50.0
    
    async def test_update_nonexistent_job_fails(self, job_store, sample_job):
        """Test updating non-existent job fails"""
        from uuid import uuid4
        sample_job.id = uuid4()
        
        with pytest.raises(ValueError, match="not found"):
            await job_store.update(sample_job)
    
    async def test_delete_job(self, job_store, sample_job):
        """Test deleting a job"""
        # Delete the job
        result = await job_store.delete(sample_job.id)
        assert result is True
        
        # Verify it's gone
        retrieved = await job_store.get(sample_job.id)
        assert retrieved is None
        
        # Delete again returns False
        result = await job_store.delete(sample_job.id)
        assert result is False
    
    async def test_list_jobs(self, job_store, sample_simulation_params):
        """Test listing jobs"""
        from app.models import SimulationJob
        
        # Create multiple jobs
        jobs = []
        for i in range(5):
            job = SimulationJob(params=sample_simulation_params)
            if i < 2:
                job.status = JobStatus.COMPLETED
            elif i < 4:
                job.status = JobStatus.RUNNING
            await job_store.create(job)
            jobs.append(job)
        
        # List all jobs
        all_jobs = await job_store.list_jobs()
        assert len(all_jobs) == 6  # 5 + 1 from fixture
        
        # List with status filter
        completed = await job_store.list_jobs(status=JobStatus.COMPLETED)
        assert len(completed) == 2
        
        running = await job_store.list_jobs(status=JobStatus.RUNNING)
        assert len(running) == 2
        
        # Test pagination
        page1 = await job_store.list_jobs(limit=3, offset=0)
        assert len(page1) == 3
        
        page2 = await job_store.list_jobs(limit=3, offset=3)
        assert len(page2) == 3
        
        # Verify no overlap
        page1_ids = {j.id for j in page1}
        page2_ids = {j.id for j in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    async def test_get_active_job_count(self, job_store, sample_simulation_params):
        """Test getting active job count"""
        from app.models import SimulationJob
        
        # Initially no running jobs
        count = await job_store.get_active_job_count()
        assert count == 0
        
        # Create running jobs
        for i in range(3):
            job = SimulationJob(params=sample_simulation_params)
            job.status = JobStatus.RUNNING
            await job_store.create(job)
        
        count = await job_store.get_active_job_count()
        assert count == 3
        
        # Create non-running jobs
        for status in [JobStatus.PENDING, JobStatus.COMPLETED, JobStatus.FAILED]:
            job = SimulationJob(params=sample_simulation_params)
            job.status = status
            await job_store.create(job)
        
        # Count should still be 3
        count = await job_store.get_active_job_count()
        assert count == 3
    
    async def test_update_job_progress(self, job_store, sample_job):
        """Test updating job progress"""
        updated = await job_store.update_job_progress(
            sample_job.id, 
            75.0,
            "Processing step 3 of 4"
        )
        
        assert updated is not None
        assert updated.progress == 75.0
        assert updated.current_step == "Processing step 3 of 4"
    
    async def test_mark_job_started(self, job_store, sample_job):
        """Test marking job as started"""
        updated = await job_store.mark_job_started(sample_job.id)
        
        assert updated is not None
        assert updated.status == JobStatus.RUNNING
        assert updated.started_at is not None
    
    async def test_mark_job_completed(self, job_store, sample_job):
        """Test marking job as completed"""
        result_files = ["output.vtu", "results.dat"]
        updated = await job_store.mark_job_completed(
            sample_job.id,
            result_files=result_files
        )
        
        assert updated is not None
        assert updated.status == JobStatus.COMPLETED
        assert updated.completed_at is not None
        assert updated.progress == 100.0
        assert updated.result_files == result_files
    
    async def test_mark_job_failed(self, job_store, sample_job):
        """Test marking job as failed"""
        error_msg = "Solver convergence failed"
        updated = await job_store.mark_job_failed(sample_job.id, error_msg)
        
        assert updated is not None
        assert updated.status == JobStatus.FAILED
        assert updated.completed_at is not None
        assert updated.error_message == error_msg 