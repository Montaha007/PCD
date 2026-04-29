// src/api/audiotherapy.js
const API_BASE = import.meta.env.VITE_API_BASE;

function getAuthHeaders() {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchRecommendation(disorder = 'normal') {
  const res = await fetch(
    `${API_BASE}/api/audio/recommendations/?disorder=${disorder}`,
    { headers: getAuthHeaders() }
  );
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Failed (${res.status})`);
  }
  return res.json();
}

export async function fetchDisorders() {
  const res = await fetch(`${API_BASE}/api/audio/disorders/`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(`Failed (${res.status})`);
  return res.json();
}