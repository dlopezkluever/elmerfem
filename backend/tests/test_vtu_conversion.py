"""
Tests for VTU result parsing and JSON conversion
"""

import asyncio
import gzip
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import meshio

from app.jobs.launcher import JobLauncher
from app.jobs.store import InMemoryJobStore
from app.services.docker_wrapper import DockerWrapper


@pytest.fixture
def job_launcher():
    """Create a JobLauncher instance for testing"""
    job_store = InMemoryJobStore()
    docker_wrapper = MagicMock(spec=DockerWrapper)
    return JobLauncher(job_store, docker_wrapper)


@pytest.fixture
def sample_mesh():
    """Create a sample mesh for testing"""
    # Create simple triangle mesh
    points = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.5, 1.0, 0.0],
        [0.5, 0.5, 1.0]
    ])
    
    cells = [
        ("triangle", np.array([[0, 1, 2]])),
        ("tetra", np.array([[0, 1, 2, 3]]))
    ]
    
    point_data = {
        "temperature": np.array([20.0, 100.0, 60.0, 80.0]),
        "displacement": np.array([
            [0.0, 0.0, 0.0],
            [0.1, 0.0, 0.0],
            [0.05, 0.1, 0.0],
            [0.05, 0.05, 0.1]
        ])
    }
    
    cell_data = {
        "material_id": [
            np.array([1]),  # For triangle cells
            np.array([2])   # For tetra cells
        ]
    }
    
    field_data = {
        "domain": np.array([1, 3]),
        "boundary": np.array([2, 2])
    }
    
    mesh = meshio.Mesh(
        points=points,
        cells=cells,
        point_data=point_data,
        cell_data=cell_data,
        field_data=field_data
    )
    
    return mesh


@pytest.mark.asyncio
async def test_convert_vtu_to_json_basic(job_launcher, sample_mesh):
    """Test basic VTU to JSON conversion"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Write sample mesh to VTU file
        vtu_path = temp_path / "test_result.vtu"
        sample_mesh.write(vtu_path)
        
        # Convert to JSON
        result_paths = await job_launcher._convert_vtu_to_json(
            vtu_path, temp_path, compress=True
        )
        
        # Check that both JSON and compressed files were created
        assert "json" in result_paths
        assert "gzip" in result_paths
        assert result_paths["json"].exists()
        assert result_paths["gzip"].exists()
        
        # Load and verify JSON content
        with open(result_paths["json"], 'r') as f:
            json_data = json.load(f)
        
        # Check structure
        assert "metadata" in json_data
        assert "points" in json_data
        assert "cells" in json_data
        assert "point_data" in json_data
        assert "cell_data" in json_data
        assert "field_data" in json_data
        
        # Verify metadata
        metadata = json_data["metadata"]
        assert metadata["format"] == "vtu_converted"
        assert metadata["source_file"] == "test_result.vtu"
        assert metadata["num_points"] == 4
        
        # Verify data conversion
        assert len(json_data["points"]) == 4
        assert "triangle" in json_data["cells"]
        assert "tetra" in json_data["cells"]
        assert "temperature" in json_data["point_data"]
        assert "displacement" in json_data["point_data"]


@pytest.mark.asyncio
async def test_convert_vtu_to_json_compression(job_launcher, sample_mesh):
    """Test that compression reduces file size"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Write sample mesh to VTU file
        vtu_path = temp_path / "test_result.vtu"
        sample_mesh.write(vtu_path)
        
        # Convert to JSON with compression
        result_paths = await job_launcher._convert_vtu_to_json(
            vtu_path, temp_path, compress=True
        )
        
        # Check file sizes
        json_size = result_paths["json"].stat().st_size
        gzip_size = result_paths["gzip"].stat().st_size
        
        # Compressed file should be smaller
        assert gzip_size < json_size
        
        # Verify compressed content can be decompressed
        with gzip.open(result_paths["gzip"], 'rt', encoding='utf-8') as f:
            compressed_data = json.load(f)
        
        with open(result_paths["json"], 'r') as f:
            original_data = json.load(f)
        
        # Data should be identical
        assert compressed_data == original_data


@pytest.mark.asyncio 
async def test_convert_vtu_nonexistent_file(job_launcher):
    """Test error handling for non-existent VTU file"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        nonexistent_path = temp_path / "nonexistent.vtu"
        
        with pytest.raises(ValueError, match="VTU conversion failed"):
            await job_launcher._convert_vtu_to_json(
                nonexistent_path, temp_path
            )


@pytest.mark.asyncio
async def test_convert_numpy_array_types(job_launcher):
    """Test _convert_numpy_array with different data types"""
    # Test integer array
    int_array = np.array([1, 2, 3], dtype=np.int32)
    result = job_launcher._convert_numpy_array(int_array)
    assert result == [1, 2, 3]
    assert all(isinstance(x, int) for x in result)
    
    # Test float array
    float_array = np.array([1.5, 2.7, 3.9], dtype=np.float64)
    result = job_launcher._convert_numpy_array(float_array)
    assert result == [1.5, 2.7, 3.9]
    assert all(isinstance(x, float) for x in result)
    
    # Test boolean array
    bool_array = np.array([True, False, True], dtype=bool)
    result = job_launcher._convert_numpy_array(bool_array)
    assert result == [True, False, True]
    assert all(isinstance(x, bool) for x in result)
    
    # Test array with NaN and infinity
    problematic_array = np.array([1.0, np.nan, np.inf, -np.inf])
    result = job_launcher._convert_numpy_array(problematic_array)
    assert len(result) == 4
    assert result[0] == 1.0
    assert result[1] == 0.0  # NaN replaced
    assert result[2] == 1e10  # +inf replaced
    assert result[3] == -1e10  # -inf replaced


@pytest.mark.asyncio
async def test_convert_vtu_with_empty_mesh(job_launcher):
    """Test handling of empty or invalid mesh data"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create minimal VTU file with no points
        empty_mesh = meshio.Mesh(
            points=np.array([]).reshape(0, 3),
            cells=[]
        )
        
        vtu_path = temp_path / "empty.vtu" 
        empty_mesh.write(vtu_path)
        
        with pytest.raises(ValueError, match="VTU file contains no mesh points"):
            await job_launcher._convert_vtu_to_json(vtu_path, temp_path)


def test_write_json_file_helpers(job_launcher):
    """Test the helper functions for writing JSON files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        test_data = {
            "test": "data",
            "numbers": [1, 2, 3],
            "unicode": "ñáéíóú"
        }
        
        # Test uncompressed JSON writing
        json_path = temp_path / "test.json"
        job_launcher._write_json_file(json_path, test_data)
        
        assert json_path.exists()
        with open(json_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data
        
        # Test compressed JSON writing
        gzip_path = temp_path / "test.json.gz"
        job_launcher._write_compressed_json_file(gzip_path, test_data)
        
        assert gzip_path.exists()
        with gzip.open(gzip_path, 'rt', encoding='utf-8') as f:
            loaded_compressed = json.load(f)
        assert loaded_compressed == test_data


@pytest.mark.asyncio
async def test_convert_vtu_without_compression(job_launcher, sample_mesh):
    """Test VTU conversion without compression"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Write sample mesh to VTU file
        vtu_path = temp_path / "test_result.vtu"
        sample_mesh.write(vtu_path)
        
        # Convert to JSON without compression
        result_paths = await job_launcher._convert_vtu_to_json(
            vtu_path, temp_path, compress=False
        )
        
        # Check that only JSON file was created
        assert "json" in result_paths
        assert "gzip" not in result_paths
        assert result_paths["json"].exists() 