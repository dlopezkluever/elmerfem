import { useState } from 'react';

interface FAQItem {
  question: string;
  answer: string;
}

const faqs: FAQItem[] = [
  {
    question: "What is Finite Element Analysis (FEA)?",
    answer: "FEA is a numerical method for solving complex engineering problems by dividing them into smaller, simpler parts called finite elements. It's widely used to analyze stress, heat transfer, and fluid flow in engineering designs."
  },
  {
    question: "How do I start my first simulation?",
    answer: "1. Click on a simulation type from the home page (Heat Transfer or Structural Mechanics). 2. Fill in the parameter form with your geometry, material, and boundary conditions. 3. Click 'Run Simulation' and monitor the progress. 4. View and download your results when complete."
  },
  {
    question: "What do the different boundary conditions mean?",
    answer: "Boundary conditions define how your model interacts with its environment. For heat transfer: Temperature sets a fixed temperature, Heat Flux defines heat flow rate, and Convection models heat exchange with surrounding fluid. For structural: Fixed prevents movement, Force applies loads, and Displacement controls movement."
  },
  {
    question: "How do I choose the right mesh density?",
    answer: "Mesh density affects accuracy and computation time. Start with medium density (1.0) for most problems. Use finer meshes (1.5-2.0) for complex geometries or high gradients. Coarser meshes (0.5-0.8) are suitable for simple geometries or quick estimates."
  },
  {
    question: "Why did my simulation fail?",
    answer: "Common causes include: Invalid boundary conditions (e.g., over-constrained model), extreme material properties, or numerical instabilities. Check your input parameters and ensure they're physically realistic."
  },
  {
    question: "How can I validate my results?",
    answer: "Compare your results with: 1. Analytical solutions for simple cases, 2. Experimental data if available, 3. Engineering intuition (e.g., heat flows from hot to cold, stress concentrates at sharp corners)."
  }
];

function Help() {
  const [expandedItems, setExpandedItems] = useState<number[]>([]);

  const toggleExpanded = (index: number) => {
    setExpandedItems(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Help & Documentation</h1>

      {/* Quick Start Guide */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-4">Quick Start Guide</h2>
        <div className="card-neumorphic">
          <ol className="space-y-4">
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">1</span>
              <div>
                <h3 className="font-bold">Select a Simulation Type</h3>
                <p className="text-gray-600">Choose between Heat Transfer or Structural Mechanics from the home page.</p>
              </div>
            </li>
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">2</span>
              <div>
                <h3 className="font-bold">Configure Parameters</h3>
                <p className="text-gray-600">Set up your geometry, select materials, and define boundary conditions.</p>
              </div>
            </li>
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">3</span>
              <div>
                <h3 className="font-bold">Run Simulation</h3>
                <p className="text-gray-600">Click the Run button and monitor progress in real-time.</p>
              </div>
            </li>
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">4</span>
              <div>
                <h3 className="font-bold">Analyze Results</h3>
                <p className="text-gray-600">View visualizations and download result files for further analysis.</p>
              </div>
            </li>
          </ol>
        </div>
      </section>

      {/* Key Concepts */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-4">Key FEA Concepts</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card-neumorphic">
            <h3 className="font-bold mb-2">Geometry</h3>
            <p className="text-sm text-gray-600">
              The physical shape of your model. Start with simple shapes (box, cylinder, sphere) 
              to understand the basics before moving to complex geometries.
            </p>
          </div>
          <div className="card-neumorphic">
            <h3 className="font-bold mb-2">Materials</h3>
            <p className="text-sm text-gray-600">
              Define how your model responds to forces and heat. Each material has unique 
              properties like stiffness (Young's Modulus) and heat conductivity.
            </p>
          </div>
          <div className="card-neumorphic">
            <h3 className="font-bold mb-2">Boundary Conditions</h3>
            <p className="text-sm text-gray-600">
              Specify how your model interacts with its environment. These are essential 
              for defining the problem and getting meaningful results.
            </p>
          </div>
          <div className="card-neumorphic">
            <h3 className="font-bold mb-2">Mesh</h3>
            <p className="text-sm text-gray-600">
              Divides your geometry into small elements for calculation. Finer meshes give 
              more accurate results but take longer to compute.
            </p>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-4">Frequently Asked Questions</h2>
        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div key={index} className="card-neumorphic">
              <button
                onClick={() => toggleExpanded(index)}
                className="w-full text-left flex justify-between items-center"
              >
                <h3 className="font-bold pr-4">{faq.question}</h3>
                <svg 
                  className={`w-5 h-5 transform transition-transform ${expandedItems.includes(index) ? 'rotate-180' : ''}`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {expandedItems.includes(index) && (
                <p className="mt-4 text-gray-600">{faq.answer}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Resources */}
      <section>
        <h2 className="text-2xl font-bold mb-4">Additional Resources</h2>
        <div className="card-neumorphic">
          <ul className="space-y-3">
            <li>
              <a 
                href="https://www.elmerfem.org/documentation/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                ElmerFEM Official Documentation
              </a>
              <p className="text-sm text-gray-600">Comprehensive guides and technical details</p>
            </li>
            <li>
              <a 
                href="https://github.com/ElmerCSC/elmerfem" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                ElmerFEM GitHub Repository
              </a>
              <p className="text-sm text-gray-600">Source code and community contributions</p>
            </li>
            <li>
              <a 
                href="#" 
                className="text-gray-400 cursor-not-allowed font-medium"
              >
                Video Tutorials (Coming Soon)
              </a>
              <p className="text-sm text-gray-600">Step-by-step walkthroughs for beginners</p>
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}

export default Help; 