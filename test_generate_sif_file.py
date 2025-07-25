#!/usr/bin/env python3
"""
Generate actual SIF files for manual inspection
Run from the elmerfem root directory
"""

import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.app.models import SimulationParamsDTO, SimulationType, MaterialProperties, BoundaryCondition
from backend.app.services.sif_generator import SIFGenerator

def generate_heat_transfer_sif():
    """Generate a heat transfer SIF file"""
    print("Generating Heat Transfer SIF file...")
    
    params = SimulationParamsDTO(
        simulation_type=SimulationType.HEAT_TRANSFER,
        geometry={"type": "rectangle", "width": 0.1, "height": 0.2},
        material_properties=MaterialProperties(
            k=50,      # Thermal conductivity (W/m·K) - Steel
            rho=7850,  # Density (kg/m³)
            C=460      # Heat capacity (J/kg·K)
        ),
        boundary_conditions=[
            BoundaryCondition(
                surface_id=1,
                type="temperature",
                value=373.15,  # 100°C in Kelvin
                location="left",
                name="Hot surface"
            ),
            BoundaryCondition(
                surface_id=3,
                type="temperature", 
                value=293.15,  # 20°C in Kelvin
                location="right",
                name="Cold surface"
            ),
            BoundaryCondition(
                surface_id=2,
                type="heat_flux",
                value=0,  # Insulated
                location="top",
                name="Insulated"
            ),
            BoundaryCondition(
                surface_id=4,
                type="heat_flux",
                value=0,  # Insulated
                location="bottom",
                name="Insulated"
            )
        ]
    )
    
    generator = SIFGenerator()
    sif_content = generator.generate(params, "heat_transfer_demo")
    
    # Save to file
    output_path = Path("heat_transfer_demo.sif")
    output_path.write_text(sif_content, encoding='utf-8')
    
    print(f"✓ Generated: {output_path}")
    print(f"  Size: {len(sif_content)} bytes")
    print(f"  Lines: {sif_content.count(chr(10))}")
    
    return output_path

def generate_structural_mechanics_sif():
    """Generate a structural mechanics SIF file"""
    print("\nGenerating Structural Mechanics SIF file...")
    
    params = SimulationParamsDTO(
        simulation_type=SimulationType.STRUCTURAL_MECHANICS,
        geometry={"type": "box", "width": 0.1, "height": 0.05, "depth": 0.02},
        material_properties=MaterialProperties(
            E=210e9,   # Young's modulus (Pa) - Steel
            nu=0.3,    # Poisson's ratio
            rho=7850   # Density (kg/m³)
        ),
        boundary_conditions=[
            # Fixed end (all displacements = 0)
            BoundaryCondition(
                surface_id=1,
                type="displacement",
                value=0,
                location="left",
                component=1,
                name="Fixed X"
            ),
            BoundaryCondition(
                surface_id=1,
                type="displacement",
                value=0,
                location="left",
                component=2,
                name="Fixed Y"
            ),
            BoundaryCondition(
                surface_id=1,
                type="displacement",
                value=0,
                location="left",
                component=3,
                name="Fixed Z"
            ),
            # Applied force on opposite end
            BoundaryCondition(
                surface_id=2,
                type="force",
                value=1000,  # 1000 N downward
                location="right",
                component=2,
                name="Load"
            )
        ],
        solver_settings={
            "linear_system_solver": "Direct",
            "linear_system_direct_method": "Umfpack"
        }
    )
    
    generator = SIFGenerator()
    sif_content = generator.generate(params, "cantilever_beam")
    
    # Save to file
    output_path = Path("cantilever_beam.sif")
    output_path.write_text(sif_content, encoding='utf-8')
    
    print(f"✓ Generated: {output_path}")
    print(f"  Size: {len(sif_content)} bytes")
    print(f"  Lines: {sif_content.count(chr(10))}")
    
    return output_path

def show_sif_preview(path):
    """Show a preview of the generated SIF file"""
    content = path.read_text()
    lines = content.split('\n')
    
    print(f"\nPreview of {path.name} (first 30 lines):")
    print("=" * 60)
    for i, line in enumerate(lines[:30]):
        print(f"{i+1:3d}: {line}")
    if len(lines) > 30:
        print(f"... ({len(lines) - 30} more lines)")
    print("=" * 60)

if __name__ == "__main__":
    print("SIF File Generator")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Generate files
        heat_file = generate_heat_transfer_sif()
        struct_file = generate_structural_mechanics_sif()
        
        # Show previews
        show_sif_preview(heat_file)
        show_sif_preview(struct_file)
        
        print("\n✅ SIF files generated successfully!")
        print("\nYou can now:")
        print("1. Open the .sif files in a text editor to inspect them")
        print("2. Run them with ElmerSolver (if you have a mesh):")
        print(f"   ElmerSolver {heat_file.name}")
        print(f"   ElmerSolver {struct_file.name}")
        print("\nNote: These files need a corresponding mesh to run.")
        
    except Exception as e:
        print(f"\n❌ Error generating SIF files: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 