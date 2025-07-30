"""
Tests for simulation result API endpoints
"""

import gzip
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import numpy as np
import pytest
import meshio
from fastapi.testclient import TestClient

from app.main import app
from app.jobs.store import InMemoryJobStore
from app.models import SimulationJob, SimulationParamsDTO, JobStatus, SimulationType
from app.dependencies import get_job_store


@pytest.fixture
def test_client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_job_store():
    """Create a mock job store with test data"""
    return InMemoryJobStore()


@pytest.fixture 
def sample_completed_job():
    """Create a sample completed job with result data"""
    job_id = uuid4()
    
    # Create temporary directory for test data
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create sample result JSON
    result_data = {
        "metadata": {
            "format": "vtu_converted",
            "source_file": "result.vtu",
            "num_points": 4,
            "num_cells": 2,
            "conversion_timestamp": "2024-01-01T12:00:00"
        },
        "points": [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 1.0, 0.0],
            [0.5, 0.5, 1.0]
        ],
        "cells": {
            "triangle": [[0, 1, 2]],
            "tetra": [[0, 1, 2, 3]]
        },
        "point_data": {
            "temperature": [20.0, 100.0, 60.0, 80.0]
        },
        "cell_data": {
            "material_id": {
                "triangle": [1],
                "tetra": [2]
            }
        },
        "field_data": {
            "domain": {"id": 1, "dim": 3}
        }
    }
    
    # Write JSON file
    json_path = temp_dir / "result_result.json"
    with open(json_path, 'w') as f:
        json.dump(result_data, f)
    
    # Write compressed JSON file
    gzip_path = temp_dir / "result_result.json.gz"
    with gzip.open(gzip_path, 'wt') as f:
        json.dump(result_data, f)
    
    # Create job with metadata
    params = SimulationParamsDTO(
        simulation_type=SimulationType.HEAT_TRANSFER,
        geometry={"type": "box", "length": 1.0, "width": 1.0, "height": 1.0},
        material_id="steel",
        boundary_conditions=[]
    )
    
    job = SimulationJob(
        id=job_id,
        params=params,
        status=JobStatus.COMPLETED,
        workspace_dir=temp_dir,
        metadata={
            "result_json": "result_result.json",
            "result_json_gzip": "result_result.json.gz"
        }
    )
    
    return job, result_data


def test_get_simulation_result_data_success(test_client, mock_job_store, sample_completed_job):
    """Test successful retrieval of simulation result data"""
    job, expected_data = sample_completed_job
    
    # Mock the job store dependency
    async def get_test_job_store():
        mock_job_store.store[job.id] = job
        return mock_job_store
    
    app.dependency_overrides[get_job_store] = get_test_job_store
    
    try:
        # Make request
        response = test_client.get(f"/api/v1/simulations/{job.id}/result-data")
        
        # Check response
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify structure
        assert "metadata" in response_data
        assert "points" in response_data
        assert "cells" in response_data
        assert "point_data" in response_data
        assert "cell_data" in response_data
        assert "field_data" in response_data
        
        # Verify data matches
        assert response_data["metadata"]["num_points"] == 4
        assert len(response_data["points"]) == 4
        assert "temperature" in response_data["point_data"]
        
    finally:
        app.dependency_overrides.clear()


