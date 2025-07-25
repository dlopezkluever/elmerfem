import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { simulationApi, downloadFileHelper } from '../api';
import { SimulationResult, SimulationStatus } from '../types/api';
import { useRecentSimulations } from '../hooks/useRecentSimulations';

function ResultPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const { updateSimulation } = useRecentSimulations();

  useEffect(() => {
    if (!id) {
      navigate('/');
      return;
    }

    fetchResults();
  }, [id, navigate]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch both result and status
      const [resultData, statusData] = await Promise.all([
        simulationApi.getSimulationResult(id!),
        simulationApi.getSimulationStatus(id!),
      ]);

      setResult(resultData);
      setStatus(statusData);

      // Update recent simulations
      updateSimulation(statusData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (filename: string, suggestedName: string) => {
    if (!id) return;

    try {
      setDownloading(filename);
      await downloadFileHelper(id, filename, suggestedName);
    } catch (err) {
      alert(`Failed to download ${filename}: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setDownloading(null);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card-neumorphic">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-300 rounded mb-4"></div>
            <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-300 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !result || !status) {
    return (
      <div className="max-w-2xl mx-auto text-center">
        <div className="card-neumorphic">
          <h1 className="text-3xl font-bold mb-4 text-red-600">Error</h1>
          <p className="text-lg mb-6">{error || 'Failed to load results'}</p>
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

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Simulation Results</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Summary Section */}
        <div className="card-neumorphic">
          <h2 className="text-2xl font-bold mb-4">Summary</h2>
          <dl className="space-y-2">
            <div className="flex justify-between">
              <dt className="text-gray-600">Simulation ID:</dt>
              <dd className="font-mono text-sm">{result.id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Status:</dt>
              <dd className="font-semibold text-green-600">
                {result.status.toUpperCase()}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Created:</dt>
              <dd>{new Date(status.created_at).toLocaleString()}</dd>
            </div>
            {status.completed_at && (
              <div className="flex justify-between">
                <dt className="text-gray-600">Completed:</dt>
                <dd>{new Date(status.completed_at).toLocaleString()}</dd>
              </div>
            )}
            <div className="flex justify-between">
              <dt className="text-gray-600">Duration:</dt>
              <dd>{calculateDuration(status.created_at, status.completed_at)}</dd>
            </div>
          </dl>
        </div>

        {/* Download Options */}
        <div className="card-neumorphic">
          <h2 className="text-2xl font-bold mb-4">Download Options</h2>
          <div className="space-y-3">
            {result.sif_file && (
              <DownloadButton
                label="Input File (SIF)"
                filename={result.sif_file}
                suggestedName={`simulation_${result.id}.sif`}
                onClick={handleDownload}
                downloading={downloading === result.sif_file}
              />
            )}
            {result.vtk_file && (
              <DownloadButton
                label="Results (VTU)"
                filename={result.vtk_file}
                suggestedName={`results_${result.id}.vtu`}
                onClick={handleDownload}
                downloading={downloading === result.vtk_file}
              />
            )}
            {result.log_file && (
              <DownloadButton
                label="Simulation Log"
                filename={result.log_file}
                suggestedName={`log_${result.id}.txt`}
                onClick={handleDownload}
                downloading={downloading === result.log_file}
              />
            )}
            <DownloadButton
              label="Full Report (PDF)"
              filename="report.pdf"
              suggestedName={`report_${result.id}.pdf`}
              onClick={handleDownload}
              downloading={downloading === 'report.pdf'}
              disabled={true}
              comingSoon={true}
            />
          </div>
        </div>
      </div>

      {/* Visualization Section */}
      <div className="card-neumorphic mb-8">
        <h2 className="text-2xl font-bold mb-4">3D Visualization</h2>
        <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center text-gray-500">
          <div className="text-center">
            <p className="text-xl mb-2">3D Visualization Coming Soon</p>
            <p className="text-sm">
              Interactive 3D results will be displayed here
            </p>
          </div>
        </div>
      </div>

      {/* Result Files List */}
      {result.result_files && result.result_files.length > 0 && (
        <div className="card-neumorphic mb-8">
          <h2 className="text-2xl font-bold mb-4">Additional Files</h2>
          <ul className="space-y-2">
            {result.result_files.map((file, index) => (
              <li key={index} className="flex items-center justify-between p-2 hover:bg-gray-100 rounded">
                <span className="font-mono text-sm">{file}</span>
                <button
                  onClick={() => handleDownload(file, file)}
                  disabled={downloading === file}
                  className="text-blue-600 hover:text-blue-700 text-sm"
                >
                  {downloading === file ? 'Downloading...' : 'Download'}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={() => navigate('/')}
          className="btn-neumorphic-primary px-8 py-4 text-lg"
        >
          Run New Simulation
        </button>
        <button
          onClick={() => window.location.reload()}
          className="btn-neumorphic px-8 py-4 text-lg"
        >
          Refresh Results
        </button>
      </div>
    </div>
  );
}

interface DownloadButtonProps {
  label: string;
  filename: string;
  suggestedName: string;
  onClick: (filename: string, suggestedName: string) => void;
  downloading: boolean;
  disabled?: boolean;
  comingSoon?: boolean;
}

function DownloadButton({
  label,
  filename,
  suggestedName,
  onClick,
  downloading,
  disabled = false,
  comingSoon = false,
}: DownloadButtonProps) {
  return (
    <button
      onClick={() => onClick(filename, suggestedName)}
      disabled={disabled || downloading}
      className={`
        w-full text-left p-3 rounded-lg transition-all duration-200
        ${disabled 
          ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
          : 'bg-white hover:shadow-neumorphic-hover active:shadow-neumorphic-inset'
        }
      `}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium">{label}</span>
        <span className="text-sm text-gray-500">
          {downloading ? 'Downloading...' : comingSoon ? 'Coming Soon' : 'Download'}
        </span>
      </div>
    </button>
  );
}

function calculateDuration(start: string, end?: string): string {
  if (!end) return 'N/A';
  
  const startTime = new Date(start).getTime();
  const endTime = new Date(end).getTime();
  const duration = endTime - startTime;
  
  const seconds = Math.floor(duration / 1000);
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

export default ResultPage;