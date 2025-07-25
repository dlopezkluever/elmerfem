# **fem Directory Architecture**

## **Purpose**
The `fem` directory constitutes the core finite element solver engine of Elmer FEM. It contains the fundamental infrastructure for finite element computations, including the main solver library, element formulations, numerical linear algebra, mesh handling, and a comprehensive collection of physics modules. This directory serves as the computational heart of the entire Elmer ecosystem, providing the foundational capabilities upon which all other specialized components are built.

## **Key Components/Subdirectories**

### **Core Infrastructure:**
* `src/`: Main source code directory containing the solver core
  - **Primary Components**: `SolverUtils.F90` (971KB, 26576 lines) - central utility functions
  - **Core Solver**: `Solver.F90` (2.4KB, 74 lines) - main solver interface
  - **Type Definitions**: `Types.F90` (42KB, 1144 lines) - fundamental data structures
  - **Main Utilities**: `MainUtils.F90` (239KB) - core application framework
  - **Mesh Handling**: `MeshUtils.F90` (1.1MB) - comprehensive mesh operations

### **Physics Modules Directory:**
* `src/modules/`: Physics-specific solver modules (60+ specialized solvers)
  - **Fluid Dynamics**: `NavierStokes.F90`, `IncompressibleNSVec.F90`, `Stokes.F90`
  - **Heat Transfer**: `HeatSolve.F90`, `HeatSolveVec.F90` 
  - **Solid Mechanics**: `StressSolve.F90`, `ShellSolver.F90`
  - **Electromagnetics**: `StatElecSolve.F90`, `MagnetoDynamics2D.F90`, `VectorHelmholtz.F90`
  - **Specialized Physics**: `Poisson.F90`, `Helmholtz.F90`, `TransportEquation.F90`

### **Supporting Infrastructure:**
* `src/binio/`: Binary I/O operations for results and mesh data
* `src/view3d/`: 3D visualization and rendering capabilities  
* `src/viewaxis/`: Axis and coordinate system visualization
* `src/lua-scripts/`: Lua scripting interface for solver customization
* `examples/`: Comprehensive example problems and tutorials
* `tests/`: Validation and regression test suite
* `benchmarks/`: Performance and accuracy benchmark problems

### **Mathematical Libraries:**
* **Linear Algebra**: Integration with BLAS, LAPACK, UMFPACK, SuperLU
* **Iterative Solvers**: Interface to `fhutiter` library for Krylov methods
* **Parallel Computing**: MPI support via `ParallelUtils.F90` (67KB)
* **Optimization**: Powell optimization methods and adjoint solvers

## **Functionality/Role in Architecture**

### **Finite Element Engine Core:**
The fem directory implements a complete finite element framework with:

#### **Mesh Management:**
- **Adaptive Meshing**: Dynamic mesh refinement and coarsening (`MeshRemeshing.F90`)
- **Mesh Partitioning**: Parallel mesh distribution (`MeshPartition.F90`)
- **Mesh Generation**: Built-in mesh generation capabilities (`MeshGenerate.F90`)
- **Mesh Utilities**: Comprehensive mesh manipulation and quality assessment

#### **Element Technology:**
- **P-Elements**: High-order polynomial basis functions (`PElementBase.F90`, `PElementMaps.F90`)
- **H1-Basis**: Standard finite element basis functions (`H1Basis.F90`)
- **Integration**: Gaussian quadrature and numerical integration (`Integration.F90`)
- **Element Library**: Comprehensive element definitions (`elements.def`)

#### **Solver Infrastructure:**
- **Linear Systems**: Advanced linear algebra with multiple solver backends
- **Nonlinear Methods**: Newton-Raphson and other nonlinear solution techniques
- **Time Integration**: Various time-stepping schemes (`TimeIntegrate.F90`)
- **Convergence Control**: Sophisticated convergence criteria and monitoring

#### **Physics Implementation Framework:**
- **Weak Formulations**: Infrastructure for defining weak forms of PDEs
- **Material Models**: Extensible material property framework (`MaterialModels.F90`)
- **Boundary Conditions**: Comprehensive boundary condition implementation
- **Coupling**: Multi-physics coupling mechanisms

### **Advanced Numerical Methods:**
#### **Linear Algebra:**
- **Direct Solvers**: UMFPACK, SuperLU integration for sparse systems
- **Iterative Methods**: Comprehensive Krylov subspace methods via HUTIter
- **Preconditioning**: Advanced preconditioning strategies (`Smoothers.F90`)
- **Parallel Linear Algebra**: Distributed memory linear algebra operations

#### **Discretization Methods:**
- **Standard FEM**: Classical Galerkin finite element methods
- **Stabilized Methods**: SUPG, PSPG, and other stabilization techniques
- **Mixed Methods**: Mixed finite element formulations
- **Discontinuous Galerkin**: DG methods for specific applications

#### **Parallel Computing:**
- **Domain Decomposition**: Efficient parallel mesh distribution
- **Communication**: Optimized inter-processor communication
- **Load Balancing**: Dynamic load balancing capabilities
- **Scalability**: Support for thousands of processors

## **Inputs and Outputs**

