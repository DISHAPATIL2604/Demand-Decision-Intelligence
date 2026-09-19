import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import "./Auth.css";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate     = useNavigate();

  const [form, setForm] = useState({
    email: "", username: "", password: "", full_name: "",
  });
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw]   = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const pwStrength = (() => {
    const p = form.password;
    if (!p) return 0;
    let s = 0;
    if (p.length >= 8)  s++;
    if (/[A-Z]/.test(p)) s++;
    if (/[0-9]/.test(p)) s++;
    if (/[^A-Za-z0-9]/.test(p)) s++;
    return s;
  })();

  const strengthLabel = ["", "Weak", "Fair", "Good", "Strong"][pwStrength];
  const strengthColor = ["", "#ef4444", "#f59e0b", "#3b82f6", "#10b981"][pwStrength];

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.email || !form.username || !form.password) {
      setError("Email, username and password are required.");
      return;
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await register(form);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const d = err?.response?.data?.detail;
      setError(typeof d === "string" ? d : "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      {/* Left branding */}
      <div className="auth-branding">
        <div className="auth-branding-inner">
          <div className="auth-logo">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <rect width="36" height="36" rx="10" fill="url(#g2)"/>
              <path d="M10 22l8-12 8 12" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M14 22l4-6 4 6" stroke="rgba(255,255,255,0.5)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <defs>
                <linearGradient id="g2" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#8b5cf6"/>
                  <stop offset="1" stopColor="#3b82f6"/>
                </linearGradient>
              </defs>
            </svg>
            <span className="auth-logo-text">DemandIQ</span>
          </div>

          <div className="auth-branding-body">
            <h1 className="auth-branding-title">
              Start your<br />
              <span className="auth-gradient-text auth-gradient-purple">intelligence journey.</span>
            </h1>
            <p className="auth-branding-sub">
              Create your account and gain access to demand forecasting, 
              inventory intelligence, and AI-driven decision support.
            </p>
          </div>

          <div className="auth-steps">
            {["Create your account", "Connect your sales data", "Get AI-powered insights"].map((s, i) => (
              <div key={s} className="auth-step">
                <div className="auth-step-num">{i + 1}</div>
                <span>{s}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="auth-blob auth-blob-1 auth-blob-purple" />
        <div className="auth-blob auth-blob-2" />
      </div>

      {/* Right form */}
      <div className="auth-form-panel">
        <div className="auth-form-card">
          <div className="auth-form-header">
            <h2 className="auth-form-title">Create account</h2>
            <p className="auth-form-sub">Join DemandIQ — it's free to start</p>
          </div>

          {error && (
            <div className="auth-error">
              <span className="auth-error-icon">⚠</span>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            <div className="auth-field-row">
              <div className="auth-field">
                <label htmlFor="reg-fullname" className="auth-label">Full Name</label>
                <div className="auth-input-wrap">
                  <span className="auth-input-icon">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  </span>
                  <input id="reg-fullname" type="text" className="auth-input" placeholder="Yash Gawande"
                    value={form.full_name} onChange={set("full_name")} autoFocus />
                </div>
              </div>
              <div className="auth-field">
                <label htmlFor="reg-username" className="auth-label">Username</label>
                <div className="auth-input-wrap">
                  <span className="auth-input-icon">@</span>
                  <input id="reg-username" type="text" className="auth-input" placeholder="yash_gawande"
                    value={form.username} onChange={set("username")} autoComplete="username" />
                </div>
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="reg-email" className="auth-label">Email Address</label>
              <div className="auth-input-wrap">
                <span className="auth-input-icon">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                </span>
                <input id="reg-email" type="email" className="auth-input" placeholder="you@example.com"
                  value={form.email} onChange={set("email")} autoComplete="email" />
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="reg-password" className="auth-label">Password</label>
              <div className="auth-input-wrap">
                <span className="auth-input-icon">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </span>
                <input id="reg-password" type={showPw ? "text" : "password"} className="auth-input auth-input-pw"
                  placeholder="Min 8 characters" value={form.password} onChange={set("password")}
                  autoComplete="new-password" />
                <button type="button" className="auth-pw-toggle" onClick={() => setShowPw(v => !v)} tabIndex={-1}>
                  {showPw
                    ? <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                    : <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  }
                </button>
              </div>
              {/* Strength bar */}
              {form.password && (
                <div className="auth-pw-strength">
                  <div className="auth-pw-bar">
                    {[1,2,3,4].map(i => (
                      <div key={i} className="auth-pw-segment"
                        style={{ background: i <= pwStrength ? strengthColor : "#1e293b" }} />
                    ))}
                  </div>
                  <span style={{ color: strengthColor, fontSize: "0.73rem" }}>{strengthLabel}</span>
                </div>
              )}
            </div>

            <button id="register-submit" type="submit" className="auth-btn auth-btn-primary auth-btn-purple" disabled={loading}>
              {loading ? <><span className="auth-spinner" /> Creating account…</> : "Create Account →"}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account?{" "}
            <Link to="/login" className="auth-link">Sign in →</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
