import axios from "axios";

// ── API Base URL Resolution (Strictly use 8000, never 8001) ─────────────────
let rawBase = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
if (rawBase.includes(":8001")) {
  rawBase = rawBase.replace(":8001", ":8000");
}
const API_BASE_URL = rawBase;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Attach JWT token from AuthContext's TOKEN_KEY (ddi_access_token)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ddi_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for clean error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      return Promise.reject(
        new Error("Unable to connect to the analytics service. Please make sure the backend is running at http://127.0.0.1:8000.")
      );
    }
    if (error.response.status === 401) {
      return Promise.reject(
        new Error("Your session has expired. Please log in again.")
      );
    }
    const msg = error.response.data?.detail || error.message || "An unexpected error occurred.";
    return Promise.reject(new Error(msg));
  }
);

export { API_BASE_URL };

function getAuthHeaders() {
  const token = localStorage.getItem("ddi_access_token");
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// ── Upload Services ──────────────────────────────────────────────────────────
export async function uploadSalesFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const token = localStorage.getItem("ddi_access_token");
  const headers = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/upload/sales`, {
      method: "POST",
      headers,
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Sales upload failed");
    }
    return data;
  } catch (err) {
    if (err.message?.includes("Failed to fetch") || !err.response) {
      throw new Error("Unable to connect to the upload service. Please verify backend is running.");
    }
    throw err;
  }
}

export async function getUploads() {
  const response = await fetch(`${API_BASE_URL}/upload/uploads`, {
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch uploads");
  }
  return data;
}

export async function getUpload(uploadId) {
  const response = await fetch(`${API_BASE_URL}/upload/uploads/${uploadId}`, {
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch upload");
  }
  return data;
}

export async function getValidationResults(uploadId) {
  const response = await fetch(`${API_BASE_URL}/upload/validation/${uploadId}`, {
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch validation results");
  }
  return data;
}

// ── Demand Intelligence Services ─────────────────────────────────────────────
export async function getDemandSummary() {
  const response = await fetch(`${API_BASE_URL}/demand/summary`, {
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch demand summary");
  }
  return data;
}

export async function getDemandInventoryRecs(params = {}) {
  const query = new URLSearchParams();
  if (params.limit) query.append("limit", params.limit);
  if (params.city) query.append("city", params.city);
  if (params.lead_time_days) query.append("lead_time_days", params.lead_time_days);
  if (params.service_level) query.append("service_level", params.service_level);

  const url = `${API_BASE_URL}/demand/inventory-recommendations${query.toString() ? `?${query.toString()}` : ""}`;
  const response = await fetch(url, { headers: getAuthHeaders() });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch inventory recommendations");
  }
  return data;
}

export async function getForecastMetrics() {
  const response = await fetch(`${API_BASE_URL}/demand/forecast-metrics`, {
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch forecast metrics");
  }
  return data;
}

// ── Forecasting Suite Services ───────────────────────────────────────────────
export async function getForecastResults(params = {}) {
  const query = new URLSearchParams();
  if (params.limit) query.append("limit", params.limit);
  if (params.product_id) query.append("product_id", params.product_id);
  if (params.city_name) query.append("city_name", params.city_name);

  const url = `${API_BASE_URL}/forecast/results${query.toString() ? `?${query.toString()}` : ""}`;
  const response = await fetch(url, { headers: getAuthHeaders() });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch forecast results");
  }
  return data;
}

export async function getForecastEvaluation() {
  const response = await fetch(`${API_BASE_URL}/forecast/evaluation`, {
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch forecast evaluation");
  }
  return data;
}

// ── Inventory Optimization Services ──────────────────────────────────────────
export async function getInventoryRecommendations(params = {}) {
  const query = new URLSearchParams();
  if (params.limit) query.append("limit", params.limit);
  if (params.product_id) query.append("product_id", params.product_id);
  if (params.city_name) query.append("city_name", params.city_name);

  const url = `${API_BASE_URL}/inventory/recommendations${query.toString() ? `?${query.toString()}` : ""}`;
  const response = await fetch(url, { headers: getAuthHeaders() });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch inventory recommendations");
  }
  return data;
}

export async function getInventoryMetadata() {
  const response = await fetch(`${API_BASE_URL}/inventory/metadata`, {
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch inventory metadata");
  }
  return data;
}

// ── Analytics & Anomalies Services ───────────────────────────────────────────
export async function getEdaSummary() {
  const response = await fetch(`${API_BASE_URL}/analytics/eda-summary`, {
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch EDA summary");
  }
  return data;
}

export async function getAnomalies(params = {}) {
  const query = new URLSearchParams();
  if (params.limit) query.append("limit", params.limit);
  if (params.severity) query.append("severity", params.severity);
  if (params.city_name) query.append("city_name", params.city_name);
  if (params.product_id) query.append("product_id", params.product_id);
  if (params.anomaly_type) query.append("anomaly_type", params.anomaly_type);

  const url = `${API_BASE_URL}/analytics/anomalies${query.toString() ? `?${query.toString()}` : ""}`;
  const response = await fetch(url, { headers: getAuthHeaders() });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch anomalies");
  }
  return data;
}

export async function getAnomalySummary() {
  const response = await fetch(`${API_BASE_URL}/analytics/summary`, {
    headers: getAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch anomaly summary");
  }
  return data;
}

// ── AI Assistant Services ────────────────────────────────────────────────────
export async function getChatSuggestions() {
  const token = localStorage.getItem("ddi_access_token");
  try {
    const response = await fetch(`${API_BASE_URL}/chat/suggestions`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
      },
    });
    if (response.status === 401) {
      throw new Error("Your session has expired. Please log in again.");
    }
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Failed to fetch suggestions");
    return data;
  } catch (err) {
    if (err.message?.includes("Failed to fetch") || err.name === "TypeError") {
      throw new Error("Unable to connect to the analytics service. Please make sure the backend is running at http://127.0.0.1:8000.");
    }
    throw err;
  }
}

export async function sendChatMessage(message, history = []) {
  const token = localStorage.getItem("ddi_access_token");
  try {
    const response = await fetch(`${API_BASE_URL}/chat/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, history }),
    });

    if (response.status === 401) {
      throw new Error("Your session has expired. Please log in again.");
    }

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "I don't have enough data to answer that yet.");
    }
    return data;
  } catch (err) {
    if (err.message?.includes("Failed to fetch") || err.name === "TypeError") {
      throw new Error("Unable to connect to the analytics service. Please make sure the backend is running at http://127.0.0.1:8000.");
    }
    throw err;
  }
}

// ── Attach All Named Functions to Default `api` Object ──────────────────────
// This guarantees that whether callers do:
//   import { sendChatMessage } from './api'
// OR
//   import api from './api'; api.sendChatMessage()
// both work without any runtime mismatch!
api.uploadSalesFile = uploadSalesFile;
api.getUploads = getUploads;
api.getUpload = getUpload;
api.getValidationResults = getValidationResults;
api.getDemandSummary = getDemandSummary;
api.getDemandInventoryRecs = getDemandInventoryRecs;
api.getForecastMetrics = getForecastMetrics;
api.getForecastResults = getForecastResults;
api.getForecastEvaluation = getForecastEvaluation;
api.getInventoryRecommendations = getInventoryRecommendations;
api.getInventoryMetadata = getInventoryMetadata;
api.getEdaSummary = getEdaSummary;
api.getAnomalies = getAnomalies;
api.getAnomalySummary = getAnomalySummary;
api.getChatSuggestions = getChatSuggestions;
api.sendChatMessage = sendChatMessage;

export default api;