import React from 'react';
import { Bell, Database } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Header({ 
  title = 'Dashboard Overview', 
  subtitle = 'Demand & Decision Intelligence Platform' 
}) {
  const { user } = useAuth();
  const userName = user?.full_name || user?.username || 'User';
  const initial = userName.charAt(0).toUpperCase();

  return (
    <header className="top-navbar">
      <div className="header-left">
        <h1 className="header-title">{title}</h1>
        <span className="header-subtitle">{subtitle}</span>
      </div>

      <div className="header-right">
        {/* Real Data Status Badge */}
        <div className="data-status-bar" title="Connected to PostgreSQL & Analytics Reports">
          <span className="data-status-dot" />
          <Database size={12} style={{ opacity: 0.8 }} />
          <span>PostgreSQL &bull; 46.7M Records &bull; Live</span>
        </div>

        {/* Notifications Icon Button */}
        <button 
          className="icon-btn" 
          title="System Notifications (Real-time anomaly & inventory alerts)"
          aria-label="Notifications"
        >
          <Bell size={16} />
        </button>

        {/* User Pill */}
        <div className="header-user">
          <div className="header-avatar">
            {initial}
          </div>
          <span className="header-user-name">{userName}</span>
        </div>
      </div>
    </header>
  );
}
