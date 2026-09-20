import React, { useState, useEffect, useMemo } from 'react';
import {
  Boxes,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
  Sliders,
  ChevronDown,
  ChevronRight,
  Info,
  Package,
} from 'lucide-react';
import { getDemandInventoryRecs } from '../../services/api';

export default function InventoryPage() {
  const [recommendations, setRecommendations] = useState([]);
  const [parameters, setParameters] = useState({
    lead_time_days: 3,
    target_service_level: 0.95,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & controls
  const [leadTime, setLeadTime] = useState(3);
  const [serviceLevel, setServiceLevel] = useState(0.95);
  const [cityFilter, setCityFilter] = useState('');
  const [skuSearch, setSkuSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [expandedRow, setExpandedRow] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDemandInventoryRecs({
        limit: 200,
        lead_time_days: leadTime,
        service_level: serviceLevel,
        city: cityFilter || undefined,
      });

      if (data?.data) {
        setRecommendations(data.data);
        if (data.parameters) {
          setParameters(data.parameters);
        }
      } else {
        setRecommendations([]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load inventory recommendations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [leadTime, serviceLevel, cityFilter]);

  // Derived classification for each item based on daily demand and safety buffer
  const enrichedData = useMemo(() => {
    return recommendations.map(item => {
      const mean = Number(item.mean_daily_demand) || 0;
      const std = Number(item.std_daily_demand) || 0;
      const cv = mean > 0 ? std / mean : 0; // Coefficient of variation

      // Risk status determination
      let status = 'SAFE';
      let statusClass = 'badge-safe';
      if (cv > 0.35 || item.reorder_point > 20000) {
        status = 'HIGH_VOLATILITY';
        statusClass = 'badge-critical';
      } else if (cv > 0.20 || item.reorder_point > 10000) {
        status = 'ATTENTION_NEEDED';
        statusClass = 'badge-medium';
      }

      return {
        ...item,
        cv: cv.toFixed(2),
        status,
        statusClass,
      };
    });
  }, [recommendations]);

  // Filtered rows
  const filteredRows = useMemo(() => {
    let list = enrichedData;
    if (skuSearch.trim()) {
      list = list.filter(item =>
        String(item.product_id).includes(skuSearch.trim())
      );
    }
    if (statusFilter !== 'ALL') {
      list = list.filter(item => item.status === statusFilter);
    }
    return list;
  }, [enrichedData, skuSearch, statusFilter]);

  // Metrics summary
  const metrics = useMemo(() => {
    const total = enrichedData.length;
    const highVol = enrichedData.filter(i => i.status === 'HIGH_VOLATILITY').length;
    const attention = enrichedData.filter(i => i.status === 'ATTENTION_NEEDED').length;
    const safe = enrichedData.filter(i => i.status === 'SAFE').length;
    const avgSafetyStock =
      total > 0
        ? Math.round(
            enrichedData.reduce((acc, i) => acc + (Number(i.safety_stock) || 0), 0) /
              total
          )
        : 0;

    return { total, highVol, attention, safe, avgSafetyStock };
  }, [enrichedData]);

  const toggleExpand = id => {
    setExpandedRow(prev => (prev === id ? null : id));
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Inventory Optimization &amp; Safety Stock</h1>
          <p className="page-subtitle">
            Dynamic Reorder Point (ROP), Safety Stock buffers, and Target Stock Level policies based on demand variance.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-ghost btn-sm" onClick={loadData} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Recalculate</span>
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

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card" style={{ '--kpi-color': 'var(--blue)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Monitored SKUs</span>
            <div className="kpi-icon"><Package size={18} /></div>
          </div>
          <div className="kpi-value">{metrics.total}</div>
          <div className="kpi-sub">Active replenishment policies</div>
        </div>

        <div className="kpi-card" style={{ '--kpi-color': 'var(--rose)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">High Volatility</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(244,63,94,0.12)', '--kpi-color': 'var(--rose)' }}>
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#fb7185' }}>{metrics.highVol}</div>
          <div className="kpi-sub">High demand variation (CV &gt; 0.35)</div>
        </div>

        <div className="kpi-card" style={{ '--kpi-color': 'var(--amber)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Attention Needed</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(245,158,11,0.12)', '--kpi-color': 'var(--amber)' }}>
              <Boxes size={18} />
            </div>
          </div>
          <div className="kpi-value" style={{ color: '#fbbf24' }}>{metrics.attention}</div>
          <div className="kpi-sub">Moderate buffer requirement</div>
        </div>

        <div className="kpi-card" style={{ '--kpi-color': 'var(--emerald)' }}>
          <div className="kpi-card-header">
            <span className="kpi-label">Avg Safety Stock</span>
            <div className="kpi-icon" style={{ '--kpi-icon-bg': 'rgba(16,185,129,0.12)', '--kpi-color': 'var(--emerald)' }}>
              <ShieldCheck size={18} />
            </div>
          </div>
          <div className="kpi-value">{metrics.avgSafetyStock.toLocaleString()}</div>
          <div className="kpi-sub">Units / SKU at {(serviceLevel * 100).toFixed(0)}% service level</div>
        </div>
      </div>

      {/* Policy Controls & Filter Bar */}
      <div className="card card-sm" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          {/* Status filter chips */}
          <div className="filter-bar" style={{ margin: 0 }}>
            <button
              className={`filter-chip ${statusFilter === 'ALL' ? 'active' : ''}`}
              onClick={() => setStatusFilter('ALL')}
            >
              All Items ({enrichedData.length})
            </button>
            <button
              className={`filter-chip chip-critical ${statusFilter === 'HIGH_VOLATILITY' ? 'active' : ''}`}
              onClick={() => setStatusFilter('HIGH_VOLATILITY')}
            >
              High Volatility ({metrics.highVol})
            </button>
            <button
              className={`filter-chip chip-warning ${statusFilter === 'ATTENTION_NEEDED' ? 'active' : ''}`}
              onClick={() => setStatusFilter('ATTENTION_NEEDED')}
            >
              Attention ({metrics.attention})
            </button>
            <button
              className={`filter-chip chip-safe ${statusFilter === 'SAFE' ? 'active' : ''}`}
              onClick={() => setStatusFilter('SAFE')}
            >
              Safe Stable ({metrics.safe})
            </button>
          </div>

          {/* Dynamic Configuration Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Sliders size={14} style={{ color: 'var(--text-muted)' }} />
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Lead Time:</span>
              <select
                className="filter-select"
                value={leadTime}
                onChange={e => setLeadTime(Number(e.target.value))}
                style={{ paddingRight: '1.8rem', minWidth: '90px' }}
              >
                <option value={1}>1 Day</option>
                <option value={2}>2 Days</option>
                <option value={3}>3 Days (Default)</option>
                <option value={5}>5 Days</option>
                <option value={7}>7 Days</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Service Level:</span>
              <select
                className="filter-select"
                value={serviceLevel}
                onChange={e => setServiceLevel(Number(e.target.value))}
                style={{ paddingRight: '1.8rem', minWidth: '95px' }}
              >
                <option value={0.90}>90% (z=1.28)</option>
                <option value={0.95}>95% (z=1.65)</option>
                <option value={0.98}>98% (z=2.05)</option>
                <option value={0.99}>99% (z=2.33)</option>
              </select>
            </div>

            {/* City Filter */}
            <select
              className="filter-select"
              value={cityFilter}
              onChange={e => setCityFilter(e.target.value)}
              style={{ minWidth: '120px' }}
            >
              <option value="">All Cities</option>
              <option value="Delhi">Delhi</option>
              <option value="Bengaluru">Bengaluru</option>
              <option value="HR-NCR">HR-NCR</option>
              <option value="Mumbai">Mumbai</option>
            </select>

            {/* SKU Search */}
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Search size={14} style={{ position: 'absolute', left: '0.65rem', color: 'var(--text-muted)', pointerEvents: 'none' }} />
              <input
                type="text"
                className="filter-input"
                style={{ paddingLeft: '2rem', width: '150px' }}
                placeholder="SKU Search..."
                value={skuSearch}
                onChange={e => setSkuSearch(e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Inventory Recommendations Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 className="card-title">Replenishment &amp; Safety Stock Policies</h3>
            <p className="card-subtitle" style={{ marginBottom: 0 }}>
              Showing {filteredRows.length} inventory series configured for {parameters.lead_time_days}-day lead time and {(parameters.target_service_level * 100).toFixed(0)}% target fill rate.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">
            <RefreshCw size={20} className="spin" />
            <span>Calculating dynamic inventory policies...</span>
          </div>
        ) : filteredRows.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <Boxes size={28} />
            </div>
            <div className="empty-state-title">No Inventory Records Found</div>
            <div className="empty-state-desc">
              {enrichedData.length === 0
                ? 'Inventory report inventory_decision_sample.csv not available. Run inventory calculations first.'
                : 'No SKUs match the current filter or search criteria.'}
            </div>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 30 }}></th>
                  <th>Product ID / SKU</th>
                  <th>City</th>
                  <th>Mean Daily Demand</th>
                  <th>Std Deviation</th>
                  <th>Safety Stock</th>
                  <th>Reorder Point (ROP)</th>
                  <th>Target Stock Level (TSL)</th>
                  <th>Risk Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((item, idx) => {
                  const isExpanded = expandedRow === `${item.product_id}-${item.city_name}`;
                  const rowKey = `${item.product_id}-${item.city_name}`;
                  const mean = Number(item.mean_daily_demand) || 0;
                  const std = Number(item.std_daily_demand) || 0;
                  const ss = Number(item.safety_stock) || 0;
                  const rop = Number(item.reorder_point) || 0;
                  const tsl = Number(item.target_stock_level) || 0;

                  return (
                    <React.Fragment key={rowKey}>
                      <tr
                        onClick={() => toggleExpand(rowKey)}
                        style={{ cursor: 'pointer', background: isExpanded ? 'rgba(59,130,246,0.06)' : undefined }}
                      >
                        <td>
                          {isExpanded ? (
                            <ChevronDown size={15} style={{ color: 'var(--blue)' }} />
                          ) : (
                            <ChevronRight size={15} style={{ color: 'var(--text-muted)' }} />
                          )}
                        </td>
                        <td className="mono bold">{item.product_id}</td>
                        <td>{item.city_name}</td>
                        <td className="mono">{mean.toFixed(1)} u/d</td>
                        <td className="mono" style={{ color: 'var(--text-muted)' }}>&plusmn;{std.toFixed(1)}</td>
                        <td className="mono bold" style={{ color: 'var(--emerald)' }}>{ss.toLocaleString()} u</td>
                        <td className="mono bold" style={{ color: '#60a5fa' }}>{rop.toLocaleString()} u</td>
                        <td className="mono">{tsl.toLocaleString()} u</td>
                        <td>
                          <span className={`badge ${item.statusClass}`}>
                            {item.status.replace(/_/g, ' ')}
                          </span>
                        </td>
                      </tr>

                      {/* Expandable Explanation Row */}
                      {isExpanded && (
                        <tr style={{ background: 'rgba(17, 24, 39, 0.95)' }}>
                          <td colSpan={9} style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-md)' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#60a5fa', fontSize: '0.82rem', fontWeight: 600 }}>
                                <Info size={15} />
                                <span>Deterministic Calculation Breakdown for SKU {item.product_id} in {item.city_name}:</span>
                              </div>
                              <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                Over a <strong>{leadTime}-day lead time</strong> with a target service level of <strong>{(serviceLevel * 100).toFixed(0)}%</strong> (normal distribution z-score = <strong>{serviceLevel === 0.95 ? '1.645' : serviceLevel === 0.99 ? '2.326' : serviceLevel === 0.90 ? '1.282' : '2.054'}</strong>):
                              </p>
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem', marginTop: '0.25rem' }}>
                                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.6rem 0.8rem', borderRadius: 6 }}>
                                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Safety Stock Buffer:</span>
                                  <div style={{ fontSize: '0.85rem', color: 'var(--emerald)', fontWeight: 600 }}>
                                    {ss.toLocaleString()} units
                                  </div>
                                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Formula: &lceil;z &times; &sigma; &times; &radic;L&rceil;</span>
                                </div>
                                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.6rem 0.8rem', borderRadius: 6 }}>
                                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Reorder Point (ROP):</span>
                                  <div style={{ fontSize: '0.85rem', color: '#60a5fa', fontWeight: 600 }}>
                                    {rop.toLocaleString()} units
                                  </div>
                                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Trigger PO when stock &le; ROP</span>
                                </div>
                                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.6rem 0.8rem', borderRadius: 6 }}>
                                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Target Stock Level (TSL):</span>
                                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                                    {tsl.toLocaleString()} units
                                  </div>
                                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>7-day review order-up-to target</span>
                                </div>
                                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.6rem 0.8rem', borderRadius: 6 }}>
                                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Demand Volatility (CV):</span>
                                  <div style={{ fontSize: '0.85rem', color: 'var(--amber)', fontWeight: 600 }}>
                                    {item.cv}
                                  </div>
                                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>std / mean daily ratio</span>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
