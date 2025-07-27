import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { materialsApi } from './materials';

vi.mock('axios');

describe('materialsApi', () => {
  const mockMaterials = [
    {
      id: 'steel',
      name: 'Steel',
      E: 210e9,
      nu: 0.3,
      k: 50,
      rho: 7850,
      description: 'Common structural steel'
    },
    {
      id: 'aluminum',
      name: 'Aluminum',
      E: 70e9,
      nu: 0.33,
      k: 237,
      rho: 2700,
      description: 'Aluminum alloy'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getAll', () => {
    it('fetches all materials successfully', async () => {
      const mockResponse = {
        data: {
          materials: mockMaterials,
          count: 2
        }
      };

      (axios.create as any).mockReturnValue({
        get: vi.fn().mockResolvedValue(mockResponse)
      });

      const result = await materialsApi.getAll();

      expect(result).toEqual(mockMaterials);
    });

    it('handles API errors', async () => {
      const mockError = new Error('Network error');

      (axios.create as any).mockReturnValue({
        get: vi.fn().mockRejectedValue(mockError)
      });

      await expect(materialsApi.getAll()).rejects.toThrow('Network error');
    });
  });

  describe('getById', () => {
    it('returns material by ID when found', async () => {
      const mockResponse = {
        data: {
          materials: mockMaterials,
          count: 2
        }
      };

      (axios.create as any).mockReturnValue({
        get: vi.fn().mockResolvedValue(mockResponse)
      });

      const result = await materialsApi.getById('steel');

      expect(result).toEqual(mockMaterials[0]);
    });

    it('returns undefined when material not found', async () => {
      const mockResponse = {
        data: {
          materials: mockMaterials,
          count: 2
        }
      };

      (axios.create as any).mockReturnValue({
        get: vi.fn().mockResolvedValue(mockResponse)
      });

      const result = await materialsApi.getById('nonexistent');

      expect(result).toBeUndefined();
    });

    it('propagates errors from getAll', async () => {
      const mockError = new Error('Network error');

      (axios.create as any).mockReturnValue({
        get: vi.fn().mockRejectedValue(mockError)
      });

      await expect(materialsApi.getById('steel')).rejects.toThrow('Network error');
    });
  });
}); 