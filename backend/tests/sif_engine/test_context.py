"""
Unit tests for SIF Engine context building
"""

import pytest
from datetime import datetime

from app.models import (
    BoundaryCondition,
    MaterialProperties,
    SimulationParamsDTO,
    SimulationType
)
from app.sif_engine.context import build_context


class TestBuildContext:
    """Test context building from simulation parameters"""
    
    @pytest.fixture
    def basic_heat_params(self):
        """Create basic heat transfer parameters"""
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
    def basic_structural_params(self):
        """Create basic structural mechanics parameters"""
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
    
    def test_basic_context_structure(self, basic_heat_params):
        """Test basic context structure"""
        context = build_context(basic_heat_params)
        
        # Check required keys
        assert "case_name" in context
        assert "simulation_type" in context
        assert "steady_state" in context
        assert "materials" in context
        assert "boundary_conditions" in context
    
    def test_simulation_type_mapping(self, basic_heat_params, basic_structural_params):
        """Test simulation type is correctly mapped"""
        heat_context = build_context(basic_heat_params)
        assert heat_context["simulation_type"] == "heat_transfer"
        
        struct_context = build_context(basic_structural_params)
        assert struct_context["simulation_type"] == "structural_mechanics"
    
    def test_steady_state_default(self, basic_heat_params):
        """Test steady state is True by default"""
        context = build_context(basic_heat_params)
        assert context["steady_state"] is True
    
    def test_material_properties_mapping(self, basic_heat_params):
        """Test material properties are correctly mapped"""
        context = build_context(basic_heat_params)
        
        # Should have materials list
        assert isinstance(context["materials"], list)
        assert len(context["materials"]) == 1
        
        material = context["materials"][0]
        assert material["id"] == 1
        assert material["name"] == "Material 1"
        assert material["youngs_modulus"] == 210e9
        assert material["poissons_ratio"] == 0.3
        assert material["density"] == 7850
        assert material["heat_conductivity"] == 50
        assert material["heat_capacity"] == 460
    
    def test_material_defaults(self):
        """Test material property defaults when not provided"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[]
        )
        
        context = build_context(params)
        material = context["materials"][0]
        
        # Check defaults
        assert material["youngs_modulus"] == 210e9
        assert material["poissons_ratio"] == 0.3
        assert material["density"] == 1000
        assert material["heat_conductivity"] == 1.0
        assert material["heat_capacity"] == 1000
    
    def test_boundary_conditions_mapping(self, basic_heat_params):
        """Test boundary conditions are correctly mapped"""
        context = build_context(basic_heat_params)
        
        # Should have boundary conditions list
        assert isinstance(context["boundary_conditions"], list)
        assert len(context["boundary_conditions"]) == 2
        
        # Check first BC
        bc1 = context["boundary_conditions"][0]
        assert bc1["id"] == 1
        assert bc1["surface_id"] == 1
        assert bc1["name"] == "Hot surface"
        assert bc1["type"] == "temperature"
        assert bc1["value"] == 300
        
        # Check second BC
        bc2 = context["boundary_conditions"][1]
        assert bc2["id"] == 2
        assert bc2["surface_id"] == 2
        assert bc2["name"] == "Heat input"
        assert bc2["type"] == "heat_flux"
        assert bc2["value"] == 1000
    
    def test_boundary_condition_components(self, basic_structural_params):
        """Test boundary conditions with components"""
        context = build_context(basic_structural_params)
        
        bc1 = context["boundary_conditions"][0]
        assert bc1["component"] == "x"
        assert bc1["has_component"] is True
        
        bc2 = context["boundary_conditions"][1]
        assert bc2["component"] == "y"
        assert bc2["has_component"] is True
    
    def test_temperature_unit_conversion(self):
        """Test temperature values are converted to Kelvin"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[
                BoundaryCondition(
                    surface_id=1,
                    type="temperature",
                    value="25 C"  # Celsius
                )
            ]
        )
        
        context = build_context(params)
        bc = context["boundary_conditions"][0]
        assert bc["value"] == pytest.approx(298.15)  # 25°C in Kelvin
    
    def test_force_unit_conversion(self):
        """Test force values are converted to Newtons"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.STRUCTURAL_MECHANICS,
            boundary_conditions=[
                BoundaryCondition(
                    surface_id=1,
                    type="force",
                    value="100 lbf"  # Pounds force
                )
            ]
        )
        
        context = build_context(params)
        bc = context["boundary_conditions"][0]
        assert bc["value"] == pytest.approx(444.822)  # 100 lbf in Newtons
    
    def test_transient_parameters(self):
        """Test transient simulation parameters"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            time_step=0.1,
            time_end=10.0,
            boundary_conditions=[]
        )
        
        context = build_context(params)
        
        # Should be transient since time_step is set
        assert context["steady_state"] is False
        assert context["time_step"] == 0.1
        assert context["time_end"] == 10.0
        assert context["num_timesteps"] == 100
    
    def test_solver_parameters(self):
        """Test solver parameter defaults"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[]
        )
        
        context = build_context(params)
        
        # Check solver defaults
        assert context["max_iterations"] == 100
        assert context["convergence_tolerance"] == pytest.approx(1e-7)
        assert context["output_intervals"] == 1
    
    def test_boundary_condition_type_flags(self):
        """Test boundary condition type flags"""
        params = SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_TRANSFER,
            boundary_conditions=[
                BoundaryCondition(surface_id=1, type="temperature", value=300),
                BoundaryCondition(surface_id=2, type="heat_flux", value=1000)
            ]
        )
        
        context = build_context(params)
        
        bc1 = context["boundary_conditions"][0]
        assert bc1["is_temperature"] is True
        assert bc1["is_heat_flux"] is False
        assert bc1["is_displacement"] is False
        assert bc1["is_force"] is False
        
        bc2 = context["boundary_conditions"][1]
        assert bc2["is_temperature"] is False
        assert bc2["is_heat_flux"] is True
        assert bc2["is_displacement"] is False
        assert bc2["is_force"] is False 