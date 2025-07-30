import apiClient from './client';
import {
  SimulationParams,
  SimulationStatus,
  SimulationResult,
} from '../types/api';
import { VTUData } from '../types/visualization';

export const simulationApi = {
  // Create a new simulation
  async createSimulation(params: SimulationParams): Promise<SimulationStatus> {
    const { data } = await apiClient.post<SimulationStatus>('/api/v1/simulations', params);
    return data;
  },

  // Get simulation status
  async getSimulationStatus(id: string): Promise<SimulationStatus> {
    const { data } = await apiClient.get<SimulationStatus>(`/api/v1/simulations/${id}/status`);
    return data;
  },

  // Get simulation result
  async getSimulationResult(id: string): Promise<SimulationResult> {
    const { data } = await apiClient.get<SimulationResult>(`/api/v1/simulations/${id}/result`);
    return data;
  },

  // Get simulation result data for visualization (uncompressed)
  async getSimulationResultData(id: string): Promise<VTUData> {
    const { data } = await apiClient.get<VTUData>(`/api/v1/simulations/${id}/result-data`);
    return data;
  },

  // Get simulation result data as compressed stream
  async getSimulationResultDataCompressed(id: string): Promise<ArrayBuffer> {
    const { data } = await apiClient.get<ArrayBuffer>(`/api/v1/simulations/${id}/result-data/compressed`, {
      responseType: 'arraybuffer',
      headers: {
        'Accept-Encoding': 'gzip',
      }
    });
    return data;
  },

  // Get simulation logs
  async getSimulationLogs(id: string): Promise<string> {
    const { data } = await apiClient.get(`/api/v1/simulations/${id}/logs`, {
      responseType: 'text'
    });
    return data;
  },

  // Download result file
  async downloadResultFile(id: string, filename: string): Promise<Blob> {
    const { data } = await apiClient.get(`/api/v1/simulations/${id}/files/${filename}`, {
      responseType: 'blob'
    });
    return data;
  },

  // Cancel a running simulation
  async cancelSimulation(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/simulations/${id}`);
  }
};

// Helper function to download file with proper filename
export const downloadFileHelper = async (
  simulationId: string,
  filename: string,
  suggestedName?: string
) => {
  try {
    const blob = await simulationApi.downloadResultFile(simulationId, filename);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = suggestedName || filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Download failed:', error);
    throw error;
  }
}; 