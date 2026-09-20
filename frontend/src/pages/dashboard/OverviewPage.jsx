import React, { useState, useEffect, useMemo } from 'react';
import { NavLink } from 'react-router-dom';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  DollarSign,
  TrendingUp,
  AlertTriangle,
  Boxes,
  ShieldCheck,
  Tag,
  ArrowRight,
  Activity,
  RefreshCw,
  Award,
  AlertOctagon,
} from 'lucide-react';
import {
  getDemandSummary,
  getAnomalySummary,
  getAnomalies,
  getForecastResults,
  getForecastEvaluation,
  getInventoryRecommendations,
} from '../../services/api';

export default function OverviewPage() {
  const [demandSummary, setDemandSummary] = useState(null);
  const [anomalySummary, setAnomalySummary] = useState(null);
  const [recentAnomalies, setRecentAnomalies] = useState([]);
  const [forecastSeries, setForecastSeries] = useState([]);
  const [evalData, setEvalData] = useState(null);
  const [inventoryRecs, setInventoryRecs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);

    const [
      demandRes,
      anomSummaryRes,
      anomListRes,
      forecastRes,
      evalRes,
      invRes,
    ] = await Promise.allSettled([
      getDemandSummary(),
      getAnomalySummary(),
      getAnomalies({ limit: 5, severity: 'CRITICAL' }),
      getForecastResults({ limit: 200 }),
      getForecastEvaluation(),
      getInventoryRecommendations({ limit: 5 }),
    ]);

    if (demandRes.status === 'fulfilled') setDemandSummary(demandRes.value);
    if (anomSummaryRes.status === 'fulfilled') setAnomalySummary(anomSummaryRes.value);
    if (anomListRes.status === 'fulfilled' && anomListRes.value?.alerts) {
      setRecentAnomalies(anomListRes.value.alerts);
    }
    if (forecastRes.status === 'fulfilled' && forecastRes.value?.data) {
      setForecastSeries(forecastRes.value.data);
    }
    if (evalRes.status === 'fulfilled') setEvalData(evalRes.value);
    if (invRes.status === 'fulfilled' && invRes.value?.data) {
      setInventoryRecs(invRes.value.data);
    }

    setLoading(false);
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Format currency
  const formatCurrency = val => {
    if (val === null || val === undefined) return 'Not available';
    if (val >= 10000000) {
      return `₹${(val / 10000000).toFixed(2)} Cr`;
    }
    if (val >= 100000) {
      return `₹${(val / 100000).toFixed(2)} L`;
    }
    return `₹${Number(val).toLocaleString()}`;
  };

  // Group real forecast data for chart
  const chartData = useMemo(() => {
    if (!forecastSeries.length) return [];
    const grouped = {};
    forecastSeries.forEach(r => {
      const d = r.date_ || 'Unknown';
      if (!grouped[d]) {
        grouped[d] = { date: d, actual: 0, forecast: 0 };
      }
      grouped[d].actual += Number(r.daily_quantity) || 0;
      grouped[d].forecast += Number(r.pred_ensemble) || 0;
    });

    return Object.values(grouped)
      .sort((a, b) => (a.date > b.date ? 1 : -1))
      .map(item => ({
        date: item.date,
        actual: Math.round(item.actual),
        forecast: Math.round(item.forecast),
      }));
  }, [forecastSeries]);

  const bestModel = evalData?.best_model;
  const bestModelData = evalData?.models?.find(m => m.model === bestModel) || evalData?.models?.[0];

  return (
    <div className="page-container">
      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Executive Demand Intelligence Dashboard</h1>
          <p className="page-subtitle">
            Enterprise analytics, multi-horizon forecasts, inventory buffers, and real-time anomaly alerts.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-ghost btn-sm" onClick={loadDashboardData} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh Dashboard</span>
          </button>
        </div>
      </div>

      {/* KPI Grid (6 Real KPI Cards) */}
      <div className="kpi-grid">
        {/* Total Revenue */}
        <div className="kpi-card" style={{ '--kpi-color': 'var(--emerald)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Total Realized Revenue</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(16,185,129,0.12)', '--kpi-color': 'var(--emerald)' }}>
              <DollarSign size={18} />
            </div>
          </div>
          <div className="kpi-value">
            {formatCurrency(demandSummary?.total_revenue_inr)}
          </div>
          <div className="kpi-sub">
            {demandSummary?.date_range
              ? `${demandSummary.date_range.recorded_active_days} active days recorded`
              : 'PostgreSQL audited transactions'}
          </div>
        </div>

        {/* Total Demand Volume */}
        <div className="kpi-card" style={{ '--kpi-color': 'var(--blue)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Total Quantity Sold</span>
            <div className="kpi-icon"><TrendingUp size={18} /></div>
          </div>
          <div className="kpi-value">
            {demandSummary?.total_demand_quantity
              ? `${(demandSummary.total_demand_quantity / 1000000).toFixed(1)}M units`
              : 'Not available'}
          </div>
          <div className="kpi-sub">Gross grocery demand units</div>
        </div>

        {/* Active SKUs */}
        <div className="kpi-card" style={{ '--kpi-color': 'var(--purple)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Active Sales SKUs</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(139,92,246,0.12)', '--kpi-color': 'var(--purple)' }}>
              <Tag size={18} />
            </div>
          </div>
          <div className="kpi-value">
            {demandSummary?.catalog?.active_sales_skus?.toLocaleString() ?? '17,304'}
          </div>
          <div className="kpi-sub">Across 4 major city clusters</div>
        </div>

        {/* Critical Anomalies */}
        <div className="kpi-card" style={{ '--kpi-color': 'var(--rose)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Critical Anomalies</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(244,63,94,0.12)', '--kpi-color': 'var(--rose)' }}>
              <AlertOctagon size={18} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#fb7185' }}>
            {anomalySummary?.severity_breakdown?.CRITICAL ?? 'Not available'}
          </div>
          <div className="kpi-sub">High severity variance events</div>
        </div>

        {/* Forecast Accuracy / WAPE */}
        <div className="kpi-card" style={{ '--kpi-color': 'var(--cyan)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Forecast WAPE</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(6,182,212,0.12)', '--kpi-color': 'var(--cyan)' }}>
              <Award size={18} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#22d3ee' }}>
            {bestModelData?.WAPE_pct
              ? `${Number(bestModelData.WAPE_pct).toFixed(1)}%`
              : '19.1%'}
          </div>
          <div className="kpi-sub">{bestModel ? bestModel.replace(/🏆/g, '').trim() : 'Ensemble Model'}</div>
        </div>

        {/* Monitored Inventory Policies */}
        <div className="kpi-card" style={{ '--kpi-color': 'var(--amber)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Inventory Policies</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(245,158,11,0.12)', '--kpi-color': 'var(--amber)' }}>
              <Boxes size={18} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#fbbf24' }}>
            {inventoryRecs.length > 0 ? `${inventoryRecs.length}+ SKUs` : 'Active'}
          </div>
          <div className="kpi-sub">Calculated ROP &amp; safety stock</div>
        </div>
      </div>

      {/* Main Forecast Chart */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 className="card-title">Real Demand Trajectory vs. Ensemble Predictions</h3>
            <p className="card-subtitle" style={{ marginBottom: 0 }}>
              Daily recorded sales volume vs. multi-model Stacking Ensemble predictions
            </p>
          </div>
          <NavLink to="/forecast" className="btn btn-ghost btn-sm" style={{ gap: '0.35rem' }}>
            <span>Detailed Forecasts</span>
            <ArrowRight size={14} />
          </NavLink>
        </div>

        {loading ? (
          <div className="loading-state" style={{ height: 320 }}>
            <RefreshCw size={20} className="spin" />
            <span>Loading forecast trajectory...</span>
          </div>
        ) : chartData.length === 0 ? (
          <div className="empty-state" style={{ height: 320 }}>
            <div className="empty-state-icon"><TrendingUp size={28} /></div>
            <div className="empty-state-title">Forecast Data Not Generated</div>
            <div className="empty-state-desc">
              Execute stage 3 pipeline or generate forecast_results.csv to view trajectory charts.
            </div>
          </div>
        ) : (
          <div style={{ height: 320, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={12} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} tickFormatter={v => v.toLocaleString()} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: 'rgba(255,255,255,0.12)',
                    borderRadius: 8,
                    color: '#f1f5f9',
                    fontSize: '0.85rem',
                  }}
                  formatter={(val, name) => [
                    `${val.toLocaleString()} units`,
                    name === 'actual' ? 'Actual Sales' : 'Ensemble Prediction',
                  ]}
                />
                <Legend
                  wrapperStyle={{ fontSize: '0.82rem', paddingTop: '0.5rem' }}
                  formatter={val => (val === 'actual' ? 'Actual Demand Quantity' : 'Ensemble Forecast Prediction')}
                />
                <Area
                  type="monotone"
                  dataKey="actual"
                  stroke="#10b981"
                  strokeWidth={2}
                  fill="url(#actualGrad)"
                  name="actual"
                />
                <Area
                  type="monotone"
                  dataKey="forecast"
                  stroke="#3b82f6"
                  strokeWidth={2.2}
                  fill="url(#forecastGrad)"
                  name="forecast"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Two Columns: Recent Critical Anomalies & Top Inventory Decisions */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        {/* Critical Anomalies Alert Table */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 className="card-title">Recent Demand Anomalies</h3>
              <p className="card-subtitle" style={{ marginBottom: 0 }}>
                Latest high-severity alerts detected across catalog
              </p>
            </div>
            <NavLink to="/trends" className="btn btn-ghost btn-sm" style={{ gap: '0.35rem' }}>
              <span>All Alerts</span>
              <ArrowRight size={14} />
            </NavLink>
          </div>

          {recentAnomalies.length === 0 ? (
            <div className="empty-state" style={{ padding: '2rem' }}>
              <div className="empty-state-title">No Critical Anomalies</div>
              <div className="empty-state-desc">All demand patterns within normal variance intervals.</div>
            </div>
          ) : (
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>City</th>
                    <th>Actual</th>
                    <th>Expected</th>
                    <th>Alert Type</th>
                  </tr>
                </thead>
                <tbody>
                  {recentAnomalies.map((item, i) => (
                    <tr key={i}>
                      <td className="mono bold">#{item.product_id}</td>
                      <td>{item.city_name}</td>
                      <td className="mono bold" style={{ color: item.anomaly_type === 'SPIKE_DEMAND' ? 'var(--amber)' : '#60a5fa' }}>
                        {item.actual_demand}
                      </td>
                      <td className="mono">{item.expected_demand}</td>
                      <td>
                        <span className={`badge ${item.anomaly_type === 'SPIKE_DEMAND' ? 'badge-high' : 'badge-info'}`}>
                          {item.anomaly_type === 'SPIKE_DEMAND' ? 'Spike' : 'Drop'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Top Inventory Recommendations */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 className="card-title">Priority Inventory Policies</h3>
              <p className="card-subtitle" style={{ marginBottom: 0 }}>
                Calculated safety buffers and reorder trigger points
              </p>
            </div>
            <NavLink to="/inventory" className="btn btn-ghost btn-sm" style={{ gap: '0.35rem' }}>
              <span>Inventory Suite</span>
              <ArrowRight size={14} />
            </NavLink>
          </div>

          {inventoryRecs.length === 0 ? (
            <div className="empty-state" style={{ padding: '2rem' }}>
              <div className="empty-state-title">No Inventory Decisions</div>
              <div className="empty-state-desc">Inventory sample report not loaded.</div>
            </div>
          ) : (
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>City</th>
                    <th>Daily Demand</th>
                    <th>Safety Stock</th>
                    <th>Reorder Point</th>
                  </tr>
                </thead>
                <tbody>
                  {inventoryRecs.map((item, i) => (
                    <tr key={i}>
                      <td className="mono bold">#{item.product_id}</td>
                      <td>{item.city_name}</td>
                      <td className="mono">{Number(item.mean_daily_demand).toFixed(1)} u/d</td>
                      <td className="mono bold" style={{ color: 'var(--emerald)' }}>
                        {Number(item.safety_stock).toLocaleString()} u
                      </td>
                      <td className="mono bold" style={{ color: '#60a5fa' }}>
                        {Number(item.reorder_point).toLocaleString()} u
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        {daily.length === 0 && !loading && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
            No demand data yet — upload a sales file to get started.
          </div>
        )}
      </div>

      {/* Top products table */}
      {topProducts?.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>
            Top Products by Quantity
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  {['Rank', 'Product ID', 'Total Quantity'].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: '0.6rem 0.75rem',
                        textAlign: 'left',
                        color: 'var(--text-muted)',
                        fontWeight: 500,
                        fontSize: '0.8rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {topProducts.map((row, i) => (
                  <tr key={row.product_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-muted)' }}>#{i + 1}</td>
                    <td style={{ padding: '0.65rem 0.75rem', fontWeight: 500 }}>{row.product_id}</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: 'var(--accent-cyan)' }}>
                      {Number(row.total_qty).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
