import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Fleet from './pages/Fleet';
import Agents from './pages/Agents';
import VisionLab from './pages/VisionLab';
import Landing from './pages/Landing';

function App() {
  return (
    <Router>
      <Routes>
        {/* Landing page — no Navbar */}
        <Route path="/" element={<Landing />} />

        {/* Main app pages — with Navbar */}
        <Route path="/fleet" element={<><Navbar /><Fleet /></>} />
        <Route path="/agents" element={<><Navbar /><Agents /></>} />
        <Route path="/vision" element={<><Navbar /><VisionLab /></>} />
      </Routes>
    </Router>
  );
}

export default App;