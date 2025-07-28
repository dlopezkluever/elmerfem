import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { simulationApi } from '../api';
import { SimulationStatus, JobStatus } from '../types/api';
import { useSimulationProgress } from '../hooks/useSimulationProgress';
import { WebSocketConnectionState } from '../types/websocket';

function ProgressPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [cancelling, setCancelling] = useState(false);
  const [initialStatus, setInitialStatus] = useState<SimulationStatus | null>(null);
  const [initialError, setInitialError] = useState<string | null>(null);

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
      // Navigate to results after a short delay
      setTimeout(() => {
        navigate(`/result/${id}`);
      }, 1500);
    },
    onError: (err) => {
      console.error('Simulation error:', err);
    }
  });

  // Fetch initial status
  useEffect(() => {
    if (!id) return;

    const fetchInitialStatus = async () => {
      try {
        const response = await simulationApi.getSimulationStatus(id);
        setInitialStatus(response.data);
      } catch (err) {
        setInitialError('Failed to load simulation status');
      }
    };

    fetchInitialStatus();
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

  const handleRetryConnection = () => {
    reconnect();
  };

  const getConnectionStatusIcon = () => {
    switch (connectionState) {
      case WebSocketConnectionState.CONNECTED:
        return <span className="text-success">●</span>;
      case WebSocketConnectionState.CONNECTING:
      case WebSocketConnectionState.RECONNECTING:
        return <span className="text-warning animate-pulse">●</span>;
      default:
        return <span className="text-error">●</span>;
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

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="card-neumorphic p-8 mb-6">
        <h1 className="text-3xl font-bold mb-2">Simulation Progress</h1>
        <p className="text-gray-600">Simulation ID: {id}</p>
      </div>

      {/* Connection Status */}
      <div className="card-neumorphic p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold">Connection Status</span>
            {getConnectionStatusIcon()}
            <span className="text-sm text-gray-600">
              {connectionState.replace('_', ' ').toLowerCase()}
            </span>
          </div>
          {connectionState === WebSocketConnectionState.ERROR && (
            <button
              onClick={handleRetryConnection}
              className="btn-neumorphic-primary text-sm"
            >
              Retry Connection
            </button>
          )}
        </div>
      </div>

      {/* Main Progress Section */}
      <div className="card-neumorphic p-8 mb-6">
        <h2 className="text-2xl font-semibold mb-6">
          Status: {currentMessage || status || initialStatus?.status || 'Starting simulation...'}
        </h2>
        
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{progressPercentage}%</span>
          </div>
          <div className="progress-neumorphic">
            <div 
              className="progress-bar"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Error Display */}
        {(error || initialError) && (
          <div className="bg-error/10 border border-error/20 rounded-xl p-4 mb-6">
            <p className="text-error font-semibold mb-1">Error</p>
            <p className="text-sm">{error || initialError}</p>
          </div>
        )}

        {/* Progress Messages */}
        {progressMessages.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-lg font-semibold mb-3">Activity Log</h3>
            <div className="bg-neumorphic-bg rounded-xl shadow-neumorphic-inset p-4 max-h-64 overflow-y-auto">
              {progressMessages.map((msg, index) => (
                <div key={index} className="text-sm text-gray-700 py-1">
                  {msg}
                </div>
              ))}
            </div>
          </div>
        )}
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
                  onClick={handleRetryConnection}
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

export default ProgressPage; 