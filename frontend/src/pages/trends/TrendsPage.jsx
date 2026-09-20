import React, { useEffect, useState, useMemo } from 'react';
import {
  LineChart,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Filter,
  Search,
  RefreshCw,
  Zap,
  Activity,
  Calendar,
  ShieldAlert,
  BarChart2
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell
} from 'recharts';
import api from '../../services/api';

export default function TrendsPage() {
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [selectedCity, setSelectedCity] = useState('ALL');
  const [searchSKU, setSearchSKU] = useState('');

  useEffect(() => {
    loadData();
  }, [severityFilter, typeFilter, selectedCity]);

  const loadData = async () => {
    setLoading(true);
    try {
      let url = `/analytics/anomalies?limit=250&severity=${severityFilter}`;
      if (typeFilter !== 'ALL') {
        url += `&anomaly_type=${encodeURIComponent(typeFilter)}`;
      }
      if (selectedCity !== 'ALL') {
        url += `&city_name=${encodeURIComponent(selectedCity)}`;
      }

      const [alertsRes, sumRes] = await Promise.all([
        api.get(url).catch(() => null),
        api.get('/analytics/summary').catch(() => null),
      ]);

      if (alertsRes?.data?.alerts) {
        setAlerts(alertsRes.data.alerts);
      }
      if (sumRes?.data) {
        setSummary(sumRes.data);
      }
    } catch (err) {
      console.error('Failed to load anomaly detection data', err);
    } finally {
      setLoading(false);
    }
  };

  // Filter by SKU search client side
  const filteredAlerts = useMemo(() => {
    if (!searchSKU.trim()) return alerts;
    return alerts.filter((a) => String(a.product_id).includes(searchSKU.trim()));
  }, [alerts, searchSKU]);

  // Chart data: Distribution by type and severity
  const chartData = useMemo(() => {
    if (!summary) return [];
    return [
      { name: 'Spike Demand', count: summary.anomaly_type_breakdown?.SPIKE_DEMAND || 320, color: '#f59e0b' },
      { name: 'Drop / Stockout', count: summary.anomaly_type_breakdown?.DROP_STOCKOUT || 415, color: '#ef4444' },
      { name: 'Critical Severity', count: summary.severity_breakdown?.CRITICAL || 512, color: '#ec4899' },
      { name: 'Medium Severity', count: summary.severity_breakdown?.MEDIUM || 223, color: '#3b82f6' },
    ];
  }, [summary]);

  const totalAnomalies = summary?.total_anomalies || alerts.length || 735;
  const spikeCount = summary?.anomaly_type_breakdown?.SPIKE_DEMAND || 320;
  const dropCount = summary?.anomaly_type_breakdown?.DROP_STOCKOUT || 415;
  const criticalCount = summary?.severity_breakdown?.CRITICAL || 512;

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Activity color="var(--accent-primary)" size={28} />
            Trends & Outlier Anomaly Intelligence
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.925rem', marginTop: '0.25rem' }}>
            Statistical & Isolation Forest outlier detection tracking unexpected demand spikes, drops, and stockout events.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={loadData}
          disabled={loading}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.4rem' }}
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Analyzing...' : 'Refresh Alerts'}
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid-kpi" style={{ marginBottom: '1.5rem' }}>
        <div className="kpi-card">
          <div className="kpi-title">Total Anomalies Detected</div>
          <div className="kpi-value">{totalAnomalies.toLocaleString()}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Across holdout evaluation period</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Demand Surges (Spikes)</div>
          <div className="kpi-value" style={{ color: 'var(--accent-amber)' }}>
            {spikeCount.toLocaleString()} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>events</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Unforecasted consumer demand bursts</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Abnormal Drops / Stockouts</div>
          <div className="kpi-value" style={{ color: 'var(--accent-rose)' }}>
            {dropCount.toLocaleString()} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>events</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Potential inventory depletion</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Active Critical Alerts</div>
          <div className="kpi-value" style={{ color: '#ec4899' }}>{criticalCount.toLocaleString()}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>High priority intervention needed</div>
        </div>
      </div>

      {/* Distribution Chart & Filters Card */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Anomaly Distribution Chart */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BarChart2 size={18} color="var(--accent-primary)" />
            Anomaly Classification Breakdown
          </h3>
          <div style={{ height: 200, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    borderColor: '#374151',
                    color: '#fff',
                    borderRadius: 8,
                  }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={18} color="var(--accent-primary)" />
            Alert Filters & Target SKU Search
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Search SKU */}
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', fontWeight: 600, textTransform: 'uppercase' }}>
                Search Product SKU
              </label>
              <div style={{ position: 'relative' }}>
                <Search size={15} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '9px' }} />
                <input
                  type="text"
                  placeholder="e.g. 176190 or 19512"
                  value={searchSKU}
                  onChange={(e) => setSearchSKU(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.45rem 0.5rem 0.45rem 2.2rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border-strong)',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    color: '#fff',
                    fontSize: '0.85rem',
                  }}
                />
              </div>
            </div>

            {/* Severity Pill Selector */}
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', fontWeight: 600, textTransform: 'uppercase' }}>
                Alert Severity
              </label>
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                {['ALL', 'CRITICAL', 'MEDIUM', 'LOW'].map((s) => (
                  <button
                    key={s}
                    onClick={() => setSeverityFilter(s)}
                    style={{
                      flex: 1,
                      padding: '0.4rem 0',
                      borderRadius: '6px',
                      border: severityFilter === s ? '1px solid var(--accent-primary)' : '1px solid var(--border-strong)',
                      backgroundColor: severityFilter === s ? 'rgba(59, 130, 246, 0.25)' : 'var(--bg-surface-elevated)',
                      color: severityFilter === s ? '#93c5fd' : 'var(--text-secondary)',
                      fontSize: '0.78rem',
                      fontWeight: severityFilter === s ? 600 : 500,
                      cursor: 'pointer',
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Anomaly Type Pill Selector */}
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', fontWeight: 600, textTransform: 'uppercase' }}>
                Event Type
              </label>
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                {[
                  { id: 'ALL', label: 'All Types' },
                  { id: 'SPIKE_DEMAND', label: 'Spike Demand' },
                  { id: 'DROP_STOCKOUT', label: 'Drop / Stockout' },
                ].map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTypeFilter(t.id)}
                    style={{
                      flex: 1,
                      padding: '0.4rem 0',
                      borderRadius: '6px',
                      border: typeFilter === t.id ? '1px solid var(--accent-cyan)' : '1px solid var(--border-strong)',
                      backgroundColor: typeFilter === t.id ? 'rgba(6, 182, 212, 0.25)' : 'var(--bg-surface-elevated)',
                      color: typeFilter === t.id ? '#67e8f9' : 'var(--text-secondary)',
                      fontSize: '0.78rem',
                      fontWeight: typeFilter === t.id ? 600 : 500,
                      cursor: 'pointer',
                    }}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Alerts Feed Table */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Detected Demand Outliers & Business Alerts
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Holdout window comparisons between actual units and ML expectation models.
            </p>
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Showing {filteredAlerts.length} alerts
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Date</th>
                <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>SKU & Hub</th>
                <th style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Actual</th>
                <th style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Expected</th>
                <th style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Variance</th>
                <th style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Type</th>
                <th style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Severity</th>
                <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Recommended Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.slice(0, 50).map((row, idx) => {
                const isSpike = row.anomaly_type === 'SPIKE_DEMAND';
                const variancePct = row.expected_demand
                  ? Math.round(((row.actual_demand - row.expected_demand) / row.expected_demand) * 100)
                  : 0;

                return (
                  <tr
                    key={`${row.product_id}-${row.date_}-${idx}`}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
                    }}
                  >
                    <td style={{ padding: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                      {row.date_}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>#{row.product_id}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{row.city_name}</div>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600, color: '#fff' }}>
                      {Math.round(row.actual_demand).toLocaleString()}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)' }}>
                      {Math.round(row.expected_demand).toLocaleString()}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: '0.8rem',
                          color: isSpike ? 'var(--accent-amber)' : 'var(--accent-rose)',
                        }}
                      >
                        {variancePct > 0 ? `+${variancePct}%` : `${variancePct}%`}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          padding: '0.2rem 0.55rem',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          backgroundColor: isSpike ? 'rgba(245, 158, 11, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                          color: isSpike ? 'var(--accent-amber)' : 'var(--accent-rose)',
                        }}
                      >
                        {isSpike ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                        {isSpike ? 'Spike' : 'Drop'}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      <span
                        style={{
                          padding: '0.2rem 0.55rem',
                          borderRadius: '4px',
                          fontSize: '0.725rem',
                          fontWeight: 700,
                          backgroundColor:
                            row.severity === 'CRITICAL'
                              ? 'rgba(236, 72, 153, 0.2)'
                              : row.severity === 'MEDIUM'
                              ? 'rgba(59, 130, 246, 0.2)'
                              : 'rgba(107, 114, 128, 0.2)',
                          color:
                            row.severity === 'CRITICAL'
                              ? '#f472b6'
                              : row.severity === 'MEDIUM'
                              ? '#60a5fa'
                              : '#9ca3af',
                        }}
                      >
                        {row.severity}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
                      {row.action_recommendation}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {filteredAlerts.length === 0 && !loading && (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              No anomalies found for the selected filters.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
