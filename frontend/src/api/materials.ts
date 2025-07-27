import apiClient from './client';

export interface Material {
  id: string;
  name: string;
  E: number;          // Young's Modulus (Pa)
  nu: number;         // Poisson's Ratio
  k: number;          // Thermal Conductivity (W/(m·K))
  rho: number;        // Density (kg/m³)
  description?: string;
  units?: {
    E: string;
    nu: string;
    k: string;
    rho: string;
  };
}

export interface MaterialsResponse {
  materials: Material[];
  count: number;
}

export const materialsApi = {
  /**
   * Get all available materials
   */
  async getAll(): Promise<Material[]> {
    try {
      const response = await apiClient.get<MaterialsResponse>('/api/materials');
      return response.data.materials;
    } catch (error) {
      console.error('Failed to fetch materials:', error);
      throw error;
    }
  },

  /**
   * Get a specific material by ID
   */
  async getById(id: string): Promise<Material | undefined> {
    try {
      const materials = await this.getAll();
      return materials.find(material => material.id === id);
    } catch (error) {
      console.error(`Failed to fetch material ${id}:`, error);
      throw error;
    }
  }
}; 