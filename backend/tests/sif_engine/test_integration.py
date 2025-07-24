"""
Integration tests for SIF Engine with backend API
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
from app.services.sif_generator import SIFGenerator


class TestSIFGeneratorIntegration:
    """Test SIFGenerator integration with new template engine"""
    
    @pytest.fixture
    def sif_generator(self):
        """Create SIFGenerator instance"""
        return SIFGenerator()
    
    @pytest.fixture
    def heat_params(self):
        """Create comprehensive heat transfer parameters"""
        return SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            material_properties=MaterialProperties(
                E=210e9,
                nu=0.3,
                rho=7850,
                k=50,
                C=460,
                alpha=1.2e-5
            ),
            boundary_conditions=[
                BoundaryCondition(
                    surface_id=1,
                    type="temperature",
                    value="100 C",  # Test unit conversion
                    name="Hot surface"
                ),
                BoundaryCondition(
                    surface_id=2,
                    type="heat_flux",
                    value=5000,
                    name="Heat flux BC"
                ),
                BoundaryCondition(
                    surface_id=3,
                    type="temperature",
                    value="20 C",
                    name="Cold surface"
                )
            ]
        )
    
    @pytest.fixture
    def structural_params(self):
        """Create comprehensive structural mechanics parameters"""
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
                    surface_id=1,
                    type="displacement",
                    value=0,
                    component="y",
                    name="Fixed Y"
                ),
                BoundaryCondition(
                    surface_id=1,
                    type="displacement",
                    value=0,
                    component="z",
                    name="Fixed Z"
                ),
                BoundaryCondition(
                    surface_id=2,
                    type="force",
                    value="1000 lbf",  # Test unit conversion
                    component="y",
                    name="Load"
                )
            ]
        )
    
    def test_generate_heat_transfer_sif(self, sif_generator, heat_params):
        """Test generating heat transfer SIF through SIFGenerator"""
        content = sif_generator.generate(heat_params, "heat_case")
        
        # Check basic structure
        assert "! Generated SIF file for heat transfer simulation" in content
        assert "! Simulation: heat_case" in content
        
        # Check header
        assert "Header" in content
        assert 'Mesh DB "." "mesh"' in content
        
        # Check simulation settings
        assert "Simulation Type = Steady state" in content
        
        # Check solver configuration
        assert 'Equation = Heat Equation' in content
        assert 'Procedure = "HeatSolve" "HeatSolver"' in content
        assert 'Variable = Temperature' in content
        
        # Check material properties
        assert "Heat Conductivity = 50" in content
        assert "Density = 7850" in content
        assert "Heat Capacity = 460" in content
        
        # Check boundary conditions with unit conversion
        assert "Temperature = 373.15" in content  # 100°C in Kelvin
        assert "Temperature = 293.15" in content  # 20°C in Kelvin
        assert "Heat Flux = 5000" in content
        
        # Check all 3 BCs are present
        assert content.count("Boundary Condition") == 3
    
    def test_generate_structural_sif(self, sif_generator, structural_params):
        """Test generating structural mechanics SIF through SIFGenerator"""
        content = sif_generator.generate(structural_params, "struct_case")
        
        # Check basic structure
        assert "! Generated SIF file for structural mechanics simulation" in content
        assert "! Simulation: struct_case" in content
        
        # Check solver configuration
        assert 'Equation = Linear elasticity' in content
        assert 'Procedure = "StressSolve" "StressSolver"' in content
        assert 'Variable = -dofs 3 Displacement' in content
        
        # Check material properties
        assert "Youngs modulus = 2.1e+11" in content
        assert "Poisson ratio = 0.3" in content
        assert "Density = 7850" in content
        
        # Check boundary conditions with unit conversion
        assert "Displacement x = 0" in content
        assert "Displacement y = 0" in content
        assert "Displacement z = 0" in content
        assert "Force y = 444.822" in content  # 1000 lbf in Newtons
        
        # Check all 4 BCs are present
        assert content.count("Boundary Condition") == 4
    
    @pytest.mark.asyncio
    async def test_write_sif_file(self, sif_generator, heat_params):
        """Test writing SIF file to disk"""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            
            sif_file = await sif_generator.write_sif_file(
                heat_params, output_path, "test_case"
            )
            
            # Check file was created
            assert sif_file.exists()
            assert sif_file.name == "test_case.sif"
            
            # Check content
            content = sif_file.read_text()
            assert "! Generated SIF file for heat transfer simulation" in content
            assert "! Simulation: test_case" in content
    
    def test_transient_simulation(self, sif_generator):
        """Test transient simulation settings"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            time_step=0.01,
            time_end=1.0,
            boundary_conditions=[
                BoundaryCondition(surface_id=1, type="temperature", value=300)
            ]
        )
        
        content = sif_generator.generate(params, "transient_case")
        
        # Check transient settings
        assert "Simulation Type = Transient" in content
        assert "Timestep intervals = 100" in content
        assert "Timestep sizes = 0.01" in content
    
    def test_invalid_boundary_condition(self, sif_generator):
        """Test validation of invalid boundary conditions"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[
                # Force BC is invalid for heat transfer
                BoundaryCondition(surface_id=1, type="force", value=1000)
            ]
        )
        
        with pytest.raises(ValueError, match="Force boundary conditions are not valid"):
            sif_generator.generate(params)
    
    def test_backward_compatibility(self, sif_generator, heat_params):
        """Test that interface remains compatible with JobLauncher"""
        # Test synchronous generate method returns string
        content = sif_generator.generate(heat_params)
        assert isinstance(content, str)
        assert len(content) > 0
        
        # Test default case name
        assert "! Simulation: case" in content 