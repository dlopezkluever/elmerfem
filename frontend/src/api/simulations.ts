import apiClient from './client';
import {
  SimulationParams,
  SimulationStatus,
  SimulationResult,
  MaterialsResponse,
} from '../types/api';

// Simulation API endpoints
export const simulationApi = {
  // Create a new simulation
  async createSimulation(params: SimulationParams): Promise<SimulationStatus> {
    const { data } = await apiClient.post<SimulationStatus>('/api/simulations', params);
    return data;
  },

  // Get simulation status
  async getSimulationStatus(id: string): Promise<SimulationStatus> {
    const { data } = await apiClient.get<SimulationStatus>(`/api/simulations/${id}/status`);
    return data;
  },

  // Get simulation result
  async getSimulationResult(id: string): Promise<SimulationResult> {
    const { data } = await apiClient.get<SimulationResult>(`/api/simulations/${id}/result`);
    return data;
  },

  // Get simulation logs
  async getSimulationLogs(id: string): Promise<string> {
    const { data } = await apiClient.get(`/api/simulations/${id}/logs`, {
      responseType: 'text',
    });
    return data;
  },

  // Download a specific file
  async downloadFile(id: string, filename: string): Promise<Blob> {
    const { data } = await apiClient.get(`/api/simulations/${id}/files/${filename}`, {
      responseType: 'blob',
    });
    return data;
  },

  // Cancel a running simulation
  async cancelSimulation(id: string): Promise<void> {
    await apiClient.delete(`/api/simulations/${id}`);
  },

  // Get available materials
  async getMaterials(): Promise<MaterialsResponse> {
    const { data } = await apiClient.get<MaterialsResponse>('/api/materials');
    return data;
  },
};

// Helper function to download file with proper filename
export const downloadFileHelper = async (
  simulationId: string,
  filename: string,
  suggestedName?: string
) => {
  try {
    const blob = await simulationApi.downloadFile(simulationId, filename);
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