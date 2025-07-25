import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import RecentSimulationsSidebar from './RecentSimulationsSidebar';

function Navbar() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <nav className="bg-neumorphic-bg shadow-neumorphic sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <Link to="/" className="flex items-center space-x-3">
            <span className="text-2xl font-bold text-gray-800">ElmerFEM Simulator</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-6">
            <NavLink to="/" isActive={isActive('/')}>
              Home
            </NavLink>
            <NavLink to="/materials" isActive={isActive('/materials')}>
              Material Library
            </NavLink>
            <NavLink to="/help" isActive={isActive('/help')}>
              Help/Documentation
            </NavLink>
            <NavLink to="/settings" isActive={isActive('/settings')}>
              Settings
            </NavLink>
            <button
              onClick={() => setSidebarOpen(true)}
              className="px-4 py-2 rounded-lg font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 transition-all duration-200"
            >
              Recent Simulations
            </button>
          </div>
        </div>
      </div>
      <RecentSimulationsSidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
      />
    </nav>
  );
}

interface NavLinkProps {
  to: string;
  isActive: boolean;
  children: React.ReactNode;
}

function NavLink({ to, isActive, children }: NavLinkProps) {
  return (
    <Link
      to={to}
      className={`
        px-4 py-2 rounded-lg font-medium transition-all duration-200
        ${
          isActive
            ? 'shadow-neumorphic-inset text-primary'
            : 'hover:shadow-neumorphic text-gray-700 hover:text-gray-900'
        }
      `}
    >
      {children}
    </Link>
  );
}

export default Navbar; 