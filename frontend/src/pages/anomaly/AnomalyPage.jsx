import React, { useState, useEffect, useMemo } from 'react';
import {
  Activity,
  AlertOctagon,
  ArrowUpRight,
  ArrowDownRight,
  Filter,
  Search,
  RefreshCw,
  AlertTriangle,
  Calendar,
  MapPin,
  HelpCircle,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { getAnomalies, getAnomalySummary } from '../../services/api';

export default function AnomalyPage() {
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('');
  const [cityFilter, setCityFilter] = useState('');
  const [skuSearch, setSkuSearch] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [alertData, sumData] = await Promise.allSettled([
        getAnomalies({
          limit: 200,
          severity: severityFilter,
          city_name: cityFilter || undefined,
          anomaly_type: typeFilter || undefined,
        }),
        getAnomalySummary(),
      ]);

      if (alertData.status === 'fulfilled' && alertData.value?.alerts) {
        setAlerts(alertData.value.alerts);
      } else {
        setAlerts([]);
      }

      if (sumData.status === 'fulfilled') {
        setSummary(sumData.value);
      }
    } catch (err) {
      setError(err.message || 'Failed to load anomalies');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [severityFilter, typeFilter, cityFilter]);

  // Filtered alerts by search
  const filteredAlerts = useMemo(() => {
    if (!skuSearch.trim()) return alerts;
    return alerts.filter(a => String(a.product_id).includes(skuSearch.trim()));
  }, [alerts, skuSearch]);

  // Cities list
  const cities = ['Delhi', 'Bengaluru', 'HR-NCR', 'Mumbai'];

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Demand Anomalies &amp; Outlier Detection</h1>
          <p className="page-subtitle">
            Automated detection of unexplained demand surges, stockout drops, and erratic consumption patterns.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-ghost btn-sm" onClick={loadData} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh Alerts</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ marginBottom: '1.5rem', borderColor: 'rgba(244,63,94,0.3)', background: 'rgba(244,63,94,0.06)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#fb7185' }}>
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* KPI Row */}
      <div className="kpi-grid">
        <div className="kpi-card" style={{ '--kpi-color': 'var(--blue)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Total Outliers</span>
            <div className="kpi-icon"><Activity size={18} /></div>
          </div>
          <div className="kpi-value">{summary?.total_anomalies ?? alerts.length}</div>
          <div className="kpi-sub">Flagged anomalies across date range</div>
        </div>

        <div className="kpi-card" style={{ '--kpi-color': 'var(--rose)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Critical Alerts</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(244,63,94,0.12)', '--kpi-color': 'var(--rose)' }}>
              <AlertOctagon size={18} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#fb7185' }}>
            {summary?.severity_breakdown?.CRITICAL ?? alerts.filter(a => a.severity === 'CRITICAL').length}
          </div>
          <div className="kpi-sub">High severity variance events</div>
        </div>

        <div className="kpi-card" style={{ '--kpi-color': 'var(--amber)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Demand Spikes</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(245,158,11,0.12)', '--kpi-color': 'var(--amber)' }}>
              <TrendingUp size={18} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#fbbf24' }}>
            {summary?.anomaly_type_breakdown?.SPIKE_DEMAND ?? alerts.filter(a => a.anomaly_type === 'SPIKE_DEMAND').length}
          </div>
          <div className="kpi-sub">Sudden unpredicted volume jumps</div>
        </div>

        <div className="kpi-card" style={{ '--kpi-color': 'var(--cyan)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Stockout Drops</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(6,182,212,0.12)', '--kpi-color': 'var(--cyan)' }}>
              <TrendingDown size={18} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#22d3ee' }}>
            {summary?.anomaly_type_breakdown?.DROP_STOCKOUT ?? alerts.filter(a => a.anomaly_type === 'DROP_STOCKOUT').length}
          </div>
          <div className="kpi-sub">Steep drops indicating stockout</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card card-sm" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          {/* Severity chips */}
          <div className="filter-bar" style={{ margin: 0 }}>
            <button
              className={`filter-chip ${severityFilter === 'ALL' ? 'active' : ''}`}
              onClick={() => setSeverityFilter('ALL')}
            >
              All Severities
            </button>
            <button
              className={`filter-chip chip-critical ${severityFilter === 'CRITICAL' ? 'active' : ''}`}
              onClick={() => setSeverityFilter('CRITICAL')}
            >
              Critical
            </button>
            <button
              className={`filter-chip chip-warning ${severityFilter === 'MEDIUM' ? 'active' : ''}`}
              onClick={() => setSeverityFilter('MEDIUM')}
            >
              Medium
            </button>
            <button
              className={`filter-chip ${severityFilter === 'LOW' ? 'active' : ''}`}
              onClick={() => setSeverityFilter('LOW')}
            >
              Low
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            {/* Type Filter */}
            <select
              className="filter-select"
              value={typeFilter}
              onChange={e => setTypeFilter(e.target.value)}
              style={{ minWidth: '150px' }}
            >
              <option value="">All Anomaly Types</option>
              <option value="SPIKE_DEMAND">Demand Spikes</option>
              <option value="DROP_STOCKOUT">Stockout Drops</option>
            </select>

            {/* City Filter */}
            <select
              className="filter-select"
              value={cityFilter}
              onChange={e => setCityFilter(e.target.value)}
              style={{ minWidth: '120px' }}
            >
              <option value="">All Cities</option>
              {cities.map(c => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>

            {/* SKU Search */}
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Search size={14} style={{ position: 'absolute', left: '0.65rem', color: 'var(--text-muted)', pointerEvents: 'none' }} />
              <input
                type="text"
                className="filter-input"
                style={{ paddingLeft: '2rem', width: '160px' }}
                placeholder="Search SKU..."
                value={skuSearch}
                onChange={e => setSkuSearch(e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Anomaly Cards Feed */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 className="card-title" style={{ margin: 0 }}>
            Active Incident Alerts ({filteredAlerts.length})
          </h3>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Latest alerts sorted by date and deviation score
          </span>
        </div>

        {loading ? (
          <div className="card loading-state">
            <RefreshCw size={20} className="spin" />
            <span>Scanning for demand anomalies...</span>
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="card empty-state">
            <div className="empty-state-icon">
              <Activity size={28} />
            </div>
            <div className="empty-state-title">No Anomalies Detected</div>
            <div className="empty-state-desc">
              {alerts.length === 0
                ? 'Anomaly deliverables report demand_anomalies.csv not found or pipeline not executed.'
                : 'No anomaly events match the selected filters.'}
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1rem' }}>
            {filteredAlerts.map((item, idx) => {
              const isSpike = item.anomaly_type === 'SPIKE_DEMAND';
              const deviationPct =
                item.expected_demand > 0
                  ? (
                      ((item.actual_demand - item.expected_demand) /
                        item.expected_demand) *
                      100
                    ).toFixed(1)
                  : 0;

              const badgeClass =
                item.severity === 'CRITICAL'
                  ? 'badge-critical'
                  : item.severity === 'MEDIUM'
                  ? 'badge-medium'
                  : 'badge-low';

              return (
                <div
                  key={`${item.date_}-${item.product_id}-${item.city_name}-${idx}`}
                  className="card"
                  style={{
                    padding: '1.25rem',
                    position: 'relative',
                    borderColor:
                      item.severity === 'CRITICAL'
                        ? 'rgba(244, 63, 94, 0.25)'
                        : 'var(--border)',
                  }}
                >
                  {/* Top row */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                        <span className="mono bold" style={{ fontSize: '0.95rem' }}>
                          SKU #{item.product_id}
                        </span>
                        <span className={`badge ${badgeClass}`}>{item.severity}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <MapPin size={12} /> {item.city_name}
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <Calendar size={12} /> {item.date_}
                        </span>
                      </div>
                    </div>

                    <span
                      className={`badge ${
                        isSpike ? 'badge-high' : 'badge-info'
                      }`}
                      style={{ fontSize: '0.65rem' }}
                    >
                      {isSpike ? (
                        <ArrowUpRight size={12} />
                      ) : (
                        <ArrowDownRight size={12} />
                      )}
                      {item.anomaly_type.replace('_', ' ')}
                    </span>
                  </div>

                  {/* Numbers Grid */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr 1fr',
                      gap: '0.5rem',
                      background: 'rgba(255,255,255,0.025)',
                      padding: '0.75rem',
                      borderRadius: 'var(--r-sm)',
                      marginBottom: '0.85rem',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Actual Demand</div>
                      <div className="mono bold" style={{ fontSize: '1.05rem', color: isSpike ? 'var(--amber)' : '#60a5fa' }}>
                        {item.actual_demand.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Expected Baseline</div>
                      <div className="mono" style={{ fontSize: '1.05rem', color: 'var(--text-secondary)' }}>
                        {item.expected_demand.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Deviation</div>
                      <div
                        className="mono bold"
                        style={{
                          fontSize: '1.05rem',
                          color: Number(deviationPct) >= 0 ? '#fb7185' : '#34d399',
                        }}
                      >
                        {Number(deviationPct) >= 0 ? `+${deviationPct}%` : `${deviationPct}%`}
                      </div>
                    </div>
                  </div>

                  {/* Recommendation action */}
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45, background: 'rgba(59,130,246,0.06)', padding: '0.5rem 0.75rem', borderRadius: 6, borderLeft: '3px solid var(--blue)' }}>
                    <strong>Action:</strong> {item.action_recommendation}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Analytical Footnote */}
      <div className="card card-sm" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
        <HelpCircle size={16} style={{ flexShrink: 0 }} />
        <span>
          Anomalies are detected using temporal moving thresholds and residual z-score metrics. SPIKE_DEMAND alerts indicate unexpected customer surges requiring emergency replenishment. DROP_STOCKOUT alerts flag sudden sales collapse typically caused by warehouse or distributor stockouts.
        </span>
      </div>
    </div>
  );
}