def test_get_simulation_result_data_not_found(test_client, mock_job_store):
    """Test retrieval of non-existent simulation"""
    fake_id = uuid4()
    
    async def get_test_job_store():
        return mock_job_store
    
    app.dependency_overrides[get_job_store] = get_test_job_store
    
    try:
        response = test_client.get(f"/api/v1/simulations/{fake_id}/result-data")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_get_simulation_result_data_not_completed(test_client, mock_job_store):
    """Test retrieval from job that is not completed"""
    job_id = uuid4()
    
    params = SimulationParamsDTO(
        simulation_type=SimulationType.HEAT_TRANSFER,
        geometry={"type": "box"},
        material_id="steel",
        boundary_conditions=[]
    )
    
    job = SimulationJob(
        id=job_id,
        params=params,
        status=JobStatus.RUNNING  # Not completed
    )
    
    async def get_test_job_store():
        mock_job_store.store[job_id] = job
        return mock_job_store
    
    app.dependency_overrides[get_job_store] = get_test_job_store
    
    try:
        response = test_client.get(f"/api/v1/simulations/{job_id}/result-data")
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_get_simulation_result_data_compressed_success(test_client, mock_job_store, sample_completed_job):
    """Test successful retrieval of compressed simulation result data"""
    job, expected_data = sample_completed_job
    
    async def get_test_job_store():
        mock_job_store.store[job.id] = job
        return mock_job_store
    
    app.dependency_overrides[get_job_store] = get_test_job_store
    
    try:
        # Make request for compressed data
        response = test_client.get(f"/api/v1/simulations/{job.id}/result-data/compressed")
        
        # Check response
        assert response.status_code == 200
        assert response.headers["content-encoding"] == "gzip"
        assert response.headers["content-type"] == "application/json"
        
        # Decompress and verify content
        decompressed_data = gzip.decompress(response.content)
        result_data = json.loads(decompressed_data)
        
        # Verify structure
        assert "metadata" in result_data
        assert "points" in result_data
        assert result_data["metadata"]["num_points"] == 4
        
    finally:
        app.dependency_overrides.clear()


def test_get_simulation_result_data_compressed_fallback(test_client, mock_job_store):
    """Test compressed endpoint fallback when no compressed file exists"""
    job_id = uuid4()
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create only uncompressed JSON file
    result_data = {
        "metadata": {"format": "vtu_converted", "num_points": 2},
        "points": [[0, 0, 0], [1, 1, 1]],
        "cells": {},
        "point_data": {},
        "cell_data": {},
        "field_data": {}
    }
    
    json_path = temp_dir / "result_result.json"
    with open(json_path, 'w') as f:
        json.dump(result_data, f)
    
    params = SimulationParamsDTO(
        simulation_type=SimulationType.HEAT_TRANSFER,
        geometry={"type": "box"},
        material_id="steel",
        boundary_conditions=[]
    )
    
    job = SimulationJob(
        id=job_id,
        params=params,
        status=JobStatus.COMPLETED,
        workspace_dir=temp_dir,
        metadata={
            "result_json": "result_result.json"
            # No compressed version
        }
    )
    
    async def get_test_job_store():
        mock_job_store.store[job_id] = job
        return mock_job_store
    
    app.dependency_overrides[get_job_store] = get_test_job_store
    
    try:
        # Request compressed data - should fallback to on-the-fly compression
        response = test_client.get(f"/api/v1/simulations/{job_id}/result-data/compressed")
        
        assert response.status_code == 200
        assert response.headers["content-encoding"] == "gzip"
        
        # Verify content can be decompressed
        decompressed_data = gzip.decompress(response.content)
        result_data_back = json.loads(decompressed_data)
        assert result_data_back["metadata"]["num_points"] == 2
        
    finally:
        app.dependency_overrides.clear()


def test_simulation_result_dto_includes_json_fields(test_client, mock_job_store, sample_completed_job):
    """Test that the simulation result DTO includes JSON result URLs"""
    job, _ = sample_completed_job
    
    async def get_test_job_store():
        mock_job_store.store[job.id] = job
        return mock_job_store
    
    app.dependency_overrides[get_job_store] = get_test_job_store
    
    try:
        # Get simulation result info
        response = test_client.get(f"/api/v1/simulations/{job.id}/result")
        
        assert response.status_code == 200
        result_info = response.json()
        
        # Check that JSON result URLs are included
        assert "result_json" in result_info
        assert "result_json_compressed" in result_info
        assert result_info["result_json"] is not None
        assert result_info["result_json_compressed"] is not None
        assert "/result-data" in result_info["result_json"]
        assert "/result-data/compressed" in result_info["result_json_compressed"]
        
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    # Run the tests
    import subprocess
    subprocess.run(["python", "-m", "pytest", __file__, "-v"]) 