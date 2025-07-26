import React, { useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';

interface MeshSceneProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Task 25.1: Three.js Scene Setup
 * Initializes a Three.js scene with camera, lighting, and basic controls
 * for educational mesh visualization.
 */
export const MeshScene: React.FC<MeshSceneProps> = ({ children, className = '' }) => {
  return (
    <div className={`w-full h-full bg-neumorphic-bg shadow-neumorphic-inset rounded-2xl ${className}`}>
      <Canvas
        shadows
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
          preserveDrawingBuffer: true,
        }}
        onCreated={({ gl }) => {
          gl.setClearColor('#F0F0F0', 1);
        }}
      >
        {/* Camera setup with appropriate field of view and positioning */}
        <PerspectiveCamera
          makeDefault
          position={[5, 5, 5]}
          fov={75}
          near={0.1}
          far={1000}
        />

        {/* Lighting setup for proper mesh illumination */}
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={1}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-camera-far={50}
          shadow-camera-left={-10}
          shadow-camera-right={10}
          shadow-camera-top={10}
          shadow-camera-bottom={-10}
        />
        <directionalLight position={[-5, -5, -5]} intensity={0.3} />

        {/* Grid helper for spatial reference */}
        <gridHelper args={[20, 20, '#E0E0E0', '#F0F0F0']} />
        
        {/* Axes helper for orientation reference */}
        <axesHelper args={[5]} />

        {/* OrbitControls will be integrated in Task 25.4 */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          dampingFactor={0.05}
          enableDamping={true}
          maxPolarAngle={Math.PI * 0.9}
          minDistance={1}
          maxDistance={50}
        />

        {/* Children components (mesh, etc.) */}
        {children}
      </Canvas>
    </div>
  );
}; 