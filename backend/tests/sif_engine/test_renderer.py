"""
Unit tests for SIF Engine rendering and validation
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.models import (
    BoundaryCondition,
    MaterialProperties,
    SimulationParamsDTO,
    SimulationType
)
from app.sif_engine.renderer import render_sif, validate_geometry_physics_compatibility


class TestValidation:
    """Test geometry-physics compatibility validation"""
    
    def test_valid_heat_transfer_config(self):
        """Test valid heat transfer configuration passes validation"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[
                BoundaryCondition(surface_id=1, type="temperature", value=300)
            ]
        )
        
        # Should not raise
        validate_geometry_physics_compatibility(params)
    
    def test_valid_structural_config(self):
        """Test valid structural mechanics configuration passes validation"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.STRUCTURAL_MECHANICS,
            boundary_conditions=[
                BoundaryCondition(surface_id=1, type="displacement", value=0)
            ]
        )
        
        # Should not raise
        validate_geometry_physics_compatibility(params)
    
    def test_invalid_bc_for_heat_transfer(self):
        """Test invalid boundary condition for heat transfer"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[
                BoundaryCondition(surface_id=1, type="force", value=1000)
            ]
        )
        
        with pytest.raises(ValueError, match="Force boundary conditions are not valid"):
            validate_geometry_physics_compatibility(params)
    
    def test_invalid_bc_for_structural(self):
        """Test invalid boundary condition for structural mechanics"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.STRUCTURAL_MECHANICS,
            boundary_conditions=[
                BoundaryCondition(surface_id=1, type="heat_flux", value=1000)
            ]
        )
        
        with pytest.raises(ValueError, match="Heat flux boundary conditions are not valid"):
            validate_geometry_physics_compatibility(params)
    
    def test_unsupported_simulation_type(self):
        """Test unsupported simulation type"""
        # This would require creating a new enum value, so we'll mock it
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[]
        )
        
        # Temporarily change the type to something else
        original_type = params.simulation_type
        params.simulation_type = "unsupported"  # type: ignore
        
        with pytest.raises(ValueError, match="not yet supported"):
            validate_geometry_physics_compatibility(params)
        
        # Restore
        params.simulation_type = original_type


class TestRenderSIF:
    """Test SIF file rendering"""
    
    @pytest.fixture
    def heat_params(self):
        """Create heat transfer simulation parameters"""
        return SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            material_properties=MaterialProperties(
                k=50,
                rho=7850,
                C=460
            ),
            boundary_conditions=[
                BoundaryCondition(
                    surface_id=1,
                    type="temperature",
                    value=300,
                    name="Hot surface"
                ),
                BoundaryCondition(
                    surface_id=2,
                    type="heat_flux",
                    value=1000,
                    name="Heat input"
                )
            ]
        )
    
    @pytest.fixture
    def structural_params(self):
        """Create structural mechanics simulation parameters"""
        return SimulationParamsDTO(
            simulation_type=SimulationType.STRUCTURAL_MECHANICS,
            material_properties=MaterialProperties(
                E=210e9,
                nu=0.3,
                rho=7850
            ),
            boundary_conditions=[
                BoundaryCondition(
                    surface_id=1,
                    type="displacement",
                    value=0,
                    component="x",
                    name="Fixed X"
                ),
                BoundaryCondition(
                    surface_id=2,
                    type="force",
                    value=1000,
                    component="y",
                    name="Load Y"
                )
            ]
        )
    
    def test_render_heat_transfer_sif(self, heat_params):
        """Test rendering heat transfer SIF file"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.sif"
            
            content = render_sif(heat_params, output_path)
            
            # Check file was created
            assert output_path.exists()
            
            # Check content
            assert "heat transfer simulation" in content
            assert "HeatSolve" in content
            assert "Temperature = 300" in content
            assert "Heat Flux = 1000" in content
            assert "Heat Conductivity = 50" in content
    
    def test_render_structural_sif(self, structural_params):
        """Test rendering structural mechanics SIF file"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.sif"
            
            content = render_sif(structural_params, output_path)
            
            # Check file was created
            assert output_path.exists()
            
            # Check content
            assert "structural mechanics simulation" in content
            assert "StressSolve" in content
            assert "Displacement x = 0" in content
            assert "Force y = 1000" in content
            assert "Youngs modulus = 2.1e+11" in content
    
    def test_render_with_transient_settings(self):
        """Test rendering with transient simulation settings"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            time_step=0.1,
            time_end=10.0,
            boundary_conditions=[]
        )
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.sif"
            
            content = render_sif(params, output_path)
            
            # Check transient settings
            assert "Simulation Type = Transient" in content
            assert "Timestep intervals = 100" in content
            assert "Timestep sizes = 0.1" in content
    
    def test_render_steady_state(self):
        """Test rendering steady state simulation"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[]
        )
        
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.sif"
            
            content = render_sif(params, output_path)
            
            # Check steady state settings
            assert "Simulation Type = Steady state" in content
            assert "Steady State Max Iterations = 100" in content
    
    def test_template_not_found(self):
        """Test error when template is not found"""
        # Create params with a non-existent simulation type by monkeypatching
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[]
        )
        
        # Temporarily modify the template mapping
        from app.sif_engine import renderer
        original_mapping = renderer.TEMPLATE_MAPPING.copy()
        renderer.TEMPLATE_MAPPING[SimulationType.HEAT_TRANSFER] = "nonexistent.sif.j2"
        
        try:
            with TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "test.sif"
                
                with pytest.raises(FileNotFoundError, match="Template not found"):
                    render_sif(params, output_path)
        finally:
            # Restore mapping
            renderer.TEMPLATE_MAPPING = original_mapping
    
    def test_file_permissions_error(self):
        """Test error handling for file write permissions"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[]
        )
        
        # Try to write to a non-existent directory
        output_path = Path("/nonexistent/directory/test.sif")
        
        with pytest.raises(IOError, match="Failed to write SIF file"):
            render_sif(params, output_path) 