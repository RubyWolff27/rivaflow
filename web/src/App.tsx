import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import LogSession from './pages/LogSession';
import Reports from './pages/Reports';
import Readiness from './pages/Readiness';
import Techniques from './pages/Techniques';
import Videos from './pages/Videos';
import Profile from './pages/Profile';
import Glossary from './pages/Glossary';
import MovementDetail from './pages/MovementDetail';
import Contacts from './pages/Contacts';
import EditSession from './pages/EditSession';
import Login from './pages/Login';
import Register from './pages/Register';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <Layout>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/log" element={<LogSession />} />
                    <Route path="/session/edit/:id" element={<EditSession />} />
                    <Route path="/reports" element={<Reports />} />
                    <Route path="/readiness" element={<Readiness />} />
                    <Route path="/techniques" element={<Techniques />} />
                    <Route path="/videos" element={<Videos />} />
                    <Route path="/glossary" element={<Glossary />} />
                    <Route path="/glossary/:id" element={<MovementDetail />} />
                    <Route path="/contacts" element={<Contacts />} />
                    <Route path="/profile" element={<Profile />} />
                  </Routes>
                </Layout>
              </PrivateRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
