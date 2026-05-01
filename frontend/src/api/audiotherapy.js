// src/api/audiotherapy.js
// ============================================================================
// Single endpoint: the audio track is fully driven by Agent 3's output.
// No manual override, no disorder picker.
// ============================================================================
const API_BASE = import.meta.env.VITE_API_BASE || '';

function authHeaders() {
  // Adjust this to match the auth pattern your other working API files use.
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function jsonOrThrow(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Fetch the audio recommendation derived from the user's latest completed
 * AI pipeline run (Agent 3's final_output → Disorder mapping).
 */
export async function getPersonalisedRecommendation() {
  const res = await fetch(`${API_BASE}/api/audio/recommendation/`, {
    headers: { ...authHeaders() },
  });
  return jsonOrThrow(res);
}