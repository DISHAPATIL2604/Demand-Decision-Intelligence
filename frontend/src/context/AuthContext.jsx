import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { loginUser, registerUser, getMe } from "../services/authService";

const AuthContext = createContext(null);

const TOKEN_KEY = "ddi_access_token";

export function AuthProvider({ children }) {
  const [token, setToken]   = useState(() => localStorage.getItem(TOKEN_KEY) || null);
  const [user, setUser]     = useState(null);
  const [loading, setLoading] = useState(!!localStorage.getItem(TOKEN_KEY)); // hydrating

  /* ── Hydrate user from stored token on first mount ── */
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) { setLoading(false); return; }
    getMe(stored)
      .then(u => { setUser(u); setToken(stored); })
      .catch(() => { localStorage.removeItem(TOKEN_KEY); setToken(null); })
      .finally(() => setLoading(false));
  }, []);

  /* ── Login ── */
  const login = useCallback(async (username, password) => {
    const data = await loginUser(username, password);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    setToken(data.access_token);
    const profile = await getMe(data.access_token);
    setUser(profile);
    return profile;
  }, []);

  /* ── Register → auto-login ── */
  const register = useCallback(async (payload) => {
    await registerUser(payload);
    return login(payload.email, payload.password);
  }, [login]);

  /* ── Logout ── */
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = { token, user, loading, login, register, logout, isAuth: !!token };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
