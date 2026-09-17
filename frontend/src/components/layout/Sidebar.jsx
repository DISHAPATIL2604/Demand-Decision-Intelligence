import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  UploadCloud,
  TrendingUp,
  Boxes,
  LineChart,
  Tag,
  ShieldCheck,
  Bot,
  LogOut,
  KeyRound,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const navItems = [
  { name: 'Dashboard',     path: '/dashboard',     icon: LayoutDashboard },
  { name: 'Data Upload',   path: '/upload',         icon: UploadCloud },
  { name: 'Forecast',      path: '/forecast',       icon: TrendingUp },
  { name: 'Inventory',     path: '/inventory',      icon: Boxes },
  { name: 'Trends',        path: '/trends',         icon: LineChart },
  { name: 'Price Insights',path: '/price-insights', icon: Tag },
  { name: 'Evaluation',    path: '/evaluation',     icon: ShieldCheck },
  { name: 'Assistant',     path: '/assistant',      icon: Bot },
  { name: 'Auth Testing',  path: '/auth-test',      icon: KeyRound },
];

/* Role badge colour map */
const roleColor = {
  admin:   { bg: 'rgba(239,68,68,0.15)',   text: '#f87171'  },
  manager: { bg: 'rgba(245,158,11,0.15)',  text: '#fbbf24'  },
  viewer:  { bg: 'rgba(59,130,246,0.15)',  text: '#60a5fa'  },
};

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  /* Derive initials & role colours */
  const initials = user
    ? (user.full_name ?? user.username ?? 'U')
        .split(' ')
        .slice(0, 2)
        .map(w => w[0])
        .join('')
        .toUpperCase()
    : '?';

  const role    = user?.role ?? 'viewer';
  const rc      = roleColor[role] ?? roleColor.viewer;

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <TrendingUp size={22} color="#3b82f6" />
        <span>DemandIQ</span>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {navItems.map(({ name, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            <Icon size={18} />
            <span>{name}</span>
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="sidebar-footer">
        {user ? (
          <div className="sb-user">
            {/* Avatar */}
            <div className="sb-avatar">{initials}</div>

            {/* Info */}
            <div className="sb-user-info">
              <span className="sb-user-name">
                {user.full_name ?? user.username}
              </span>
              <span
                className="sb-role-badge"
                style={{ background: rc.bg, color: rc.text }}
              >
                {role}
              </span>
            </div>

            {/* Logout */}
            <button className="sb-logout" onClick={handleLogout} title="Sign out">
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <NavLink to="/login" className="nav-link" style={{ color: 'var(--text-muted)' }}>
            <LogOut size={18} />
            <span>Sign In</span>
          </NavLink>
        )}
      </div>
    </aside>
  );
}
