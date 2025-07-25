# **ElmerWorkflows Directory Architecture**

## **Purpose**
The `ElmerWorkflows` directory contains integration tools and workflow scripts that bridge external CAD/FEA software with the Elmer finite element ecosystem. Its primary purpose is to facilitate seamless data exchange and automated workflow creation between popular engineering design tools and Elmer's simulation capabilities, enabling users to leverage existing CAD geometries and third-party mesh generators within Elmer workflows.

## **Key Components/Subdirectories**

### **Integration Modules:**
* `FreeCADBatchFEMTools/`: Automated FEM workflow tools for FreeCAD integration
  - `FreeCADBatchFEMTools.py`: Main Python module (57KB, 1343 lines)
  - `meshutils.py`: Mesh handling utilities (7.4KB, 165 lines)
  - `tests/`: Validation tests for FreeCAD integration
  - `README.md`: Documentation for FreeCAD workflow automation

* `Gid2Elmer/`: Conversion tools for GiD pre-processor integration
  - Handles mesh and boundary condition translation from GiD format

* `Ansys2Elmer/`: ANSYS to Elmer data conversion utilities
  - Enables migration of ANSYS models to Elmer ecosystem
  - Supports mesh, material, and boundary condition translation

## **Functionality/Role in Architecture**

### **CAD-to-FEM Workflow Automation:**
The ElmerWorkflows directory serves as a critical bridge in the modern engineering simulation pipeline by:

- **Geometry Import**: Seamless import of complex CAD geometries from industry-standard tools
- **Mesh Translation**: Conversion of high-quality meshes from external generators
- **Boundary Condition Mapping**: Intelligent translation of boundary conditions and material properties
- **Workflow Automation**: Batch processing capabilities for repetitive simulation tasks

### **FreeCAD Integration (Primary Component):**
The `FreeCADBatchFEMTools` module provides comprehensive automation for FreeCAD-based workflows:

#### **Key Features:**
- **Automated Mesh Generation**: Leverages FreeCAD's mesh generation capabilities
- **Batch Processing**: Handles multiple geometries and configurations automatically
- **Material Assignment**: Maps FreeCAD material definitions to Elmer format
- **Boundary Condition Setup**: Translates FreeCAD constraints to Elmer boundary conditions
- **Result Post-processing**: Converts Elmer results back to FreeCAD for visualization

#### **Technical Capabilities:**
- **Python-based API**: Full programmatic control over FreeCAD operations
- **Mesh Quality Control**: Utilities for mesh validation and refinement
- **Parametric Studies**: Support for parameter sweeps and optimization
- **Error Handling**: Robust error detection and recovery mechanisms

### **Third-party Software Integration:**
- **GiD Integration**: Professional pre-processor for complex geometries
- **ANSYS Migration**: Enables users to transition from ANSYS to open-source Elmer
- **Format Standardization**: Consistent data formats across different CAD systems

## **Inputs and Outputs**

### **Typical Inputs:**
- **CAD Geometries**: 
  - FreeCAD documents (.FCStd files)
  - STEP/IGES files from various CAD systems
  - GiD geometry and mesh files
  - ANSYS model files and databases

- **Configuration Data**:
  - Material property definitions
  - Boundary condition specifications
  - Mesh generation parameters
  - Simulation setup parameters

- **Control Scripts**:
  - Python automation scripts
  - Batch job definitions
  - Parameter study configurations

### **Typical Outputs:**
- **Elmer-compatible Files**:
  - Mesh files in Elmer format (nodes, elements, boundaries)
  - Material property files
  - Boundary condition definitions
  - Solver input files (.sif format)

- **Workflow Documentation**:
  - Processing logs and reports
  - Mesh quality metrics
  - Conversion status and error reports

- **Post-processing Data**:
  - Results in FreeCAD-compatible formats
  - Visualization-ready output files
  - Export data for external analysis tools

## **Interactions with other components**

### **Core Elmer Integration:**
- **`elmergrid/`**: Utilizes ElmerGrid for final mesh processing and format conversion
- **`fem/`**: Generates solver input files compatible with ElmerSolver
- **`post/`**: Coordinates with post-processing tools for result visualization

### **External Software Ecosystem:**
- **FreeCAD**: Direct API integration for geometry and mesh handling
- **GiD**: Import/export capabilities for professional pre-processing workflows
- **ANSYS**: Migration tools for existing ANSYS users transitioning to Elmer

### **File System Integration:**
- **Automated File Management**: Handles complex directory structures and file naming
- **Version Control Support**: Compatible with git and other VCS systems
- **Network Deployment**: Supports distributed computing environments

### **Workflow Management:**
- **Task Scheduling**: Integration with job schedulers and workflow managers
- **Parameter Management**: Handles complex parameter spaces for optimization studies
- **Results Archiving**: Automated storage and organization of simulation results

## **Example Files/Code Snippets**

### **FreeCAD Integration Example:**
```python
# From FreeCADBatchFEMTools.py - Automated FEM workflow
class FEMWorkflow:
    def __init__(self, freecad_doc):
        self.document = freecad_doc
        self.mesh_object = None
        self.analysis = None
    
    def generate_mesh(self, element_size=1.0):
        # Automated mesh generation with quality control
        # Interfaces with FreeCAD's built-in meshers
        
    def export_to_elmer(self, output_directory):
        # Convert FreeCAD mesh and boundaries to Elmer format
        # Generate .sif files for solver configuration
```

### **Batch Processing Pattern:**
```python
# Automated parameter study workflow
def run_parameter_study(geometry_file, parameter_ranges):
    for params in parameter_ranges:
        # Load geometry
        doc = load_freecad_document(geometry_file)
        
        # Apply parameters
        update_geometry_parameters(doc, params)
        
        # Generate mesh
        mesh = generate_mesh(doc)
        
        # Export to Elmer
        export_to_elmer(mesh, f"case_{params}")
        
        # Run simulation
        run_elmer_simulation(f"case_{params}")
```

### **Mesh Utility Functions:**
```python
# From meshutils.py - Mesh quality and conversion utilities
def validate_mesh_quality(mesh):
    # Check element quality metrics
    # Detect degenerate elements
    # Report mesh statistics

def convert_mesh_format(input_mesh, target_format):
    # Handle various mesh format conversions
    # Preserve boundary information
    # Maintain element connectivity
```

### **Typical Usage Scenarios:**

1. **Industrial Design Workflow**:
   ```
   CAD Design (FreeCAD) → Automated Meshing → Elmer Simulation → Results Analysis
   ```

2. **Academic Research Pipeline**:
   ```
   Parametric Geometry → Batch Processing → Parameter Study → Optimization
   ```

3. **Legacy Model Migration**:
   ```
   ANSYS Model → Conversion Tools → Elmer Format → Validation → Production
   ```

### **Integration Benefits:**
- **Reduced Learning Curve**: Users can leverage familiar CAD interfaces
- **Workflow Efficiency**: Automated processes reduce manual intervention
- **Quality Assurance**: Built-in validation and error checking
- **Scalability**: Batch processing capabilities for large studies
- **Interoperability**: Seamless integration with existing engineering toolchains

This directory enables Elmer to integrate seamlessly into modern engineering workflows, making advanced finite element simulation accessible to users working with standard CAD and engineering software packages. 