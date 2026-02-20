import axios from 'axios';

// API base URL - use environment variable if set, otherwise default to relative path for production
// In development, Vite proxy will forward /api requests to localhost:8000
// In production, API and frontend are served from the same domain
// Using /api/v1 for versioned endpoints with backward compatibility via redirect middleware
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

// In-memory token store — access tokens are NEVER persisted to localStorage
// to reduce XSS token-theft risk.  On page reload the token is obtained via
// the httpOnly refresh-token cookie (/auth/refresh).
let _accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  _accessToken = token;
}

export function getAccessToken(): string | null {
  return _accessToken;
}

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth header from in-memory store
api.interceptors.request.use(
  (config) => {
    if (_accessToken) {
      config.headers.Authorization = `Bearer ${_accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Extract a human-readable error message from an API error response.
 * Handles both structured format: { error: { message: "..." } }
 * and FastAPI format: { detail: "..." }
 */
export function getErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const resp = (error as { response?: { data?: unknown } }).response;
    const data = resp?.data;
    if (data && typeof data === 'object') {
      // Structured error format: { error: { message: "..." } }
      if ('error' in data) {
        const errObj = (data as { error: { message?: string } }).error;
        if (errObj?.message) return errObj.message;
      }
      // FastAPI HTTPException format: { detail: "..." }
      if ('detail' in data) {
        const detail = (data as { detail: unknown }).detail;
        if (typeof detail === 'string') return detail;
      }
    }
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred. Please try again.';
}

// Shared refresh promise to prevent concurrent refresh race conditions
let refreshPromise: Promise<string> | null = null;

// Response interceptor - handle 401 and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Reuse in-flight refresh or start a new one
        if (!refreshPromise) {
          refreshPromise = (async () => {
            const { authApi } = await import('./auth');
            const response = await authApi.refresh();
            const newToken = response.data.access_token;
            setAccessToken(newToken);
            return newToken;
          })().finally(() => {
            refreshPromise = null;
          });
        }

        const newToken = await refreshPromise;

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api.request(originalRequest);
      } catch (refreshError) {
        // Refresh failed - logout user
        setAccessToken(null);
        window.dispatchEvent(new CustomEvent('auth:session-expired'));
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export const userTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
