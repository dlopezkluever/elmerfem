import { useState, useEffect } from 'react';
import { SimulationStatus } from '../types/api';

const STORAGE_KEY = 'elmerfem_recent_simulations';
const MAX_RECENT_SIMULATIONS = 10;

export interface RecentSimulation {
  id: string;
  type: string;
  status: string;
  createdAt: string;
  completedAt?: string;
  summary?: string;
}

export function useRecentSimulations() {
  const [recentSimulations, setRecentSimulations] = useState<RecentSimulation[]>([]);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setRecentSimulations(parsed);
      } catch (error) {
        console.error('Failed to parse recent simulations:', error);
      }
    }
  }, []);

  // Save to localStorage whenever the list changes
  const saveToLocalStorage = (simulations: RecentSimulation[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(simulations));
      setRecentSimulations(simulations);
    } catch (error) {
      console.error('Failed to save recent simulations:', error);
    }
  };

  // Add a new simulation
  const addSimulation = (status: SimulationStatus) => {
    const newSimulation: RecentSimulation = {
      id: status.id,
      type: status.message || 'Unknown',
      status: status.status,
      createdAt: status.created_at,
      completedAt: status.completed_at,
      summary: status.message,
    };

    const updated = [newSimulation, ...recentSimulations.filter(s => s.id !== status.id)]
      .slice(0, MAX_RECENT_SIMULATIONS);
    
    saveToLocalStorage(updated);
  };

  // Update an existing simulation
  const updateSimulation = (status: SimulationStatus) => {
    const updated = recentSimulations.map(sim => 
      sim.id === status.id
        ? {
            ...sim,
            status: status.status,
            completedAt: status.completed_at,
            summary: status.message,
          }
        : sim
    );
    
    saveToLocalStorage(updated);
  };

  // Remove a simulation
  const removeSimulation = (id: string) => {
    const updated = recentSimulations.filter(sim => sim.id !== id);
    saveToLocalStorage(updated);
  };

  // Clear all simulations
  const clearAll = () => {
    localStorage.removeItem(STORAGE_KEY);
    setRecentSimulations([]);
  };

  return {
    recentSimulations,
    addSimulation,
    updateSimulation,
    removeSimulation,
    clearAll,
  };
} 