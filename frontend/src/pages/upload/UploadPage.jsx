import React, { useEffect, useState } from "react";
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  Clock,
  RefreshCw,
  FileCheck,
  Layers,
  Database,
} from "lucide-react";
import { uploadSalesFile, getUploads } from "../../services/api";

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [uploads, setUploads] = useState([]);
  const [loadingUploads, setLoadingUploads] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const loadUploads = async () => {
    try {
      setLoadingUploads(true);
      const data = await getUploads();
      setUploads(data.uploads || []);
    } catch (err) {
      console.error("Failed to fetch uploads:", err);
    } finally {
      setLoadingUploads(false);
    }
  };

  useEffect(() => {
    loadUploads();
  }, []);

  const handleFileSelect = (selectedFile) => {
    setError("");
    setResult(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Please select a valid CSV file (e.g. sales_transactions.csv).");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleFileChange = (e) => {
    handleFileSelect(e.target.files[0]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a sales CSV spreadsheet first.");
      return;
    }

    try {
      setUploading(true);
      setError("");
      setResult(null);

      const data = await uploadSalesFile(file);
      setResult(data);
      await loadUploads();
      setFile(null);
    } catch (err) {
      setError(err.message || "File upload failed");
    } finally {
      setUploading(false);
    }
  };

  const downloadSampleTemplate = () => {
    const csvContent =
      "date_,city_name,order_id,cart_id,dim_customer_key,procured_quantity,unit_selling_price,total_discount_amount,product_id,total_weighted_landing_price\n" +
      "2026-04-01,Delhi,ORD101,CRT101,CUST101,10,150.00,15.00,19512,120.00\n" +
      "2026-04-01,Bengaluru,ORD102,CRT102,CUST102,5,245.00,20.00,391306,190.00\n" +
      "2026-04-02,Mumbai,ORD103,CRT103,CUST103,12,28.00,0.00,12872,22.00\n";

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "sample_sales_template.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Sales Data Ingestion &amp; Validation</h1>
          <p className="page-subtitle">
            Upload commercial grocery sales batches, run automated forensic integrity checks, and load into PostgreSQL.
          </p>
        </div>
        <div className="page-header-actions">
          <button
            className="btn btn-ghost btn-sm"
            onClick={loadUploads}
            disabled={loadingUploads}
          >
            <RefreshCw size={14} className={loadingUploads ? "spin" : ""} />
            <span>Refresh History</span>
          </button>
        </div>
      </div>

      {/* Upload Zone Card */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2 className="card-title">Upload Sales Batch (CSV)</h2>
        <p className="card-subtitle">
          Expected schema: <code className="mono">date, product_id, city, units_sold, sales_revenue</code>. Max file size: 100MB.
        </p>

        {/* Drag-and-Drop Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${
              isDragOver
                ? "var(--blue)"
                : file
                ? "var(--emerald)"
                : "rgba(255,255,255,0.15)"
            }`,
            borderRadius: "var(--r-md)",
            background: isDragOver
              ? "rgba(59, 130, 246, 0.08)"
              : file
              ? "rgba(16, 185, 129, 0.04)"
              : "rgba(255, 255, 255, 0.02)",
            padding: "2.5rem 1.5rem",
            textAlign: "center",
            cursor: "pointer",
            transition: "all 0.2s ease",
            position: "relative",
          }}
          onClick={() => document.getElementById("file-upload-input").click()}
        >
          <input
            id="file-upload-input"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            style={{ display: "none" }}
          />

          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: "14px",
              background: file ? "rgba(16,185,129,0.15)" : "rgba(59,130,246,0.12)",
              color: file ? "var(--emerald)" : "var(--blue-light)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 1rem",
            }}
          >
            {file ? <FileSpreadsheet size={28} /> : <UploadCloud size={28} />}
          </div>

          {file ? (
            <div>
              <div style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--text-primary)" }}>
                {file.name}
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                Size: {(file.size / 1024).toFixed(1)} KB &bull; Ready for validation
              </div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--text-primary)" }}>
                Drag and drop your sales CSV here, or <span style={{ color: "var(--blue-light)" }}>browse file</span>
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.35rem" }}>
                Supports standard comma-delimited sales logs with transaction dates and quantities
              </div>
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "1.25rem" }}>
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="btn btn-primary"
            style={{ minWidth: "160px" }}
          >
            {uploading ? (
              <>
                <RefreshCw size={15} className="spin" />
                <span>Validating &amp; Uploading...</span>
              </>
            ) : (
              <>
                <UploadCloud size={16} />
                <span>Upload &amp; Process CSV</span>
              </>
            )}
          </button>

          {file && (
            <button
              className="btn btn-ghost btn-sm"
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
              }}
            >
              Clear
            </button>
          )}
        </div>

        {/* Error Banner */}
        {error && (
          <div
            style={{
              marginTop: "1.25rem",
              padding: "0.85rem 1rem",
              borderRadius: "var(--r-sm)",
              background: "rgba(244, 63, 94, 0.1)",
              border: "1px solid rgba(244, 63, 94, 0.25)",
              color: "#fb7185",
              display: "flex",
              alignItems: "center",
              gap: "0.6rem",
              fontSize: "0.85rem",
            }}
          >
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Upload & Validation Result Feedback */}
      {result && (
        <div
          className="card"
          style={{
            marginBottom: "1.5rem",
            borderColor: "rgba(16, 185, 129, 0.3)",
            background: "rgba(16, 185, 129, 0.03)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
            <CheckCircle2 size={20} style={{ color: "var(--emerald)" }} />
            <h3 className="card-title" style={{ margin: 0, color: "var(--text-primary)" }}>
              Ingestion Succeeded &bull; Batch Validated
            </h3>
          </div>

          <div className="kpi-grid" style={{ marginBottom: "1rem" }}>
            <div className="kpi-card" style={{ '--kpi-color': 'var(--emerald)' }}>
              <div className="kpi-label">Status</div>
              <div className="kpi-value" style={{ fontSize: "1.3rem", color: "var(--emerald)" }}>
                {result.status || "SUCCESS"}
              </div>
            </div>

            <div className="kpi-card" style={{ '--kpi-color': 'var(--blue)' }}>
              <div className="kpi-label">Total Rows</div>
              <div className="kpi-value" style={{ fontSize: "1.3rem" }}>
                {result.total_rows?.toLocaleString() ?? 0}
              </div>
            </div>

            <div className="kpi-card" style={{ '--kpi-color': 'var(--emerald)' }}>
              <div className="kpi-label">Valid Rows</div>
              <div className="kpi-value" style={{ fontSize: "1.3rem", color: "var(--emerald)" }}>
                {result.valid_rows?.toLocaleString() ?? 0}
              </div>
            </div>

            <div className="kpi-card" style={{ '--kpi-color': 'var(--rose)' }}>
              <div className="kpi-label">Invalid Rows</div>
              <div className="kpi-value" style={{ fontSize: "1.3rem", color: result.invalid_rows > 0 ? "#fb7185" : "inherit" }}>
                {result.invalid_rows?.toLocaleString() ?? 0}
              </div>
            </div>
          </div>

          {result.validation && (
            <div style={{ marginTop: "1rem", borderTop: "1px solid var(--border)", paddingTop: "1rem" }}>
              <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.65rem" }}>
                Automated Integrity Audit
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.75rem" }}>
                {Object.entries(result.validation).map(([k, v]) => (
                  <div
                    key={k}
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      padding: "0.6rem 0.8rem",
                      borderRadius: "var(--r-sm)",
                      border: "1px solid var(--border)",
                    }}
                  >
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "capitalize" }}>
                      {k.replace(/_/g, " ")}:
                    </span>
                    <div className="mono bold" style={{ fontSize: "0.88rem", marginTop: "2px" }}>
                      {String(v)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Upload History Table */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
          <div>
            <h3 className="card-title">Upload History &amp; Audit Log</h3>
            <p className="card-subtitle" style={{ marginBottom: 0 }}>
              Audit trail of uploaded sales batches and processing milestones
            </p>
          </div>
          <span className="badge badge-neutral">
            <Clock size={12} /> {uploads.length} Batches
          </span>
        </div>

        {loadingUploads ? (
          <div className="loading-state">
            <RefreshCw size={20} className="spin" />
            <span>Fetching upload history...</span>
          </div>
        ) : uploads.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <FileSpreadsheet size={28} />
            </div>
            <div className="empty-state-title">No Uploads Recorded</div>
            <div className="empty-state-desc">
              Uploaded files will be registered in the system audit log and persisted in PostgreSQL.
            </div>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Batch ID</th>
                  <th>File Name</th>
                  <th>Ingestion Status</th>
                  <th>Total Rows</th>
                  <th>Processed Rows</th>
                  <th>Audited Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {uploads.map((u) => (
                  <tr key={u.id}>
                    <td className="mono bold">#{u.id}</td>
                    <td className="bold" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <FileSpreadsheet size={15} style={{ color: "var(--blue-light)" }} />
                      <span>{u.filename}</span>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          u.status === "COMPLETED" || u.status === "SUCCESS"
                            ? "badge-safe"
                            : u.status === "FAILED"
                            ? "badge-critical"
                            : "badge-medium"
                        }`}
                      >
                        {u.status || "COMPLETED"}
                      </span>
                    </td>
                    <td className="mono">{u.total_rows?.toLocaleString() ?? "-"}</td>
                    <td className="mono">{u.processed_rows?.toLocaleString() ?? "-"}</td>
                    <td style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                      {u.created_at ? new Date(u.created_at).toLocaleString() : "Recorded"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}