import { Link, useLocation } from 'react-router-dom';
import { LogOut, Users, FolderKanban, ClipboardList, BarChart3, LayoutDashboard, FileText, Sparkles } from 'lucide-react';
import { useState } from 'react';
import ConfirmModal from './ConfirmModal';

function Header({ user, onLogout }) {
  const location = useLocation();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const isActive = (path) => location.pathname === path;

  const handleLogoutClick = () => {
    setShowLogoutConfirm(true);
  };

  const handleConfirmLogout = () => {
    setShowLogoutConfirm(false);
    onLogout();
  };

  return (
    <header className="header">
      <div className="container">
        <nav className="nav">
          <div style={{ display: 'flex', alignItems: 'center', gap: '40px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ 
                width: '40px', 
                height: '40px', 
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.5)'
              }}>
                <Sparkles size={22} color="white" />
              </div>
              <h1 style={{ 
                fontSize: '20px', 
                fontWeight: '800', 
                background: 'linear-gradient(135deg, #a78bfa 0%, #c4b5fd 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                letterSpacing: '-0.02em'
              }}>
                Peer Evaluation
              </h1>
            </div>
            <ul className="nav-links">
              <li>
                <Link 
                  to="/dashboard" 
                  className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
                >
                  <LayoutDashboard size={16} />
                  Dashboard
                </Link>
              </li>
              <li>
                <Link 
                  to="/projects" 
                  className={`nav-link ${isActive('/projects') ? 'active' : ''}`}
                >
                  <FolderKanban size={16} />
                  Projects
                </Link>
              </li>
              <li>
                <Link 
                  to="/teams" 
                  className={`nav-link ${isActive('/teams') ? 'active' : ''}`}
                >
                  <Users size={16} />
                  Teams
                </Link>
              </li>
              <li>
                <Link 
                  to="/forms" 
                  className={`nav-link ${isActive('/forms') ? 'active' : ''}`}
                >
                  <FileText size={16} />
                  Forms
                </Link>
              </li>
              <li>
                <Link 
                  to="/evaluations" 
                  className={`nav-link ${isActive('/evaluations') ? 'active' : ''}`}
                >
                  <ClipboardList size={16} />
                  Evaluations
                </Link>
              </li>
              <li>
                <Link 
                  to="/reports" 
                  className={`nav-link ${isActive('/reports') ? 'active' : ''}`}
                >
                  <BarChart3 size={16} />
                  Reports
                </Link>
              </li>
            </ul>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ 
              padding: '8px 16px', 
              background: 'rgba(99, 102, 241, 0.1)',
              borderRadius: '10px',
              border: '1px solid rgba(99, 102, 241, 0.3)'
            }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e4e4e7' }}>
                {user.name}
              </span>
              <span style={{ fontSize: '13px', color: '#a1a1aa', marginLeft: '8px' }}>
                · {user.role}
              </span>
            </div>
            <button onClick={handleLogoutClick} className="btn btn-secondary" style={{ padding: '9px 18px' }}>
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </nav>
      </div>

      <ConfirmModal
        show={showLogoutConfirm}
        onConfirm={handleConfirmLogout}
        onCancel={() => setShowLogoutConfirm(false)}
        title="Confirm Logout"
        message="Are you sure you want to logout? Any unsaved changes will be lost."
        confirmText="Logout"
        cancelText="Cancel"
        variant="danger"
      />
    </header>
  );
}

export default Header;
