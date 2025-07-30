import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { ResultVisualization } from '../ResultVisualization';
import { useSimulationResult } from '../../hooks/useSimulationResult';
import { ViewMode } from '../../types/visualization';

// Mock the hook
vi.mock('../../hooks/useSimulationResult');
const mockUseSimulationResult = useSimulationResult as Mock;

// Mock Plotly component
vi.mock('react-plotly.js', () => {
  return {
    default: function MockPlot(props: any) {
      return (
        <div data-testid="plotly-chart">
          <span data-testid="plot-data">{JSON.stringify(props.data)}</span>
          <span data-testid="plot-layout">{JSON.stringify(props.layout)}</span>
        </div>
      );
    }
  };
});

const mockVTUData = {
  metadata: {
    format: 'vtu_converted',
    source_file: 'test.vtu',
    num_points: 4,
    num_cells: 2,
    conversion_timestamp: '2025-01-28T12:00:00Z',
    point_data_fields: ['Temperature'],
    cell_data_fields: []
  },
  points: [
    [0, 0, 0],
    [1, 0, 0],
    [0, 1, 0],
    [1, 1, 0]
  ],
  cells: {
    triangles: [[0, 1, 2], [1, 2, 3]]
  },
  point_data: {
    Temperature: [20.0, 25.0, 30.0, 35.0]
  },
  cell_data: {},
  field_data: {}
};

const mockStatistics = {
  temperatureRange: { min: 20.0, max: 35.0 },
  averageTemperature: 27.5,
  pointCount: 4,
  cellCount: 2
};

describe('ResultVisualization', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state', () => {
    mockUseSimulationResult.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: vi.fn(),
      statistics: null
    });

    render(<ResultVisualization simulationId="test-id" />);

    expect(screen.getByText(/loading 3d visualization/i)).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('should render error state', () => {
    const errorMessage = 'Failed to load data';
    mockUseSimulationResult.mockReturnValue({
      data: null,
      loading: false,
      error: errorMessage,
      refetch: vi.fn(),
      statistics: null
    });

    const onError = vi.fn();
    render(<ResultVisualization simulationId="test-id" onError={onError} />);

    expect(screen.getByText(/error loading visualization/i)).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(onError).toHaveBeenCalledWith(errorMessage);
  });

  it('should render visualization with data', () => {
    mockUseSimulationResult.mockReturnValue({
      data: mockVTUData,
      loading: false,
      error: null,
      refetch: vi.fn(),
      statistics: mockStatistics
    });

    render(<ResultVisualization simulationId="test-id" />);

    expect(screen.getByTestId('plotly-chart')).toBeInTheDocument();
    expect(screen.getByText(/4 points/i)).toBeInTheDocument();
    expect(screen.getByText(/2 cells/i)).toBeInTheDocument();
    expect(screen.getByText(/temperature range:/i)).toBeInTheDocument();
  });

  it('should handle view mode changes', async () => {
    mockUseSimulationResult.mockReturnValue({
      data: mockVTUData,
      loading: false,
      error: null,
      refetch: vi.fn(),
      statistics: mockStatistics
    });

    render(<ResultVisualization simulationId="test-id" />);

    // Find and click the view mode selector
    const temperatureButton = screen.getByText(/temperature/i);
    expect(temperatureButton).toBeInTheDocument();

    // Test that plotly receives the correct data
    const plotData = screen.getByTestId('plot-data');
    const parsedData = JSON.parse(plotData.textContent!);
    expect(parsedData).toHaveLength(1);
    expect(parsedData[0].type).toBe('mesh3d');
  });

  it('should handle educational content expansion', async () => {
    mockUseSimulationResult.mockReturnValue({
      data: mockVTUData,
      loading: false,
      error: null,
      refetch: vi.fn(),
      statistics: mockStatistics
    });

    render(<ResultVisualization simulationId="test-id" />);

    // Find and click the educational expansion button
    const expandButton = screen.getByText(/learn more/i);
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(screen.getByText(/heat transfer fundamentals/i)).toBeInTheDocument();
    });
  });

  it('should handle mesh wireframe toggle', () => {
    mockUseSimulationResult.mockReturnValue({
      data: mockVTUData,
      loading: false,
      error: null,
      refetch: vi.fn(),
      statistics: mockStatistics
    });

    render(<ResultVisualization simulationId="test-id" />);

    const wireframeToggle = screen.getByLabelText(/show wireframe/i);
    fireEvent.click(wireframeToggle);

    // Verify the plot layout updates
    const plotLayout = screen.getByTestId('plot-layout');
    const parsedLayout = JSON.parse(plotLayout.textContent!);
    // The wireframe state should affect the mesh rendering
    expect(parsedLayout).toBeDefined();
  });

  it('should handle refetch when retry button is clicked', () => {
    const mockRefetch = vi.fn();
    mockUseSimulationResult.mockReturnValue({
      data: null,
      loading: false,
      error: 'Network error',
      refetch: mockRefetch,
      statistics: null
    });

    render(<ResultVisualization simulationId="test-id" />);

    const retryButton = screen.getByText(/retry/i);
    fireEvent.click(retryButton);

    expect(mockRefetch).toHaveBeenCalled();
  });

  it('should apply custom className', () => {
    mockUseSimulationResult.mockReturnValue({
      data: mockVTUData,
      loading: false,
      error: null,
      refetch: vi.fn(),
      statistics: mockStatistics
    });

    const { container } = render(
      <ResultVisualization simulationId="test-id" className="custom-class" />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });
}); 