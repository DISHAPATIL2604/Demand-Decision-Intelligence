import React, { useEffect, useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  TrendingUp,
  Cpu,
  Sparkles,
  BarChart3,
  Calendar,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Award,
  Layers,
  Activity,
  History,
} from 'lucide-react';
import api from '../../services/api';

const HORIZONS = [7, 14, 30];
const AVAILABLE_MODELS = [
  { id: 'prophet', name: 'Facebook Prophet', tag: 'ML / Seasonality', color: '#3b82f6' },
  { id: 'moving_avg', name: 'Moving Average (7d)', tag: 'Statistical', color: '#f59e0b' },
  { id: 'naive', name: 'Naive Baseline', tag: 'Baseline', color: '#06b6d4' },
];

export default function ForecastPage() {
  // Config state
  const [topProducts, setTopProducts] = useState(['19512', '391306', '12872', '3881', '445675']);
  const [selectedProduct, setSelectedProduct] = useState('19512');
  const [selectedHorizon, setSelectedHorizon] = useState(7);
  const [selectedModels, setSelectedModels] = useState(['prophet', 'moving_avg', 'naive']);
  const [activeModelTab, setActiveModelTab] = useState('prophet');

  // Data state
  const [runs, setRuns] = useState([]);
  const [activeRunDetail, setActiveRunDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chartLoading, setChartLoading] = useState(false);
  const [runningForecast, setRunningForecast] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // 1. Initial Load: Fetch top products & existing runs
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      // Fetch demand summary to discover top products
      const sumRes = await api.get('/api/demand/summary').catch(() => null);
      if (sumRes?.data?.top_products_by_qty?.length > 0) {
        const pIds = sumRes.data.top_products_by_qty.map((p) => p.product_id);
        setTopProducts(pIds);
        if (!pIds.includes(selectedProduct)) {
          setSelectedProduct(pIds[0]);
        }
      }

      // Fetch existing forecast runs
      await loadRuns();
    } catch (err) {
      console.error('Failed to load initial forecast data', err);
    } finally {
      setLoading(false);
    }
  };

  const loadRuns = async () => {
    try {
      const res = await api.get('/api/forecast/runs?page=1&page_size=50');
      if (res?.data?.results) {
        setRuns(res.data.results);
      }
    } catch (err) {
      console.error('Failed to fetch runs', err);
    }
  };

  // 2. Load detail for selected product, horizon, and active model
  useEffect(() => {
    loadSelectedRunDetail();
  }, [selectedProduct, selectedHorizon, activeModelTab, runs]);

  const loadSelectedRunDetail = async () => {
    // Find matching completed run in memory
    const match = runs.find(
      (r) =>
        r.product_id === String(selectedProduct) &&
        r.horizon_days === Number(selectedHorizon) &&
        r.model_name === activeModelTab &&
        r.status === 'complete'
    );

    if (match) {
      setChartLoading(true);
      try {
        const { data } = await api.get(`/api/forecast/${match.id}`);
        setActiveRunDetail(data);
      } catch (err) {
        console.error('Failed to fetch run details', err);
      } finally {
        setChartLoading(false);
      }
    } else {
      setActiveRunDetail(null);
    }
  };

  // 3. Trigger new forecast run
  const handleTriggerForecast = async () => {
    setRunningForecast(true);
    setFeedbackMsg('');
    setErrorMsg('');
    try {
      const payload = {
        product_ids: [selectedProduct],
        models: selectedModels,
        horizon_days: selectedHorizon,
      };
      const { data } = await api.post('/api/forecast/run', payload);
      setFeedbackMsg(`Successfully generated ${data.successful_runs} forecast model run(s)!`);
      await loadRuns();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMsg(typeof detail === 'string' ? detail : 'Failed to run forecast.');
    } finally {
      setRunningForecast(false);
    }
  };

  // 4. Transform points into chart series
  const chartData = useMemo(() => {
    if (!activeRunDetail?.points?.length) return [];
    return activeRunDetail.points.map((p) => {
      const dateLabel = typeof p.forecast_date === 'string' ? p.forecast_date.slice(5) : p.forecast_date;
      return {
        date: dateLabel,
        fullDate: p.forecast_date,
        Actual: p.actual != null ? Math.round(p.actual) : null,
        Forecast: Math.round(p.yhat),
        LowerCI: p.yhat_lower != null ? Math.round(p.yhat_lower) : null,
        UpperCI: p.yhat_upper != null ? Math.round(p.yhat_upper) : null,
        isFuture: p.is_future,
      };
    });
  }, [activeRunDetail]);

  // Find competing runs for the current product & horizon to render comparison leaderboard
  const comparisonRuns = useMemo(() => {
    return runs.filter(
      (r) =>
        r.product_id === String(selectedProduct) &&
        r.horizon_days === Number(selectedHorizon) &&
        r.status === 'complete' &&
        r.evaluation != null
    );
  }, [runs, selectedProduct, selectedHorizon]);

  // Find best model by WAPE (or MAE)
  const bestModel = useMemo(() => {
    if (!comparisonRuns.length) return null;
    const sorted = [...comparisonRuns].sort((a, b) => {
      const wapeA = a.evaluation?.wape ?? Infinity;
      const wapeB = b.evaluation?.wape ?? Infinity;
      return wapeA - wapeB;
    });
    return sorted[0];
  }, [comparisonRuns]);

  // Format helper
  const fmt = (n) =>
    n == null ? '—' : Number(n).toLocaleString('en-US', { maximumFractionDigits: 1 });

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <TrendingUp color="var(--accent-primary)" size={28} />
            Demand Forecasting & Evaluation Studio
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.925rem', marginTop: '0.25rem' }}>
            Chronological multi-horizon predictions with Naive, Moving Average, and Facebook Prophet models.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={handleTriggerForecast}
          disabled={runningForecast}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.4rem' }}
        >
          <RefreshCw size={16} className={runningForecast ? 'animate-spin' : ''} />
          {runningForecast ? 'Training Models...' : 'Run Forecast'}
        </button>
      </div>

      {/* Alerts */}
      {feedbackMsg && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '0.85rem 1.25rem', backgroundColor: 'rgba(16, 185, 129, 0.12)', border: '1px solid var(--accent-emerald)', borderRadius: '8px', color: 'var(--accent-emerald)', marginBottom: '1.5rem' }}>
          <CheckCircle2 size={18} />
          <span>{feedbackMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '0.85rem 1.25rem', backgroundColor: 'rgba(244, 63, 94, 0.12)', border: '1px solid var(--accent-rose)', borderRadius: '8px', color: 'var(--accent-rose)', marginBottom: '1.5rem' }}>
          <AlertCircle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Controls Bar */}
      <div className="card" style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Product SKU Selector */}
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', marginBottom: '0.4rem', fontWeight: 600 }}>
            Target Product SKU
          </label>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {topProducts.slice(0, 5).map((pid) => (
              <button
                key={pid}
                onClick={() => setSelectedProduct(pid)}
                style={{
                  padding: '0.45rem 0.9rem',
                  borderRadius: '6px',
                  border: selectedProduct === pid ? '1px solid var(--accent-primary)' : '1px solid var(--border-strong)',
                  backgroundColor: selectedProduct === pid ? 'rgba(59, 130, 246, 0.2)' : 'var(--bg-surface-elevated)',
                  color: selectedProduct === pid ? '#93c5fd' : 'var(--text-secondary)',
                  fontWeight: selectedProduct === pid ? 600 : 500,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                SKU #{pid}
              </button>
            ))}
          </div>
        </div>

        {/* Horizon Selector */}
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', marginBottom: '0.4rem', fontWeight: 600 }}>
            Forecast Horizon
          </label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {HORIZONS.map((h) => (
              <button
                key={h}
                onClick={() => setSelectedHorizon(h)}
                style={{
                  padding: '0.45rem 1rem',
                  borderRadius: '6px',
                  border: selectedHorizon === h ? '1px solid var(--accent-cyan)' : '1px solid var(--border-strong)',
                  backgroundColor: selectedHorizon === h ? 'rgba(6, 182, 212, 0.2)' : 'var(--bg-surface-elevated)',
                  color: selectedHorizon === h ? '#67e8f9' : 'var(--text-secondary)',
                  fontWeight: selectedHorizon === h ? 600 : 500,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {h} Days
              </button>
            ))}
          </div>
        </div>

        {/* Model Selector for Training */}
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', marginBottom: '0.4rem', fontWeight: 600 }}>
            Active Models
          </label>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            {AVAILABLE_MODELS.map((m) => {
              const active = selectedModels.includes(m.id);
              return (
                <label
                  key={m.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    fontSize: '0.85rem',
                    color: active ? 'var(--text-primary)' : 'var(--text-muted)',
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={active}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedModels([...selectedModels, m.id]);
                      } else if (selectedModels.length > 1) {
                        setSelectedModels(selectedModels.filter((id) => id !== m.id));
                      }
                    }}
                    style={{ accentColor: 'var(--accent-primary)', cursor: 'pointer' }}
                  />
                  <span>{m.name}</span>
                </label>
              );
            })}
          </div>
        </div>
      </div>

      {/* Model Leaderboard & Evaluation Overview */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Award size={20} color="var(--accent-amber)" />
            Model Accuracy Leaderboard (Holdout Evaluation Split)
          </h2>
          {bestModel && (
            <span style={{ fontSize: '0.8rem', padding: '0.25rem 0.75rem', borderRadius: '999px', backgroundColor: 'rgba(16, 185, 129, 0.15)', border: '1px solid var(--accent-emerald)', color: 'var(--accent-emerald)', fontWeight: 600 }}>
              Top Performer: {bestModel.model_name.toUpperCase()} (WAPE {bestModel.evaluation?.wape}%)
            </span>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
          {AVAILABLE_MODELS.map((m) => {
            const run = comparisonRuns.find((r) => r.model_name === m.id);
            const isWinner = bestModel?.model_name === m.id;
            const isSelected = activeModelTab === m.id;

            return (
              <div
                key={m.id}
                onClick={() => setActiveModelTab(m.id)}
                style={{
                  backgroundColor: isSelected ? 'var(--bg-surface-elevated)' : 'var(--bg-surface)',
                  border: isSelected
                    ? `2px solid ${m.color}`
                    : isWinner
                    ? '1px solid var(--accent-emerald)'
                    : '1px solid var(--border-subtle)',
                  borderRadius: '12px',
                  padding: '1.25rem',
                  cursor: 'pointer',
                  position: 'relative',
                  transition: 'all 0.2s ease',
                }}
              >
                {isWinner && (
                  <span
                    style={{
                      position: 'absolute',
                      top: '0.75rem',
                      right: '0.75rem',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      backgroundColor: 'rgba(16, 185, 129, 0.2)',
                      color: 'var(--accent-emerald)',
                      padding: '0.15rem 0.5rem',
                      borderRadius: '4px',
                    }}
                  >
                    BEST ACCURACY
                  </span>
                )}

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: m.color }} />
                  <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)' }}>{m.name}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({m.tag})</span>
                </div>

                {run?.evaluation ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginTop: '0.5rem' }}>
                    <div>
                      <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)' }}>WAPE</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: m.color }}>
                        {run.evaluation.wape != null ? `${run.evaluation.wape}%` : '—'}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)' }}>MAE</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {fmt(run.evaluation.mae)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)' }}>RMSE</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {fmt(run.evaluation.rmse)}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic', marginTop: '0.5rem' }}>
                    No run found for this configuration. Click "Run Forecast" to train.
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Forecast Chart Card */}
      <div className="card" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={20} color={AVAILABLE_MODELS.find((m) => m.id === activeModelTab)?.color || '#3b82f6'} />
              Time Series Prediction Curve & 80% Confidence Interval
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Showing {activeModelTab.toUpperCase()} model | Product SKU #{selectedProduct} | {selectedHorizon}-Day Horizon
            </p>
          </div>

          {/* Model toggle pills inside chart header */}
          <div style={{ display: 'flex', gap: '0.5rem', backgroundColor: 'var(--bg-surface-elevated)', padding: '0.3rem', borderRadius: '8px' }}>
            {AVAILABLE_MODELS.map((m) => (
              <button
                key={m.id}
                onClick={() => setActiveModelTab(m.id)}
                style={{
                  padding: '0.4rem 0.85rem',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: activeModelTab === m.id ? m.color : 'transparent',
                  color: activeModelTab === m.id ? '#fff' : 'var(--text-secondary)',
                  fontWeight: activeModelTab === m.id ? 600 : 500,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {m.name}
              </button>
            ))}
          </div>
        </div>

        {/* Chart Viewport */}
        {chartLoading ? (
          <div style={{ height: '360px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            <RefreshCw size={24} className="animate-spin" style={{ marginRight: '0.5rem' }} />
            Loading prediction points...
          </div>
        ) : chartData.length > 0 ? (
          <div style={{ width: '100%', height: 380 }}>
            <ResponsiveContainer>
              <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <defs>
                  {/* Shaded Confidence Interval Gradient */}
                  <linearGradient id="ciGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0.03} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                <XAxis
                  dataKey="date"
                  stroke="var(--text-muted)"
                  fontSize={12}
                  tickLine={false}
                />
                <YAxis
                  stroke="var(--text-muted)"
                  fontSize={12}
                  tickLine={false}
                  tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v)}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0]?.payload;
                      return (
                        <div
                          style={{
                            backgroundColor: 'var(--bg-surface)',
                            border: '1px solid var(--border-strong)',
                            borderRadius: '8px',
                            padding: '0.85rem',
                            fontSize: '0.85rem',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                          }}
                        >
                          <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                            {d?.fullDate} {d?.isFuture ? '(Future Projection)' : '(Holdout Test)'}
                          </div>
                          {d?.Actual != null && (
                            <div style={{ color: '#fff', display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                              <span>Actual Demand:</span>
                              <strong>{d.Actual.toLocaleString()} units</strong>
                            </div>
                          )}
                          <div style={{ color: AVAILABLE_MODELS.find((m) => m.id === activeModelTab)?.color || '#3b82f6', display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                            <span>Forecast (yhat):</span>
                            <strong>{d?.Forecast?.toLocaleString()} units</strong>
                          </div>
                          {d?.LowerCI != null && (
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', marginTop: '0.2rem' }}>
                              80% CI: [{d.LowerCI.toLocaleString()} – {d.UpperCI.toLocaleString()}]
                            </div>
                          )}
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend verticalAlign="top" height={36} />

                {/* Upper CI boundary / area */}
                <Area
                  type="monotone"
                  dataKey="UpperCI"
                  name="80% Upper CI"
                  stroke="none"
                  fill="url(#ciGradient)"
                  isAnimationActive={false}
                />
                {/* Predicted line */}
                <Line
                  type="monotone"
                  dataKey="Forecast"
                  name={`Predicted (${activeModelTab.toUpperCase()})`}
                  stroke={AVAILABLE_MODELS.find((m) => m.id === activeModelTab)?.color || '#3b82f6'}
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: AVAILABLE_MODELS.find((m) => m.id === activeModelTab)?.color || '#3b82f6' }}
                  activeDot={{ r: 6 }}
                />
                {/* Actual historical line */}
                <Line
                  type="monotone"
                  dataKey="Actual"
                  name="Historical Actual"
                  stroke="#f9fafb"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={{ r: 3, fill: '#f9fafb' }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No forecast points available for this product and model combination. Click <strong>"Run Forecast"</strong> above to generate forecasts.
          </div>
        )}
      </div>

      {/* Runs History Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <History size={18} color="var(--accent-purple)" />
            Recent Forecast Database Runs
          </h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {runs.length} runs recorded in database
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Run ID</th>
                <th style={{ padding: '0.75rem 1rem' }}>Product SKU</th>
                <th style={{ padding: '0.75rem 1rem' }}>Model</th>
                <th style={{ padding: '0.75rem 1rem' }}>Horizon</th>
                <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                <th style={{ padding: '0.75rem 1rem' }}>WAPE</th>
                <th style={{ padding: '0.75rem 1rem' }}>MAE</th>
                <th style={{ padding: '0.75rem 1rem' }}>RMSE</th>
                <th style={{ padding: '0.75rem 1rem' }}>Created At</th>
              </tr>
            </thead>
            <tbody>
              {runs.slice(0, 10).map((r) => {
                const isSelected = activeRunDetail?.id === r.id;
                return (
                  <tr
                    key={r.id}
                    onClick={() => {
                      setSelectedProduct(r.product_id);
                      setSelectedHorizon(r.horizon_days);
                      setActiveModelTab(r.model_name);
                    }}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                      cursor: 'pointer',
                      transition: 'background-color 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      #{r.id}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--text-primary)' }}>
                      SKU #{r.product_id}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span
                        style={{
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          backgroundColor:
                            r.model_name === 'prophet'
                              ? 'rgba(59, 130, 246, 0.15)'
                              : r.model_name === 'moving_avg'
                              ? 'rgba(245, 158, 11, 0.15)'
                              : 'rgba(6, 182, 212, 0.15)',
                          color:
                            r.model_name === 'prophet'
                              ? '#93c5fd'
                              : r.model_name === 'moving_avg'
                              ? '#fcd34d'
                              : '#67e8f9',
                        }}
                      >
                        {r.model_name.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)' }}>
                      {r.horizon_days} Days
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          color: r.status === 'complete' ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                          fontSize: '0.8rem',
                          fontWeight: 500,
                        }}
                      >
                        {r.status === 'complete' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                        {r.status}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {r.evaluation?.wape != null ? `${r.evaluation.wape}%` : '—'}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)' }}>
                      {fmt(r.evaluation?.mae)}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)' }}>
                      {fmt(r.evaluation?.rmse)}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
