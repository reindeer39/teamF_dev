const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000/api';

const TOKEN_STORAGE_KEY = 'teamf.authToken';

export function getStoredToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeToken(token) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

function errorMessage(data, status) {
  if (data.error) return data.error;
  if (data.errors) {
    return Object.values(data.errors).flat().join(' ');
  }
  return `API request failed (${status})`;
}

export async function request(path, options = {}) {
  const token = getStoredToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Token ${token}` } : {}),
      ...options.headers,
    },
  });
  const data = response.status === 204
    ? null
    : await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(errorMessage(data || {}, response.status));
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}
