# **matc Directory Architecture**

## **Purpose**
The `matc` directory contains the MATC (Mathematical Calculator) library, which provides numerical evaluation of mathematical expressions. MATC serves as a mathematical expression parser and evaluator that allows Elmer FEM users to define complex mathematical expressions in command files, which can be evaluated either at parse time or runtime.

## **Key Components/Subdirectories**
* `src/`: Contains the core C source files for the MATC library
  * `main.c`: Main entry point for standalone MATC program
  * `matc.c`: Core MATC functionality and expression evaluation engine
  * `parser.c`: Mathematical expression parser implementation  
  * `eval.c`: Expression evaluation and computation engine
  * `matrix.c`: Matrix operations and linear algebra functions
  * `funcs.c`: Built-in mathematical functions library
  * `variable.c`: Variable storage and management system
  * `files.c`: File I/O operations for MATC
  * `elmer/`: Elmer-specific integration components
* `doc/`: Documentation for MATC usage and API
* License files: `GPL-2`, `LGPL-2.1` for open source licensing
* `CMakeLists.txt`: Build configuration for the library

## **Functionality/Role in Architecture**
MATC serves as a crucial mathematical expression evaluation component in the Elmer FEM workflow. Key functionalities include:

* **Expression Parsing**: Converts mathematical expressions from text into executable computational trees
* **Runtime Evaluation**: Evaluates mathematical expressions during ElmerSolver execution
* **Variable Management**: Stores and manages variables, constants, and intermediate results
* **Mathematical Functions**: Provides extensive library of mathematical, trigonometric, and statistical functions
* **Matrix Operations**: Supports matrix arithmetic, linear algebra operations, and eigenvalue computations
* **File I/O**: Handles reading/writing of mathematical data and results
* **Graphics Support**: Basic plotting and visualization capabilities (`gra.c`, `dri_ps.c`)
* **Interactive Mode**: Can be used as standalone mathematical calculator

The library integrates with ElmerSolver to allow users to define complex boundary conditions, material properties, and forcing functions using mathematical expressions rather than hardcoded values.

## **Inputs and Outputs**
* **Inputs:** 
  * Mathematical expressions as text strings from Elmer command files (.sif)
  * Variable definitions and assignments
  * Matrix and vector data for computations
  * Function parameters and arguments
* **Outputs:** 
  * Evaluated numerical results (scalars, vectors, matrices)
  * Variables and computed values for use in ElmerSolver
  * Graphics output (PostScript format via `dri_ps.c`)
  * Error messages and diagnostic information

## **Interactions with other components**
* **`fem/src/ElmerSolver.F90`**: ElmerSolver calls MATC functions to evaluate mathematical expressions defined in .sif files during simulation setup and runtime
* **`ElmerGUI`**: The GUI may use MATC for parameter validation and expression evaluation in the interface
* **User .sif files**: MATC expressions are embedded directly in Elmer solver input files using syntax like `$ expression` for runtime evaluation
* **External libraries**: MATC may interface with mathematical libraries in `mathlibs/` for advanced computations
* **Post-processing tools**: Results computed by MATC can be used by post-processing components in the `post/` directory

## **Example Files/Code Snippets (if applicable)**
* **Expression syntax in .sif files:**
  ```
  Material 1
    Density = $ 1000 + 50*sin(2*pi*tx)
    Heat Conductivity = $ if(tx>0.5) 10; else 5;
  End
  ```
* **Key source files:**
  * `parser.c`: Implements recursive descent parser for mathematical expressions
  * `eval.c`: Core evaluation engine with operator precedence and function calls
  * `matrix.c`: Matrix operations using efficient algorithms for FEM applications
  * `funcs.c`: Built-in functions like `sin()`, `cos()`, `sqrt()`, `max()`, `min()`, etc.

MATC provides flexibility and power to Elmer FEM users by allowing sophisticated mathematical expressions while maintaining good performance for computational requirements. 