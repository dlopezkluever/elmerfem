import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import ParameterForm from './pages/ParameterForm';
import SimulationPage from './pages/SimulationPage';
import ResultPage from './pages/ResultPage';
import MaterialLibrary from './pages/MaterialLibrary';
import Help from './pages/Help';
import Settings from './pages/Settings';
import { GeometryTestPage } from './pages/GeometryTestPage';
import { MeshPreviewTestPage } from './pages/MeshPreviewTestPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-neumorphic-bg">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/form" element={<ParameterForm />} />
            <Route path="/progress/:id" element={<SimulationPage />} />
            <Route path="/result/:id" element={<ResultPage />} />
            <Route path="/materials" element={<MaterialLibrary />} />
            <Route path="/help" element={<Help />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/geometry-test" element={<GeometryTestPage />} />
            <Route path="/mesh-preview-test" element={<MeshPreviewTestPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function NotFound() {
  return (
    <div className="text-center py-20">
      <h1 className="text-4xl font-bold mb-4">404 - Page Not Found</h1>
      <p className="text-gray-600 mb-8">The page you're looking for doesn't exist.</p>
      <a href="/" className="btn-neumorphic-primary">
        Back to Home
      </a>
    </div>
  );
}

export default App; 