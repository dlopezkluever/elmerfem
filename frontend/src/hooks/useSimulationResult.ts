import { useState, useEffect, useCallback, useMemo } from 'react';
import * as pako from 'pako';
import { simulationApi } from '../api';
import { 
  VTUData, 
  UseSimulationResultResult, 
  ViewMode, 
  ResultStatistics 
} from '../types/visualization';

/**
 * Custom hook to fetch and process VTU simulation result data
 * Handles both compressed and uncompressed data with fallback mechanisms
 */
export function useSimulationResult(simulationId: string): UseSimulationResultResult {
  const [data, setData] = useState<VTUData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Memoize statistics calculation to avoid recalculation on every render
  const statistics = useMemo(() => {
    if (!data || !data.point_data) return null;
    return calculateStatistics(data, ViewMode.TEMPERATURE);
  }, [data]);

  const fetchResultData = useCallback(async () => {
    if (!simulationId) return;
    
    try {
      setLoading(true);
      setError(null);

      console.log(`🔍 Starting VTU data fetch for simulation: ${simulationId}`);

      // Try compressed endpoint first for efficiency
      let resultData: VTUData;
      
      try {
        console.log(`📥 Attempting compressed endpoint: /api/v1/simulations/${simulationId}/result-data/compressed`);
        const compressedData = await simulationApi.getSimulationResultDataCompressed(simulationId);
        console.log('✅ Compressed data received, attempting decompression...');
        resultData = await decompressGzipData(compressedData);
        console.log('✅ Successfully decompressed VTU data');
      } catch (compressedError) {
        console.warn('❌ Compressed endpoint failed:', compressedError);
        
        // Fallback to uncompressed endpoint
        try {
          console.log(`📥 Attempting uncompressed endpoint: /api/v1/simulations/${simulationId}/result-data`);
          resultData = await simulationApi.getSimulationResultData(simulationId);
          console.log('✅ Successfully received uncompressed VTU data');
        } catch (fallbackError) {
          console.error('❌ Uncompressed endpoint also failed:', fallbackError);
          // Check if it's a 404 or conversion error
          const errorMsg = fallbackError instanceof Error ? fallbackError.message : 'Unknown error';
          if (errorMsg.includes('404') || errorMsg.includes('not found')) {
            throw new Error('VTU result data not found. The simulation may not have generated visualization data, or the VTU to JSON conversion may have failed.');
          } else {
            throw new Error(`Both compressed and uncompressed endpoints failed: ${errorMsg}`);
          }
        }
      }

      // Validate the received data structure
      if (!isValidVTUData(resultData)) {
        throw new Error('Invalid VTU data structure received from server');
      }

      console.log('Successfully loaded VTU data:', {
        points: resultData.points.length,
        cells: Object.keys(resultData.cells).length,
        pointDataFields: Object.keys(resultData.point_data),
        metadata: resultData.metadata
      });

      setData(resultData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load simulation results';
      console.error('Error fetching simulation result data:', err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [simulationId]);

  useEffect(() => {
    fetchResultData();
  }, [fetchResultData]);

  const refetch = useCallback(async () => {
    await fetchResultData();
  }, [fetchResultData]);

  return {
    data,
    loading,
    error,
    refetch,
    statistics,
  };
}

/**
 * Decompress gzipped ArrayBuffer and parse as JSON
 */
async function decompressGzipData(compressedData: ArrayBuffer): Promise<VTUData> {
  try {
    // Convert ArrayBuffer to Uint8Array for pako
    const uint8Array = new Uint8Array(compressedData);
    
    // Decompress using pako
    const decompressed = pako.ungzip(uint8Array, { to: 'string' });
    
    // Parse the JSON data
    const parsed = JSON.parse(decompressed);
    
    return parsed as VTUData;
  } catch (error) {
    console.error('Decompression failed:', error);
    throw new Error('Failed to decompress result data');
  }
}

/**
 * Validate VTU data structure at runtime
 */
function isValidVTUData(data: any): data is VTUData {
  if (!data || typeof data !== 'object') {
    console.error('VTU data is not an object');
    return false;
  }

  // Check required top-level properties
  const requiredProperties = ['metadata', 'points', 'cells', 'point_data'];
  for (const prop of requiredProperties) {
    if (!(prop in data)) {
      console.error(`Missing required property: ${prop}`);
      return false;
    }
  }

  // Check metadata structure
  if (!data.metadata || typeof data.metadata !== 'object') {
    console.error('Invalid metadata structure');
    return false;
  }

  // Check points array
  if (!Array.isArray(data.points) || data.points.length === 0) {
    console.error('Points array is invalid or empty');
    return false;
  }

  // Check cells object
  if (!data.cells || typeof data.cells !== 'object') {
    console.error('Cells object is invalid');
    return false;
  }

  // Check point_data object
  if (!data.point_data || typeof data.point_data !== 'object') {
    console.error('Point data object is invalid');
    return false;
  }

  return true;
}

/**
 * Calculate comprehensive statistics for a given field
 */
function calculateStatistics(data: VTUData, fieldName: ViewMode): ResultStatistics | null {
  try {
    console.log(`Calculating statistics for ${fieldName}`);
    
    let values: number[] = [];
    let unit = '';
    let fieldKey = '';

    // Handle different field types and extract values accordingly
    switch (fieldName) {
      case ViewMode.TEMPERATURE:
        fieldKey = 'Temperature';
        unit = '°C';
        const tempData = data.point_data[fieldKey] || data.point_data.temperature;
        if (Array.isArray(tempData)) {
          values = tempData.filter(val => typeof val === 'number' && !isNaN(val));
        }
        break;

      case ViewMode.HEAT_FLUX:
        fieldKey = 'Heat Flux';
        unit = 'W/m²';
        const heatFluxData = data.point_data[fieldKey] || data.point_data['heat flux'] || data.point_data.HeatFlux;
        if (Array.isArray(heatFluxData)) {
          // Heat flux is a vector field - calculate magnitude for each point
          values = heatFluxData
            .filter(val => Array.isArray(val) && val.length >= 3)
            .map(vector => {
              const [vx, vy, vz] = vector;
              return Math.sqrt(vx*vx + vy*vy + vz*vz);
            })
            .filter(magnitude => !isNaN(magnitude));
        }
        break;

      case ViewMode.GRADIENT:
        fieldKey = 'Temperature Gradient';
        unit = '°C/m';
        const gradientData = data.point_data[fieldKey] || data.point_data['temperature gradient'] || data.point_data.TemperatureGradient;
        if (Array.isArray(gradientData)) {
          // Temperature gradient is a vector field - calculate magnitude for each point
          values = gradientData
            .filter(val => Array.isArray(val) && val.length >= 3)
            .map(vector => {
              const [gx, gy, gz] = vector;
              return Math.sqrt(gx*gx + gy*gy + gz*gz);
            })
            .filter(magnitude => !isNaN(magnitude));
        }
        break;
    }

    console.log(`Extracted ${values.length} values for ${fieldName}:`, { min: Math.min(...values), max: Math.max(...values) });

    if (values.length === 0) {
      console.warn(`No valid data found for field: ${fieldName}`);
      return null;
    }

    // Calculate comprehensive statistics
    const min = Math.min(...values);
    const max = Math.max(...values);
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    
    // Calculate standard deviation
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const std = Math.sqrt(variance);

    // Calculate median
    const sortedValues = [...values].sort((a, b) => a - b);
    const median = sortedValues.length % 2 === 0
      ? (sortedValues[sortedValues.length / 2 - 1] + sortedValues[sortedValues.length / 2]) / 2
      : sortedValues[Math.floor(sortedValues.length / 2)];

    // Calculate percentiles
    const p25 = sortedValues[Math.floor(sortedValues.length * 0.25)];
    const p75 = sortedValues[Math.floor(sortedValues.length * 0.75)];

    // Find extreme values and their locations
    const minIndex = values.indexOf(min);
    const maxIndex = values.indexOf(max);

    // Find hot spots (top 10% of values) with locations
    const threshold = min + (max - min) * 0.9;
    const hotSpots = values
      .map((value, index) => ({
        value,
        location: data.points[index] as [number, number, number],
        index
      }))
      .filter(spot => spot.value >= threshold)
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);

    // Calculate coefficient of variation (relative variability)
    const coefficientOfVariation = mean !== 0 ? (std / Math.abs(mean)) * 100 : 0;

    console.log(`Statistics calculated for ${fieldName}:`, { min, max, mean, std, median });

    return {
      fieldName: fieldKey,
      min,
      max,
      mean,
      std,
      median,
      p25,
      p75,
      range: max - min,
      coefficientOfVariation,
      unit,
      sampleSize: values.length,
      hotSpots,
      minLocation: data.points[minIndex] as [number, number, number],
      maxLocation: data.points[maxIndex] as [number, number, number]
    };

  } catch (error) {
    console.error(`Error calculating statistics for ${fieldName}:`, error);
    return null;
  }
} 