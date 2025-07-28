import React, { useState } from 'react';
import { useSimulationProgress } from '../hooks/useSimulationProgress';
import { WebSocketConnectionState } from '../types/websocket';

export function WebSocketTest() {
  const [simulationId, setSimulationId] = useState('');
  const [testId, setTestId] = useState('');

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
    simulationId: testId,
    onComplete: () => {
      console.log('Simulation completed!');
    },
    onError: (err) => {
      console.error('Simulation error:', err);
    }
  });

  const handleConnect = () => {
    if (simulationId) {
      setTestId(simulationId);
    }
  };

  const handleDisconnect = () => {
    disconnect();
    setTestId('');
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4">WebSocket Test</h2>
      
      <div className="mb-4">
        <input
          type="text"
          placeholder="Enter Simulation ID"
          value={simulationId}
          onChange={(e) => setSimulationId(e.target.value)}
          className="input input-bordered w-full max-w-xs mr-2"
        />
        <button 
          onClick={handleConnect} 
          className="btn btn-primary mr-2"
          disabled={!simulationId || testId !== ''}
        >
          Connect
        </button>
        <button 
          onClick={handleDisconnect} 
          className="btn btn-secondary mr-2"
          disabled={testId === ''}
        >
          Disconnect
        </button>
        <button 
          onClick={reconnect} 
          className="btn btn-info"
          disabled={testId === '' || connectionState === WebSocketConnectionState.CONNECTED}
        >
          Reconnect
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h3 className="card-title">Connection Status</h3>
            <p>State: {connectionState}</p>
            <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
            <p>Simulation ID: {testId || 'None'}</p>
          </div>
        </div>

        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h3 className="card-title">Simulation Status</h3>
            <p>Status: {status || 'N/A'}</p>
            <p>Progress: {progress}%</p>
            <p>Current: {currentMessage || 'N/A'}</p>
            {error && <p className="text-error">Error: {error}</p>}
          </div>
        </div>
      </div>

      <div className="card bg-base-100 shadow-xl mt-4">
        <div className="card-body">
          <h3 className="card-title">Progress Messages</h3>
          <div className="max-h-64 overflow-y-auto">
            {progressMessages.length === 0 ? (
              <p className="text-gray-500">No messages yet...</p>
            ) : (
              <ul className="text-sm">
                {progressMessages.map((msg, idx) => (
                  <li key={idx} className="py-1 border-b">{msg}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 