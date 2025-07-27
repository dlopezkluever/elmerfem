import React, { useState, useCallback, useMemo, Suspense } from 'react';
import { useFrame } from '@react-three/fiber';
import { MeshScene } from './MeshScene';
import { STLMeshLoader } from './STLMeshLoader';
import { MeshHeatMap } from './MeshHeatMap';
import * as THREE from 'three';

interface MeshPreviewProps {
  meshId?: string;
  qualityMetrics?: {
    total_nodes: number;
    total_elements: number;
    min_angle: number;
    max_angle: number;
    aspect_ratio_avg: number;
    aspect_ratio_max: number;
    aspect_ratios?: number[];
    element_quality?: number[];
  };
  className?: string;
  showHeatMap?: boolean;
  autoRotate?: boolean;
  useMockData?: boolean;
  showMeshOutline?: boolean;
}

/**
 * Task 25.5: Optimize Performance for Educational Preview
 * Main component that integrates all mesh visualization features with performance optimizations.
 * Uses React.memo and Suspense for optimal rendering performance.
 */
export const MeshPreview: React.FC<MeshPreviewProps> = React.memo(({
  meshId = 'default-mesh',
  qualityMetrics,
  className = '',
  showHeatMap = false,
  autoRotate = false,
  useMockData = false,
  showMeshOutline = false
}) => {
  const [loadedGeometry, setLoadedGeometry] = useState<THREE.BufferGeometry | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const handleMeshLoaded = useCallback((geometry: THREE.BufferGeometry) => {
    setLoadedGeometry(geometry);
    setIsLoading(false);
  }, []);

  // Memoize quality metrics to prevent unnecessary re-renders
  const memoizedQualityMetrics = useMemo(() => qualityMetrics, [qualityMetrics]);

  return (
    <div className={`relative w-full h-full ${className}`}>
      <MeshScene className="w-full h-full">
        <Suspense fallback={<LoadingIndicator />}>
          {/* Main mesh */}
          <STLMeshLoader
            meshId={meshId}
            onMeshLoaded={handleMeshLoaded}
            wireframe={false}
            useMockData={useMockData}
            showMeshOutline={showMeshOutline}
          />
          
          {/* Heat map visualization overlay */}
          {showHeatMap && loadedGeometry && memoizedQualityMetrics && (
            <MeshHeatMap
              geometry={loadedGeometry}
              qualityMetrics={memoizedQualityMetrics}
              minQuality={0.5}
              maxQuality={1.0}
            />
          )}
          
          {/* Auto-rotation */}
          {autoRotate && <AutoRotate />}
        </Suspense>
      </MeshScene>
      
      {/* Quality metrics overlay */}
      {!isLoading && memoizedQualityMetrics && (
        <div className="absolute top-4 left-4 bg-neumorphic-bg shadow-neumorphic p-4 rounded-lg max-w-xs">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Mesh Quality Metrics</h3>
          <div className="text-xs text-gray-600 space-y-1">
            <p>Nodes: {memoizedQualityMetrics.total_nodes}</p>
            <p>Elements: {memoizedQualityMetrics.total_elements}</p>
            <p>Min Angle: {memoizedQualityMetrics.min_angle.toFixed(1)}°</p>
            <p>Max Angle: {memoizedQualityMetrics.max_angle.toFixed(1)}°</p>
            <p>Avg Aspect Ratio: {memoizedQualityMetrics.aspect_ratio_avg.toFixed(2)}</p>
            <p>Max Aspect Ratio: {memoizedQualityMetrics.aspect_ratio_max.toFixed(2)}</p>
          </div>
        </div>
      )}
      
      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-neumorphic-bg bg-opacity-50">
          <LoadingIndicator />
        </div>
      )}
    </div>
  );
});

// Loading indicator component
const LoadingIndicator: React.FC = () => (
  <div className="flex flex-col items-center">
    <div className="w-12 h-12 border-4 border-electric-blue border-t-transparent rounded-full animate-spin" />
    <p className="mt-4 text-gray-700">Loading mesh...</p>
  </div>
);

// Auto-rotation component using react-three-fiber hooks
const AutoRotate: React.FC = () => {
  useFrame((state) => {
    state.scene.rotation.y += 0.005;
  });
  
  return null;
};

MeshPreview.displayName = 'MeshPreview'; 