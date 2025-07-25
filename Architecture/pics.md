# **pics Directory Architecture**

## **Purpose**
The `pics` directory serves as a centralized repository for graphical assets, logos, and visual resources used throughout the Elmer FEM software suite. Its primary function is to provide consistent branding elements, application icons, documentation images, and promotional materials that maintain visual identity across all Elmer FEM components and user interfaces.

## **Key Components/Subdirectories**
* **`Elmerlogo.png` (9.5KB)**: Standard Elmer FEM logo in PNG format for general use
* **`ElmerLogoPlain128x128.png` (20KB)**: High-resolution plain Elmer logo optimized for 128x128 pixel display
* **`ElmerLogoPlain64x64.png` (7.6KB)**: Medium-resolution plain Elmer logo optimized for 64x64 pixel display
* **`Elmer-pump-heatequation.png` (536KB)**: Large promotional/demonstration image showcasing Elmer FEM capabilities in pump heat equation simulation

## **Functionality/Role in Architecture**
The pics directory provides essential visual assets that serve multiple roles within the Elmer FEM ecosystem:

**Branding and Identity:**
- Maintains consistent visual identity across all Elmer FEM applications
- Provides official logos in multiple resolutions for different use cases
- Ensures professional presentation in user interfaces and documentation

**Application Integration:**
- Supplies application icons for ElmerGUI, ElmerPost, and other tools
- Provides splash screen images and about dialog graphics
- Supports desktop integration with properly sized icon sets

**Documentation and Promotion:**
- Contains demonstration images showcasing Elmer FEM simulation capabilities
- Provides visual examples for tutorials and educational materials
- Supports marketing and presentation materials with professional graphics

**User Interface Resources:**
- Supplies icons and graphics for toolbar buttons and menu items
- Provides visual feedback elements for application status and branding
- Maintains resolution-appropriate assets for different display densities

## **Inputs and Outputs**
**Inputs:**
- Original artwork and design files (likely processed externally)
- Brand guidelines and visual identity specifications
- Application requirements for specific icon sizes and formats
- User interface design specifications from development teams

**Outputs:**
- PNG image files in various resolutions (64x64, 128x128, and larger formats)
- Application icons embedded in executables and installers
- Graphics referenced by Qt resource files (.qrc) and CMake build systems
- Web-ready images for documentation and promotional websites
- Print-ready graphics for academic papers and presentations

## **Interactions with other components**
**Direct Integration Points:**
- **`ElmerGUI`**: Uses logo images in application interface, about dialogs, and splash screens
- **`ElmerGUIlogger`**: References icons through Qt resource system for branding consistency
- **`ElmerGUItester`**: May use reference images for visual validation testing
- **`post/`**: ElmerPost application incorporates logos and icons for professional presentation

**Build System Integration:**
- **CMake build files**: Reference pics directory for resource compilation and installation
- **Qt resource files (.qrc)**: Include images from pics directory for application embedding
- **Installation packages**: Copy appropriate logos and icons to system directories
- **Desktop integration**: Provides icons for application launchers and file associations

**Documentation Integration:**
- **README files**: Reference demonstration images to showcase capabilities
- **User manuals**: Include screenshots and promotional images from pics directory
- **Academic publications**: Utilize demonstration images to illustrate simulation results
- **Web documentation**: Display logos and example images on project websites

**Cross-Platform Considerations:**
- **Windows**: Provides .ico format icons for Windows executable resources
- **Linux**: Supplies PNG icons for desktop environment integration
- **macOS**: Offers appropriate resolution images for Retina display support
- **Web platforms**: Optimized images for online documentation and presentations

## **Example Files/Code Snippets (if applicable)**
**Qt Resource File Integration:**
```xml
<!-- ElmerGUI.qrc example -->
<RCC>
    <qresource prefix="/icons">
        <file>../pics/ElmerLogoPlain64x64.png</file>
        <file>../pics/Elmerlogo.png</file>
    </qresource>
</RCC>
```

**CMake Installation Example:**
```cmake
# Install application icons
install(FILES
    pics/ElmerLogoPlain64x64.png
    pics/ElmerLogoPlain128x128.png
    DESTINATION share/pixmaps
)
```

**Application Integration Pattern:**
```cpp
// Loading application icon in Qt application
QApplication app(argc, argv);
app.setWindowIcon(QIcon(":/icons/ElmerLogoPlain64x64.png"));
```

**Typical Usage Scenarios:**
1. **Application Branding**: Desktop applications load appropriate logos for window decorations
2. **About Dialogs**: Applications display official Elmer logos in help/about sections
3. **Splash Screens**: Loading screens show professional branding during application startup
4. **Documentation**: Manuals and websites reference demonstration images to illustrate capabilities
5. **Academic Presentations**: Researchers use official logos and demonstration images in publications

**Asset Management Best Practices:**
- Multiple resolution versions ensure optimal display on different devices
- Consistent naming convention facilitates easy integration across applications
- PNG format provides high quality with transparency support
- Demonstration images showcase real-world application capabilities 