/**
 * Auth API service — wraps all /api/auth/* calls.
 * NOTE: baseURL is already "http://localhost:8000/api" so paths start with /auth/
 */
import api from "./api";

/**
 * Register a new user account.
 * @param {Object} data  { email, username, password, full_name? }
 */
export async function registerUser(data) {
  const res = await api.post("/auth/register", data);
  return res.data;
}

/**
 * Login with email/username + password.
 * @param {string} username  email or username
 * @param {string} password
 * @returns {{ access_token: string, token_type: string }}
 */
export async function loginUser(username, password) {
  const res = await api.post("/auth/login", { username, password });
  return res.data;
}

/**
 * Fetch the profile of the currently authenticated user.
 * @param {string} token  Bearer JWT
 */
export async function getMe(token) {
  const res = await api.get("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

