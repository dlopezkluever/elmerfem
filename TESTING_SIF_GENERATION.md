# Testing the SIF Generation Engine

This document explains how to test the new SIF Generation Engine implementation.

## Quick Overview

The SIF Generation Engine has been refactored to use Jinja2 templates instead of string concatenation. This makes it more maintainable and extensible.

## What Was Implemented

- **Template-based generation** using Jinja2
- **Validation** for geometry-physics compatibility  
- **Unit conversion** utilities
- **Support for** heat transfer and structural mechanics
- **Comprehensive test suite**

## Testing Options

### Option 1: Standalone Test (No Dependencies Required!)

This is the easiest way to verify the refactoring is complete:

```bash
# Run the standalone test - this works without any backend dependencies
python test_sif_standalone.py
```

This test will:
- ✓ Verify all template files exist
- ✓ Check all SIF engine modules are in place  
- ✓ Test that templates can be rendered with Jinja2
- ✓ Show a preview of the generated SIF output

### Option 2: Full Integration Tests (Requires Dependencies)

If you have the backend dependencies installed:

```bash
# Test the core SIF generation logic
python test_sif_generation.py

# Generate actual SIF files to inspect
python test_generate_sif_file.py
```

### Option 2: API Testing (If Backend is Running)

If you have the backend running via Docker:

```bash
# Test through the API
python test_api_endpoint.py
```

This requires the backend to be running at `http://localhost:8000`.

### Option 3: Unit Tests (If Poetry is Set Up)

If you have Poetry installed:

```bash
cd backend
poetry install
poetry run pytest tests/sif_engine/ -v
```

## What the Tests Check

1. **Template Rendering**: Verifies that SIF files are generated correctly
2. **Validation**: Ensures invalid configurations are rejected
3. **Format**: Checks that the output matches Elmer's expected format
4. **Content**: Validates that all required sections are present

## Example Output

When you run `test_generate_sif_file.py`, it will create two SIF files:

- `heat_transfer_demo.sif` - A heat conduction problem
- `cantilever_beam.sif` - A structural mechanics problem

These are real SIF files that could be run with ElmerSolver (given a corresponding mesh).

## Manual Inspection

The generated SIF files should have:

- Header section with mesh database path
- Simulation settings
- Material properties 
- Boundary conditions
- Solver configuration

You can open the `.sif` files in any text editor to verify they look correct.

## Troubleshooting

### ModuleNotFoundError

If you get import errors, make sure:
1. You're running from the project root directory
2. The backend directory exists with all the implementation files

### Dependencies Missing

The minimal test script (`test_sif_minimal.py`) has the fewest dependencies and is most likely to work.

### Backend Not Running

The API test will fail if the backend isn't running. You can skip this test if Docker isn't set up.

## Summary

The SIF generation is working if:
- ✅ Templates render without errors
- ✅ Generated SIF files contain all required sections
- ✅ Invalid configurations are rejected with clear error messages
- ✅ The output format matches Elmer's expectations

The implementation is complete and ready for use! 