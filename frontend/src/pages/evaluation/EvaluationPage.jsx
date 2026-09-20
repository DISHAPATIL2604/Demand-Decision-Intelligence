import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Award,
  BarChart2,
  TrendingUp,
  RefreshCw,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  Layers,
} from 'lucide-react';
import { getForecastEvaluation } from '../../services/api';

export default function EvaluationPage() {
  const [evalData, setEvalData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getForecastEvaluation();
      setEvalData(data);
    } catch (err) {
      setError(err.message || 'Failed to load model evaluation benchmarks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const models = evalData?.models || [];
  const bestModelName = evalData?.best_model || 'Stacking Ensemble';
  const bestModel = models.find(m => m.model === bestModelName) || models[0];

  // Helper to categorize model type
  const getModelFamily = name => {
    if (!name) return 'Model';
    if (name.includes('Ensemble') || name.includes('Stacking')) return 'Meta-Ensemble';
    if (name.includes('XGBoost') || name.includes('LightGBM') || name.includes('HistGradient'))
      return 'Gradient Boosted Trees';
    if (name.includes('Prophet')) return 'Additive Seasonality';
    if (name.includes('Moving Average')) return 'Time-Series Heuristic';
    if (name.includes('Ridge')) return 'Linear Regularized';
    return 'Statistical Baseline';
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Forecast Model Evaluation &amp; Benchmarking</h1>
          <p className="page-subtitle">
            Hold-out validation metrics, model ranking, error distributions, and backtesting benchmarks.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-ghost btn-sm" onClick={loadData} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh Metrics</span>
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

      {/* Best Model Callout Banner */}
      {bestModel && (
        <div
          className="card"
          style={{
            marginBottom: '1.5rem',
            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%)',
            borderColor: 'rgba(59, 130, 246, 0.3)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                <Award size={20} style={{ color: '#60a5fa' }} />
                <span className="badge badge-safe">Top Ranked Model</span>
                <span className="badge badge-purple">{getModelFamily(bestModel.model)}</span>
              </div>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0.2rem 0' }}>
                {bestModel.model}
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', maxWidth: '650px', marginTop: '0.35rem' }}>
                Selected as the primary production engine for demand generation. Combines non-linear gradient tree regressors with Ridge meta-weights to minimize peak deviation across intermittent and seasonal series.
              </p>
            </div>

            {/* Metric pill row */}
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem 1.25rem', borderRadius: 'var(--r)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>WAPE Error</span>
                <div className="mono bold" style={{ fontSize: '1.35rem', color: 'var(--emerald)' }}>
                  {Number(bestModel.WAPE_pct).toFixed(2)}%
                </div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Top accuracy threshold</span>
              </div>

              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem 1.25rem', borderRadius: 'var(--r)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>MAE</span>
                <div className="mono bold" style={{ fontSize: '1.35rem', color: '#60a5fa' }}>
                  {Number(bestModel.MAE).toFixed(1)} u
                </div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Mean absolute units</span>
              </div>

              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem 1.25rem', borderRadius: 'var(--r)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>RMSE</span>
                <div className="mono bold" style={{ fontSize: '1.35rem', color: 'var(--text-primary)' }}>
                  {Number(bestModel.RMSE).toFixed(1)} u
                </div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Variance penalty</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Comparative Evaluation Benchmark Table */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 className="card-title">Full Model Benchmark Comparison</h3>
            <p className="card-subtitle" style={{ marginBottom: 0 }}>
              Performance of all 8 evaluated candidate architectures evaluated on the Stage S3 temporal split.
            </p>
          </div>
          <span className="badge badge-info">
            <Layers size={12} /> {models.length} Models Tested
          </span>
        </div>

        {loading ? (
          <div className="loading-state">
            <RefreshCw size={20} className="spin" />
            <span>Loading model comparison metrics...</span>
          </div>
        ) : models.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-title">No Evaluation Report Found</div>
            <div className="empty-state-desc">
              model_comparison.csv not generated yet. Execute the stage 3 training and evaluation pipeline.
            </div>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Candidate Architecture</th>
                  <th>Model Paradigm</th>
                  <th>MAE (Units)</th>
                  <th>RMSE (Units)</th>
                  <th>WAPE (%)</th>
                  <th>Production Verdict</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m, idx) => {
                  const isTop = idx === 0 || m.model.includes('🏆');
                  const wape = Number(m.WAPE_pct);

                  return (
                    <tr key={m.model || idx} style={isTop ? { background: 'rgba(59,130,246,0.06)' } : {}}>
                      <td className="mono bold" style={{ color: isTop ? '#60a5fa' : 'var(--text-muted)' }}>
                        #{idx + 1}
                      </td>
                      <td className="bold" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {isTop && <CheckCircle2 size={15} style={{ color: 'var(--emerald)' }} />}
                        <span>{m.model}</span>
                      </td>
                      <td>
                        <span className="badge badge-neutral">{getModelFamily(m.model)}</span>
                      </td>
                      <td className="mono">{Number(m.MAE).toFixed(2)}</td>
                      <td className="mono">{Number(m.RMSE).toFixed(2)}</td>
                      <td className="mono bold" style={{ color: wape < 19.5 ? 'var(--emerald)' : wape < 20.5 ? '#60a5fa' : 'inherit' }}>
                        {wape.toFixed(2)}%
                      </td>
                      <td>
                        {isTop ? (
                          <span className="badge badge-safe">Primary Selected</span>
                        ) : wape < 19.5 ? (
                          <span className="badge badge-low">High Quality Alternative</span>
                        ) : wape < 20.5 ? (
                          <span className="badge badge-medium">Acceptable Heuristic</span>
                        ) : (
                          <span className="badge badge-neutral">Baseline Reference</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Metric Glossary Guide */}
      <div className="card">
        <h3 className="card-title">Evaluation Glossary &amp; Formulation</h3>
        <p className="card-subtitle">
          How forecasting accuracy and error tolerances are measured across this system.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginTop: '1rem' }}>
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: 'var(--r)' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--blue-light)', marginBottom: '0.35rem' }}>
              WAPE (Weighted Absolute Percentage Error)
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Calculated as &Sigma;|Actual - Forecast| &divide; &Sigma;Actual. Unlike standard MAPE, WAPE avoids infinite or inflated errors when daily demand is 0 or low, making it the industry standard for FMCG grocery forecasting.
            </p>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: 'var(--r)' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--emerald)', marginBottom: '0.35rem' }}>
              MAE (Mean Absolute Error)
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              The unweighted linear average error in daily units sold. Directly represents how many units off on average the procurement team can expect the model to be per product per day.
            </p>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: 'var(--r)' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fbbf24', marginBottom: '0.35rem' }}>
              RMSE (Root Mean Squared Error)
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              By squaring errors before averaging, RMSE places higher weight on large out-of-distribution misses. Models with lower RMSE provide superior protection against sudden warehouse stockouts.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
