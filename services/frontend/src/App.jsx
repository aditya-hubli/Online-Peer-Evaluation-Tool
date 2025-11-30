import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence } from 'framer-motion';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Teams from './pages/Teams';
import Forms from './pages/Forms';
import Evaluations from './pages/Evaluations';
import Reports from './pages/Reports';
import Header from './components/Header';
import PageTransition from './components/PageTransition';

function AnimatedRoutes({ user, handleLogin, handleLogout }) {
  const location = useLocation();

  return (
    <>
      {user && <Header user={user} onLogout={handleLogout} />}
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route 
            path="/login" 
            element={user ? <Navigate to="/dashboard" /> : <PageTransition><Login onLogin={handleLogin} /></PageTransition>} 
          />
          <Route 
            path="/register" 
            element={user ? <Navigate to="/dashboard" /> : <PageTransition><Register /></PageTransition>} 
          />
          <Route 
            path="/dashboard" 
            element={user ? <PageTransition><Dashboard user={user} /></PageTransition> : <Navigate to="/login" />} 
          />
          <Route 
            path="/projects" 
            element={user ? <PageTransition><Projects user={user} /></PageTransition> : <Navigate to="/login" />} 
          />
          <Route 
            path="/teams" 
            element={user ? <PageTransition><Teams user={user} /></PageTransition> : <Navigate to="/login" />} 
          />
          <Route 
            path="/forms" 
            element={user ? <PageTransition><Forms user={user} /></PageTransition> : <Navigate to="/login" />} 
          />
          <Route 
            path="/evaluations" 
            element={user ? <PageTransition><Evaluations user={user} /></PageTransition> : <Navigate to="/login" />} 
          />
          <Route 
            path="/reports" 
            element={user ? <PageTransition><Reports user={user} /></PageTransition> : <Navigate to="/login" />} 
          />
          <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} />} />
        </Routes>
      </AnimatePresence>
    </>
  );
}

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  return (
    <Router>
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'rgba(24, 24, 36, 0.95)',
            color: '#e4e4e7',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            borderRadius: '12px',
            padding: '16px',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(20px)',
            fontSize: '14px',
            fontWeight: '600'
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
            style: {
              border: '1px solid rgba(16, 185, 129, 0.3)',
            }
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
            style: {
              border: '1px solid rgba(239, 68, 68, 0.3)',
            }
          },
        }}
      />
      <AnimatedRoutes user={user} handleLogin={handleLogin} handleLogout={handleLogout} />
    </Router>
  );
}

export default App;
