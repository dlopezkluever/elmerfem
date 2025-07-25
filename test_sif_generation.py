#!/usr/bin/env python3
"""
Simple test script to verify SIF generation works
Run from the elmerfem root directory
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.app.models import SimulationParamsDTO, SimulationType, MaterialProperties, BoundaryCondition
from backend.app.services.sif_generator import SIFGenerator

def test_heat_transfer():
    """Test heat transfer SIF generation"""
    print("=== Testing Heat Transfer SIF Generation ===\n")
    
    # Create test parameters
    params = SimulationParamsDTO(
        simulation_type=SimulationType.HEAT_TRANSFER,
        geometry={"type": "rectangle", "width": 1.0, "height": 1.0},
        material_properties=MaterialProperties(
            k=50,      # Thermal conductivity
            rho=7850,  # Density
            C=460      # Heat capacity
        ),
        boundary_conditions=[
            BoundaryCondition(
                surface_id=1,
                type="temperature",
                value=300,
                location="left",
                name="Hot surface"
            ),
            BoundaryCondition(
                surface_id=2,
                type="heat_flux",
                value=1000,
                location="right",
                name="Heat input"
            )
        ]
    )
    
    # Generate SIF
    generator = SIFGenerator()
    sif_content = generator.generate(params, "test_case")
    
    # Display results
    print("Generated SIF file:")
    print("-" * 60)
    print(sif_content[:500] + "..." if len(sif_content) > 500 else sif_content)
    print("-" * 60)
    
    # Validate key elements
    checks = [
        ("Header section", "Header" in sif_content),
        ("Simulation section", "Simulation" in sif_content),
        ("Material properties", "Heat Conductivity = 50" in sif_content),
        ("Temperature BC", "Temperature = 300" in sif_content),
        ("Heat flux BC", "Heat Flux = 1000" in sif_content),
        ("Heat solver", "HeatSolve" in sif_content),
    ]
    
    print("\nValidation:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def test_structural_mechanics():
    """Test structural mechanics SIF generation"""
    print("\n=== Testing Structural Mechanics SIF Generation ===\n")
    
    # Create test parameters
    params = SimulationParamsDTO(
        simulation_type=SimulationType.STRUCTURAL_MECHANICS,
        geometry={"type": "box", "width": 1.0, "height": 1.0, "depth": 1.0},
        material_properties=MaterialProperties(
            E=210e9,   # Young's modulus (Steel)
            nu=0.3,    # Poisson's ratio
            rho=7850   # Density
        ),
        boundary_conditions=[
            BoundaryCondition(
                surface_id=1,
                type="displacement",
                value=0,
                location="bottom",
                component=1,
                name="Fixed X"
            ),
            BoundaryCondition(
                surface_id=1,
                type="displacement",
                value=0,
                location="bottom", 
                component=2,
                name="Fixed Y"
            ),
            BoundaryCondition(
                surface_id=2,
                type="force",
                value=1000,
                location="top",
                component=3,
                name="Load"
            )
        ]
    )
    
    # Generate SIF
    generator = SIFGenerator()
    sif_content = generator.generate(params, "struct_case")
    
    print("Generated SIF preview:")
    print("-" * 60)
    print(sif_content[:500] + "..." if len(sif_content) > 500 else sif_content)
    print("-" * 60)
    
    # Validate
    checks = [
        ("Young's modulus", "Youngs modulus = 2.1e+11" in sif_content),
        ("Poisson ratio", "Poisson ratio = 0.3" in sif_content),
        ("Displacement BC", "Displacement 1 = 0" in sif_content),
        ("Force BC", "Force 3 = 1000" in sif_content),
        ("Stress solver", "StressSolve" in sif_content),
    ]
    
    print("\nValidation:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def test_validation():
    """Test that invalid configurations are caught"""
    print("\n=== Testing Validation ===\n")
    
    # Invalid BC type for heat transfer
    params = SimulationParamsDTO(
        simulation_type=SimulationType.HEAT_TRANSFER,
        geometry={"type": "rectangle", "width": 1.0, "height": 1.0},
        material_properties=MaterialProperties(k=50),
        boundary_conditions=[
            BoundaryCondition(
                surface_id=1,
                type="force",  # Invalid for heat transfer!
                value=1000,
                location="left"
            )
        ]
    )
    
    generator = SIFGenerator()
    try:
        generator.generate(params)
        print("✗ Validation failed - invalid BC not caught")
        return False
    except ValueError as e:
        print(f"✓ Validation correctly caught error: {e}")
        return True

if __name__ == "__main__":
    print("SIF Generation Engine Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    try:
        results.append(("Heat Transfer", test_heat_transfer()))
    except Exception as e:
        print(f"\nError in heat transfer test: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Heat Transfer", False))
    
    try:
        results.append(("Structural Mechanics", test_structural_mechanics()))
    except Exception as e:
        print(f"\nError in structural mechanics test: {e}")
        results.append(("Structural Mechanics", False))
    
    try:
        results.append(("Validation", test_validation()))
    except Exception as e:
        print(f"\nError in validation test: {e}")
        results.append(("Validation", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("-" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("-" * 60)
    print(f"Overall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    sys.exit(0 if all_passed else 1) 