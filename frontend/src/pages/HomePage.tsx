import { useNavigate } from 'react-router-dom';
import { SimulationType } from '../types/api';

function HomePage() {
  const navigate = useNavigate();

  const handleSimulationSelect = (type: SimulationType) => {
    // Store selected simulation type and navigate to form
    sessionStorage.setItem('selectedSimulationType', type);
    navigate('/form');
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header Section */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-gray-800 mb-4">
          Welcome to Finite Element Analysis
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Learn the fundamentals of FEA through hands-on simulations. Choose a simulation type
          below to begin your journey into computational engineering.
        </p>
      </div>

      {/* Simulation Type Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <SimulationCard
          title="Heat Transfer"
          description="Analyze temperature distribution and heat flow in materials. Perfect for understanding thermal dynamics."
          onClick={() => handleSimulationSelect(SimulationType.HEAT_TRANSFER)}
          available={true}
        />
        <SimulationCard
          title="Structural Mechanics"
          description="Study stress, strain, and deformation in structures. Essential for mechanical design analysis."
          onClick={() => handleSimulationSelect(SimulationType.STRUCTURAL_MECHANICS)}
          available={true}
        />
        <SimulationCard
          title="Fluid Dynamics"
          description="Explore fluid flow patterns and pressure distributions. Coming soon."
          onClick={() => {}}
          available={false}
        />
        <SimulationCard
          title="Electromagnetics"
          description="Investigate electric and magnetic field interactions. Coming soon."
          onClick={() => {}}
          available={false}
        />
      </div>

      {/* Educational Content */}
      <div className="card-neumorphic mb-8">
        <h2 className="text-2xl font-bold mb-4">Getting Started</h2>
        <div className="space-y-4 text-gray-700">
          <p>
            <strong>For Beginners:</strong> Start with Heat Transfer simulations to understand
            the basics of FEA. The guided interface will walk you through each step.
          </p>
          <p>
            <strong>Advanced Users:</strong> Structural Mechanics offers more complex scenarios
            with multiple boundary conditions and material properties.
          </p>
        </div>
      </div>
    </div>
  );
}

interface SimulationCardProps {
  title: string;
  description: string;
  onClick: () => void;
  available: boolean;
}

function SimulationCard({ title, description, onClick, available }: SimulationCardProps) {
  return (
    <button
      onClick={onClick}
      disabled={!available}
      className={`
        card-neumorphic text-left transition-all duration-300
        ${
          available
            ? 'hover:shadow-neumorphic-hover active:shadow-neumorphic-inset cursor-pointer'
            : 'opacity-60 cursor-not-allowed'
        }
      `}
    >
      <h3 className="text-2xl font-bold mb-3">{title}</h3>
      <p className="text-gray-600">{description}</p>
      {!available && (
        <span className="inline-block mt-3 text-sm text-gray-500 font-medium">
          Coming Soon
        </span>
      )}
    </button>
  );
}

export default HomePage; 