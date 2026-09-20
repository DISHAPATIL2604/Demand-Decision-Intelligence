import React, { useEffect, useState } from "react";
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Info,
  Download,
  Check,
  X,
  FileCheck,
  ArrowRight,
  ShieldCheck,
  Calendar,
  Layers,
  HelpCircle
} from "lucide-react";
import { uploadSalesFile, getUploads } from "../../services/api";
import { Link } from "react-router-dom";

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [uploads, setUploads] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [showGuide, setShowGuide] = useState(false);

  const loadUploads = async () => {
    try {
      const data = await getUploads();
      setUploads(data.uploads || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadUploads();
  }, []);

  const handleFile = (selectedFile) => {
    setError("");
    setResult(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Please select a valid CSV spreadsheet file (.csv).");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
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
      setError(err.message || "Failed to upload file. Please verify CSV format.");
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
    <div style={{ maxWidth: "1300px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <UploadCloud color="var(--accent-primary)" size={28} />
              Upload Daily Sales Sheet
            </h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.925rem", marginTop: "0.25rem" }}>
              Upload your store's daily sales spreadsheet (CSV). The system automatically checks every item, updates your inventory, and tells you what to reorder today.
            </p>
          </div>

          <button
            onClick={downloadSampleTemplate}
            className="btn"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              backgroundColor: "var(--bg-surface-elevated)",
              border: "1px solid var(--border-strong)",
              color: "var(--accent-cyan)",
              padding: "0.6rem 1.1rem",
              borderRadius: "8px",
              fontSize: "0.85rem",
              fontWeight: 600,
              cursor: "pointer"
            }}
          >
            <Download size={15} />
            Download Sample CSV Template
          </button>
        </div>
      </div>

      {/* 3-Step Simple Guide Card */}
      <div className="card" style={{ padding: "1.25rem 1.5rem", marginBottom: "1.5rem", backgroundColor: "rgba(59, 130, 246, 0.05)", border: "1px solid rgba(59, 130, 246, 0.2)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.85rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 600, color: "var(--accent-primary)", fontSize: "0.95rem" }}>
            <HelpCircle size={18} />
            How It Works in 3 Simple Steps
          </div>
          <button
            onClick={() => setShowGuide(!showGuide)}
            style={{ background: "none", border: "none", color: "var(--text-secondary)", fontSize: "0.8rem", cursor: "pointer", textDecoration: "underline" }}
          >
            {showGuide ? "Hide Column Details" : "View Required Spreadsheet Columns"}
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem" }}>
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
            <div style={{ width: "26px", height: "26px", borderRadius: "50%", backgroundColor: "var(--accent-primary)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: "0.8rem", flexShrink: 0 }}>1</div>
            <div>
              <div style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: "0.85rem" }}>Export Daily Sales</div>
              <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>Export your billing/POS sales report as a <code>.csv</code> file.</div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
            <div style={{ width: "26px", height: "26px", borderRadius: "50%", backgroundColor: "var(--accent-primary)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: "0.8rem", flexShrink: 0 }}>2</div>
            <div>
              <div style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: "0.85rem" }}>Drop File Below</div>
              <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>Drag and drop or select the file in the upload box.</div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
            <div style={{ width: "26px", height: "26px", borderRadius: "50%", backgroundColor: "var(--accent-primary)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: "0.8rem", flexShrink: 0 }}>3</div>
            <div>
              <div style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: "0.85rem" }}>Instant Decision Update</div>
              <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>The system immediately checks for errors and tells you how much stock to reorder.</div>
            </div>
          </div>
        </div>

        {/* Expandable column guide */}
        {showGuide && (
          <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid rgba(255,255,255,0.06)", fontSize: "0.8rem" }}>
            <div style={{ fontWeight: 600, color: "#fff", marginBottom: "0.5rem" }}>Expected Spreadsheet Columns:</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.5rem" }}>
              <div style={{ color: "var(--text-secondary)" }}>• <strong>date_</strong>: Sale date (YYYY-MM-DD)</div>
              <div style={{ color: "var(--text-secondary)" }}>• <strong>city_name</strong>: Store hub (e.g. Delhi, Mumbai)</div>
              <div style={{ color: "var(--text-secondary)" }}>• <strong>product_id</strong>: Product code from catalog</div>
              <div style={{ color: "var(--text-secondary)" }}>• <strong>procured_quantity</strong>: Units sold</div>
              <div style={{ color: "var(--text-secondary)" }}>• <strong>unit_selling_price</strong>: Selling price per unit</div>
              <div style={{ color: "var(--text-secondary)" }}>• <strong>order_id</strong>: Bill / Order number</div>
            </div>
          </div>
        )}
      </div>

      {/* Main Upload Dropzone Card */}
      <div className="card" style={{ padding: "2rem", marginBottom: "1.5rem" }}>
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          style={{
            border: dragActive ? "2px dashed var(--accent-primary)" : "2px dashed var(--border-strong)",
            borderRadius: "12px",
            padding: "3rem 1.5rem",
            textAlign: "center",
            backgroundColor: dragActive ? "rgba(59, 130, 246, 0.1)" : "var(--bg-surface-elevated)",
            cursor: "pointer",
            transition: "all 0.2s ease",
            position: "relative"
          }}
        >
          <input
            type="file"
            accept=".csv"
            onChange={(e) => handleFile(e.target.files[0])}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              opacity: 0,
              cursor: "pointer"
            }}
          />

          <div style={{ width: "56px", height: "56px", borderRadius: "50%", backgroundColor: "rgba(59, 130, 246, 0.15)", color: "var(--accent-primary)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1rem" }}>
            <FileSpreadsheet size={28} />
          </div>

          <h3 style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.3rem" }}>
            {file ? file.name : "Drag & Drop Your Sales CSV Here"}
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
            {file ? `${(file.size / 1024).toFixed(1)} KB • Click or drop another file to replace` : "or click to browse files from your computer"}
          </p>

          <span
            style={{
              display: "inline-block",
              padding: "0.5rem 1.25rem",
              borderRadius: "6px",
              backgroundColor: "var(--bg-surface)",
              border: "1px solid var(--border-strong)",
              color: "#fff",
              fontSize: "0.85rem",
              fontWeight: 500
            }}
          >
            {file ? "Change Selected File" : "Choose CSV File"}
          </span>
        </div>

        {/* Selected File Details & Upload Action */}
        {file && (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1.25rem", padding: "1rem", backgroundColor: "var(--bg-surface-elevated)", borderRadius: "8px", border: "1px solid var(--border-strong)", flexWrap: "wrap", gap: "1rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <CheckCircle2 color="var(--accent-emerald)" size={20} />
              <div>
                <div style={{ fontWeight: 600, color: "#fff", fontSize: "0.9rem" }}>{file.name}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Ready to verify • {(file.size / 1024).toFixed(1)} KB</div>
              </div>
            </div>

            <button
              onClick={handleUpload}
              disabled={uploading}
              className="btn btn-primary"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.7rem 1.5rem",
                fontWeight: 600
              }}
            >
              {uploading ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  Verifying & Storing Rows...
                </>
              ) : (
                <>
                  <FileCheck size={16} />
                  Analyze & Save Sales Sheet
                </>
              )}
            </button>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div style={{ marginTop: "1rem", padding: "0.85rem 1.25rem", backgroundColor: "rgba(244, 63, 94, 0.12)", border: "1px solid var(--accent-rose)", borderRadius: "8px", color: "var(--accent-rose)", fontSize: "0.875rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Upload Results Card (Plain English) */}
      {result && (
        <div className="card" style={{ padding: "1.5rem", marginBottom: "1.5rem", border: "1px solid var(--accent-emerald)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem", flexWrap: "wrap", gap: "0.5rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <div style={{ width: "28px", height: "28px", borderRadius: "50%", backgroundColor: "rgba(16, 185, 129, 0.2)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--accent-emerald)" }}>
                <Check size={16} />
              </div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 600, color: "#fff" }}>
                Sales Sheet Successfully Processed & Saved
              </h3>
            </div>

            <Link
              to="/inventory"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.3rem",
                color: "var(--accent-cyan)",
                fontSize: "0.85rem",
                fontWeight: 600,
                textDecoration: "none"
              }}
            >
              View Updated Reorder Plan <ArrowRight size={14} />
            </Link>
          </div>

          {/* KPI Summary Tiles */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "1rem", marginBottom: "1.25rem" }}>
            <div style={{ padding: "1rem", backgroundColor: "var(--bg-surface-elevated)", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>File Status</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-emerald)", marginTop: "0.2rem" }}>
                {result.status}
              </div>
            </div>

            <div style={{ padding: "1rem", backgroundColor: "var(--bg-surface-elevated)", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>Total Rows Read</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#fff", marginTop: "0.2rem" }}>
                {result.total_rows}
              </div>
            </div>

            <div style={{ padding: "1rem", backgroundColor: "var(--bg-surface-elevated)", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>Accepted & Stored</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-cyan)", marginTop: "0.2rem" }}>
                {result.valid_rows}
              </div>
            </div>

            <div style={{ padding: "1rem", backgroundColor: "var(--bg-surface-elevated)", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600 }}>Rejected / Errors</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: result.invalid_rows > 0 ? "var(--accent-rose)" : "var(--accent-emerald)", marginTop: "0.2rem" }}>
                {result.invalid_rows}
              </div>
            </div>
          </div>

          {/* Plain English Verification Checklist */}
          {result.validation && (
            <div>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.6rem" }}>
                Data Health Checklist
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "0.75rem" }}>
                <div style={{ padding: "0.75rem 1rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "6px", border: "1px solid var(--border-subtle)", display: "flex", alignItems: "center", gap: "0.6rem" }}>
                  <Check size={16} color="var(--accent-emerald)" />
                  <span style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>All required columns present</span>
                </div>

                <div style={{ padding: "0.75rem 1rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "6px", border: "1px solid var(--border-subtle)", display: "flex", alignItems: "center", gap: "0.6rem" }}>
                  {result.validation.invalid_dates === 0 ? <Check size={16} color="var(--accent-emerald)" /> : <X size={16} color="var(--accent-rose)" />}
                  <span style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
                    Dates valid ({result.validation.invalid_dates || 0} issues)
                  </span>
                </div>

                <div style={{ padding: "0.75rem 1rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "6px", border: "1px solid var(--border-subtle)", display: "flex", alignItems: "center", gap: "0.6rem" }}>
                  {result.validation.unmatched_product_ids === 0 ? <Check size={16} color="var(--accent-emerald)" /> : <X size={16} color="var(--accent-amber)" />}
                  <span style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
                    Product codes matched store catalog
                  </span>
                </div>

                <div style={{ padding: "0.75rem 1rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "6px", border: "1px solid var(--border-subtle)", display: "flex", alignItems: "center", gap: "0.6rem" }}>
                  {result.validation.negative_quantity === 0 ? <Check size={16} color="var(--accent-emerald)" /> : <X size={16} color="var(--accent-rose)" />}
                  <span style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
                    Quantities and prices positive & valid
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Upload History Table */}
      <div className="card" style={{ padding: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
          <div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Spreadsheet Upload History
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              Audit trail of all sales files uploaded to the store system.
            </p>
          </div>
          <button
            onClick={loadUploads}
            className="btn"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.3rem",
              backgroundColor: "var(--bg-surface-elevated)",
              border: "1px solid var(--border-strong)",
              color: "var(--text-secondary)",
              padding: "0.45rem 0.85rem",
              borderRadius: "6px",
              fontSize: "0.8rem",
              cursor: "pointer"
            }}
          >
            <RefreshCw size={14} /> Refresh List
          </button>
        </div>

        {uploads.length === 0 ? (
          <div style={{ textAlign: "center", padding: "3rem", color: "var(--text-muted)" }}>
            No sales spreadsheets have been uploaded yet. Upload your first CSV above.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <th style={{ padding: "0.75rem", textAlign: "left", color: "var(--text-muted)", fontSize: "0.78rem", textTransform: "uppercase" }}>File Name</th>
                  <th style={{ padding: "0.75rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.78rem", textTransform: "uppercase" }}>Processing Status</th>
                  <th style={{ padding: "0.75rem", textAlign: "right", color: "var(--text-muted)", fontSize: "0.78rem", textTransform: "uppercase" }}>Total Rows</th>
                  <th style={{ padding: "0.75rem", textAlign: "right", color: "var(--text-muted)", fontSize: "0.78rem", textTransform: "uppercase" }}>Stored Rows</th>
                  <th style={{ padding: "0.75rem", textAlign: "left", color: "var(--text-muted)", fontSize: "0.78rem", textTransform: "uppercase" }}>Upload Date</th>
                </tr>
              </thead>
              <tbody>
                {uploads.map((upload, idx) => {
                  const isCompleted = upload.status === "COMPLETED";
                  const isProcessing = upload.status === "PROCESSING" || upload.status === "VALIDATING";

                  const badgeColor = isCompleted
                    ? "var(--accent-emerald)"
                    : isProcessing
                    ? "var(--accent-amber)"
                    : "var(--accent-rose)";

                  const badgeBg = isCompleted
                    ? "rgba(16, 185, 129, 0.15)"
                    : isProcessing
                    ? "rgba(245, 158, 11, 0.15)"
                    : "rgba(244, 63, 94, 0.15)";

                  return (
                    <tr
                      key={upload.id || idx}
                      style={{
                        borderBottom: "1px solid var(--border-subtle)",
                        backgroundColor: idx % 2 === 0 ? "transparent" : "rgba(255, 255, 255, 0.01)"
                      }}
                    >
                      <td style={{ padding: "0.75rem", fontWeight: 600, color: "#fff", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <FileSpreadsheet size={16} color="var(--accent-primary)" />
                        {upload.filename || "sales_file.csv"}
                      </td>

                      <td style={{ padding: "0.75rem", textAlign: "center" }}>
                        <span
                          style={{
                            padding: "0.25rem 0.65rem",
                            borderRadius: "6px",
                            fontSize: "0.75rem",
                            fontWeight: 700,
                            backgroundColor: badgeBg,
                            color: badgeColor,
                            display: "inline-block"
                          }}
                        >
                          {isCompleted ? "VERIFIED & SAVED" : upload.status}
                        </span>
                      </td>

                      <td style={{ padding: "0.75rem", textAlign: "right", color: "var(--text-secondary)" }}>
                        {upload.total_rows?.toLocaleString() || "—"}
                      </td>

                      <td style={{ padding: "0.75rem", textAlign: "right", fontWeight: 600, color: "var(--accent-cyan)" }}>
                        {upload.processed_rows?.toLocaleString() || "—"}
                      </td>

                      <td style={{ padding: "0.75rem", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                        {upload.created_at ? new Date(upload.created_at).toLocaleString() : "Recently"}
                      </td>
                    </tr>
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