import { useState, useEffect } from 'react';
import { materialsApi, Material } from '../api';

export function useMaterials() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMaterials();
  }, []);

  const fetchMaterials = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await materialsApi.getAll();
      setMaterials(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load materials');
    } finally {
      setLoading(false);
    }
  };

  const getMaterialById = (id: string) => {
    return materials.find(m => m.id === id);
  };

  return {
    materials,
    loading,
    error,
    refetch: fetchMaterials,
    getMaterialById,
  };
} 