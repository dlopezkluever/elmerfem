# **fhutiter Directory Architecture**

## **Purpose**
The `fhutiter` directory contains the HUTIter (Helsinki University of Technology Iterative) library, which provides a comprehensive collection of Krylov subspace iterative methods for solving large sparse linear systems. Originally developed at Helsinki University of Technology by Jouni Malinen, this library serves as the primary iterative linear solver backend for Elmer FEM, offering both serial and parallel implementations of state-of-the-art iterative algorithms essential for finite element computations.

## **Key Components/Subdirectories**

### **Core Source Files:**
* `src/`: Main library implementation in Fortran 90
  - `huti_cg.F90`: Conjugate Gradient method implementation
  - `huti_cgs.F90`: Conjugate Gradient Squared method
  - `huti_bicgstab.F90`: BiConjugate Gradient Stabilized method
  - `huti_bicgstab_2.F90`: BiConjugate Gradient Stabilized(2) method  
  - `huti_gmres.F90`: Generalized Minimum Residual method
  - `huti_qmr.F90`: Quasi-Minimal Residual method
  - `huti_tfqmr.F90`: Transpose-Free Quasi-Minimal Residual method
  - `huti_interfaces.F90`: Procedure interfaces for solver framework
  - `huti_sfe.F90`: Solver front-end and unified interface
  - `huti_aux.F90`: Auxiliary functions and utilities

### **Header Definitions:**
* `include/huti_fdefs.h`: Fortran preprocessor definitions
* `src/huti_fdefs.h`: Fortran constants and parameter definitions
* `src/huti_intdefs.h`: Integer type definitions for portability

### **Documentation and Examples:**
* `doc/`: LaTeX documentation including theoretical background
  - `hutidoc.tex`: Comprehensive user guide and mathematical theory
* `examples/`: Sample programs demonstrating library usage
  - `ex1/huti-ex.F90`: Basic usage example with matrix I/O
* `README.md`: Library overview and compilation instructions

### **Build System:**
* `CMakeLists.txt`: Modern CMake build configuration
* Cross-platform compilation support for Linux, Windows, and macOS

## **Functionality/Role in Architecture**

### **Iterative Method Implementation:**
The fhutiter library implements seven major Krylov subspace methods, each optimized for different matrix properties and problem characteristics:

#### **Symmetric Positive Definite Systems:**
- **Conjugate Gradient (CG)**: Optimal method for SPD systems
  - Minimal storage requirements (4 work vectors)
  - Theoretical convergence guarantee
  - Ideal for structural mechanics and thermal problems

#### **Nonsymmetric Systems:**
- **Conjugate Gradient Squared (CGS)**: Fast convergence but potentially unstable
- **BiConjugate Gradient Stabilized (BiCGSTAB)**: Improved stability over CGS
- **BiConjugate Gradient Stabilized(2) (BiCGSTAB(2))**: Enhanced robustness
- **Transpose-Free QMR (TFQMR)**: Smoother convergence without matrix transpose
- **Quasi-Minimal Residual (QMR)**: Minimal residual property

#### **General Purpose Method:**
- **Generalized Minimum Residual (GMRES)**: Robust for difficult problems
  - Restart capability for memory management
  - Excellent convergence properties
  - Higher memory requirements

### **Advanced Features:**

#### **Preconditioning Support:**
- **Left/Right Preconditioning**: Flexible preconditioning interfaces
- **User-Defined Preconditioners**: Custom preconditioning functions
- **Matrix-Free Operations**: Support for matrix-free implementations
- **Parallel Preconditioning**: Distributed memory preconditioning

#### **Parallel Computing:**
- **MPI Parallelization**: Native support for distributed memory systems
- **Scalable Communication**: Optimized communication patterns
- **Load Balancing**: Efficient parallel load distribution
- **Portable Parallelism**: Works with various MPI implementations

#### **Convergence Control:**
- **Multiple Stopping Criteria**: 
  - True residual: ||Ax - b||
  - Scaled residual: ||Ax - b|| / ||b||
  - Pseudo residual: ||r_k||
  - Solution difference: ||x_k - x_{k-1}||
- **User-Defined Criteria**: Custom convergence functions
- **Convergence Monitoring**: Detailed convergence history

#### **Numerical Robustness:**
- **Breakdown Detection**: Automatic detection and handling of method breakdown
- **Stagnation Detection**: Identification of convergence stagnation
- **Restart Mechanisms**: Automatic restart for GMRES and other methods
- **Precision Control**: Support for single, double, and complex arithmetic

## **Inputs and Outputs**

### **Typical Inputs:**
- **Matrix Operations**: User-provided matrix-vector multiplication routines
  ```fortran
  SUBROUTINE matvec(x, y, ipar)
    ! Computes y = A*x (or y = A^T*x for transpose operations)
  ```

- **Preconditioning Functions**: Optional preconditioning operations
  ```fortran
  SUBROUTINE precond_left(x, y, ipar)   ! y = M^(-1)*x (left preconditioning)
  SUBROUTINE precond_right(x, y, ipar)  ! y = M^(-1)*x (right preconditioning)
  ```

- **Vector Operations**: Dot product and norm functions
- **Control Parameters**: 
  - `IPAR`: Integer parameter array (method selection, iteration limits, etc.)
  - `DPAR`: Double precision parameter array (tolerance, convergence criteria)

