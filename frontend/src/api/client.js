const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  let data;
  try {
    data = await response.json();
  } catch (err) {
    data = { detail: 'An unexpected response was received from the server' };
  }

  if (!response.ok) {
    const errorMsg = data?.detail || data?.message || 'Request failed';
    throw new Error(errorMsg);
  }

  return data;
}
