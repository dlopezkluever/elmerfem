import React, { useState } from 'react';
import { MeshPreview } from '../components/mesh';

/**
 * Test page for demonstrating the WebGL mesh preview functionality.
 * Shows the completed implementation of Task 25 with all subtasks.
 */
export const MeshPreviewTestPage: React.FC = () => {
  const [showHeatMap, setShowHeatMap] = useState(false);
  const [meshId, setMeshId] = useState<string>('test-mesh-123');
  const [useMockData, setUseMockData] = useState(true);
  const [autoRotate, setAutoRotate] = useState(true);

  // Sample quality metrics for testing
  const sampleQualityMetrics = {
    total_nodes: 1234,
    total_elements: 2345,
    min_angle: 45.2,
    max_angle: 89.8,
    aspect_ratio_avg: 1.2,
    aspect_ratio_max: 1.8,
    aspect_ratios: Array.from({ length: 100 }, () => Math.random() * 0.8 + 1.0),
    element_quality: Array.from({ length: 100 }, () => Math.random() * 0.5 + 0.5)
  };

  return (
    <div className="min-h-screen bg-neumorphic-bg p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-electric-blue mb-8">
          WebGL Mesh Preview Test
        </h1>
        
        {/* Control Panel */}
        <div className="bg-neumorphic-bg shadow-neumorphic p-6 rounded-2xl mb-8">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Test Controls</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Mock Data Toggle */}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="mockData"
                checked={useMockData}
                onChange={(e) => setUseMockData(e.target.checked)}
                className="w-4 h-4 text-electric-blue rounded"
              />
              <label htmlFor="mockData" className="text-gray-700">
                Use Mock Data
              </label>
            </div>

            {/* Heat Map Toggle */}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="heatMap"
                checked={showHeatMap}
                onChange={(e) => setShowHeatMap(e.target.checked)}
                className="w-4 h-4 text-electric-blue rounded"
              />
              <label htmlFor="heatMap" className="text-gray-700">
                Show Heat Map
              </label>
            </div>

            {/* Auto Rotate Toggle */}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoRotate"
                checked={autoRotate}
                onChange={(e) => setAutoRotate(e.target.checked)}
                className="w-4 h-4 text-electric-blue rounded"
              />
              <label htmlFor="autoRotate" className="text-gray-700">
                Auto Rotate
              </label>
            </div>

            {/* Mesh ID Input */}
            <div className="flex items-center space-x-2">
              <label htmlFor="meshId" className="text-gray-700">
                Mesh ID:
              </label>
              <input
                type="text"
                id="meshId"
                value={meshId}
                onChange={(e) => setMeshId(e.target.value)}
                className="px-3 py-1 bg-neumorphic-bg shadow-neumorphic-inset rounded"
                disabled={useMockData}
              />
            </div>
          </div>

          {useMockData && (
            <div className="mt-4 p-4 bg-success-green bg-opacity-20 rounded-lg">
              <p className="text-sm text-gray-700">
                Using mock data: A wavy surface mesh is being displayed for testing purposes.
              </p>
            </div>
          )}
        </div>

        {/* Mesh Preview */}
        <div className="bg-neumorphic-bg shadow-neumorphic p-6 rounded-2xl">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Mesh Visualization</h2>
          
          <div className="h-[600px]">
            <MeshPreview
              meshId={meshId}
              qualityMetrics={sampleQualityMetrics}
              showHeatMap={showHeatMap}
              autoRotate={autoRotate}
              useMockData={useMockData}
            />
          </div>
        </div>

        {/* Testing Instructions */}
        <div className="mt-8 bg-neumorphic-bg shadow-neumorphic p-6 rounded-2xl">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Testing Instructions</h2>
          
          <div className="space-y-2 text-gray-600">
            <p>
              <strong>Mouse Controls:</strong>
            </p>
            <ul className="list-disc list-inside ml-4">
              <li>Left Click + Drag: Rotate the view</li>
              <li>Right Click + Drag: Pan the view</li>
              <li>Scroll: Zoom in/out</li>
            </ul>
            
            <p className="mt-4">
              <strong>Heat Map Visualization:</strong>
            </p>
            <ul className="list-disc list-inside ml-4">
              <li>Toggle "Show Heat Map" to visualize mesh quality</li>
              <li>Use dat.GUI controls (top right) to adjust visualization settings</li>
              <li>Choose between aspect ratio and element quality metrics</li>
              <li>Select different color scales: rainbow, thermal, or grayscale</li>
            </ul>
            
            <p className="mt-4">
              <strong>Testing Options:</strong>
            </p>
            <ul className="list-disc list-inside ml-4">
              <li>Mock Data: Uses a generated wavy surface mesh for testing</li>
              <li>Real Data: Disable mock data and enter a valid mesh ID from the backend</li>
              <li>Auto Rotate: Toggles automatic rotation of the mesh</li>
            </ul>
          </div>
        </div>

        {/* Educational Content: Understanding Meshes in FEA */}
        <div className="mt-8 bg-neumorphic-bg shadow-neumorphic p-6 rounded-2xl">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Understanding Meshes in Finite Element Analysis</h2>
          
          <div className="space-y-4 text-gray-600">
            <div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">What is a Mesh?</h3>
              <p>
                A mesh is a collection of vertices, edges, and faces that defines the shape of a 3D object 
                in computational modeling. In Finite Element Analysis (FEA), complex geometries are divided 
                into smaller, simpler elements (triangles, quadrilaterals, tetrahedra, or hexahedra) that 
                can be mathematically analyzed.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Why are Meshes Important?</h3>
              <p>
                The quality and density of a mesh directly impacts the accuracy of FEA results. A well-constructed 
                mesh ensures that:
              </p>
              <ul className="list-disc list-inside ml-4 mt-2">
                <li>Physical phenomena are accurately captured</li>
                <li>Computational resources are used efficiently</li>
                <li>Numerical errors are minimized</li>
                <li>Convergence to the correct solution is achieved</li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Key Mesh Quality Metrics</h3>
              <div className="bg-gray-100 p-4 rounded-lg mt-2">
                <p className="mb-2"><strong>Aspect Ratio:</strong> The ratio of the longest to shortest side of an element. 
                Ideal value is 1.0 (perfectly regular shape). High aspect ratios (&gt;3) can lead to numerical instability.</p>
                
                <p className="mb-2"><strong>Minimum/Maximum Angles:</strong> For triangular elements, angles should ideally 
                be close to 60°. For quadrilaterals, close to 90°. Extreme angles (&lt;30° or &gt;120°) reduce solution accuracy.</p>
                
                <p><strong>Element Quality:</strong> A composite measure combining multiple metrics to assess overall 
                element shape quality. Values range from 0 (poor) to 1 (excellent).</p>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Mesh Density and the h-p Method</h3>
              <p>
                The accuracy of FEA solutions can be improved through two primary approaches:
              </p>
              <ul className="list-disc list-inside ml-4 mt-2">
                <li><strong>h-refinement:</strong> Decreasing element size (h) to increase mesh density</li>
                <li><strong>p-refinement:</strong> Increasing the polynomial order (p) of shape functions</li>
              </ul>
              <p className="mt-2">
                The convergence rate follows the relationship: ||e|| ≤ Ch^p, where e is the error, 
                C is a constant, h is the element size, and p is the polynomial order.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Heat Map Visualization</h3>
              <p>
                The heat map overlay provides a visual representation of mesh quality metrics across the entire mesh:
              </p>
              <ul className="list-disc list-inside ml-4 mt-2">
                <li><strong>Red/Orange regions:</strong> Poor quality elements requiring attention</li>
                <li><strong>Yellow regions:</strong> Acceptable quality elements</li>
                <li><strong>Green/Blue regions:</strong> High quality elements</li>
              </ul>
              <p className="mt-2">
                This visualization helps identify areas where mesh refinement may be needed to improve 
                simulation accuracy, particularly in regions with high stress gradients or complex geometry.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Mathematical Foundation</h3>
              <p>
                The finite element method approximates the solution u(x) as:
              </p>
              <div className="bg-gray-100 p-4 rounded-lg mt-2 font-mono">
                u(x) ≈ u_h(x) = Σᵢ uᵢ φᵢ(x)
              </div>
              <p className="mt-2">
                where uᵢ are nodal values and φᵢ(x) are shape functions defined over each element. 
                The quality of this approximation depends critically on the mesh characteristics.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}; 