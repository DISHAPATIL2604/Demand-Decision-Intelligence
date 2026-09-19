import React, { useState } from "react";
import { registerUser, loginUser, getMe } from "../../services/authService";
import "./AuthTestPage.css";

/* ─── Status badge helper ─────────────────────────────────── */
function StatusBadge({ status }) {
  if (!status) return null;
  const isOk = status === "success";
  return (
    <span className={`atb-badge ${isOk ? "atb-badge--ok" : "atb-badge--err"}`}>
      {isOk ? "✓ Success" : "✗ Error"}
    </span>
  );
}

/* ─── JSON response display ───────────────────────────────── */
function ResponseBox({ label, data, status, loading }) {
  return (
    <div className="atb-response">
      <div className="atb-response-header">
        <span className="atb-response-label">{label}</span>
        <StatusBadge status={status} />
      </div>
      <pre className="atb-response-body">
        {loading
          ? "⏳ Sending request..."
          : data
          ? JSON.stringify(data, null, 2)
          : <span className="atb-response-empty">Response will appear here…</span>}
      </pre>
    </div>
  );
}

/* ─── Input helper ────────────────────────────────────────── */
function Field({ label, id, type = "text", placeholder, value, onChange }) {
  return (
    <div className="atb-field">
      <label htmlFor={id} className="atb-label">{label}</label>
      <input
        id={id}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className="atb-input"
        autoComplete="off"
      />
    </div>
  );
}

