import React from 'react';
import { GeometryParameters, EducationalGeometryType } from '../../types/geometry';

interface GeometryPreviewProps {
  geometry: GeometryParameters | null;
  meshDensity: number;
  estimatedElements: number;
}

export const GeometryPreview: React.FC<GeometryPreviewProps> = ({
  geometry,
  meshDensity,
  estimatedElements
}) => {
  const renderGeometry = () => {
    if (!geometry) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          <p>Select a geometry type to preview</p>
        </div>
      );
    }

    const svgSize = 200;
    const padding = 20;
    const scale = (svgSize - 2 * padding) / 10; // Scale to fit 10m max dimension

    switch (geometry.type) {
      case EducationalGeometryType.RECTANGLE: {
        const width = geometry.params.width * scale;
        const height = geometry.params.height * scale;
        const x = (svgSize - width) / 2;
        const y = (svgSize - height) / 2;

        return (
          <svg width={svgSize} height={svgSize} className="bg-neumorphic-bg shadow-neumorphic-inset rounded-xl">
            <rect
              x={x}
              y={y}
              width={width}
              height={height}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-gray-700"
            />
            {/* Grid lines to represent mesh density */}
            {renderMeshGrid(x, y, width, height, meshDensity)}
          </svg>
        );
      }

      case EducationalGeometryType.CIRCLE: {
        const radius = geometry.params.radius * scale;
        const cx = svgSize / 2;
        const cy = svgSize / 2;

        return (
          <svg width={svgSize} height={svgSize} className="bg-neumorphic-bg shadow-neumorphic-inset rounded-xl">
            <circle
              cx={cx}
              cy={cy}
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-gray-700"
            />
            {/* Radial mesh representation */}
            {renderRadialMesh(cx, cy, radius, meshDensity)}
          </svg>
        );
      }

      case EducationalGeometryType.ANNULUS: {
        const innerRadius = geometry.params.innerRadius * scale;
        const outerRadius = geometry.params.outerRadius * scale;
        const cx = svgSize / 2;
        const cy = svgSize / 2;

        return (
          <svg width={svgSize} height={svgSize} className="bg-neumorphic-bg shadow-neumorphic-inset rounded-xl">
            <circle
              cx={cx}
              cy={cy}
              r={outerRadius}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-gray-700"
            />
            <circle
              cx={cx}
              cy={cy}
              r={innerRadius}
              fill="#F0F0F0"
              stroke="currentColor"
              strokeWidth="2"
              className="text-gray-700"
            />
            {/* Annular mesh representation */}
            {renderAnnularMesh(cx, cy, innerRadius, outerRadius, meshDensity)}
          </svg>
        );
      }

      case EducationalGeometryType.L_SHAPE: {
        const width = geometry.params.width * scale;
        const height = geometry.params.height * scale;
        const notchWidth = geometry.params.notchWidth * scale;
        const notchHeight = geometry.params.notchHeight * scale;
        const x = (svgSize - width) / 2;
        const y = (svgSize - height) / 2;

        const path = `
          M ${x} ${y}
          L ${x + width} ${y}
          L ${x + width} ${y + height}
          L ${x + width - notchWidth} ${y + height}
          L ${x + width - notchWidth} ${y + height - notchHeight}
          L ${x} ${y + height - notchHeight}
          Z
        `;

        return (
          <svg width={svgSize} height={svgSize} className="bg-neumorphic-bg shadow-neumorphic-inset rounded-xl">
            <path
              d={path}
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-gray-700"
            />
            {/* L-shape mesh representation */}
            {renderLShapeMesh(x, y, width, height, notchWidth, notchHeight, meshDensity)}
          </svg>
        );
      }

      default:
        return null;
    }
  };

  const renderMeshGrid = (x: number, y: number, width: number, height: number, density: number) => {
    const lines = [];
    const divisions = density * 2; // More divisions for higher density

    // Vertical lines
    for (let i = 1; i < divisions; i++) {
      const xPos = x + (width * i) / divisions;
      lines.push(
        <line
          key={`v-${i}`}
          x1={xPos}
          y1={y}
          x2={xPos}
          y2={y + height}
          stroke="currentColor"
          strokeWidth="0.5"
          opacity="0.3"
          className="text-gray-500"
        />
      );
    }

    // Horizontal lines
    for (let i = 1; i < divisions; i++) {
      const yPos = y + (height * i) / divisions;
      lines.push(
        <line
          key={`h-${i}`}
          x1={x}
          y1={yPos}
          x2={x + width}
          y2={yPos}
          stroke="currentColor"
          strokeWidth="0.5"
          opacity="0.3"
          className="text-gray-500"
        />
      );
    }

    return lines;
  };

  const renderRadialMesh = (cx: number, cy: number, radius: number, density: number) => {
    const lines = [];
    const radialDivisions = density * 4;
    const circularDivisions = density * 2;

    // Radial lines
    for (let i = 0; i < radialDivisions; i++) {
      const angle = (i * 2 * Math.PI) / radialDivisions;
      lines.push(
        <line
          key={`r-${i}`}
          x1={cx}
          y1={cy}
          x2={cx + radius * Math.cos(angle)}
          y2={cy + radius * Math.sin(angle)}
          stroke="currentColor"
          strokeWidth="0.5"
          opacity="0.3"
          className="text-gray-500"
        />
      );
    }

    // Circular lines
    for (let i = 1; i < circularDivisions; i++) {
      const r = (radius * i) / circularDivisions;
      lines.push(
        <circle
          key={`c-${i}`}
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth="0.5"
          opacity="0.3"
          className="text-gray-500"
        />
      );
    }

    return lines;
  };

  const renderAnnularMesh = (cx: number, cy: number, innerRadius: number, outerRadius: number, density: number) => {
    const lines = [];
    const radialDivisions = density * 6;
    const circularDivisions = density;

    // Radial lines
    for (let i = 0; i < radialDivisions; i++) {
      const angle = (i * 2 * Math.PI) / radialDivisions;
      const x1 = cx + innerRadius * Math.cos(angle);
      const y1 = cy + innerRadius * Math.sin(angle);
      const x2 = cx + outerRadius * Math.cos(angle);
      const y2 = cy + outerRadius * Math.sin(angle);

      lines.push(
        <line
          key={`r-${i}`}
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke="currentColor"
          strokeWidth="0.5"
          opacity="0.3"
          className="text-gray-500"
        />
      );
    }

    // Circular lines
    for (let i = 1; i < circularDivisions; i++) {
      const r = innerRadius + ((outerRadius - innerRadius) * i) / circularDivisions;
      lines.push(
        <circle
          key={`c-${i}`}
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth="0.5"
          opacity="0.3"
          className="text-gray-500"
        />
      );
    }

    return lines;
  };

  const renderLShapeMesh = (
    x: number,
    y: number,
    width: number,
    height: number,
    notchWidth: number,
    notchHeight: number,
    density: number
  ) => {
    const lines = [];
    const divisions = density * 2;

    // Simplified mesh representation for L-shape
    // Vertical lines
    for (let i = 1; i < divisions; i++) {
      const xPos = x + (width * i) / divisions;
      if (xPos < x + width - notchWidth) {
        lines.push(
          <line
            key={`v-${i}`}
            x1={xPos}
            y1={y}
            x2={xPos}
            y2={y + height - notchHeight}
            stroke="currentColor"
            strokeWidth="0.5"
            opacity="0.3"
            className="text-gray-500"
          />
        );
      } else {
        lines.push(
          <line
            key={`v-${i}`}
            x1={xPos}
            y1={y}
            x2={xPos}
            y2={y + height}
            stroke="currentColor"
            strokeWidth="0.5"
            opacity="0.3"
            className="text-gray-500"
          />
        );
      }
    }

    // Horizontal lines
    for (let i = 1; i < divisions; i++) {
      const yPos = y + (height * i) / divisions;
      if (yPos < y + height - notchHeight) {
        lines.push(
          <line
            key={`h-${i}`}
            x1={x}
            y1={yPos}
            x2={x + width}
            y2={yPos}
            stroke="currentColor"
            strokeWidth="0.5"
            opacity="0.3"
            className="text-gray-500"
          />
        );
      } else {
        lines.push(
          <line
            key={`h-${i}`}
            x1={x}
            y1={yPos}
            x2={x + width - notchWidth}
            y2={yPos}
            stroke="currentColor"
            strokeWidth="0.5"
            opacity="0.3"
            className="text-gray-500"
          />
        );
      }
    }

    return lines;
  };

  return (
    <div className="card-neumorphic">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Geometry Preview</h3>
      <div className="flex flex-col items-center">
        {renderGeometry()}
        {geometry && (
          <div className="mt-4 text-sm text-gray-600 text-center">
            <p>Mesh Density: Level {meshDensity}</p>
            <p>Estimated Elements: ~{estimatedElements.toLocaleString()}</p>
          </div>
        )}
      </div>
    </div>
  );
}; 