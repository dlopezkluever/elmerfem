import { useMaterials } from '../hooks/useMaterials';

function MaterialLibrary() {
  const { materials, loading, error } = useMaterials();

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Material Library</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card-neumorphic animate-pulse">
              <div className="h-6 bg-gray-300 rounded mb-4"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-300 rounded"></div>
                <div className="h-4 bg-gray-300 rounded w-3/4"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto text-center">
        <h1 className="text-4xl font-bold mb-4">Material Library</h1>
        <div className="card-neumorphic">
          <p className="text-red-600 text-lg">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="btn-neumorphic-primary mt-4"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-4xl font-bold mb-4">Material Library</h1>
      <p className="text-lg text-gray-600 mb-8">
        Browse our collection of pre-defined materials for your FEA simulations. 
        Each material includes essential properties for heat transfer and structural mechanics analyses.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {materials.map((material) => (
          <div key={material.id} className="card-neumorphic hover:shadow-neumorphic-hover transition-all">
            <h3 className="text-xl font-bold mb-3">{material.name}</h3>
            <dl className="space-y-2 text-sm">
              {material.properties.E && (
                <div className="flex justify-between">
                  <dt className="text-gray-600">Young's Modulus:</dt>
                  <dd className="font-mono">{formatScientific(material.properties.E)} Pa</dd>
                </div>
              )}
              {material.properties.nu !== undefined && (
                <div className="flex justify-between">
                  <dt className="text-gray-600">Poisson's Ratio:</dt>
                  <dd className="font-mono">{material.properties.nu}</dd>
                </div>
              )}
              {material.properties.rho && (
                <div className="flex justify-between">
                  <dt className="text-gray-600">Density:</dt>
                  <dd className="font-mono">{material.properties.rho} kg/m³</dd>
                </div>
              )}
              {material.properties.k && (
                <div className="flex justify-between">
                  <dt className="text-gray-600">Thermal Conductivity:</dt>
                  <dd className="font-mono">{material.properties.k} W/m·K</dd>
                </div>
              )}
              {material.properties.C && (
                <div className="flex justify-between">
                  <dt className="text-gray-600">Specific Heat:</dt>
                  <dd className="font-mono">{material.properties.C} J/kg·K</dd>
                </div>
              )}
            </dl>
          </div>
        ))}
      </div>

      <div className="mt-12 card-neumorphic bg-blue-50">
        <h2 className="text-2xl font-bold mb-4">Understanding Material Properties</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-bold mb-2">Mechanical Properties</h3>
            <ul className="space-y-2 text-sm">
              <li><strong>Young's Modulus (E):</strong> Measures material stiffness</li>
              <li><strong>Poisson's Ratio (ν):</strong> Ratio of transverse to axial strain</li>
              <li><strong>Density (ρ):</strong> Mass per unit volume</li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold mb-2">Thermal Properties</h3>
            <ul className="space-y-2 text-sm">
              <li><strong>Thermal Conductivity (k):</strong> Heat transfer rate</li>
              <li><strong>Specific Heat (cp):</strong> Heat capacity per unit mass</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function formatScientific(value: number): string {
  if (value >= 1e9) {
    return (value / 1e9).toFixed(1) + 'e9';
  } else if (value >= 1e6) {
    return (value / 1e6).toFixed(1) + 'e6';
  } else if (value >= 1e3) {
    return (value / 1e3).toFixed(1) + 'e3';
  }
  return value.toString();
}

export default MaterialLibrary; 