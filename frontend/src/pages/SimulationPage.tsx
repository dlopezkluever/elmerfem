import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { simulationApi } from '../api';
import { SimulationStatus, JobStatus, GeometryParams } from '../types/api';
import { useSimulationProgress } from '../hooks/useSimulationProgress';
import { WebSocketConnectionState } from '../types/websocket';
import { MeshPreview } from '../components/mesh';

/**
 * Unified Simulation Page combining progress tracking and mesh visualization.
 * Task 6 Implementation: Displays simulation progress and mesh preview in a single view.
 */
function SimulationPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [cancelling, setCancelling] = useState(false);
  const [initialStatus, setInitialStatus] = useState<SimulationStatus | null>(null);
  const [initialError, setInitialError] = useState<string | null>(null);
  const [geometry, setGeometry] = useState<GeometryParams | null>(null);
  const [showMeshOutline, setShowMeshOutline] = useState(true);

  // Use WebSocket hook for real-time progress
  const {
    isConnected,
    connectionState,
    status,
    progress,
    currentMessage,
    progressMessages,
    error,
    reconnect,
    disconnect
  } = useSimulationProgress({
    simulationId: id || '',
    onComplete: () => {
      // Progress is already at 100%, button will be enabled
    },
    onError: (err) => {
      console.error('Simulation error:', err);
    }
  });

  // Load initial data
  useEffect(() => {
    if (!id) return;

    const loadInitialData = async () => {
      try {
        // Only fetch simulation status - geometry comes from sessionStorage
        const statusResponse = await simulationApi.getSimulationStatus(id);
        setInitialStatus(statusResponse);
        
        // Get geometry from sessionStorage
        const storedGeometry = sessionStorage.getItem(`simulation_${id}_geometry`);
        if (storedGeometry) {
          try {
            const parsedGeometry = JSON.parse(storedGeometry);
            setGeometry(parsedGeometry);
          } catch (e) {
            console.warn('Failed to parse stored geometry:', e);
          }
        }
      } catch (err) {
        console.error('Error loading simulation data:', err);
        setInitialError('Failed to load simulation status');
      }
    };

    loadInitialData();
  }, [id]);

  const handleCancel = async () => {
    if (!id || cancelling) return;
    
    setCancelling(true);
    try {
      await simulationApi.cancelSimulation(id);
      disconnect();
      navigate('/');
    } catch (err) {
      console.error('Failed to cancel simulation:', err);
    } finally {
      setCancelling(false);
    }
  };

  const handleSeeResults = () => {
    if (progress === 100) {
      navigate(`/result/${id}`);
    }
  };

  const getProgressPercentage = () => {
    // If WebSocket is connected, use its progress
    if (isConnected && progress > 0) return progress;
    
    // Otherwise, estimate based on status
    switch (status || initialStatus?.status) {
      case JobStatus.PENDING:
        return 5;
      case JobStatus.RUNNING:
        return progress || 50;
      case JobStatus.COMPLETED:
        return 100;
      case JobStatus.FAILED:
      case JobStatus.CANCELLED:
        return 0;
      default:
        return 0;
    }
  };

  const progressPercentage = getProgressPercentage();

  // Get last 3 messages for compact display
  const recentMessages = progressMessages.slice(-3);

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      {/* Unified Progress Card */}
      <div className="card-neumorphic p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold">Simulation Progress</h1>
          <button
            onClick={handleSeeResults}
            disabled={progressPercentage !== 100}
            className={`btn-neumorphic-primary px-6 py-2 text-lg font-semibold ${
              progressPercentage !== 100 ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            See Results
          </button>
        </div>

        {/* Connection Status and ID */}
        <div className="flex items-center gap-4 mb-4 text-gray-600">
          <span>ID: {id}</span>
          <div className="flex items-center gap-2">
            <span className={`text-${
              connectionState === WebSocketConnectionState.CONNECTED ? 'success' : 
              connectionState === WebSocketConnectionState.ERROR ? 'error' : 'warning'
            }`}>●</span>
            <span className="text-sm">
              {connectionState.replace('_', ' ').toLowerCase()}
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>{currentMessage || status || initialStatus?.status || 'Starting simulation...'}</span>
            <span>{progressPercentage}%</span>
          </div>
          <div className="progress-neumorphic">
            <div 
              className="progress-bar"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Compact Activity Log */}
        {recentMessages.length > 0 && (
          <div className="bg-neumorphic-bg rounded-xl shadow-neumorphic-inset p-3">
            <div className="space-y-1 max-h-[4.5rem] overflow-y-auto">
              {recentMessages.map((msg, index) => (
                <div key={index} className="text-sm text-gray-700">
                  {msg}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error Display */}
        {(error || initialError) && (
          <div className="bg-error/10 border border-error/20 rounded-xl p-3 mt-4">
            <p className="text-error font-semibold text-sm">Error: {error || initialError}</p>
          </div>
        )}
      </div>

      {/* 3D Mesh Visualization */}
      <div className="card-neumorphic p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">3D Mesh Visualization</h2>
        
        <div className="h-[500px] mb-4">
          {geometry ? (
            <MeshPreview
              meshId={id}
              useMockData={false}
              geometry={geometry}
              showMeshOutline={showMeshOutline}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gray-100 rounded-lg">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading simulation geometry...</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mesh View Controls */}
      <div className="card-neumorphic p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Mesh View Controls</h2>
        
        <div className="flex items-center gap-6 mb-4">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="meshOutline"
              checked={showMeshOutline}
              onChange={(e) => setShowMeshOutline(e.target.checked)}
              className="w-4 h-4 text-electric-blue rounded"
            />
            <label htmlFor="meshOutline" className="text-gray-700">
              Mesh Outline
            </label>
          </div>
        </div>

        <div className="text-gray-600 text-sm flex flex-wrap gap-6">
          <span><strong>Left Click + Drag:</strong> Rotate</span>
          <span><strong>Right Click + Drag:</strong> Pan</span>
          <span><strong>Scroll:</strong> Zoom</span>
        </div>
      </div>

      {/* Educational Content */}
      <div className="card-neumorphic p-6 mb-6">
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

      {/* Action Buttons */}
      <div className="flex gap-4 justify-center">
        {status !== JobStatus.COMPLETED && status !== JobStatus.FAILED && (
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="btn-neumorphic px-8 py-3 text-error font-semibold"
          >
            {cancelling ? 'Cancelling...' : 'Cancel Simulation'}
          </button>
        )}
        
        {(status === JobStatus.FAILED || connectionState === WebSocketConnectionState.ERROR) && (
          <button
            onClick={() => navigate('/')}
            className="btn-neumorphic-primary px-8 py-3"
          >
            Back to Home
          </button>
        )}
      </div>

      {/* Connection Error Modal */}
      {connectionState === WebSocketConnectionState.ERROR && 
       !isConnected && 
       progressMessages.length === 0 && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="card-neumorphic p-8 max-w-md">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-4">Connection Error</h2>
              <p className="text-gray-600 mb-6">
                Failed to connect after multiple attempts
              </p>
              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => navigate('/')}
                  className="btn-neumorphic px-6 py-3"
                >
                  Back to Home
                </button>
                <button
                  onClick={reconnect}
                  className="btn-neumorphic-primary px-6 py-3"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Simulation Started Time */}
      <div className="text-center mt-6 text-sm text-gray-600">
        Simulation started at {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
}

export default SimulationPage; 