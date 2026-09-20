import React, { useState, useEffect, useMemo } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  TrendingUp,
  Filter,
  Layers,
  Award,
  AlertCircle,
  HelpCircle,
  RefreshCw,
  Search,
} from 'lucide-react';
import { getForecastResults, getForecastEvaluation } from '../../services/api';

export default function ForecastPage() {
  const [results, setResults] = useState([]);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [cityFilter, setCityFilter] = useState('');
  const [productFilter, setProductFilter] = useState('');
  const [selectedModel, setSelectedModel] = useState('pred_ensemble');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [resData, evalData] = await Promise.allSettled([
        getForecastResults({ limit: 300 }),
        getForecastEvaluation(),
      ]);

      if (resData.status === 'fulfilled' && resData.value?.data) {
        setResults(resData.value.data);
      } else {
        setResults([]);
      }

      if (evalData.status === 'fulfilled') {
        setEvaluation(evalData.value);
      }
    } catch (err) {
      setError(err.message || 'Failed to load forecast intelligence');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered dataset
  const filteredData = useMemo(() => {
    let data = [...results];
    if (cityFilter) {
      data = data.filter(
        item => item.city_name?.toLowerCase() === cityFilter.toLowerCase()
      );
    }
    if (productFilter.trim()) {
      data = data.filter(item =>
        String(item.product_id).includes(productFilter.trim())
      );
    }
    return data;
  }, [results, cityFilter, productFilter]);

  // Aggregate time series for chart (group by date_)
  const chartData = useMemo(() => {
    if (!filteredData.length) return [];

    const grouped = {};
    filteredData.forEach(row => {
      const d = row.date_ || 'Unknown';
      if (!grouped[d]) {
        grouped[d] = {
          date: d,
          actual: 0,
          pred_ensemble: 0,
          pred_lgb: 0,
          pred_xgb: 0,
          pred_croston: 0,
          count: 0,
        };
      }
      grouped[d].actual += Number(row.daily_quantity) || 0;
      grouped[d].pred_ensemble += Number(row.pred_ensemble) || 0;
      grouped[d].pred_lgb += Number(row.pred_lgb) || 0;
      grouped[d].pred_xgb += Number(row.pred_xgb) || 0;
      grouped[d].pred_croston += Number(row.pred_croston) || 0;
      grouped[d].count += 1;
    });

    return Object.values(grouped)
      .sort((a, b) => (a.date > b.date ? 1 : -1))
      .map(item => ({
        ...item,
        actual: Math.round(item.actual),
        pred_ensemble: Math.round(item.pred_ensemble),
        pred_lgb: Math.round(item.pred_lgb),
        pred_xgb: Math.round(item.pred_xgb),
        pred_croston: Math.round(item.pred_croston),
      }));
  }, [filteredData]);

  // Available unique cities
  const cities = useMemo(() => {
    const set = new Set();
    results.forEach(r => {
      if (r.city_name) set.add(r.city_name);
    });
    return Array.from(set).sort();
  }, [results]);

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Demand Forecast Intelligence</h1>
          <p className="page-subtitle">
            Historical backtest predictions, multi-model comparisons, and daily sales validation.
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

      {/* Filter Toolbar */}
      <div className="card card-sm" style={{ marginBottom: '1.5rem' }}>
        <div className="filter-bar" style={{ margin: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={15} style={{ color: 'var(--text-muted)' }} />
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Filters:</span>
          </div>

          {/* City Dropdown */}
          <select
            className="filter-select"
            value={cityFilter}
            onChange={e => setCityFilter(e.target.value)}
          >
            <option value="">All Cities ({cities.length || 4})</option>
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
              style={{ paddingLeft: '2rem', width: '180px' }}
              placeholder="Search SKU / Product ID..."
              value={productFilter}
              onChange={e => setProductFilter(e.target.value)}
            />
          </div>

          {/* Model toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginLeft: 'auto' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Display Model:</span>
            <select
              className="filter-select"
              value={selectedModel}
              onChange={e => setSelectedModel(e.target.value)}
            >
              <option value="pred_ensemble">Stacking Ensemble (Recommended)</option>
              <option value="pred_xgb">XGBoost</option>
              <option value="pred_lgb">LightGBM</option>
              <option value="pred_croston">Croston (Intermittent)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Trajectory Chart */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
          <div>
            <h3 className="card-title">Historical Actual Demand vs Model Prediction</h3>
            <p className="card-subtitle" style={{ marginBottom: 0 }}>
              Aggregation of {filteredData.length} records across {chartData.length} recorded forecast dates
            </p>
          </div>
          {evaluation?.best_model && (
            <div className="badge badge-safe">
              <Award size={12} />
              Best Model: {evaluation.best_model}
            </div>
          )}
        </div>

        {loading ? (
          <div className="loading-state">
            <RefreshCw size={20} className="spin" />
            <span>Loading forecast series...</span>
          </div>
        ) : chartData.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <TrendingUp size={28} />
            </div>
            <div className="empty-state-title">No Forecast Records Available</div>
            <div className="empty-state-desc">
              {results.length === 0
                ? 'Forecast results CSV has not been generated yet. Run the forecasting pipeline first.'
                : 'No records match the selected city or SKU filter.'}
            </div>
          </div>
        ) : (
          <div style={{ width: '100%', height: 360 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
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
                  formatter={(value, name) => [
                    value.toLocaleString() + ' units',
                    name === 'actual'
                      ? 'Actual Demand'
                      : name === 'pred_ensemble'
                      ? 'Stacking Ensemble'
                      : name === 'pred_xgb'
                      ? 'XGBoost'
                      : name === 'pred_lgb'
                      ? 'LightGBM'
                      : 'Croston',
                  ]}
                />
                <Legend
                  wrapperStyle={{ fontSize: '0.82rem', paddingTop: '0.75rem' }}
                  formatter={value =>
                    value === 'actual'
                      ? 'Actual Demand (Units)'
                      : value === 'pred_ensemble'
                      ? 'Stacking Ensemble Forecast'
                      : value === 'pred_xgb'
                      ? 'XGBoost Prediction'
                      : value === 'pred_lgb'
                      ? 'LightGBM Prediction'
                      : 'Croston'
                  }
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
                  dataKey={selectedModel}
                  stroke="#3b82f6"
                  strokeWidth={2.2}
                  fill="url(#forecastGrad)"
                  name={selectedModel}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
          <HelpCircle size={14} />
          <span>
            Actual demand reflects daily recorded sales quantity. Predictions are generated using historical temporal features and tree-based ensemble weights.
          </span>
        </div>
      </div>

      {/* Model Benchmark Performance Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 className="card-title">Forecasting Benchmark Models &amp; Error Metrics</h3>
            <p className="card-subtitle" style={{ marginBottom: 0 }}>
              Stage S3 validation metrics computed on hold-out temporal test splits
            </p>
          </div>
          <span className="badge badge-info">
            <Layers size={12} />
            {evaluation?.models?.length || 0} Models Evaluated
          </span>
        </div>

        {evaluation?.models && evaluation.models.length > 0 ? (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank &amp; Model Architecture</th>
                  <th>MAE (Units)</th>
                  <th>RMSE (Units)</th>
                  <th>WAPE (%)</th>
                  <th>Status / Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {evaluation.models.map((m, idx) => {
                  const isTop = idx === 0 || m.model.includes('🏆');
                  return (
                    <tr key={m.model || idx} style={isTop ? { background: 'rgba(59,130,246,0.06)' } : {}}>
                      <td className="bold" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {isTop ? <Award size={15} style={{ color: '#60a5fa' }} /> : <span style={{ width: 15 }} />}
                        <span>{m.model}</span>
                      </td>
                      <td className="mono">{Number(m.MAE).toFixed(2)}</td>
                      <td className="mono">{Number(m.RMSE).toFixed(2)}</td>
                      <td className="mono" style={{ color: Number(m.WAPE_pct) < 20 ? 'var(--emerald)' : 'inherit' }}>
                        {Number(m.WAPE_pct).toFixed(2)}%
                      </td>
                      <td>
                        {isTop ? (
                          <span className="badge badge-safe">Selected Production</span>
                        ) : Number(m.WAPE_pct) <= 20 ? (
                          <span className="badge badge-low">Competitive Baseline</span>
                        ) : (
                          <span className="badge badge-neutral">Standard Baseline</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state" style={{ padding: '2rem' }}>
            <div className="empty-state-title">Model comparison metrics unavailable</div>
            <div className="empty-state-desc">Reports file model_comparison.csv not found or yet to be executed.</div>
          </div>
        )}

        <div style={{ marginTop: '1.25rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: 'var(--r-sm)' }}>
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>MAE (Mean Absolute Error)</div>
            <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>Average magnitude of forecast errors in units sold. Lower is better.</div>
          </div>
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>RMSE (Root Mean Squared Error)</div>
            <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>Penalizes larger variance errors more heavily. Useful for safety stock planning.</div>
          </div>
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>WAPE (Weighted Absolute % Error)</div>
            <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>Aggregate absolute error divided by total actual demand. Essential for high-volume grocery demand.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
