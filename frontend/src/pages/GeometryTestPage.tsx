import React, { useState } from 'react';
import { Provider } from 'react-redux';
import { store } from '../store';
import { GeometrySetup } from '../components/simulation/GeometrySetup';
import { GeometrySetupConnected } from '../components/simulation/GeometrySetupConnected';
import { EducationalMeshParams } from '../types/geometry';

/**
 * Test page for demonstrating geometry setup components.
 * Shows both standalone and Redux-connected versions.
 */
export const GeometryTestPage: React.FC = () => {
  const [meshParams, setMeshParams] = useState<EducationalMeshParams | null>(null);
  const [showConnected, setShowConnected] = useState(false);

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          Educational Mesh Generator - Geometry Setup
        </h1>
        <p className="text-lg text-gray-600 mb-6">
          This page demonstrates the geometry setup interface for the educational mesh generator.
          Switch between standalone and Redux-connected versions to see both implementations.
        </p>

        {/* Version Toggle */}
        <div className="flex items-center space-x-4 mb-8">
          <button
            onClick={() => setShowConnected(false)}
            className={`btn-neumorphic px-6 py-3 font-medium transition-all duration-200 ${
              !showConnected
                ? 'shadow-neumorphic-inset text-primary'
                : 'hover:shadow-neumorphic-hover'
            }`}
          >
            Standalone Version
          </button>
          <button
            onClick={() => setShowConnected(true)}
            className={`btn-neumorphic px-6 py-3 font-medium transition-all duration-200 ${
              showConnected
                ? 'shadow-neumorphic-inset text-primary'
                : 'hover:shadow-neumorphic-hover'
            }`}
          >
            Redux-Connected Version
          </button>
        </div>
      </div>

      {/* Component Display */}
      {showConnected ? (
        <Provider store={store}>
          <div>
            <div className="card-neumorphic mb-6">
              <p className="font-semibold text-gray-800">Redux-Connected Version</p>
              <p className="text-sm text-gray-600 mt-1">
                This version uses Redux Toolkit for state management. All state is stored in the Redux store.
              </p>
            </div>
            <GeometrySetupConnected />
          </div>
        </Provider>
      ) : (
        <div>
          <div className="card-neumorphic mb-6">
            <p className="font-semibold text-gray-800">Standalone Version</p>
            <p className="text-sm text-gray-600 mt-1">
              This version uses local React state. It can accept an onGeometryChange callback.
            </p>
          </div>
          <GeometrySetup onGeometryChange={setMeshParams} />
        </div>
      )}

      {/* Current Mesh Parameters Display (Standalone only) */}
      {!showConnected && meshParams && (
        <div className="mt-8 card-neumorphic">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Current Mesh Parameters</h2>
          <pre className="bg-neumorphic-bg shadow-neumorphic-inset p-4 rounded-xl overflow-x-auto text-sm">
            {JSON.stringify(meshParams, null, 2)}
          </pre>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-8 card-neumorphic">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Instructions</h2>
        <ul className="list-disc list-inside space-y-2 text-gray-700">
          <li>Select a geometry type from the available options (Rectangle, Circle, Annulus, L-Shape)</li>
          <li>Enter the geometry parameters - the form will validate inputs in real-time</li>
          <li>Choose a mesh density level based on your accuracy requirements</li>
          <li>Optionally enable boundary layer for fluid/heat transfer simulations</li>
          <li>The preview shows your geometry with an estimated mesh representation</li>
          <li>Estimated element count helps you understand computational requirements</li>
        </ul>
      </div>

      {/* Feature Summary */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card-neumorphic">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">
            Real-Time Validation
          </h3>
          <p className="text-gray-600 text-sm">
            Parameters are validated as you type, with clear error messages for invalid inputs.
          </p>
        </div>

        <div className="card-neumorphic">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">
            Visual Preview
          </h3>
          <p className="text-gray-600 text-sm">
            See your geometry and mesh density in real-time with an interactive SVG preview.
          </p>
        </div>

        <div className="card-neumorphic">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">
            Educational Tips
          </h3>
          <p className="text-gray-600 text-sm">
            Context-sensitive tips help students understand the best use cases for each geometry.
          </p>
        </div>

        <div className="card-neumorphic">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">
            Responsive Design
          </h3>
          <p className="text-gray-600 text-sm">
            The interface adapts to different screen sizes, from mobile to desktop.
          </p>
        </div>

        <div className="card-neumorphic">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">
            Redux Integration
          </h3>
          <p className="text-gray-600 text-sm">
            State management with Redux Toolkit enables seamless integration with other components.
          </p>
        </div>

        <div className="card-neumorphic">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">
            Performance
          </h3>
          <p className="text-gray-600 text-sm">
            Optimized rendering and validation ensure smooth interaction even with frequent updates.
          </p>
        </div>
      </div>
    </div>
  );
}; 