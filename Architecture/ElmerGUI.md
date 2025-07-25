# **ElmerGUI Directory Architecture**

## **Purpose**
The `ElmerGUI` directory contains the source code for the ElmerGUI application, which is the primary graphical user interface for the Elmer FEM software suite. ElmerGUI provides a comprehensive, user-friendly environment for setting up finite element simulations, including geometry handling, mesh generation, material property assignment, boundary condition specification, solver configuration, and post-processing visualization. It serves as the central hub that integrates all components of the Elmer FEM workflow into a cohesive graphical environment.

## **Key Components/Subdirectories**
* **`Application/`**: Main GUI application with multiple subdirectories:
  - **`src/`**: Core C++ source files (60+ files) including:
    - `main.cpp`: Application entry point and initialization
    - `mainwindow.cpp` (260KB): Primary application window and workflow management
    - `meshutils.cpp` (58KB): Mesh handling and manipulation utilities
    - `objectbrowser.cpp` (71KB): Project tree and object management
    - `sifgenerator.cpp` (43KB): SIF (Solver Input File) generation logic
    - `glwidget.cpp` (62KB): OpenGL-based 3D visualization widget
    - `dynamiceditor.cpp` (25KB): Dynamic form generation for solver parameters
    - `edfeditor.cpp` (26KB): Elmer Definition File (EDF) editor
  - **`forms/`**: Qt UI form files for dialog boxes and windows
  - **`icons/`** & **`images/`**: GUI icons and graphical resources
  - **`vtkpost/`**: VTK-based post-processing visualization components
  - **`twod/`**: 2D mesh generation and manipulation tools
  - **`plugins/`**: Plugin architecture for extending functionality
  - **`cad/`**: CAD file import/export capabilities
  - **`edf/`** & **`edf-extra/`**: Elmer Definition Files for solver configuration
* **`samples/`**: Example projects and tutorial materials
* **`scripts/`**: Utility scripts for various operations
* **`netgen/`**: Integration with Netgen mesh generator
* **`PythonQt/`**: Python scripting integration framework
* **`matc/`**: MATC (Matrix Calculator) integration for mathematical expressions
* **Configuration files**: ElmerGUI.pro, CMakeLists.txt, and Qt resource files

## **Functionality/Role in Architecture**
ElmerGUI serves as the primary user interface and workflow orchestrator for Elmer FEM, providing:

**Project Management:**
- Complete project lifecycle management from creation to simulation
- Workspace organization with hierarchical object browser
- Project serialization and persistence (`.egf` project files)
- Multi-document interface for managing multiple projects

**Geometry and CAD Integration:**
- CAD file import through OpenCASCADE integration (`.step`, `.iges`, `.brep`)
- Basic geometry creation and manipulation tools
- Geometry repair and healing capabilities
- Boundary and volume identification for physics assignment

**Mesh Generation and Management:**
- Integration with multiple mesh generators (Netgen, Tetgen, ElmerGrid)
- Mesh visualization and quality assessment
- Mesh refinement and adaptation tools
- Support for structured and unstructured meshes
- Mesh format conversion and import/export

**Physics Setup and Simulation Configuration:**
- Intuitive physics-based problem setup
- Material property assignment with extensive material library
- Boundary condition specification through graphical selection
- Multi-physics coupling configuration
- Solver parameter management through dynamic forms

**Solver Integration:**
- Direct integration with ElmerSolver through SIF file generation
- Real-time solver monitoring and convergence visualization
- Parallel execution support with MPI configuration
- Solution progress tracking and log analysis

**Post-Processing and Visualization:**
- Integrated VTK-based 3D visualization
- Contour plots, vector fields, and isosurfaces
- Animation capabilities for transient results
- Data export for external visualization tools
- Convergence monitoring and analysis

## **Inputs and Outputs**
**Inputs:**
- CAD geometry files (`.step`, `.iges`, `.brep`, `.stl`)
- Mesh files from external generators (`.msh`, `.neu`, `.unv`)
- Material property databases and user-defined materials
- Elmer Definition Files (`.edf`) for solver configuration
- Previous project files (`.egf`) for workflow continuation
- Python scripts for automation and customization

**Outputs:**
- Elmer Solver Input Files (`.sif`) containing complete problem definition
- Elmer mesh format files for solver consumption
- Project files (`.egf`) for saving complete workflow state
- VTK files for external visualization
- Convergence data and simulation logs
- Post-processing results and animations
- Screenshots and reports for documentation

## **Interactions with other components**
**Downstream Dependencies:**
- **`elmergrid`**: Invoked for mesh generation and format conversion
- **`fem/src/ElmerSolver`**: Receives SIF files and mesh data for simulation execution
- **`post/`**: Utilizes post-processing tools for advanced visualization
- **External mesh generators**: Tetgen, Netgen for unstructured mesh generation
- **OpenCASCADE**: For CAD geometry import and manipulation
- **VTK library**: For 3D visualization and post-processing
- **Qt framework**: For GUI components and cross-platform compatibility

**Configuration and Data Exchange:**
- **EDF files**: Define available solvers, equations, and parameters
- **Material library**: Provides physics-based material properties
- **SIF generation**: Translates GUI configuration to solver input format
- **Mesh interfaces**: Standardized mesh data exchange with various generators

**Workflow Integration:**
1. Imports geometry from CAD systems or creates simple geometries
2. Generates or imports computational meshes
3. Assigns materials and boundary conditions through graphical selection
4. Configures solver parameters using dynamic forms
5. Generates SIF files for ElmerSolver consumption
6. Monitors solver execution and convergence
7. Visualizes results using integrated post-processing tools

## **Example Files/Code Snippets (if applicable)**
**Main Application Structure (from main.cpp):**
```cpp
#include <QApplication>
#include "mainwindow.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    MainWindow window;
    window.show();
    return app.exec();
}
```

**SIF File Generation Pattern:**
```cpp
// From sifgenerator.cpp
void SifGenerator::generateSif(QString projectDir) {
    // Translate GUI settings to Elmer Solver Input Format
    writeSolverSection();
    writeEquationSections();
    writeMaterialSections();
    writeBoundaryConditions();
    // ... other sections
}
```

**Typical Project Workflow:**
1. **Project Creation**: `File -> New Project` creates new `.egf` project
2. **Geometry Import**: CAD files loaded through OpenCASCADE integration
3. **Mesh Generation**: Calls to ElmerGrid or external mesh generators
4. **Physics Setup**: Material assignment and boundary condition specification
5. **Solver Configuration**: Parameter setting through dynamic EDF-based forms
6. **Simulation Execution**: SIF generation and ElmerSolver invocation
7. **Results Visualization**: VTK-based post-processing and analysis

**Integration Examples:**
- **Mesh Generation Call**: `elmergrid 14 2 input.msh -out outputdir`
- **Solver Invocation**: `ElmerSolver case.sif`
- **VTK Output**: Results exported to `.vtu` format for visualization
- **Python Scripting**: Automation through PythonQt integration 