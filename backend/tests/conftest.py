"""
Pytest configuration and shared fixtures
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.jobs.store import InMemoryJobStore
from app.main import app
from app.models import SimulationJob, SimulationParamsDTO, SimulationType


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Test settings with temporary workspace"""
    return Settings(
        workspace_base_dir=Path("/tmp/test_workspace") / str(uuid4()),
        debug=True,
        max_concurrent_jobs=2,
        job_timeout_seconds=30
    )


@pytest.fixture
def app(test_settings, monkeypatch):
    """Create test application"""
    # Monkey patch the settings
    monkeypatch.setattr("app.config.settings.settings", test_settings)
    monkeypatch.setattr("app.main.settings", test_settings)
    
    # Return app instance
    return app


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def job_store() -> AsyncGenerator[InMemoryJobStore, None]:
    """Create test job store"""
    store = InMemoryJobStore()
    yield store


@pytest.fixture
def sample_simulation_params() -> SimulationParamsDTO:
    """Sample simulation parameters for testing"""
    return SimulationParamsDTO(
        simulation_type=SimulationType.HEAT_TRANSFER,
        geometry={
            "type": "rectangle",
            "width": 1.0,
            "height": 1.0
        },
        material_id=1,
        boundary_conditions=[
            {
                "type": "temperature",
                "value": 100.0,
                "location": "left"
            },
            {
                "type": "temperature",
                "value": 0.0,
                "location": "right"
            }
        ],
        mesh_density=2.0
    )


@pytest.fixture
async def sample_job(job_store, sample_simulation_params) -> SimulationJob:
    """Create a sample job"""
    job = SimulationJob(params=sample_simulation_params)
    await job_store.create(job)
    return job 