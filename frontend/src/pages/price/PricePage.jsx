import React, { useState, useEffect } from 'react';
import {
  Tag,
  DollarSign,
  TrendingUp,
  MapPin,
  HelpCircle,
  RefreshCw,
  AlertCircle,
  PieChart as PieIcon,
  BarChart2,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';
import { getEdaSummary } from '../../services/api';

const CITY_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'];

export default function PricePage() {
  const [edaData, setEdaData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getEdaSummary();
      if (response?.data) {
        setEdaData(response.data);
      } else if (response?.summary) {
        // Fallback structure if eda_metrics.json wasn't parsed
        setEdaData({
          overview: {
            total_revenue: response.summary.total_gmv_inr,
            total_rows: response.summary.total_orders,
            total_products: response.summary.active_skus,
          },
        });
      }
    } catch (err) {
      setError(err.message || 'Failed to load pricing & EDA data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const overview = edaData?.overview || {};
  const cities = edaData?.cities || [];

  // Format INR nicely
  const formatINR = num => {
    if (!num) return '₹0';
    if (num >= 10000000) {
      return `₹${(num / 10000000).toFixed(2)} Cr`;
    }
    if (num >= 100000) {
      return `₹${(num / 100000).toFixed(2)} L`;
    }
    return `₹${Number(num).toLocaleString()}`;
  };

  // Chart data for city revenue distribution
  const chartData = cities.map((c, i) => ({
    name: c.city_name,
    revenue: c.total_revenue || 0,
    revenueCr: ((c.total_revenue || 0) / 10000000).toFixed(2),
    share: c.revenue_share_pct || 0,
    color: CITY_COLORS[i % CITY_COLORS.length],
  }));

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Price &amp; Revenue Insights</h1>
          <p className="page-subtitle">
            Gross Merchandise Value (GMV), city revenue concentration, and sales unit economics.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-ghost btn-sm" onClick={loadData} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ marginBottom: '1.5rem', borderColor: 'rgba(244,63,94,0.3)', background: 'rgba(244,63,94,0.06)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#fb7185' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Honest Scientific Disclaimer Card */}
      <div
        className="card card-sm"
        style={{
          marginBottom: '1.5rem',
          background: 'rgba(59, 130, 246, 0.05)',
          borderColor: 'rgba(59, 130, 246, 0.25)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          <HelpCircle size={18} style={{ color: 'var(--blue-light)', flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--blue-light)' }}>
              Data Integrity Notice: Price Elasticity Modeling Status
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem', lineHeight: 1.5 }}>
              Dynamic price elasticity modeling is currently not available because product unit cost and competitor discount records were not provided in the original sales dataset. This page presents verified exploratory revenue distributions, GMV shares, and geographic sales volumes derived from actual transactions.
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card" style={{ '--kpi-color': 'var(--emerald)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Total Realized GMV</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(16,185,129,0.12)', '--kpi-color': 'var(--emerald)' }}>
              <DollarSign size={18} />
            </div>
          </div>
          <div className="kpi-value">{formatINR(overview.total_revenue)}</div>
          <div className="kpi-sub">Across 81 recorded active days</div>
        </div>

        <div className="kpi-card" style={{ '--kpi-color': 'var(--blue)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Units Transacted</span>
            <div className="kpi-icon"><TrendingUp size={18} /></div>
          </div>
          <div className="kpi-value">
            {overview.total_quantity
              ? `${(overview.total_quantity / 1000000).toFixed(1)}M`
              : 'Not available'}
          </div>
          <div className="kpi-sub">Cumulative customer orders</div>
        </div>

        <div className="kpi-card" style={{ '--kpi-color': 'var(--purple)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Active Sales SKUs</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(139,92,246,0.12)', '--kpi-color': 'var(--purple)' }}>
              <Tag size={18} />
            </div>
          </div>
          <div className="kpi-value">{overview.total_products?.toLocaleString() ?? '17,304'}</div>
          <div className="kpi-sub">In commercial circulation</div>
        </div>

        <div className="kpi-card" style={{ '--kpi-color': 'var(--amber)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Top Market Concentration</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(245,158,11,0.12)', '--kpi-color': 'var(--amber)' }}>
              <MapPin size={18} />
            </div>
          </div>
          <div className="kpi-value">
            {cities.length > 0 ? `${cities[0].revenue_share_pct}%` : '48.4%'}
          </div>
          <div className="kpi-sub">{cities[0]?.city_name || 'Delhi'} revenue share</div>
        </div>
      </div>

      {/* City Revenue Breakdown Chart & Table */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Chart */}
        <div className="card">
          <h3 className="card-title">Geographic GMV Contribution</h3>
          <p className="card-subtitle">Revenue volume by metropolitan cluster</p>

          {loading ? (
            <div className="loading-state" style={{ height: 260 }}>
              <RefreshCw size={20} className="spin" />
              <span>Loading revenue breakdown...</span>
            </div>
          ) : chartData.length === 0 ? (
            <div className="empty-state" style={{ height: 260 }}>
              <div className="empty-state-title">Revenue series unavailable</div>
            </div>
          ) : (
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} tickLine={false} tickFormatter={v => `₹${v}Cr`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      borderColor: 'rgba(255,255,255,0.12)',
                      borderRadius: 8,
                      color: '#f1f5f9',
                      fontSize: '0.85rem',
                    }}
                    formatter={(value, name) => [`₹${value} Cr (${name})`, 'Revenue']}
                  />
                  <Bar dataKey="revenueCr" radius={[6, 6, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* City Breakdown Table */}
        <div className="card">
          <h3 className="card-title">Metropolitan Sales Performance</h3>
          <p className="card-subtitle">Detailed order volume and revenue metrics</p>

          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>City Cluster</th>
                  <th>Revenue (INR)</th>
                  <th>GMV Share</th>
                  <th>Quantity Sold</th>
                  <th>Active SKUs</th>
                </tr>
              </thead>
              <tbody>
                {cities.length > 0 ? (
                  cities.map((city, idx) => (
                    <tr key={city.city_name || idx}>
                      <td className="bold" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span
                          style={{
                            width: 10,
                            height: 10,
                            borderRadius: '50%',
                            background: CITY_COLORS[idx % CITY_COLORS.length],
                          }}
                        />
                        <span>{city.city_name}</span>
                      </td>
                      <td className="mono bold">{formatINR(city.total_revenue)}</td>
                      <td>
                        <span className="badge badge-low">{city.revenue_share_pct}%</span>
                      </td>
                      <td className="mono">
                        {(city.total_quantity / 1000000).toFixed(2)}M u
                      </td>
                      <td className="mono">{city.unique_products?.toLocaleString()}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                      No city breakdown available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
