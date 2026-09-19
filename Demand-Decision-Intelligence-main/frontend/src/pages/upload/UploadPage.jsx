import React, { useRef, useState } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, FileText, X } from 'lucide-react';
import api from '../../services/api';

export default function UploadPage() {
  const fileInputRef          = useRef(null);
  const [file, setFile]       = useState(null);
  const [fillDates, setFillDates] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult]   = useState(null);   // AggregateResponse from API
  const [error, setError]     = useState('');
  const [dragOver, setDragOver] = useState(false);

  const acceptFile = (f) => {
    if (!f) return;
    const ext = f.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
      setError('Unsupported file type. Please upload a .csv, .xlsx, or .xls file.');
      return;
    }
    setFile(f);
    setResult(null);
    setError('');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    acceptFile(e.dataTransfer.files?.[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    setResult(null);

    const form = new FormData();
    form.append('file', file);

    try {
      const { data } = await api.post(
        `/api/demand/aggregate?fill_missing_dates=${fillDates}`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setResult(data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : detail?.message ?? 'Upload failed. Please try again.'
      );
    } finally {
      setUploading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setResult(null);
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div>
      {/* Drop zone */}
      <div
        className="card"
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragOver ? 'var(--accent-primary)' : 'var(--border-strong)'}`,
          textAlign: 'center',
          padding: '3rem 2rem',
          transition: 'border-color 0.2s',
          backgroundColor: dragOver ? 'rgba(59,130,246,0.05)' : undefined,
        }}
      >
        <UploadCloud size={48} color={dragOver ? '#3b82f6' : '#6b7280'} style={{ margin: '0 auto 1rem' }} />
        <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Upload Sales Dataset</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Drag &amp; drop a <strong>.csv</strong>, <strong>.xlsx</strong>, or <strong>.xls</strong> file,
          or click below to browse.
        </p>

        <input
          ref={fileInputRef}
          id="file-upload-input"
          type="file"
          accept=".csv,.xlsx,.xls"
          style={{ display: 'none' }}
          onChange={(e) => acceptFile(e.target.files?.[0])}
        />
        <button
          id="browse-files-btn"
          className="btn btn-primary"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
        >
          Browse Files
        </button>
      </div>

      {/* Selected file info */}
      {file && !result && (
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <FileText size={20} color="#3b82f6" />
            <div>
              <div style={{ fontWeight: 600 }}>{file.name}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {(file.size / 1024).toFixed(1)} KB
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                id="fill-dates-checkbox"
                checked={fillDates}
                onChange={(e) => setFillDates(e.target.checked)}
              />
              Fill missing dates (zero demand)
            </label>
            <button
              id="upload-btn"
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={uploading}
              style={{ opacity: uploading ? 0.7 : 1 }}
            >
              {uploading ? 'Uploading…' : 'Upload & Validate'}
            </button>
            <button
              id="reset-btn"
              className="btn"
              onClick={reset}
              disabled={uploading}
              style={{ background: 'transparent', color: 'var(--text-muted)', padding: '0.5rem' }}
              title="Remove file"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card" style={{
          border: '1px solid var(--accent-rose)',
          backgroundColor: 'rgba(244,63,94,0.08)',
          color: 'var(--accent-rose)',
          display: 'flex', gap: '0.75rem', alignItems: 'flex-start',
        }}>
          <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
          <span style={{ fontSize: '0.9rem' }}>{error}</span>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <CheckCircle2 size={22} color="#10b981" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>
                {result.status === 'complete' ? 'Upload Successful' : 'Upload Failed'}
              </h3>
            </div>
            <button className="btn" onClick={reset} style={{ background: 'transparent', color: 'var(--text-muted)', padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}>
              Upload another
            </button>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>{result.message}</p>

          {/* Summary grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            {[
              { label: 'Total Rows Read',    value: result.validation.total_rows_read },
              { label: 'Valid Rows',          value: result.validation.valid_rows, color: '#10b981' },
              { label: 'Rejected Rows',       value: result.validation.rejected_rows, color: result.validation.rejected_rows > 0 ? '#f43f5e' : undefined },
              { label: 'Aggregated Records',  value: result.aggregated_rows, color: '#3b82f6' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ backgroundColor: 'var(--bg-main)', borderRadius: 8, padding: '0.875rem 1rem', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.35rem' }}>{label}</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: color ?? '#f9fafb' }}>{value.toLocaleString()}</div>
              </div>
            ))}
          </div>

          {/* Date coverage */}
          {result.validation.date_coverage?.date_min && (
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              📅 Date coverage: <strong>{result.validation.date_coverage.date_min}</strong> → <strong>{result.validation.date_coverage.date_max}</strong>
            </div>
          )}

          {/* Fills applied */}
          {result.validation.fills_applied?.length > 0 && (
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                Optional fills applied:
              </div>
              <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.8 }}>
                {result.validation.fills_applied.map((fill, i) => (
                  <li key={i}>{fill}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Validation checklist card */}
      {!result && (
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Dataset Validation Checklist</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {[
              { ok: true,  label: 'Required columns: date_, product_id, procured_quantity, unit_selling_price' },
              { ok: true,  label: 'Date format validation &amp; parsing' },
              { ok: true,  label: 'Negative / zero quantity &amp; price rejection' },
              { ok: true,  label: 'Optional fills: city_name, discount, order_id' },
              { ok: true,  label: 'Duplicate row detection' },
              { ok: false, label: 'Negative or outlier price checks (pre-processing filter)' },
            ].map(({ ok, label }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-secondary)' }}>
                {ok
                  ? <CheckCircle2 size={18} color="#10b981" />
                  : <AlertCircle  size={18} color="#f59e0b" />
                }
                <span dangerouslySetInnerHTML={{ __html: label }} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
