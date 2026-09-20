import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  UploadCloud,
  TrendingUp,
  Boxes,
  Activity,
  Tag,
  ShieldCheck,
  Bot,
  LogOut,
  BarChart3,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

/* ── Nav sections (auth-test removed from nav) ────────────────────── */
const navSections = [
  {
    label: 'Overview',
    items: [
      { name: 'Dashboard',     path: '/dashboard',     icon: LayoutDashboard },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { name: 'Demand Forecast', path: '/forecast',     icon: TrendingUp },
      { name: 'Inventory',       path: '/inventory',    icon: Boxes },
      { name: 'Trends & Anomalies', path: '/trends',   icon: Activity },
      { name: 'Price Insights',  path: '/price-insights', icon: Tag },
      { name: 'Evaluation',      path: '/evaluation',   icon: ShieldCheck },
    ],
  },
  {
    label: 'Tools',
    items: [
      { name: 'Data Upload',   path: '/upload',    icon: UploadCloud },
      { name: 'AI Assistant',  path: '/assistant', icon: Bot },
    ],
  },
];

/* Role badge colour map */
const roleColors = {
  admin:   { bg: 'rgba(244,63,94,0.14)',   text: '#fb7185'  },
  manager: { bg: 'rgba(245,158,11,0.14)',  text: '#fbbf24'  },
  viewer:  { bg: 'rgba(59,130,246,0.14)',  text: '#60a5fa'  },
};

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  const displayName = user?.full_name ?? user?.username ?? 'User';
  const initials = displayName
    .split(' ')
    .slice(0, 2)
    .map(w => w[0] ?? '')
    .join('')
    .toUpperCase() || '?';

  const role = user?.role ?? 'viewer';
  const rc = roleColors[role] ?? roleColors.viewer;

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M3 17l5-8 4 5 3-4 6 7" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <span className="sidebar-brand-name">DemandIQ</span>
        <span className="sidebar-brand-tag">AI</span>
      </div>

      {/* Navigation */}
      <nav className="sidebar-scroll">
        {navSections.map(section => (
          <div key={section.label}>
            <div className="sidebar-section-label">{section.label}</div>
            {section.items.map(({ name, path, icon: Icon }) => (
              <NavLink
                key={path}
                to={path}
                className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
              >
                <Icon size={17} className="nav-link-icon" />
                <span>{name}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* User footer */}
      <div className="sidebar-footer">
        {user ? (
          <div className="sb-user">
            <div className="sb-avatar">{initials}</div>
            <div className="sb-user-info">
              <span className="sb-user-name">{displayName}</span>
              <span className="sb-role-badge" style={{ background: rc.bg, color: rc.text }}>
                {role}
              </span>
            </div>
            <button className="sb-logout" onClick={handleLogout} title="Sign out">
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <NavLink to="/login" className="nav-link" style={{ color: 'var(--text-muted)' }}>
            <LogOut size={17} />
            <span>Sign In</span>
          </NavLink>
        )}
      </div>
    </aside>
  );
}
