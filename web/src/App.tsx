import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import LogSession from './pages/LogSession';
import Reports from './pages/Reports';
import Readiness from './pages/Readiness';
import Techniques from './pages/Techniques';
import Videos from './pages/Videos';
import Profile from './pages/Profile';
import Glossary from './pages/Glossary';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/log" element={<LogSession />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/readiness" element={<Readiness />} />
          <Route path="/techniques" element={<Techniques />} />
          <Route path="/videos" element={<Videos />} />
          <Route path="/glossary" element={<Glossary />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
