"""
Tests for API endpoints
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
    
    @patch("app.main.docker_wrapper")
    def test_health_endpoint(self, mock_docker, client):
        """Test health endpoint"""
        # Mock Docker health check
        mock_docker.check_elmer_health = AsyncMock(return_value=True)
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "elmer_available" in data
        assert "active_jobs" in data


class TestSimulationEndpoints:
    """Test simulation API endpoints"""
    
    def test_create_simulation_success(self, client, sample_simulation_params):
        """Test successful simulation creation"""
        response = client.post(
            "/api/simulations",
            json=sample_simulation_params.dict()
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert "created_at" in data
        assert data["status"] == "pending"
        assert data["message"] == "Simulation job created successfully"
    
    def test_create_simulation_invalid_params(self, client):
        """Test simulation creation with invalid parameters"""
        # Missing required fields
        response = client.post(
            "/api/simulations",
            json={"simulation_type": "heat_transfer"}
        )
        assert response.status_code == 422
    
    @patch("app.main.job_launcher")
    def test_create_simulation_max_jobs_reached(self, mock_launcher, client, sample_simulation_params):
        """Test simulation creation when max jobs reached"""
        # Mock launcher to raise RuntimeError
        mock_launcher.launch_job = AsyncMock(
            side_effect=RuntimeError("Maximum concurrent jobs (5) reached")
        )
        
        response = client.post(
            "/api/simulations",
            json=sample_simulation_params.dict()
        )
        
        assert response.status_code == 503
        assert "Maximum concurrent jobs" in response.json()["detail"]
    
    def test_get_simulation_status(self, client, sample_simulation_params):
        """Test getting simulation status"""
        # First create a simulation
        create_response = client.post(
            "/api/simulations",
            json=sample_simulation_params.dict()
        )
        job_id = create_response.json()["id"]
        
        # Get status
        response = client.get(f"/api/simulations/{job_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == job_id
        assert "status" in data
        assert "progress" in data
        assert "created_at" in data
    
    def test_get_nonexistent_simulation_status(self, client):
        """Test getting status of non-existent simulation"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/simulations/{fake_id}/status")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_simulation_result(self, client, sample_simulation_params):
        """Test getting simulation results"""
        # Create a simulation
        create_response = client.post(
            "/api/simulations",
            json=sample_simulation_params.dict()
        )
        job_id = create_response.json()["id"]
        
        # Get results
        response = client.get(f"/api/simulations/{job_id}/result")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == job_id
        assert "status" in data
        assert "result_files" in data
        assert isinstance(data["result_files"], list)
    
    def test_list_simulations(self, client, sample_simulation_params):
        """Test listing simulations"""
        # Create multiple simulations
        job_ids = []
        for _ in range(3):
            response = client.post(
                "/api/simulations",
                json=sample_simulation_params.dict()
            )
            job_ids.append(response.json()["id"])
        
        # List all
        response = client.get("/api/simulations")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        
        # Check that our jobs are in the list
        listed_ids = {item["id"] for item in data}
        for job_id in job_ids:
            assert job_id in listed_ids
    
    def test_list_simulations_with_filter(self, client):
        """Test listing simulations with status filter"""
        response = client.get("/api/simulations?status=pending")
        assert response.status_code == 200
        
        # Invalid status
        response = client.get("/api/simulations?status=invalid")
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]
    
    def test_list_simulations_with_pagination(self, client):
        """Test listing simulations with pagination"""
        response = client.get("/api/simulations?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    @patch("app.main.job_launcher")
    def test_cancel_simulation(self, mock_launcher, client, sample_simulation_params):
        """Test cancelling a simulation"""
        # Create a simulation
        create_response = client.post(
            "/api/simulations",
            json=sample_simulation_params.dict()
        )
        job_id = create_response.json()["id"]
        
        # Mock successful cancellation
        mock_launcher.cancel_job = AsyncMock(return_value=True)
        
        # Cancel it
        response = client.delete(f"/api/simulations/{job_id}")
        assert response.status_code == 200
        assert "cancelled successfully" in response.json()["message"]
    
    @patch("app.main.job_launcher")
    def test_cancel_completed_simulation_fails(self, mock_launcher, client, sample_simulation_params):
        """Test cancelling completed simulation fails"""
        # Create a simulation
        create_response = client.post(
            "/api/simulations",
            json=sample_simulation_params.dict()
        )
        job_id = create_response.json()["id"]
        
        # Mock cancellation failure
        mock_launcher.cancel_job = AsyncMock(return_value=False)
        
        # Try to cancel
        response = client.delete(f"/api/simulations/{job_id}")
        assert response.status_code == 400
        assert "not running" in response.json()["detail"]


class TestMaterialsEndpoint:
    """Test materials endpoint"""
    
    def test_get_materials(self, client):
        """Test getting materials list"""
        response = client.get("/api/materials")
        assert response.status_code == 200
        
        data = response.json()
        assert "materials" in data
        assert isinstance(data["materials"], list)
        assert len(data["materials"]) >= 1
        
        # Check material structure
        material = data["materials"][0]
        assert "id" in material
        assert "name" in material
        assert "properties" in material
        
        # Check properties
        props = material["properties"]
        assert "E" in props
        assert "nu" in props
        assert "rho" in props
        assert "k" in props 