- **Initial Guess**: Starting vector for iterative process
- **Right-Hand Side**: Target vector b in Ax = b

### **Typical Outputs:**
- **Solution Vector**: Approximate solution x to the linear system
- **Convergence Information**:
  - Final residual norm
  - Number of iterations performed
  - Convergence status (success, maximum iterations, breakdown)
- **Iteration History**: Optional detailed convergence history
- **Work Arrays**: Reusable workspace for subsequent solves

## **Interactions with other components**

### **Core Elmer Integration:**
- **`fem/src/`**: Primary interface through ElmerSolver linear algebra infrastructure
- **`fem/src/SolverUtils.F90`**: Integration with Elmer's solver framework
- **`fem/src/IterativeMethods.F90`**: Higher-level iterative solver interface
- **`fem/src/ParallelUtils.F90`**: Parallel finite element assembly and distribution

### **Linear Algebra Stack:**
- **BLAS Libraries**: Leverages optimized BLAS for vector operations
- **Parallel Communication**: MPI for distributed memory operations
- **Matrix Storage**: Compatible with various sparse matrix formats (CRS, CCS, etc.)

### **Solver Integration Pattern:**
```fortran
! Typical integration with Elmer
CALL HUTI_D_CG( Solution, RHS, IPAR, DPAR, Work, &
                MatVec, PrecondL, PrecondR, &
                DotProd, Norm, StopCrit )
```

### **Preconditioning Ecosystem:**
- **`fem/src/Smoothers.F90`**: Interfaces with Elmer's preconditioning methods
- **External Libraries**: Can interface with PETSc, Trilinos, and Hypre preconditioners
- **Multigrid**: Integration with geometric and algebraic multigrid methods

## **Example Files/Code Snippets**

### **Basic Usage Pattern:**
```fortran
! From examples/ex1/huti-ex.F90
#include "huti_fdefs.h"

! Set solver parameters
HUTI_NDIM = ndim                    ! Problem dimension
HUTI_WRKDIM = HUTI_CG_WORKSIZE     ! Work array size
HUTI_MAXIT = 1000                  ! Maximum iterations
HUTI_TOLERANCE = 1.0D-8            ! Convergence tolerance
HUTI_DBUGLVL = HUTI_ITEROUTPUT     ! Debug output level

! Call iterative solver
CALL HUTI_D_CG( x, b, ipar, dpar, work, &
                own_matvec, 0, 0, 0, 0, 0 )

! Check convergence
IF (HUTI_INFO == HUTI_CONVERGENCE) THEN
  PRINT *, 'Converged in', HUTI_ITERS, 'iterations'
END IF
```

### **Matrix-Vector Multiplication Interface:**
```fortran
! User-provided matrix-vector routine
SUBROUTINE own_matvec(x, y, ipar)
  USE globals_module
  IMPLICIT NONE
  DOUBLE PRECISION :: x(*), y(*)
  INTEGER :: ipar(*)
  INTEGER :: i, j
  
  ! Compute y = A*x
  DO i = 1, ndim
    y(i) = 0.0D0
    DO j = 1, ndim
      y(i) = y(i) + A_ptr(i,j) * x(j)
    END DO
  END DO
END SUBROUTINE
```

### **Advanced Solver Configuration:**
```fortran
! GMRES with restart
HUTI_GMRES_RESTART = 30             ! Restart after 30 iterations
HUTI_STOPC = HUTI_TRUERESIDUAL     ! Use true residual for stopping

! BiCGSTAB with preconditioning
CALL HUTI_D_BICGSTAB( x, b, ipar, dpar, work, &
                      matvec, ilu_precond, 0, &
                      ddot, dnrm2, stopc )
```

### **Parallel Usage Pattern:**
```fortran
! MPI parallel execution
CALL MPI_INIT(ierr)
CALL MPI_COMM_RANK(MPI_COMM_WORLD, myrank, ierr)

! Distributed matrix-vector operation
SUBROUTINE parallel_matvec(x, y, ipar)
  ! Local matrix-vector multiplication
  CALL local_matvec(x_local, y_local)
  
  ! Communication for ghost values
  CALL MPI_ALLGATHERV(y_local, y_global, ...)
END SUBROUTINE
```

### **Method Selection Guidelines:**

1. **CG**: Symmetric positive definite matrices (heat conduction, linear elasticity)
2. **BiCGSTAB**: General nonsymmetric systems (convection-diffusion, Navier-Stokes)
3. **GMRES**: Difficult nonsymmetric problems (indefinite systems, poor conditioning)
4. **TFQMR**: When matrix transpose is expensive or unavailable

### **Performance Characteristics:**

- **Memory Usage**: 4-14 work vectors depending on method
- **Computational Cost**: 1-2 matrix-vector products per iteration
- **Parallel Efficiency**: Excellent scaling on distributed memory systems
- **Convergence Rate**: Problem-dependent, typically superlinear for well-conditioned systems

The fhutiter library provides Elmer FEM with robust, efficient, and scalable iterative linear solvers essential for large-scale finite element computations. Its comprehensive method collection and parallel capabilities enable Elmer to solve systems with millions of unknowns on modern supercomputing platforms. 