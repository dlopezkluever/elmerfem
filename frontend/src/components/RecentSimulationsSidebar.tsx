import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRecentSimulations } from '../hooks/useRecentSimulations';

interface RecentSimulationsSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

function RecentSimulationsSidebar({ isOpen, onClose }: RecentSimulationsSidebarProps) {
  const navigate = useNavigate();
  const { recentSimulations, removeSimulation, clearAll } = useRecentSimulations();
  const [confirmClear, setConfirmClear] = useState(false);

  const handleSimulationClick = (id: string) => {
    navigate(`/result/${id}`);
    onClose();
  };

  const handleClearAll = () => {
    if (confirmClear) {
      clearAll();
      setConfirmClear(false);
    } else {
      setConfirmClear(true);
      setTimeout(() => setConfirmClear(false), 3000);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'running':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed right-0 top-0 h-full w-96 bg-neumorphic-bg shadow-neumorphic-hover
        transform transition-transform duration-300 z-50
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}
      `}>
        <div className="p-6 h-full flex flex-col">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Recent Simulations</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-200 transition-colors"
              aria-label="Close sidebar"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Simulations List */}
          <div className="flex-1 overflow-y-auto">
            {recentSimulations.length === 0 ? (
              <div className="text-center text-gray-500 mt-8">
                <p className="text-lg mb-2">No recent simulations</p>
                <p className="text-sm">Your simulation history will appear here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentSimulations.map((sim) => (
                  <div
                    key={sim.id}
                    className="card-neumorphic p-4 cursor-pointer hover:shadow-neumorphic-hover transition-all"
                    onClick={() => handleSimulationClick(sim.id)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold">{sim.type}</h3>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeSimulation(sim.id);
                        }}
                        className="text-gray-400 hover:text-red-600 transition-colors"
                        aria-label="Remove simulation"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    <div className="text-sm text-gray-600 space-y-1">
                      <p>Status: <span className={`font-medium ${getStatusColor(sim.status)}`}>{sim.status}</span></p>
                      <p>Created: {new Date(sim.createdAt).toLocaleString()}</p>
                      {sim.completedAt && (
                        <p>Completed: {new Date(sim.completedAt).toLocaleString()}</p>
                      )}
                      {sim.summary && (
                        <p className="mt-2 text-xs">{sim.summary}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer Actions */}
          {recentSimulations.length > 0 && (
            <div className="pt-4 border-t border-gray-300">
              <button
                onClick={handleClearAll}
                className={`w-full py-2 rounded-lg transition-all ${
                  confirmClear
                    ? 'bg-red-500 text-white hover:bg-red-600'
                    : 'bg-gray-200 hover:bg-gray-300'
                }`}
              >
                {confirmClear ? 'Click again to confirm' : 'Clear All'}
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default RecentSimulationsSidebar; 