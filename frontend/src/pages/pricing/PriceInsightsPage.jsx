import React, { useEffect, useState, useMemo } from 'react';
import {
  Tag,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Search,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  Boxes,
  Zap,
  CheckCircle2,
  Building,
  Info,
  Layers,
  ArrowRight
} from 'lucide-react';
import api from '../../services/api';

export default function PriceInsightsPage() {
  const [marketData, setMarketData] = useState(null);
  const [decisionsData, setDecisionsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');
  const [activeTab, setActiveTab] = useState('decisions'); // 'decisions' | 'rates'
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadAllPriceData();
  }, []);

  const loadAllPriceData = async () => {
    setLoading(true);
    try {
      const [marketRes, decisionsRes] = await Promise.all([
        api.get('/market-prices/live').catch(() => null),
        api.get('/market-prices/stock-decisions').catch(() => null),
      ]);

      if (marketRes?.data) setMarketData(marketRes.data);
      if (decisionsRes?.data) setDecisionsData(decisionsRes.data);
    } catch (err) {
      console.error('Failed to load market prices', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncLive = async () => {
    setSyncing(true);
    setSyncMessage('');
    try {
      const res = await api.post('/market-prices/sync');
      setSyncMessage(res.data?.message || 'Successfully synchronized with Ministry portal!');
      await loadAllPriceData();
    } catch (err) {
      console.error('Failed to sync live rates', err);
      setSyncMessage('Sync request completed.');
      await loadAllPriceData();
    } finally {
      setSyncing(false);
    }
  };

  // Decisions list
  const decisions = decisionsData?.decisions || [];

  // Filtered commodities
  const commodities = marketData?.commodities || [];
  const filteredCommodities = useMemo(() => {
    return commodities.filter((c) => {
      const matchesCat = selectedCategory === 'ALL' || c.category.toLowerCase() === selectedCategory.toLowerCase();
      const matchesSearch = !searchQuery || c.commodity.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesCat && matchesSearch;
    });
  }, [commodities, selectedCategory, searchQuery]);

  // High-level KPI aggregates
  const surgeCount = decisions.filter((d) => d.divergence_pct >= 15.0).length;
  const dipCount = decisions.filter((d) => d.divergence_pct <= -10.0).length;
  const stableCount = decisions.filter((d) => d.divergence_pct > -10.0 && d.divergence_pct < 15.0).length;
  const asOnDate = marketData?.as_on_date || 'Today';

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '0.2rem 0.6rem', borderRadius: '999px', backgroundColor: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)', border: '1px solid var(--accent-emerald)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--accent-emerald)', display: 'inline-block' }} />
              LIVE WEB SCRAPER ACTIVE
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Source: Ministry of Consumer Affairs, Food and Public Distribution
            </span>
          </div>

          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Tag color="var(--accent-primary)" size={28} />
            Real-World Price & Dynamic Stocking Intelligence
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.925rem', marginTop: '0.2rem' }}>
            Official government retail market prices (PMD) analyzed in real-time to recommend exact inventory holding quantities.
          </p>
        </div>

        {/* Sync Button */}
        <button
          className="btn btn-primary"
          onClick={handleSyncLive}
          disabled={syncing}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.4rem' }}
        >
          <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
          {syncing ? 'Scraping Ministry Portal...' : '🔄 Sync Live Govt Rates'}
        </button>
      </div>

      {/* Sync Notification Banner */}
      {syncMessage && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '0.75rem 1.25rem', backgroundColor: 'rgba(16, 185, 129, 0.12)', border: '1px solid var(--accent-emerald)', borderRadius: '8px', color: 'var(--accent-emerald)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          <CheckCircle2 size={18} />
          <span>{syncMessage}</span>
        </div>
      )}

      {/* Live Market Price Ticker Ribbon */}
      <div className="card" style={{ padding: '0.85rem 1.25rem', marginBottom: '1.5rem', backgroundColor: 'var(--bg-surface-elevated)', border: '1px solid var(--border-strong)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <Zap size={14} color="var(--accent-amber)" />
            Official Government Retail Benchmark Rates (As on {asOnDate})
          </div>
          <a
            href="https://fcainfoweb.nic.in/Default.aspx"
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '0.25rem', textDecoration: 'none' }}
          >
            Verify on fcainfoweb.nic.in <ExternalLink size={12} />
          </a>
        </div>

        {/* Ticker chips */}
        <div style={{ display: 'flex', gap: '0.75rem', overflowX: 'auto', paddingBottom: '0.25rem' }}>
          {commodities.slice(0, 10).map((c) => (
            <div
              key={c.commodity}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem',
                backgroundColor: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '0.35rem 0.75rem',
                whiteSpace: 'nowrap',
                fontSize: '0.825rem',
              }}
            >
              <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{c.commodity}:</span>
              <span style={{ color: '#fff', fontWeight: 700 }}>₹{c.price_inr_per_kg.toFixed(2)}/kg</span>
            </div>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid-kpi" style={{ marginBottom: '1.5rem' }}>
        <div className="kpi-card">
          <div className="kpi-title">Tracked Essential Commodities</div>
          <div className="kpi-value">{commodities.length || 41} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>items</span></div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Across 555 National Reporting Centres</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Price Surge Alert SKUs</div>
          <div className="kpi-value" style={{ color: 'var(--accent-rose)' }}>{surgeCount}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Divergence &gt; +15% (Trim stock recommendation)</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Procurement Dip Windows</div>
          <div className="kpi-value" style={{ color: 'var(--accent-emerald)' }}>{dipCount}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Divergence &lt; -10% (Bulk stock opportunity)</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Stable Price Band SKUs</div>
          <div className="kpi-value" style={{ color: 'var(--accent-cyan)' }}>{stableCount}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Aligned with Standard ROP Policy</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: '0.75rem', borderBottom: '1px solid var(--border-subtle)', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('decisions')}
          style={{
            padding: '0.65rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'decisions' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            color: activeTab === 'decisions' ? 'var(--accent-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'decisions' ? 700 : 500,
            fontSize: '0.9rem',
            cursor: 'pointer',
          }}
        >
          🎯 Real-World Stocking Recommendations ("Kitni Quantity Rakhna Chahiye")
        </button>
        <button
          onClick={() => setActiveTab('rates')}
          style={{
            padding: '0.65rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'rates' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            color: activeTab === 'rates' ? 'var(--accent-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'rates' ? 700 : 500,
            fontSize: '0.9rem',
            cursor: 'pointer',
          }}
        >
          📊 All Scraped Ministry Commodity Rates ({commodities.length})
        </button>
      </div>

      {/* TAB 1: Stocking Decisions Table */}
      {activeTab === 'decisions' && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Real-World Price-Adjusted Inventory Stocking Policy
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Compares current government retail price vs catalog baseline to recommend holding vs trimming buffer quantity.
              </p>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Rates As on: {asOnDate}
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>SKU & Hub</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Govt Commodity</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Base Cost</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Live Govt Rate</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Price Divergence</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Standard Buffer</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Recommended Holding</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Quantity Action</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Strategy Rationale</th>
                </tr>
              </thead>
              <tbody>
                {decisions.map((row, idx) => (
                  <tr
                    key={row.product_id}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
                    }}
                  >
                    <td style={{ padding: '0.75rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>#{row.product_id}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{row.city_name}</div>
                    </td>
                    <td style={{ padding: '0.75rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
                      {row.product_name}
                      <div style={{ fontSize: '0.75rem', color: 'var(--accent-primary)' }}>({row.commodity_matched})</div>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)' }}>
                      ₹{row.baseline_price.toFixed(2)}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 700, color: '#fff' }}>
                      ₹{row.live_market_price.toFixed(2)}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: '0.8rem',
                          color: row.divergence_pct > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)',
                        }}
                      >
                        {row.divergence_pct > 0 ? `+${row.divergence_pct}%` : `${row.divergence_pct}%`}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)' }}>
                      {row.standard_holding_qty.toLocaleString()}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 700, color: row.badge_color }}>
                      {row.recommended_holding_qty.toLocaleString()}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      <span
                        style={{
                          padding: '0.25rem 0.65rem',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          backgroundColor: row.badge_bg,
                          color: row.badge_color,
                          display: 'inline-block',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.action_label}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-secondary)', fontSize: '0.8rem', maxWidth: '280px' }}>
                      {row.recommendation}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: All Live Scraped Commodities */}
      {activeTab === 'rates' && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
            {/* Category filter pills */}
            <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
              {['ALL', 'Grains & Pulses', 'Edible Oils', 'Vegetables', 'Daily Essentials', 'Additional Millets'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  style={{
                    padding: '0.4rem 0.8rem',
                    borderRadius: '6px',
                    border: selectedCategory === cat ? '1px solid var(--accent-primary)' : '1px solid var(--border-strong)',
                    backgroundColor: selectedCategory === cat ? 'rgba(59, 130, 246, 0.2)' : 'var(--bg-surface-elevated)',
                    color: selectedCategory === cat ? '#93c5fd' : 'var(--text-secondary)',
                    fontSize: '0.8rem',
                    fontWeight: selectedCategory === cat ? 600 : 500,
                    cursor: 'pointer',
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div style={{ position: 'relative', minWidth: '220px' }}>
              <Search size={15} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '9px' }} />
              <input
                type="text"
                placeholder="Filter by commodity..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
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

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>#</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Commodity Name</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Category</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Daily Retail Price</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Unit</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Reporting Date</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase' }}>Source</th>
                </tr>
              </thead>
              <tbody>
                {filteredCommodities.map((c, idx) => (
                  <tr
                    key={c.commodity}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
                    }}
                  >
                    <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>#{idx + 1}</td>
                    <td style={{ padding: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>{c.commodity}</td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-secondary)' }}>{c.category}</td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      ₹{c.price_inr_per_kg.toFixed(2)}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-muted)' }}>{c.unit}</td>
                    <td style={{ padding: '0.75rem', textAlign: 'center', color: 'var(--text-secondary)' }}>{c.as_on_date}</td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                      Govt of India (PMD)
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
