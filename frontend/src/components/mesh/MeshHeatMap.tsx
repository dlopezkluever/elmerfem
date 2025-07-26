import React, { useEffect, useRef, useState } from 'react';
import { extend, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { GUI } from 'dat.gui';

interface MeshHeatMapProps {
  geometry: THREE.BufferGeometry;
  qualityMetrics?: {
    aspect_ratios?: number[];
    element_quality?: number[];
  };
  minQuality?: number;
  maxQuality?: number;
}

interface HeatMapControls {
  enabled: boolean;
  metric: 'aspect_ratio' | 'element_quality';
  colorScale: 'rainbow' | 'thermal' | 'grayscale';
  opacity: number;
}

/**
 * Task 25.3: Implement Heat-Map Visualization
 * Applies heat-map coloring to mesh based on quality metrics.
 * Includes dat.GUI controls for toggling and customization.
 */
export const MeshHeatMap: React.FC<MeshHeatMapProps> = ({ 
  geometry, 
  qualityMetrics,
  minQuality = 0,
  maxQuality = 1
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const guiRef = useRef<GUI | null>(null);
  const { scene } = useThree();

  const [controls, setControls] = useState<HeatMapControls>({
    enabled: true,
    metric: 'aspect_ratio',
    colorScale: 'rainbow',
    opacity: 1.0
  });

  // Color scale functions
  const getColorForValue = (value: number, scale: string): THREE.Color => {
    const normalized = (value - minQuality) / (maxQuality - minQuality);
    
    switch (scale) {
      case 'rainbow':
        // Rainbow scale: red (bad) -> yellow -> green (good) -> blue (excellent)
        const hue = normalized * 0.8; // 0 to 0.8 (red to blue)
        return new THREE.Color().setHSL(hue, 1, 0.5);
      
      case 'thermal':
        // Thermal scale: blue (cold/good) -> red (hot/bad)
        const r = 1 - normalized;
        const b = normalized;
        return new THREE.Color(r, 0, b);
      
      case 'grayscale':
        // Grayscale: black (bad) -> white (good)
        const gray = normalized;
        return new THREE.Color(gray, gray, gray);
      
      default:
        return new THREE.Color(0.5, 0.5, 0.5);
    }
  };

  // Apply heat map colors to geometry
  const applyHeatMap = () => {
    if (!geometry || !qualityMetrics) return;

    const metrics = controls.metric === 'aspect_ratio' 
      ? qualityMetrics.aspect_ratios 
      : qualityMetrics.element_quality;

    if (!metrics || metrics.length === 0) return;

    const positionAttribute = geometry.getAttribute('position');
    const vertexCount = positionAttribute.count;
    
    // Create color attribute if it doesn't exist
    const colors = new Float32Array(vertexCount * 3);
    const colorAttribute = new THREE.BufferAttribute(colors, 3);

    // For each vertex, find the corresponding quality metric
    // This is a simplified approach - in practice, you'd map elements to vertices
    for (let i = 0; i < vertexCount; i++) {
      const metricIndex = Math.min(i % metrics.length, metrics.length - 1);
      const quality = metrics[metricIndex];
      const color = getColorForValue(quality, controls.colorScale);
      
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }

    geometry.setAttribute('color', colorAttribute);
    geometry.attributes.color.needsUpdate = true;
  };

  // Setup dat.GUI controls
  useEffect(() => {
    if (!guiRef.current) {
      const gui = new GUI({ autoPlace: false });
      gui.domElement.style.position = 'absolute';
      gui.domElement.style.top = '10px';
      gui.domElement.style.right = '10px';
      gui.domElement.style.zIndex = '1000';
      
      // Add to the canvas container
      const container = document.querySelector('.mesh-preview-container');
      if (container) {
        container.appendChild(gui.domElement);
      }

      const heatMapFolder = gui.addFolder('Heat Map Visualization');
      
      heatMapFolder.add(controls, 'enabled')
        .name('Enable Heat Map')
        .onChange((value: boolean) => {
          setControls(prev => ({ ...prev, enabled: value }));
        });

      heatMapFolder.add(controls, 'metric', ['aspect_ratio', 'element_quality'])
        .name('Quality Metric')
        .onChange((value: string) => {
          setControls(prev => ({ ...prev, metric: value as any }));
        });

      heatMapFolder.add(controls, 'colorScale', ['rainbow', 'thermal', 'grayscale'])
        .name('Color Scale')
        .onChange((value: string) => {
          setControls(prev => ({ ...prev, colorScale: value as any }));
        });

      heatMapFolder.add(controls, 'opacity', 0, 1, 0.1)
        .name('Opacity')
        .onChange((value: number) => {
          setControls(prev => ({ ...prev, opacity: value }));
        });

      heatMapFolder.open();
      guiRef.current = gui;
    }

    return () => {
      if (guiRef.current) {
        guiRef.current.destroy();
        guiRef.current = null;
      }
    };
  }, []);

  // Apply heat map when controls change
  useEffect(() => {
    if (controls.enabled) {
      applyHeatMap();
    }
  }, [controls, geometry, qualityMetrics]);

  return (
    <mesh
      ref={meshRef}
      geometry={geometry}
      castShadow
      receiveShadow
    >
      <meshStandardMaterial
        vertexColors={controls.enabled}
        opacity={controls.opacity}
        transparent={controls.opacity < 1}
        side={THREE.DoubleSide}
        metalness={0.3}
        roughness={0.7}
      />
    </mesh>
  );
}; 