/* ─── Section card wrapper ────────────────────────────────── */
function Panel({ icon, title, endpoint, method, children }) {
  return (
    <div className="atb-panel">
      <div className="atb-panel-header">
        <span className="atb-panel-icon">{icon}</span>
        <div>
          <h3 className="atb-panel-title">{title}</h3>
          <code className="atb-panel-endpoint">
            <span className={`atb-method atb-method--${method.toLowerCase()}`}>{method}</span>
            {endpoint}
          </code>
        </div>
      </div>
      {children}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════ */
export default function AuthTestPage() {
  /* ── Shared state ─────────────────────────────────────── */
  const [storedToken, setStoredToken] = useState("");

  /* ── Register state ───────────────────────────────────── */
  const [reg, setReg] = useState({
    email: "", username: "", password: "", full_name: "",
  });
  const [regRes, setRegRes]     = useState(null);
  const [regStatus, setRegStatus]   = useState(null);
  const [regLoading, setRegLoading] = useState(false);

  /* ── Login state ──────────────────────────────────────── */
  const [login, setLogin] = useState({ username: "", password: "" });
  const [loginRes, setLoginRes]     = useState(null);
  const [loginStatus, setLoginStatus]   = useState(null);
  const [loginLoading, setLoginLoading] = useState(false);

  /* ── Profile state ────────────────────────────────────── */
  const [meRes, setMeRes]     = useState(null);
  const [meStatus, setMeStatus]   = useState(null);
  const [meLoading, setMeLoading] = useState(false);

  /* ── Handlers ─────────────────────────────────────────── */
  async function handleRegister(e) {
    e.preventDefault();
    setRegLoading(true); setRegStatus(null); setRegRes(null);
    try {
      const data = await registerUser(reg);
      setRegRes(data); setRegStatus("success");
    } catch (err) {
      setRegRes(err?.response?.data ?? { error: err.message });
      setRegStatus("error");
    } finally { setRegLoading(false); }
  }

  async function handleLogin(e) {
    e.preventDefault();
    setLoginLoading(true); setLoginStatus(null); setLoginRes(null);
    try {
      const data = await loginUser(login.username, login.password);
      setLoginRes(data); setLoginStatus("success");
      if (data?.access_token) setStoredToken(data.access_token);
    } catch (err) {
      setLoginRes(err?.response?.data ?? { error: err.message });
      setLoginStatus("error");
    } finally { setLoginLoading(false); }
  }

  async function handleGetMe() {
    setMeLoading(true); setMeStatus(null); setMeRes(null);
    try {
      const data = await getMe(storedToken);
      setMeRes(data); setMeStatus("success");
    } catch (err) {
      setMeRes(err?.response?.data ?? { error: err.message });
      setMeStatus("error");
    } finally { setMeLoading(false); }
  }

  /* ── Render ───────────────────────────────────────────── */
  return (
    <div className="atb-root">
      {/* ── Page header ────────────────────────── */}
      <div className="atb-hero">
        <div className="atb-hero-icon">🔐</div>
        <div>
          <h1 className="atb-hero-title">Auth &amp; User Management</h1>
          <p className="atb-hero-sub">
            Phase 2 · Live endpoint tester — register, login, and inspect the
            protected <code>/me</code> profile.
          </p>
        </div>
        <div className="atb-phase-badge">Phase 2</div>
      </div>

      {/* ── Checklist ──────────────────────────── */}
      <div className="atb-checklist">
        {[
          { done: true,  text: "verify_password() + get_password_hash() (bcrypt)" },
          { done: true,  text: "create_access_token() with JWT (HS256)" },
          { done: true,  text: "POST /api/auth/register" },
          { done: true,  text: "POST /api/auth/login" },
          { done: true,  text: "GET  /api/auth/me (protected)" },
          { done: true,  text: "get_current_user dependency (Bearer → DB lookup)" },
          { done: true,  text: "DB session wired via get_db() dependency" },
        ].map(({ done, text }) => (
          <div key={text} className="atb-check-item">
            <span className={`atb-check-dot ${done ? "atb-check-dot--done" : ""}`}>
              {done ? "✓" : "○"}
            </span>
            <span>{text}</span>
          </div>
        ))}
      </div>

      {/* ── Token banner ───────────────────────── */}
      {storedToken && (
        <div className="atb-token-banner">
          <span className="atb-token-label">🎟 Active JWT</span>
          <code className="atb-token-value">{storedToken.slice(0, 60)}…</code>
          <button
            className="atb-token-clear"
            onClick={() => { setStoredToken(""); setMeRes(null); setMeStatus(null); }}
          >
            Clear
          </button>
        </div>
      )}

      <div className="atb-grid">

        {/* ══ REGISTER ══════════════════════════ */}
        <Panel icon="👤" title="Register" endpoint="/api/auth/register" method="POST">
          <form onSubmit={handleRegister} className="atb-form">
            <Field
              label="Email" id="reg-email" type="email"
              placeholder="user@example.com"
              value={reg.email}
              onChange={e => setReg({ ...reg, email: e.target.value })}
            />
            <Field
              label="Username" id="reg-username"
              placeholder="john_doe"
              value={reg.username}
              onChange={e => setReg({ ...reg, username: e.target.value })}
            />
            <Field
              label="Password" id="reg-password" type="password"
              placeholder="Min 8 characters"
              value={reg.password}
              onChange={e => setReg({ ...reg, password: e.target.value })}
            />
            <Field
              label="Full Name (optional)" id="reg-fullname"
              placeholder="John Doe"
              value={reg.full_name}
              onChange={e => setReg({ ...reg, full_name: e.target.value })}
            />
            <button
              type="submit"
              className="atb-btn atb-btn--register"
              disabled={regLoading}
            >
              {regLoading ? "Registering…" : "Register User"}
            </button>
          </form>
          <ResponseBox
            label="Server Response"
            data={regRes}
            status={regStatus}
            loading={regLoading}
          />
        </Panel>

        {/* ══ LOGIN ═════════════════════════════ */}
        <Panel icon="🔑" title="Login" endpoint="/api/auth/login" method="POST">
          <form onSubmit={handleLogin} className="atb-form">
            <Field
              label="Email or Username" id="login-user"
              placeholder="admin@demandintelligence.com"
              value={login.username}
              onChange={e => setLogin({ ...login, username: e.target.value })}
            />
            <Field
              label="Password" id="login-pass" type="password"
              placeholder="••••••••"
              value={login.password}
              onChange={e => setLogin({ ...login, password: e.target.value })}
            />

            {/* Quick-fill demo credentials */}
            <div className="atb-demo-creds">
              <span className="atb-demo-label">Quick fill:</span>
              <button
                type="button"
                className="atb-demo-chip"
                onClick={() => setLogin({ username: "admin@demandintelligence.com", password: "Admin@123" })}
              >
                admin
              </button>
            </div>

            <button
              type="submit"
              className="atb-btn atb-btn--login"
              disabled={loginLoading}
            >
              {loginLoading ? "Authenticating…" : "Login & Get Token"}
            </button>
          </form>
          <ResponseBox
            label="Server Response"
            data={loginRes}
            status={loginStatus}
            loading={loginLoading}
          />
        </Panel>

        {/* ══ GET /ME ═══════════════════════════ */}
        <Panel icon="🛡" title="Get Profile" endpoint="/api/auth/me" method="GET">
          <div className="atb-form">
            <div className="atb-field">
              <label htmlFor="me-token" className="atb-label">
                Bearer Token
                {storedToken && (
                  <span className="atb-auto-tag">auto-filled from login</span>
                )}
              </label>
              <textarea
                id="me-token"
                className="atb-input atb-textarea"
                placeholder="Paste your JWT here, or login above to auto-fill"
                value={storedToken}
                onChange={e => setStoredToken(e.target.value)}
                rows={4}
              />
            </div>
            <button
              type="button"
              className="atb-btn atb-btn--me"
              onClick={handleGetMe}
              disabled={meLoading || !storedToken}
            >
              {meLoading ? "Fetching…" : "Get My Profile"}
            </button>
          </div>
          <ResponseBox
            label="Protected Resource"
            data={meRes}
            status={meStatus}
            loading={meLoading}
          />
        </Panel>

      </div>

      {/* ── Swagger link ───────────────────────── */}
      <div className="atb-footer">
        <a
          href="http://localhost:8000/api/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="atb-docs-link"
        >
          📖 Open interactive /api/docs (Swagger UI) →
        </a>
      </div>
    </div>
  );
}
