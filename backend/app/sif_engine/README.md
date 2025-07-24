# SIF Engine Module

The SIF Engine module provides template-based generation of Elmer Solver Input Files (SIF) for the ElmerFEM Educational Platform.

## Architecture

The module is organized into several components:

- **env.py** - Jinja2 environment configuration and custom filters
- **units.py** - Unit conversion utilities (SI units)
- **context.py** - Parameter-to-template context mapping
- **renderer.py** - Main rendering function and validation

## Usage

### Basic Usage

```python
from app.sif_engine import render_sif
from app.models import SimulationParamsDTO

# Create simulation parameters
params = SimulationParamsDTO(
    simulation_type=SimulationType.HEAT_TRANSFER,
    geometry={"type": "rectangle", "width": 1.0, "height": 1.0},
    material_properties=MaterialProperties(k=50, rho=7850, C=460),
    boundary_conditions=[
        BoundaryCondition(
            surface_id=1,
            type="temperature",
            value=300,
            location="left",
            name="Hot surface"
        )
    ]
)

# Render SIF file
output_path = Path("simulation.sif")
content = render_sif(params, output_path)
```

### Validation

The module includes built-in validation for geometry-physics compatibility:

```python
from app.sif_engine import validate_geometry_physics_compatibility

try:
    validate_geometry_physics_compatibility(params)
except ValueError as e:
    print(f"Invalid configuration: {e}")
```

## Templates

Templates are stored in `backend/templates/sif/` and use Jinja2 syntax:

- `heat_transfer.sif.j2` - Heat equation solver configuration
- `structural_mechanics.sif.j2` - Linear elasticity solver
- `fluid_dynamics.sif.j2` - (Placeholder for future implementation)
- `electromagnetics.sif.j2` - (Placeholder for future implementation)

### Template Variables

Templates have access to the following context variables:

- `case_name` - Name of the simulation case
- `simulation_type` - Type of physics simulation
- `steady_state` - Boolean for steady/transient simulation
- `max_iterations` - Maximum solver iterations
- `time_step`, `time_end` - For transient simulations
- `material` - Material properties object
- `boundary_conditions` - List of boundary condition objects
- `solver_settings` - Advanced solver configuration

### Custom Filters

The following Jinja2 filters are available:

- `format_float` - Format floating point numbers for SIF
- `format_boolean` - Convert Python bool to Fortran logical
- `to_upper` - Convert string to uppercase
- `to_lower` - Convert string to lowercase

## Unit Conversion

The module supports automatic unit conversion:

```python
from app.sif_engine.units import convert_temperature, convert_length

# Convert 25°C to Kelvin
temp_k = convert_temperature(25, "C")  # Returns 298.15

# Convert 10 inches to meters
length_m = convert_length(10, "in")  # Returns 0.254
```

## Extending the Module

### Adding New Physics Types

1. Create a new template in `templates/sif/physics_type.sif.j2`
2. Add the mapping in `renderer.py`:
   ```python
   TEMPLATE_MAPPING = {
       SimulationType.NEW_PHYSICS: "new_physics.sif.j2",
       ...
   }
   ```
3. Add validation rules in `validate_geometry_physics_compatibility()`
4. Update context building in `context.py` if needed

### Adding New Boundary Condition Types

1. Add the BC type to validation rules in `renderer.py`
2. Update the template to handle the new BC type
3. Add any necessary unit conversions in `context.py`

## Testing

Unit tests are provided in `backend/tests/sif_engine/`:

- `test_env.py` - Environment and filter tests
- `test_units.py` - Unit conversion tests
- `test_context.py` - Context building tests
- `test_renderer.py` - Rendering and validation tests
- `test_integration.py` - Full integration tests

Run tests with:
```bash
poetry run pytest tests/sif_engine/
``` 