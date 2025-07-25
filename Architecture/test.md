# **test Directory Architecture**

## **Purpose**
The `test` directory serves as a minimal reference testing framework and validation suite for Elmer FEM components. Its primary purpose is to provide basic test cases, example configurations, and validation data that can be used to verify the correct installation, basic functionality, and integration of Elmer FEM software components. This directory contains simple, well-defined test problems that serve as both validation tools and educational examples for new users.

## **Key Components/Subdirectories**
* **`simple.sif` (1.9KB)**: Complete Solver Input File (SIF) defining a basic heat equation test case
* **`mesh/`**: Directory containing Elmer mesh format files for the test geometry:
  - `mesh.header` (60B): Mesh metadata defining mesh structure and properties
  - `mesh.nodes` (170B): Node coordinates for the test mesh (13 nodes)
  - `mesh.elements` (106B): Element connectivity information (7 elements)
  - `mesh.boundary` (567B): Boundary condition definitions and boundary element data
* **`square.grd` (269B)**: ElmerGrid geometry definition file for a simple 2x2 square domain
* **`case_t0001.vtu` (2.0KB)**: VTK unstructured grid file containing sample results for validation

## **Functionality/Role in Architecture**
The test directory provides essential validation and educational functions within the Elmer FEM ecosystem:

**System Validation and Verification:**
- Provides a simple, well-defined test case for verifying correct Elmer installation
- Enables quick verification that ElmerSolver can read mesh files and execute simulations
- Validates the complete workflow from mesh generation to solution and post-processing
- Serves as a regression testing baseline for detecting software issues

**Educational and Training Resources:**
- Offers a minimal working example for new users learning Elmer FEM
- Demonstrates proper SIF file structure and syntax for basic problems
- Shows the relationship between mesh files and solver configuration
- Provides a foundation for understanding Elmer FEM workflow and file formats

**Development and Debugging Support:**
- Supplies reference data for developers working on Elmer FEM components
- Enables rapid testing during development cycles without complex geometry setup
- Provides known-good mesh and configuration files for troubleshooting
- Serves as a minimal test case for continuous integration systems

**File Format Documentation:**
- Demonstrates proper structure of Elmer mesh format files
- Shows correct SIF file syntax and section organization
- Illustrates VTK output format for result visualization
- Provides examples of ElmerGrid geometry definition format

## **Inputs and Outputs**
**Inputs:**
- **Developer/User Actions**: Manual execution of test cases for validation
- **Build Systems**: Automated testing during software compilation and installation
- **Continuous Integration**: Automated execution in CI/CD pipelines
- **Educational Use**: Student and researcher exploration of example problems

**Outputs:**
- **Validation Results**: Pass/fail status for basic Elmer FEM functionality
- **Solution Files**: Numerical results from solving the test heat equation problem
- **Log Files**: Solver execution logs and diagnostic information
- **Educational Understanding**: User comprehension of Elmer FEM workflow and syntax
- **Debugging Information**: Error traces and diagnostic data for troubleshooting

## **Interactions with other components**
**Primary Testing Targets:**
- **`elmergrid`**: Validates mesh generation from `square.grd` geometry definition
- **`fem/src/ElmerSolver`**: Tests solver execution with `simple.sif` input file
- **`post/`**: Validates post-processing capabilities with generated result files
- **File I/O systems**: Tests proper reading and writing of Elmer format files

**Workflow Integration:**
- **ElmerGrid Mesh Generation**: `elmergrid 1 2 square.grd` converts geometry to mesh format
- **Solver Execution**: `ElmerSolver simple.sif` runs the heat equation simulation
- **Result Verification**: Compare generated outputs with expected reference solutions
- **Post-Processing**: Load results in ElmerPost or convert to VTK format for visualization

**Integration with Development Tools:**
- **Version Control**: Track changes in reference solutions and expected outputs
- **Build Systems**: CMake and other build tools execute tests during compilation
- **Documentation Systems**: Reference test cases in user manuals and tutorials
- **Quality Assurance**: Automated testing in continuous integration pipelines

**Educational Workflow:**
1. New users examine `square.grd` to understand geometry definition syntax
2. Users study `simple.sif` to learn SIF file structure and heat equation setup
3. Mesh generation demonstrates ElmerGrid usage and output format
4. Solver execution shows basic ElmerSolver operation and result generation
5. Post-processing examples illustrate visualization and analysis techniques

## **Example Files/Code Snippets (if applicable)**
**Test Geometry Definition (square.grd):**
```
***** ElmerGrid input *****
Version = 210903
Coordinate System = Cartesian 2D
Subcell Divisions = 2 2
Subcell Sizes 1 = 0.5 0.5
Subcell Sizes 2 = 0.5 0.5
Material Structure
  1 1
  1 1
End
Boundary Definitions
  -1 1 1 1    ! Bottom boundary
  -2 1 1 2    ! Right boundary  
  -3 1 2 1    ! Top boundary
  -4 1 1 3    ! Left boundary
  -5 1 2 2    ! Internal boundary
End
```

**Test SIF File Structure (simple.sif excerpt):**
```
Header
  Mesh DB "." "mesh"
  Results Directory "."
End

Simulation
  Coordinate System = Cartesian
  Simulation Type = Steady state
  Steady State Max Iterations = 1
End

Body 1
  Target Bodies(1) = 1
  Equation = 1
  Material = 1
End

Solver 1
  Equation = Heat Equation
  Procedure = "HeatSolve" "HeatSolver"
  Variable = Temperature
  Linear System Solver = Iterative
  Linear System Iterative Method = BiCGStab
End
```

**Mesh File Format Example (mesh.header):**
```
2 2 4
4
2 1
```

**Typical Testing Workflow:**
```bash
# Generate mesh from geometry
elmergrid 1 2 square.grd

# Run simulation
ElmerSolver simple.sif

# Verify results exist
ls -la case_t0001.vtu

# Optional: Visualize results
ElmerPost case_t0001.vtu
```

**Automated Testing Integration:**
```cmake
# CMakeLists.txt test configuration
enable_testing()
add_test(
    NAME basic_heat_equation
    COMMAND ElmerSolver simple.sif
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/test
)
```

**Validation Characteristics:**
- **Problem Type**: 2D steady-state heat conduction
- **Geometry**: Simple 1x1 square domain with structured 2x2 element mesh
- **Boundary Conditions**: Mixed Dirichlet and Neumann conditions
- **Solution Method**: Iterative BiCGStab linear solver
- **Expected Behavior**: Smooth temperature distribution with known analytical solution
- **Verification**: Numerical solution convergence and result file generation 