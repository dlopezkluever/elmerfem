"""
Tests for data models and DTOs
"""

import pytest
from pydantic import ValidationError

from app.models import (
    BoundaryCondition,
    JobStatus,
    MaterialProperties,
    SimulationJob,
    SimulationParamsDTO,
    SimulationType,
)


class TestMaterialProperties:
    """Test MaterialProperties model"""
    
    def test_valid_material_properties(self):
        """Test creating valid material properties"""
        props = MaterialProperties(
            E=210e9,
            nu=0.3,
            rho=7850,
            k=50
        )
        assert props.E == 210e9
        assert props.nu == 0.3
        assert props.rho == 7850
        assert props.k == 50
    
    def test_invalid_youngs_modulus(self):
        """Test that negative Young's modulus is rejected"""
        with pytest.raises(ValidationError):
            MaterialProperties(E=-1, nu=0.3, rho=1000, k=1)
    
    def test_invalid_poisson_ratio(self):
        """Test that invalid Poisson's ratio is rejected"""
        with pytest.raises(ValidationError):
            MaterialProperties(E=1e9, nu=0.6, rho=1000, k=1)
        
        with pytest.raises(ValidationError):
            MaterialProperties(E=1e9, nu=-0.1, rho=1000, k=1)
    
    def test_optional_properties(self):
        """Test that all properties are optional"""
        props = MaterialProperties()
        assert props.E is None
        assert props.nu is None
        assert props.rho is None
        assert props.k is None


class TestBoundaryCondition:
    """Test BoundaryCondition model"""
    
    def test_valid_boundary_condition(self):
        """Test creating valid boundary condition"""
        bc = BoundaryCondition(
            type="temperature",
            value=100.0,
            location="left"
        )
        assert bc.type == "temperature"
        assert bc.value == 100.0
        assert bc.location == "left"


class TestSimulationParamsDTO:
    """Test SimulationParamsDTO model"""
    
    def test_valid_params_with_material_id(self):
        """Test valid parameters with material ID"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            geometry={"type": "box", "size": 1.0},
            material_id=1,
            boundary_conditions=[
                BoundaryCondition(type="temp", value=0, location="left")
            ]
        )
        assert params.simulation_type == SimulationType.HEAT_TRANSFER
        assert params.material_id == 1
        assert params.custom_material is None
    
    def test_valid_params_with_custom_material(self):
        """Test valid parameters with custom material"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.STRUCTURAL_MECHANICS,
            geometry={"type": "beam"},
            custom_material=MaterialProperties(E=70e9, nu=0.33),
            boundary_conditions=[]
        )
        assert params.custom_material.E == 70e9
        assert params.material_id is None
    
    def test_missing_material_raises_error(self):
        """Test that missing both material_id and custom_material raises error"""
        with pytest.raises(ValidationError) as exc_info:
            SimulationParamsDTO(
                simulation_type=SimulationType.HEAT_TRANSFER,
                geometry={"type": "box"},
                boundary_conditions=[]
            )
        assert "material_id or custom_material must be provided" in str(exc_info.value)
    
    def test_mesh_density_validation(self):
        """Test mesh density validation"""
        # Valid mesh density
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            geometry={},
            material_id=1,
            mesh_density=5.0
        )
        assert params.mesh_density == 5.0
        
        # Invalid mesh density (too high)
        with pytest.raises(ValidationError):
            SimulationParamsDTO(
                simulation_type=SimulationType.HEAT_TRANSFER,
                geometry={},
                material_id=1,
                mesh_density=11.0
            )


class TestSimulationJob:
    """Test SimulationJob model"""
    
    def test_job_creation(self, sample_simulation_params):
        """Test creating a simulation job"""
        job = SimulationJob(params=sample_simulation_params)
        
        assert job.id is not None
        assert job.params == sample_simulation_params
        assert job.status == JobStatus.PENDING
        assert job.progress == 0.0
        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None
    
    def test_job_defaults(self, sample_simulation_params):
        """Test job default values"""
        job = SimulationJob(params=sample_simulation_params)
        
        assert job.workspace_dir is None
        assert job.sif_file_path is None
        assert job.output_dir is None
        assert job.log_file_path is None
        assert job.process_id is None
        assert job.error_message is None
        assert job.result_files == []
        assert job.vtk_file_path is None
        assert job.current_step is None
        assert job.total_steps is None
        assert job.metadata == {} 