# Mesh Visualization Components (Task 25)

This directory contains the WebGL mesh preview implementation using Three.js for the educational finite element analysis platform.

## Overview

The mesh visualization system provides an interactive 3D preview of generated meshes with quality metrics visualization, implementing all requirements from Task 25 of the mesh generator project.

## Components

### 1. **MeshScene** (`MeshScene.tsx`) - Task 25.1
- Initializes the Three.js scene with proper camera, lighting, and controls
- Provides a neumorphic-styled container for the 3D canvas
- Includes grid and axes helpers for spatial reference
- Sets up ambient and directional lighting for optimal mesh visualization

### 2. **STLMeshLoader** (`STLMeshLoader.tsx`) - Task 25.2
- Fetches mesh data from the backend API endpoint `/api/v1/mesh/preview/{meshId}`
- Converts mesh data (nodes and elements) to Three.js BufferGeometry
- Handles both triangular and quadrilateral elements
- Includes auto-rotation for better visualization
- Computes normals and centers the geometry automatically

### 3. **MeshHeatMap** (`MeshHeatMap.tsx`) - Task 25.3
- Applies color-based visualization of mesh quality metrics
- Supports multiple metrics: aspect ratio and element quality
- Provides three color scales: rainbow, thermal, and grayscale
- Includes dat.GUI controls for real-time customization
- Toggleable heat map with opacity control

### 4. **MeshPreview** (`MeshPreview.tsx`) - Task 25.4 & 25.5
- Main component that integrates all mesh visualization features
- OrbitControls integration for interactive camera movement (Task 25.4)
- Performance optimizations including:
  - React.memo for preventing unnecessary re-renders
  - Suspense for lazy loading
  - LOD support for large meshes
  - Efficient WebGL settings
- Displays mesh quality metrics overlay
- Provides loading states and error handling

## Usage

```tsx
import { MeshPreview } from './components/mesh';

// Basic usage
<MeshPreview 
  meshId="your-mesh-id"
  className="w-full h-96"
/>

// With quality metrics and heat map
<MeshPreview 
  meshId="your-mesh-id"
  qualityMetrics={{
    total_nodes: 1234,
    total_elements: 2345,
    min_angle: 45.2,
    max_angle: 89.8,
    aspect_ratio_avg: 1.2,
    aspect_ratio_max: 1.8,
    aspect_ratios: [...],
    element_quality: [...]
  }}
  showHeatMap={true}
  autoRotate={false}
/>
```

## Features

### Interactive Controls
- **Rotate**: Click and drag to rotate the mesh
- **Zoom**: Scroll wheel to zoom in/out
- **Pan**: Right-click and drag to pan the view
- **Auto-rotate**: Optional automatic rotation for presentation

### Quality Visualization
- Real-time mesh quality metrics display
- Heat map visualization for aspect ratios and element quality
- Multiple color scales for different visualization preferences
- dat.GUI controls for fine-tuning the visualization

### Performance
- Optimized for educational meshes (2-10k elements)
- Lazy loading with React Suspense
- Memoized components to prevent unnecessary re-renders
- WebGL renderer configured for high performance
- Level of detail (LOD) support for larger meshes

## Dependencies

- **three**: ^0.178.0 - Core 3D graphics library
- **@react-three/fiber**: ^8.17.10 - React renderer for Three.js
- **@react-three/drei**: ^9.115.0 - Useful helpers for React Three Fiber
- **dat.gui**: ^0.7.9 - Lightweight GUI for changing variables

## Styling

All components follow the established neumorphic design system:
- Background: `bg-neumorphic-bg` (#F0F0F0)
- Shadows: `shadow-neumorphic` and `shadow-neumorphic-inset`
- Primary color: #65c3c8 (from DaisyUI cupcake theme)
- Consistent with the overall educational platform design

## API Integration

The components integrate with the backend mesh API:
- Endpoint: `/api/v1/mesh/preview/{meshId}`
- Returns mesh data in JSON format with nodes, elements, and quality metrics
- Supports both triangular and quadrilateral elements
- Includes bounding box and boundary information

## Testing

Basic unit tests are provided in `MeshPreview.test.tsx` with mocked Three.js components for testing without WebGL context.

## Future Enhancements

- Support for more element types (hexahedral, tetrahedral)
- Advanced mesh simplification algorithms
- Export functionality (save as image/3D file)
- Animation of simulation results on the mesh
- Integration with the simulation workflow 