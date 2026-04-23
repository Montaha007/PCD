// src/api/lifestyle.js
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * Normalized error wrapper so components can handle {status, data} uniformly.
 */
class ApiError extends Error {
  constructor(status, data) {
    super(`API error ${status}`);
    this.status = status;
    this.data = data;
  }
}

function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * POST a new lifestyle log.
 * @param {Object} payload - 6 raw features + date
 * @returns {Promise<Object>} saved log with {id, ...}
 */
export async function submitLifestyleLog(payload) {
  const res = await fetch(`${API_BASE}/lifestyle/logs/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

/**
 * GET prediction for an existing lifestyle log.
 * @param {number} logId
 * @returns {Promise<{predicted_sleep_hours: number, quality_label: string, feature_snapshot: object}>}
 */
export async function getLifestylePrediction(logId) {
  const res = await fetch(`${API_BASE}/lifestyle/logs/${logId}/predict/`, {
    method: "GET",
    headers: getAuthHeaders(),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

/**
 * GET list of user's lifestyle logs.
 */
export async function listLifestyleLogs() {
  const res = await fetch(`${API_BASE}/lifestyle/logs/`, {
    method: "GET",
    headers: getAuthHeaders(),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}