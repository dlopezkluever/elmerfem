import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { simulationApi } from '../api';
import { SimulationStatus, JobStatus } from '../types/api';

function ProgressPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    if (!id) {
      navigate('/');
      return;
    }

    // Poll for status updates
    const pollInterval = setInterval(async () => {
      try {
        const result = await simulationApi.getSimulationStatus(id);
        setStatus(result);

        // Navigate to results if completed
        if (result.status === JobStatus.COMPLETED) {
          clearInterval(pollInterval);
          navigate(`/result/${id}`);
        } else if (result.status === JobStatus.FAILED) {
          clearInterval(pollInterval);
          setError(result.error_message || 'Simulation failed');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get status');
      }
    }, 3000); // Poll every 3 seconds

    // Initial fetch
    simulationApi.getSimulationStatus(id)
      .then(setStatus)
      .catch(err => setError(err instanceof Error ? err.message : 'Failed to get status'));

    return () => clearInterval(pollInterval);
  }, [id, navigate]);

  const handleCancel = async () => {
    if (!id || cancelling) return;
    
    try {
      setCancelling(true);
      await simulationApi.cancelSimulation(id);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel simulation');
    } finally {
      setCancelling(false);
    }
  };

  if (error) {
    return (
      <div className="max-w-2xl mx-auto text-center">
        <div className="card-neumorphic">
          <h1 className="text-3xl font-bold mb-4 text-red-600">Error</h1>
          <p className="text-lg mb-6">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="btn-neumorphic-primary"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="max-w-2xl mx-auto text-center">
        <div className="card-neumorphic">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-300 rounded mb-4"></div>
            <div className="h-4 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const getStatusColor = () => {
    switch (status.status) {
      case JobStatus.PENDING:
        return 'text-yellow-600';
      case JobStatus.RUNNING:
        return 'text-blue-600';
      case JobStatus.COMPLETED:
        return 'text-green-600';
      case JobStatus.FAILED:
        return 'text-red-600';
      case JobStatus.CANCELLED:
        return 'text-gray-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusMessage = () => {
    switch (status.status) {
      case JobStatus.PENDING:
        return 'Preparing simulation...';
      case JobStatus.RUNNING:
        return status.current_step || 'Running simulation...';
      case JobStatus.COMPLETED:
        return 'Simulation completed!';
      case JobStatus.FAILED:
        return 'Simulation failed';
      case JobStatus.CANCELLED:
        return 'Simulation cancelled';
      default:
        return 'Unknown status';
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Simulation Progress</h1>

      <div className="card-neumorphic mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Status</h2>
          <span className={`text-xl font-semibold ${getStatusColor()}`}>
            {status.status.toUpperCase()}
          </span>
        </div>

        <div className="space-y-4">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>{getStatusMessage()}</span>
              <span>{Math.round(status.progress)}%</span>
            </div>
            <div className="progress-neumorphic">
              <div
                className="progress-bar"
                style={{ width: `${status.progress}%` }}
              />
            </div>
          </div>

          {/* Steps Information */}
          {status.current_step && (
            <div className="bg-gray-100 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-700">Current Step:</p>
              <p className="text-lg">{status.current_step}</p>
              {status.total_steps && (
                <p className="text-sm text-gray-600 mt-1">
                  Step {Math.ceil(status.progress / (100 / status.total_steps))} of {status.total_steps}
                </p>
              )}
            </div>
          )}

          {/* Time Information */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Started:</p>
              <p className="font-medium">
                {status.started_at 
                  ? new Date(status.started_at).toLocaleTimeString()
                  : 'Not started'}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Elapsed Time:</p>
              <p className="font-medium">
                {status.started_at
                  ? formatElapsedTime(new Date(status.started_at))
                  : 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={handleCancel}
          disabled={cancelling || status.status !== JobStatus.RUNNING}
          className="btn-neumorphic text-red-600 hover:text-red-700"
        >
          {cancelling ? 'Cancelling...' : 'Cancel Simulation'}
        </button>
      </div>
    </div>
  );
}

function formatElapsedTime(startTime: Date): string {
  const elapsed = Date.now() - startTime.getTime();
  const seconds = Math.floor(elapsed / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

export default ProgressPage; 