import React, { useEffect, useState, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { GeometryParams } from '../../types/api';
import * as THREE from 'three';

interface MeshPreviewData {
  mesh_id: string;
  geometry_type: string;
  nodes: number[][];
  elements: number[][];
  element_type: 'triangle' | 'quad';
  boundaries: Record<string, number[]>;
  quality_metrics: any;
  bounding_box: {
    min_x: number;
    max_x: number;
    min_y: number;
    max_y: number;
    min_z: number;
    max_z: number;
  };
}

interface STLMeshLoaderProps {
  meshId: string;
  geometry?: GeometryParams;
  onMeshLoaded?: (geometry: THREE.BufferGeometry) => void;
  color?: string;
  wireframe?: boolean;
  useMockData?: boolean;
  showMeshOutline?: boolean;
}

/**
 * Task 25.2: Load and Display Mesh
 * Fetches mesh data from the preview endpoint and converts it to Three.js geometry.
 * Now supports generating geometry from simulation parameters.
 */
export const STLMeshLoader: React.FC<STLMeshLoaderProps> = ({ 
  meshId, 
  geometry: geometryParams,
  onMeshLoaded,
  color = '#65c3c8',
  wireframe = false,
  useMockData = false,
  showMeshOutline = false
}) => {
  const [geometry, setGeometry] = useState<THREE.BufferGeometry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const meshRef = useRef<THREE.Mesh>(null);

  // Animation for loading state
  useFrame(() => {
    if (loading && meshRef.current) {
      meshRef.current.rotation.x += 0.01;
      meshRef.current.rotation.y += 0.01;
    }
  });

  // Create Three.js geometry from simulation geometry parameters
  const createGeometryFromParams = (geometryParams: GeometryParams): THREE.BufferGeometry => {
    const { type, dimensions } = geometryParams;
    
    switch (type) {
      case 'box':
        return new THREE.BoxGeometry(
          dimensions.length || 2,
          dimensions.width || 2,
          dimensions.height || 2
        );
      
      case 'cylinder':
        return new THREE.CylinderGeometry(
          dimensions.radius || 1,
          dimensions.radius || 1,
          dimensions.height || 2,
          32
        );
      
      case 'sphere':
        return new THREE.SphereGeometry(
          dimensions.radius || 1,
          32,
          16
        );
      
      default:
        // Fallback to a box if unknown type
        return new THREE.BoxGeometry(2, 2, 2);
    }
  };

  // Create mock mesh data for testing
  const createMockMeshData = (): MeshPreviewData => {
    const size = 10;
    const divisions = 10;
    const nodes: number[][] = [];
    const elements: number[][] = [];
    
    // Create a grid of nodes
    for (let i = 0; i <= divisions; i++) {
      for (let j = 0; j <= divisions; j++) {
        const x = (i / divisions - 0.5) * size;
        const y = (j / divisions - 0.5) * size;
        const z = Math.sin(x * 0.5) * Math.cos(y * 0.5) * 2; // Create a wavy surface
        nodes.push([x, y, z]);
      }
    }
    
    // Create quad elements
    for (let i = 0; i < divisions; i++) {
      for (let j = 0; j < divisions; j++) {
        const n0 = i * (divisions + 1) + j;
        const n1 = n0 + 1;
        const n2 = n0 + divisions + 1;
        const n3 = n2 + 1;
        elements.push([n0, n1, n3, n2]);
      }
    }
    
    return {
      mesh_id: meshId,
      geometry_type: 'rectangle',
      nodes,
      elements,
      element_type: 'quad',
      boundaries: {
        bottom: Array.from({ length: divisions + 1 }, (_, i) => i),
        top: Array.from({ length: divisions + 1 }, (_, i) => divisions * (divisions + 1) + i),
        left: Array.from({ length: divisions + 1 }, (_, i) => i * (divisions + 1)),
        right: Array.from({ length: divisions + 1 }, (_, i) => i * (divisions + 1) + divisions)
      },
      quality_metrics: {
        total_nodes: nodes.length,
        total_elements: elements.length,
        min_angle: 85.2,
        max_angle: 94.8,
        aspect_ratio_avg: 1.05,
        aspect_ratio_max: 1.12
      },
      bounding_box: {
        min_x: -size/2,
        max_x: size/2,
        min_y: -size/2,
        max_y: size/2,
        min_z: -2,
        max_z: 2
      }
    };
  };

  // Convert mesh data to Three.js BufferGeometry
  const createGeometryFromMeshData = (data: MeshPreviewData): THREE.BufferGeometry => {
    const geometry = new THREE.BufferGeometry();
    const vertices: number[] = [];
    const indices: number[] = [];
    
    // Add vertices
    data.nodes.forEach(node => {
      vertices.push(node[0], node[1], node[2] || 0);
    });
    
    // Add faces based on element type
    if (data.element_type === 'triangle') {
      data.elements.forEach(element => {
        indices.push(element[0], element[1], element[2]);
      });
    } else if (data.element_type === 'quad') {
      data.elements.forEach(element => {
        // Convert quad to two triangles
        indices.push(element[0], element[1], element[2]);
        indices.push(element[0], element[2], element[3]);
      });
    }
    
    // Set geometry attributes
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    
    return geometry;
  };

  useEffect(() => {
    const loadMesh = async () => {
      try {
        setLoading(true);
        setError(null);

        let newGeometry: THREE.BufferGeometry;

        if (geometryParams && !useMockData) {
          // Use geometry parameters from simulation to create the 3D shape
          newGeometry = createGeometryFromParams(geometryParams);
        } else if (useMockData) {
          // Use mock data for testing
          const meshData = createMockMeshData();
          newGeometry = createGeometryFromMeshData(meshData);
        } else {
          // Fallback: try to fetch from API
          try {
            const response = await fetch(`/api/v1/mesh/preview/${meshId}`);
            if (!response.ok) {
              throw new Error(`Failed to load mesh: ${response.statusText}`);
            }
            const meshData = await response.json();
            newGeometry = createGeometryFromMeshData(meshData);
          } catch (apiError) {
            console.warn('API fetch failed, using fallback geometry:', apiError);
            // Create a fallback cube geometry
            newGeometry = new THREE.BoxGeometry(2, 2, 2);
          }
        }

        setGeometry(newGeometry);
        
        if (onMeshLoaded) {
          onMeshLoaded(newGeometry);
        }
      } catch (err) {
        console.error('Error loading mesh:', err);
        setError(err instanceof Error ? err.message : 'Failed to load mesh');
        
        // Create a fallback cube geometry
        const fallbackGeometry = new THREE.BoxGeometry(2, 2, 2);
        setGeometry(fallbackGeometry);
      } finally {
        setLoading(false);
      }
    };

    loadMesh();
  }, [meshId, geometryParams, onMeshLoaded, useMockData]);

  if (loading) {
    return (
      <mesh>
        <boxGeometry args={[1, 1, 1]} />
        <meshBasicMaterial color="#CCCCCC" wireframe />
      </mesh>
    );
  }

  if (error || !geometry) {
    return (
      <mesh>
        <boxGeometry args={[2, 2, 2]} />
        <meshBasicMaterial color="#FF0000" wireframe />
      </mesh>
    );
  }

  return (
    <>
      {/* Main mesh */}
      <mesh ref={meshRef} geometry={geometry} castShadow receiveShadow>
        <meshStandardMaterial 
          color={color} 
          wireframe={wireframe}
          metalness={0.3}
          roughness={0.7}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* Black wireframe overlay when outline is enabled */}
      {showMeshOutline && geometry && (
        <mesh geometry={geometry}>
          <meshBasicMaterial 
            color="#000000" 
            wireframe={true}
            wireframeLinewidth={2}
          />
        </mesh>
      )}
    </>
  );
}; 