import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { useSimulationResult } from '../useSimulationResult';
import { simulationApi } from '../../api';
import * as pako from 'pako';

// Mock the API module
vi.mock('../../api');
const mockSimulationApi = simulationApi as {
  getResultDataCompressed: Mock;
  getResultDataRaw: Mock;
};

// Mock pako for gzip decompression
vi.mock('pako');
const mockPako = pako as {
  inflate: Mock;
};

// Mock VTU data for testing
const mockVTUData = {
  metadata: {
    format: 'vtu_converted',
    source_file: 'test.vtu',
    num_points: 100,
    num_cells: 50,
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

describe('useSimulationResult', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch and decompress simulation result data', async () => {
    const mockCompressedData = new Uint8Array([1, 2, 3, 4]);
    const mockDecompressedData = JSON.stringify(mockVTUData);

    mockSimulationApi.getResultDataCompressed.mockResolvedValue({
      data: mockCompressedData,
      headers: { 'content-type': 'application/gzip' }
    });

    mockPako.inflate.mockReturnValue(new TextEncoder().encode(mockDecompressedData));

    const { result } = renderHook(() => useSimulationResult('test-sim-id'));

    // Initially loading
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBe(null);

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Check that data is loaded correctly
    expect(result.current.data).toEqual(mockVTUData);
    expect(result.current.error).toBe(null);
    expect(mockSimulationApi.getResultDataCompressed).toHaveBeenCalledWith('test-sim-id');
  });

  it('should fallback to raw data when compressed data fails', async () => {
    mockSimulationApi.getResultDataCompressed.mockRejectedValue(new Error('Compressed data not available'));
    mockSimulationApi.getResultDataRaw.mockResolvedValue({ data: mockVTUData });

    const { result } = renderHook(() => useSimulationResult('test-sim-id'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockVTUData);
    expect(result.current.error).toBe(null);
    expect(mockSimulationApi.getResultDataRaw).toHaveBeenCalledWith('test-sim-id');
  });

  it('should handle errors when both compressed and raw data fail', async () => {
    const errorMessage = 'Network error';
    mockSimulationApi.getResultDataCompressed.mockRejectedValue(new Error('Compressed failed'));
    mockSimulationApi.getResultDataRaw.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useSimulationResult('test-sim-id'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBe(null);
    expect(result.current.error).toBe(`Failed to fetch result data: ${errorMessage}`);
  });

  it('should calculate statistics correctly', async () => {
    mockSimulationApi.getResultDataCompressed.mockResolvedValue({
      data: new Uint8Array([1, 2, 3, 4]),
      headers: { 'content-type': 'application/gzip' }
    });

    mockPako.inflate.mockReturnValue(new TextEncoder().encode(JSON.stringify(mockVTUData)));

    const { result } = renderHook(() => useSimulationResult('test-sim-id'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.statistics).toEqual({
      temperatureRange: { min: 20.0, max: 35.0 },
      averageTemperature: 27.5,
      pointCount: 100,
      cellCount: 50
    });
  });

  it('should provide refetch functionality', async () => {
    mockSimulationApi.getResultDataCompressed.mockResolvedValue({
      data: new Uint8Array([1, 2, 3, 4]),
      headers: { 'content-type': 'application/gzip' }
    });

    mockPako.inflate.mockReturnValue(new TextEncoder().encode(JSON.stringify(mockVTUData)));

    const { result } = renderHook(() => useSimulationResult('test-sim-id'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Clear the mock call count
    mockSimulationApi.getResultDataCompressed.mockClear();

    // Call refetch
    result.current.refetch();

    // Should make another API call
    expect(mockSimulationApi.getResultDataCompressed).toHaveBeenCalledWith('test-sim-id');
  });
}); 