### **Typical Inputs:**
- **Mesh Files**: Elmer mesh format (nodes, elements, boundary conditions)
  - `mesh.header`: Mesh metadata
  - `mesh.nodes`: Node coordinates
  - `mesh.elements`: Element connectivity
  - `mesh.boundary`: Boundary element definitions

- **Solver Input Files** (`.sif` format):
  - Simulation parameters and physics configuration
  - Material properties and constitutive laws
  - Boundary and initial conditions
  - Solver control parameters

- **Restart Files**: Previous simulation state for continuation runs
- **External Data**: Time-dependent boundary conditions and forcing functions

### **Typical Outputs:**
- **Solution Fields**: Primary variables (temperature, velocity, pressure, etc.)
- **Result Files**: 
  - `.ep` files: Elmer post-processing format
  - VTU/VTK files: ParaView/VTK compatible formats
  - `.dat` files: ASCII data output

- **Convergence Information**: Residual histories and solver statistics
- **Mesh Data**: Adapted meshes and mesh quality metrics
- **Post-processing Data**: Derived quantities and secondary variables

## **Interactions with other components**

### **Core Integration:**
- **`elmergrid/`**: Receives mesh data from ElmerGrid mesh generator
- **`elmerice/`**: Provides base solver infrastructure for glaciological extensions
- **`fhutiter/`**: Utilizes iterative linear solvers for large sparse systems
- **`matc/`**: Integrates MATC mathematical expression evaluator
- **`mathlibs/`**: Links with mathematical libraries (BLAS, LAPACK, etc.)

### **Pre-processing:**
- **`ElmerGUI/`**: Receives simulation setup from graphical user interface
- **`ElmerWorkflows/`**: Integrates with external CAD/FEA workflow tools
- **Mesh Import**: Supports various external mesh formats

### **Post-processing:**
- **`post/`**: Provides results to post-processing and visualization tools
- **External Tools**: Exports to ParaView, VisIt, and other visualization packages
- **Data Analysis**: Interfaces with MATLAB, Python, and R for analysis

### **Parallel Execution:**
- **MPI Libraries**: Interfaces with various MPI implementations
- **Parallel File Systems**: Optimized I/O for large-scale parallel simulations
- **Job Schedulers**: Integration with cluster job management systems

## **Example Files/Code Snippets**

### **Core Solver Architecture:**
```fortran
! From SolverUtils.F90 - Central solver infrastructure
SUBROUTINE SolverInitialize( Solver, Mesh, SolverName )
  ! Initialize solver with mesh and configuration
  ! Set up degrees of freedom and matrix structure
  ! Configure parallel communication patterns
END SUBROUTINE

FUNCTION SolveSystem( Solver, Matrix, RHS, Solution ) RESULT(Converged)
  ! Main linear system solution interface
  ! Handles both direct and iterative solution methods
  ! Includes preconditioning and parallel communication
END FUNCTION
```

### **Physics Module Pattern:**
```fortran
! Typical physics solver structure (e.g., HeatSolve.F90)
SUBROUTINE HeatSolver( Model, Solver, dt, TransientSimulation )
  ! Assemble heat equation: ρc ∂T/∂t - ∇·(k∇T) = f
  ! Handle material nonlinearities and phase change
  ! Implement boundary conditions and coupling
  ! Solve linear/nonlinear system
END SUBROUTINE
```

### **Element Assembly:**
```fortran
! Element-level operations pattern
DO t = 1, GetNOFActive()
  Element => GetActiveElement(t)
  n = GetElementNOFNodes()
  
  ! Get element matrix and load vector
  CALL LocalMatrix( MASS, STIFF, FORCE, Element, n )
  
  ! Add to global system
  CALL DefaultUpdateEquations( STIFF, FORCE )
END DO
```

### **Advanced Features:**

#### **Adaptive Mesh Refinement:**
```fortran
! Mesh adaptation based on error estimation
CALL ErrorEstimate( ErrorIndicator, Solution )
CALL AdaptMesh( ErrorIndicator, RefinementLevel )
CALL RemeshDomain( NewMesh, OldMesh )
```

#### **Multi-physics Coupling:**
```fortran
! Coupled field solution
DO WHILE (.NOT. Converged)
  CALL SolveField1( Temperature )
  CALL SolveField2( Displacement, Temperature )
  CALL CheckCouplingConvergence( Converged )
END DO
```

### **Parallel Execution Pattern:**
```fortran
! Parallel solver initialization
CALL ParallelInitialize( MyPE, NumberOfPEs )
CALL DistributeMesh( LocalMesh, GlobalMesh )
CALL SetupCommunication( CommPattern )

! Parallel solution
CALL ParallelSolve( LocalMatrix, LocalRHS, Solution )
CALL ParallelAssemble( GlobalSolution, LocalSolution )
```

### **Key Technical Features:**

1. **High Performance**: Optimized for large-scale simulations
2. **Extensibility**: Plugin architecture for new physics modules
3. **Robustness**: Extensive error handling and numerical stability
4. **Scalability**: Efficient parallel execution on supercomputers
5. **Versatility**: Support for diverse element types and physics

The fem directory represents a mature, production-quality finite element framework capable of handling complex multi-physics simulations with high performance and numerical robustness. It provides the computational foundation that enables Elmer to tackle challenging engineering and scientific problems across diverse application domains. 