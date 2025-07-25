# **elmerice Directory Architecture**

## **Purpose**
The `elmerice` directory contains specialized glaciological extensions to the Elmer finite element code, providing advanced ice sheet and glacier modeling capabilities. It serves as a comprehensive toolkit for ice dynamics simulations, including ice flow, thermal processes, calving dynamics, and climate-ice interactions.

## **Key Components/Subdirectories**

### **Core Directories:**
* `Solvers/`: Contains over 80 specialized Fortran 90 solvers for ice-specific physics
* `Tests/`: Validation and test cases for ice modeling scenarios
* `Examples/`: Demonstration cases and tutorials for ice simulations
* `UserFunctions/`: Custom functions for ice-specific boundary conditions and material properties
* `Utils/`: Utility scripts and tools for ice modeling workflows
* `Meshers/`: Specialized mesh generation tools for ice geometries
* `IceSheet/`: Large-scale ice sheet modeling components
* `cmake/`: Build configuration files specific to ice modeling dependencies
* `ReleaseNotes/`: Documentation of version-specific changes and improvements

### **Specialized Solver Categories:**
* **Ice Flow Solvers**: `SSASolver.F90`, `SIASolver.F90`, `AIFlowSolve_nlD2.F90`, `AIFlowSolve_nlS2.F90`
* **Thermal Solvers**: `EnthalpySolver.F90`, `TemperateIce.F90`, `DeformationalHeat.F90`
* **Calving Dynamics**: `Calving.F90`, `Calving3D.F90`, `CalvingGeometry.F90`, `ProjectCalving.F90`
* **Thickness Evolution**: `ThicknessSolver.F90`, `Flotation.F90`, `GroundedSolver.F90`
* **Hydrology**: `GlaDSCoupledSolver.F90`, `GlaDSchannelSolver.F90`, `HydroRestart.F90`
* **Optimization/Inversion**: `CostSolver_Adjoint.F90`, `DJDBeta_Adjoint.F90`, `Optimize_m1qn3Parallel.F90`

## **Functionality/Role in Architecture**
Elmer/Ice extends the core Elmer FEM capabilities with ice-specific physics and numerical methods:

### **Ice Dynamics Modeling:**
- **Shallow Ice Approximation (SIA)**: Simplified ice flow for large-scale modeling
- **Shallow Shelf Approximation (SSA)**: Ice shelf and fast-flowing ice stream dynamics
- **Full Stokes**: Complete 3D ice flow including all stress components
- **Higher-order models**: Blatter-Pattyn approximations for intermediate complexity

### **Thermal Processes:**
- **Enthalpy method**: Phase change modeling with liquid water content
- **Temperature evolution**: Heat transport in ice with strain heating
- **Temperate ice**: Handling of ice at pressure melting point

### **Calving and Frontal Dynamics:**
- **Level-set calving**: Advanced calving front evolution
- **Stress-based calving**: Calving rates based on stress criteria
- **3D calving**: Full three-dimensional calving dynamics
- **Remeshing**: Adaptive mesh capabilities for moving boundaries

### **Subglacial Processes:**
- **Basal hydrology**: Distributed and channelized drainage systems
- **Basal sliding**: Various sliding laws and friction models
- **Bed evolution**: Erosion and sediment transport

### **Climate Coupling:**
- **Surface mass balance**: Accumulation and ablation processes
- **Ocean interactions**: Sub-shelf melting and marine ice sheet dynamics
- **Permafrost**: Frozen ground dynamics in glaciated regions

## **Inputs and Outputs**

### **Typical Inputs:**
- **Mesh files**: Ice geometry from ElmerGrid or external mesh generators
- **Climate data**: Temperature, precipitation, ocean temperatures
- **Topographic data**: Bed elevation, surface elevation, ice thickness
- **Initial conditions**: Velocity fields, temperature distributions
- **Material parameters**: Ice rheology, sliding parameters, thermal properties
- **Boundary conditions**: Surface climate, basal heat flux, calving criteria

### **Typical Outputs:**
- **Velocity fields**: 3D ice velocities (u, v, w components)
- **Temperature/enthalpy**: Thermal state of ice
- **Stress tensors**: Full stress and strain rate fields
- **Ice thickness evolution**: Temporal changes in ice geometry
- **Calving rates**: Frontal mass loss quantification
- **Hydrological variables**: Water pressure, discharge in subglacial systems
- **Optimization results**: Inverted parameters (friction, accumulation)

## **Interactions with other components**

### **Core FEM Integration:**
- **`fem/src/`**: Utilizes core Elmer solver infrastructure, mesh handling, and linear algebra
- **`fem/src/modules/`**: Extends standard physics modules with ice-specific implementations
- **`fem/src/SolverUtils.F90`**: Leverages utility functions for finite element operations

### **Mesh Generation:**
- **`elmergrid/`**: Receives structured and unstructured meshes, including extrusion capabilities for 3D ice geometries
- **`meshgen2d/`**: May utilize 2D mesh generation for flowline or map-plane models

### **Post-processing:**
- **`post/`**: Outputs data in formats compatible with visualization tools
- **Custom exporters**: Specialized output for ice modeling community tools

### **External Tools:**
- **Climate models**: Interfaces with regional climate models for boundary conditions
- **GIS systems**: Imports/exports geospatial data formats
- **Observation data**: Assimilates satellite and field measurements

## **Example Files/Code Snippets**

### **Key Solver Implementation Pattern:**
```fortran
! Typical ice solver structure (from SSASolver.F90)
SUBROUTINE SSASolver( Model, Solver, dt, TransientSimulation )
  ! Shallow Shelf Approximation for ice dynamics
  ! Solves: div(H*tau) = rho*g*H*grad(h) + tau_b
  ! Where H=thickness, tau=membrane stress, h=surface elevation
```

### **Calving Implementation:**
```fortran
! Advanced calving dynamics (from Calving3D_lset.F90)
! Level-set method for tracking calving front evolution
! Stress-based calving criteria with remeshing capabilities
```

### **Typical Usage Workflow:**
1. **Setup**: Define ice geometry and mesh using ElmerGrid
2. **Physics**: Configure ice flow law, thermal model, boundary conditions
3. **Solve**: Run transient simulation with coupled stress-thermal-thickness
4. **Analysis**: Post-process velocity, temperature, and calving fields
5. **Optimization**: Optionally invert for unknown parameters using adjoint methods

### **Integration Example:**
- **Solver configuration**: Uses `.sif` files to specify physics combinations
- **Mesh adaptation**: Interfaces with MMG libraries for dynamic remeshing
- **Parallel execution**: Supports MPI parallelization for large-scale simulations

This directory represents one of the most comprehensive ice sheet modeling toolkits available, providing research-grade capabilities for understanding ice dynamics from local glacier scales to continental ice sheet evolution. 