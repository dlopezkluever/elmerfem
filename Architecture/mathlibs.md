# **mathlibs Directory Architecture**

## **Purpose**
The `mathlibs` directory contains essential mathematical libraries that provide the computational foundation for Elmer FEM. It includes ScaLAPACK components: BLAS (Basic Linear Algebra Subprograms), LAPACK (Linear Algebra PACKage), ARPACK (ARnoldi PACKage), and PARPACK (Parallel ARPACK) wrapped in autoconf/automake build scripts for integration with Elmer.

## **Key Components/Subdirectories**
* `src/`: Root source directory containing mathematical library implementations
  * `blas/`: Basic Linear Algebra Subprograms - fundamental vector and matrix operations
  * `lapack/`: Linear Algebra PACKage - higher-level linear algebra routines
  * `arpack/`: ARnoldi PACKage - large sparse eigenvalue problem solvers
  * `parpack/`: Parallel ARPACK - parallel versions of ARPACK algorithms
* `CMakeLists.txt`: Build configuration for mathematical libraries
* `README`: Brief description of included ScaLAPACK components

## **Functionality/Role in Architecture**
The mathlibs directory provides the mathematical computational backbone for Elmer FEM's numerical algorithms. Key functionalities include:

* **BLAS Operations**: 
  * Level 1: Vector operations (dot products, norms, scaling)
  * Level 2: Matrix-vector operations (matrix-vector multiplication, solving triangular systems)
  * Level 3: Matrix-matrix operations (matrix multiplication, rank-k updates)
  * Support for single, double, complex, and double complex precision

* **LAPACK Functions**:
  * Linear system solving (LU, Cholesky, QR decompositions)
  * Eigenvalue and eigenvector computations
  * Singular value decomposition (SVD)
  * Matrix factorizations and condition number estimation
  * Specialized routines for symmetric, Hermitian, and general matrices

* **ARPACK Capabilities**:
  * Large sparse eigenvalue problems using iterative methods
  * Arnoldi and Lanczos algorithms for eigenvalue computation
  * Both standard and generalized eigenvalue problems
  * Computing selected eigenvalues (smallest, largest, closest to target)

* **PARPACK Features**:
  * Parallel implementations of ARPACK algorithms
  * Distributed memory parallel eigenvalue solvers
  * MPI-based communication for large-scale problems

## **Inputs and Outputs**
* **Inputs:**
  * Dense and sparse matrices from FEM discretizations
  * Vectors for linear system right-hand sides
  * Matrix dimensions, operation parameters, and convergence tolerances
  * Problem specifications (eigenvalue targets, number of desired eigenvalues)
* **Outputs:**
  * Solution vectors for linear systems
  * Eigenvalues and eigenvectors for modal analysis
  * Matrix factorizations and decompositions
  * Convergence information and error estimates
  * Condition numbers and numerical diagnostics

## **Interactions with other components**
* **`fem/src/ElmerSolver.F90`**: The main solver calls BLAS/LAPACK routines for linear algebra operations in finite element computations
* **`fem/src/` modules**: Various solver modules use these libraries for:
  * Assembling and solving finite element matrix systems
  * Computing eigenvalues for stability analysis and modal problems
  * Performing matrix operations in iterative solvers
* **Linear solvers**: Direct and iterative solvers in Elmer rely heavily on BLAS/LAPACK for efficiency
* **Eigenvalue solvers**: ARPACK/PARPACK are used for computing natural frequencies, buckling modes, and other eigenvalue problems
* **Parallel processing**: PARPACK enables parallel eigenvalue computations for large-scale problems
* **External solver interfaces**: May interface with external solvers like MUMPS, UMFPACK that also use these libraries

## **Example Files/Code Snippets (if applicable)**
* **BLAS routine examples:**
  * `dgemm.f`: Double precision general matrix multiplication
  * `dgemv.f`: Matrix-vector multiplication
  * `ddot.f`: Dot product computation
  * `daxpy.f`: Vector addition with scaling

* **LAPACK routine examples:**
  * `dgesv.f`: General linear system solver using LU decomposition
  * `dsyev.f`: Symmetric eigenvalue problem solver
  * `dgesvd.f`: Singular value decomposition
  * `dgetrf.f`: LU factorization with partial pivoting

* **ARPACK usage patterns:**
  * Computing natural frequencies in structural analysis
  * Finding dominant eigenvalues in stability analysis
  * Modal analysis for vibration problems

* **Precision support:**
  * `s` prefix: Single precision (real)
  * `d` prefix: Double precision (real)
  * `c` prefix: Complex single precision
  * `z` prefix: Complex double precision

The mathlibs directory ensures that Elmer FEM has access to highly optimized, well-tested mathematical algorithms that form the computational core of finite element analysis, providing both performance and numerical stability for large-scale engineering simulations. 