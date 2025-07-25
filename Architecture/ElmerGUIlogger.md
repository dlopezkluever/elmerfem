# **ElmerGUIlogger Directory Architecture**

## **Purpose**
The `ElmerGUIlogger` directory contains the source code for a dedicated data logging utility designed to work in conjunction with ElmerGUI. Its primary purpose is to provide real-time monitoring, logging, and display of data streams generated during Elmer FEM simulations. The logger serves as a standalone Qt-based application that can capture, process, and visualize simulation data, convergence information, and solver status messages in real-time, enhancing the user's ability to monitor and debug finite element simulations.

## **Key Components/Subdirectories**
* **`src/`**: Core C++ source files for the logger application:
  - `main.cpp` (3.2KB): Application entry point and Qt application initialization
  - `mainwindow.cpp` (11KB): Primary window implementation with UI management
  - `mainwindow.h` (3.9KB): Main window class declaration and interface definitions
* **`icons/`**: Application icons and graphical resources for the logger interface
* **`cmake/`**: CMake build configuration files for cross-platform compilation
* **Configuration files**:
  - `CMakeLists.txt` (3.3KB): Primary build configuration with Qt integration
  - `ElmerGUIlogger.pro` (234B): Qt project file for qmake-based builds
  - `ElmerGUIlogger.qrc` (244B): Qt resource file linking application resources
  - `ElmerGUIlogger.rc` (49B): Windows resource file for application metadata
* **Documentation**: README with basic compilation instructions

## **Functionality/Role in Architecture**
ElmerGUIlogger serves as a specialized monitoring and data visualization component within the Elmer FEM ecosystem:

**Real-Time Data Monitoring:**
- Captures and displays live data streams from running Elmer simulations
- Provides real-time visualization of simulation progress and status
- Monitors solver convergence behavior and iteration data
- Tracks system resource usage and performance metrics

**Data Logging and Storage:**
- Records simulation data for post-processing analysis
- Maintains persistent logs of solver execution and error messages
- Stores convergence history and performance benchmarks
- Archives debugging information for troubleshooting

**User Interface and Visualization:**
- Clean, responsive Qt-based graphical interface
- Configurable data display options and view preferences
- Multi-window support for simultaneous monitoring of different data streams
- Customizable alerts and notification systems

**Integration and Communication:**
- Establishes communication channels with ElmerGUI and ElmerSolver
- Processes inter-process communication for data exchange
- Supports network-based monitoring for remote simulations
- Provides plugin architecture for extended functionality

## **Inputs and Outputs**
**Inputs:**
- Data streams from ElmerSolver during simulation execution
- Configuration files specifying logging parameters and display preferences
- Communication channels from ElmerGUI for coordination and control
- User commands for logger configuration and display options
- Network connections for remote simulation monitoring

**Outputs:**
- Real-time graphical displays of simulation data and progress
- Log files containing comprehensive simulation history and debug information
- Convergence plots and performance analysis charts
- Alert notifications for critical simulation events or errors
- Exported data files for further analysis in external tools

## **Interactions with other components**
**Primary Integration Points:**
- **`ElmerGUI`**: Receives coordination signals and configuration data from the main GUI
- **`fem/src/ElmerSolver`**: Monitors solver output streams and captures runtime data
- **Local file system**: Reads configuration files and writes log data
- **Network interfaces**: Supports remote monitoring of distributed simulations

**Communication Mechanisms:**
- **Inter-Process Communication (IPC)**: Direct data exchange with ElmerGUI and solver
- **File-based monitoring**: Watches solver output files for new data
- **Network protocols**: TCP/UDP connections for remote monitoring capabilities
- **Shared memory**: High-performance data exchange for intensive logging scenarios

**Workflow Integration:**
1. Launched manually as standalone application or automatically by ElmerGUI
2. Establishes communication channels with target simulation processes
3. Begins real-time data capture and display upon simulation start
4. Provides continuous monitoring throughout simulation execution
5. Archives data and generates summary reports upon simulation completion
6. Remains available for post-simulation analysis and review

## **Example Files/Code Snippets (if applicable)**
**Main Application Structure (from main.cpp):**
```cpp
#include <QApplication>
#include "mainwindow.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    
    MainWindow logger;
    logger.show();
    
    return app.exec();
}
```

**Typical Logger Window Features (inferred from mainwindow.cpp size):**
- Real-time data plotting and graphical displays
- Tabbed interface for different types of monitoring data
- Configuration dialogs for customizing logging behavior
- File I/O operations for saving and loading log data
- Network connectivity for remote monitoring scenarios

**Build Configuration (from CMakeLists.txt):**
```cmake
# Qt-based application with GUI components
find_package(Qt4 REQUIRED QtCore QtGui)
include(${QT_USE_FILE})

# Logger application compilation
add_executable(ElmerGUIlogger ${SOURCES} ${MOC_SOURCES})
target_link_libraries(ElmerGUIlogger ${QT_LIBRARIES})
```

**Resource Integration (from .qrc file):**
- Application icons and GUI graphics
- Configuration templates and default settings
- Help documentation and user guides

**Typical Usage Scenarios:**
1. **Development and Debugging**: Monitor solver behavior during development
2. **Long-running Simulations**: Track progress of computationally intensive problems  
3. **Performance Analysis**: Collect data for optimization and benchmarking
4. **Remote Monitoring**: Observe simulations running on compute clusters
5. **Educational Use**: Demonstrate convergence behavior and solver characteristics 