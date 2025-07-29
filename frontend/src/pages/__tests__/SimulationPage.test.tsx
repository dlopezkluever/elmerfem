import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import SimulationPage from '../SimulationPage';
import { simulationApi } from '../../api';
import { WebSocketConnectionState } from '../../types/websocket';
import { JobStatus } from '../../types/api';

// Mock modules
vi.mock('../../api');
vi.mock('../../hooks/useSimulationProgress');
vi.mock('../../components/mesh', () => ({
  MeshPreview: ({ meshId, showMeshOutline }: any) => (
    <div data-testid="mesh-preview">
      Mesh Preview for {meshId}
      {showMeshOutline && <span>Outline enabled</span>}
    </div>
  )
}));
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ id: 'test-sim-123' }),
    useNavigate: () => vi.fn()
  };
});

import { useSimulationProgress } from '../../hooks/useSimulationProgress';

const mockUseSimulationProgress = vi.mocked(useSimulationProgress);

describe('SimulationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock implementation
    mockUseSimulationProgress.mockReturnValue({
      isConnected: true,
      connectionState: WebSocketConnectionState.CONNECTED,
      status: JobStatus.RUNNING,
      progress: 50,
      currentMessage: 'Running simulation...',
      progressMessages: ['Starting...', 'Meshing...', 'Solving...'],
      error: null,
      reconnect: vi.fn(),
      disconnect: vi.fn()
    } as any);
    
    vi.mocked(simulationApi.getSimulationStatus).mockResolvedValue({
      status: JobStatus.RUNNING,
      job_id: 'test-sim-123',
      created_at: new Date().toISOString()
    });
  });

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <SimulationPage />
      </BrowserRouter>
    );
  };

  it('renders all main sections', async () => {
    renderComponent();
    
    // Check main sections are present
    expect(screen.getByText('Simulation Progress')).toBeInTheDocument();
    expect(screen.getByText('3D Mesh Visualization')).toBeInTheDocument();
    expect(screen.getByText('Mesh View Controls')).toBeInTheDocument();
    expect(screen.getByText('Understanding Meshes in Finite Element Analysis')).toBeInTheDocument();
  });

  it('displays simulation ID and connection status', async () => {
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText(/ID: test-sim-123/)).toBeInTheDocument();
      expect(screen.getByText(/connected/i)).toBeInTheDocument();
    });
  });

  it('shows progress bar with correct percentage', () => {
    renderComponent();
    
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText('Running simulation...')).toBeInTheDocument();
  });

  it('displays recent activity messages (max 3)', () => {
    renderComponent();
    
    // Should show only the last 3 messages
    expect(screen.getByText('Starting...')).toBeInTheDocument();
    expect(screen.getByText('Meshing...')).toBeInTheDocument();
    expect(screen.getByText('Solving...')).toBeInTheDocument();
  });

  it('disables See Results button when progress < 100%', () => {
    renderComponent();
    
    const seeResultsButton = screen.getByText('See Results');
    expect(seeResultsButton).toBeDisabled();
    expect(seeResultsButton).toHaveClass('opacity-50', 'cursor-not-allowed');
  });

  it('enables See Results button when progress = 100%', () => {
    mockUseSimulationProgress.mockReturnValue({
      isConnected: true,
      connectionState: WebSocketConnectionState.CONNECTED,
      status: JobStatus.COMPLETED,
      progress: 100,
      currentMessage: 'Simulation completed',
      progressMessages: [],
      error: null,
      reconnect: vi.fn(),
      disconnect: vi.fn()
    } as any);
    
    renderComponent();
    
    const seeResultsButton = screen.getByText('See Results');
    expect(seeResultsButton).toBeEnabled();
    expect(seeResultsButton).not.toHaveClass('opacity-50');
  });

  it('toggles mesh outline when checkbox is clicked', () => {
    renderComponent();
    
    const meshOutlineCheckbox = screen.getByLabelText('Mesh Outline');
    expect(meshOutlineCheckbox).not.toBeChecked();
    
    fireEvent.click(meshOutlineCheckbox);
    expect(meshOutlineCheckbox).toBeChecked();
    
    // Check if MeshPreview receives the updated prop
    expect(screen.getByText('Outline enabled')).toBeInTheDocument();
  });

  it('displays mouse controls horizontally', () => {
    renderComponent();
    
    // The flex container is the parent of the span that contains "Left Click + Drag:"
    const controlSpan = screen.getByText('Left Click + Drag:').parentElement;
    const controlsContainer = controlSpan?.parentElement;
    expect(controlsContainer).toHaveClass('text-gray-600', 'text-sm', 'flex', 'flex-wrap', 'gap-6');
    
    expect(screen.getByText(/Left Click \+ Drag:.*Rotate/)).toBeInTheDocument();
    expect(screen.getByText(/Right Click \+ Drag:.*Pan/)).toBeInTheDocument();
    expect(screen.getByText(/Scroll:.*Zoom/)).toBeInTheDocument();
  });

  it('shows error when simulation fails', () => {
    mockUseSimulationProgress.mockReturnValue({
      isConnected: true,
      connectionState: WebSocketConnectionState.ERROR,
      status: JobStatus.FAILED,
      progress: 0,
      currentMessage: 'Simulation failed',
      progressMessages: [],
      error: 'Solver convergence failed',
      reconnect: vi.fn(),
      disconnect: vi.fn()
    } as any);
    
    renderComponent();
    
    expect(screen.getByText('Error: Solver convergence failed')).toBeInTheDocument();
  });

  it('shows cancel button when simulation is running', () => {
    renderComponent();
    
    expect(screen.getByText('Cancel Simulation')).toBeInTheDocument();
  });

  it('hides cancel button when simulation is completed', () => {
    mockUseSimulationProgress.mockReturnValue({
      isConnected: true,
      connectionState: WebSocketConnectionState.CONNECTED,
      status: JobStatus.COMPLETED,
      progress: 100,
      currentMessage: 'Simulation completed',
      progressMessages: [],
      error: null,
      reconnect: vi.fn(),
      disconnect: vi.fn()
    } as any);
    
    renderComponent();
    
    expect(screen.queryByText('Cancel Simulation')).not.toBeInTheDocument();
  });

  it('displays educational content sections', () => {
    renderComponent();
    
    // Check for educational content headings
    expect(screen.getByText('What is a Mesh?')).toBeInTheDocument();
    expect(screen.getByText('Why are Meshes Important?')).toBeInTheDocument();
    expect(screen.getByText('Key Mesh Quality Metrics')).toBeInTheDocument();
    expect(screen.getByText('Mesh Density and the h-p Method')).toBeInTheDocument();
    expect(screen.getByText('Heat Map Visualization')).toBeInTheDocument();
    expect(screen.getByText('Mathematical Foundation')).toBeInTheDocument();
  });
}); 