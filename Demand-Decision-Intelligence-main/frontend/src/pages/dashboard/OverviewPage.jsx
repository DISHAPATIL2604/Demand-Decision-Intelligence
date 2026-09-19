import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { TrendingUp, AlertTriangle, PackageCheck, BarChart2 } from 'lucide-react';
import api from '../../services/api';

export default function OverviewPage() {
  const [summary, setSummary] = useState(null);
  const [daily, setDaily]     = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [sumRes, dayRes] = await Promise.all([
          api.get('/api/demand/summary'),
          api.get('/api/demand/daily?page_size=30&exclude_zeros=true'),
        ]);
        setSummary(sumRes.data);

        // Build chart data: aggregate total_quantity per date for top-level view
        const byDate = {};
        for (const row of dayRes.data.results) {
          byDate[row.sale_date] = (byDate[row.sale_date] ?? 0) + row.total_quantity;
        }
        const chartData = Object.entries(byDate)
          .sort(([a], [b]) => a.localeCompare(b))
          .slice(-14)
          .map(([date, qty]) => ({ date: date.slice(5), quantity: qty })); // MM-DD
        setDaily(chartData);
      } catch {
        // silently fall back to empty state
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const fmt = (n) =>
    n == null ? '—' : n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n / 1_000).toFixed(1)}K` : String(n);

  const fmtRev = (n) =>
    n == null ? '—' : `₹${(n / 1_000_000).toFixed(2)}M`;

  return (
    <div>
      <div className="grid-kpi">
        <div className="kpi-card">
          <div className="kpi-title">Total Demand (All Time)</div>
          <div className="kpi-value">
            {loading ? '…' : fmt(summary?.total_quantity)}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Units across all SKUs
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Total Revenue</div>
          <div className="kpi-value" style={{ color: 'var(--accent-emerald)' }}>
            {loading ? '…' : fmtRev(summary?.total_revenue)}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Validated sales revenue
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Unique Products</div>
          <div className="kpi-value" style={{ color: 'var(--accent-cyan)' }}>
            {loading ? '…' : fmt(summary?.unique_products)}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Active product SKUs
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">Cities Covered</div>
          <div className="kpi-value" style={{ color: 'var(--accent-amber)' }}>
            {loading ? '…' : fmt(summary?.unique_cities)}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Demand coverage locations
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Daily Demand Trajectory</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {summary?.date_min && summary?.date_max
                ? `Showing ${summary.date_min} → ${summary.date_max}`
                : 'Aggregated daily units from validated uploads'}
            </p>
          </div>
        </div>
        <div style={{ height: 320, width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            {daily.length > 0 ? (
              <AreaChart data={daily}>
                <defs>
                  <linearGradient id="demandGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}   />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="date" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff', borderRadius: 8 }} />
                <Area type="monotone" dataKey="quantity" stroke="#3b82f6" fill="url(#demandGrad)" strokeWidth={2} name="Daily Units" />
              </AreaChart>
            ) : (
              <AreaChart data={[{ date: 'No data', quantity: 0 }]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="date" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Area type="monotone" dataKey="quantity" stroke="#374151" fill="#1f2937" strokeWidth={1} />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>
        {daily.length === 0 && !loading && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
            No demand data yet — upload a sales file to get started.
          </div>
        )}
      </div>

      {/* Top products table */}
      {summary?.top_products_by_qty?.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>Top Products by Quantity</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  {['Rank', 'Product ID', 'Total Quantity'].map((h) => (
                    <th key={h} style={{ padding: '0.6rem 0.75rem', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 500, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {summary.top_products_by_qty.map((row, i) => (
                  <tr key={row.product_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '0.65rem 0.75rem', color: 'var(--text-muted)' }}>#{i + 1}</td>
                    <td style={{ padding: '0.65rem 0.75rem', fontWeight: 500 }}>{row.product_id}</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: 'var(--accent-cyan)' }}>{row.total_qty.toLocaleString()}</td>
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
