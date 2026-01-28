import axios from 'axios';

// API base URL - use environment variable if set, otherwise default to relative path
const API_BASE = import.meta.env.VITE_API_URL || '/api';

// Create a separate axios instance for auth (no interceptors to avoid circular dependencies)
const authClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  };
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}

export const authApi = {
  register: (data: RegisterRequest) =>
    authClient.post<TokenResponse>('/auth/register', data),

  login: (data: LoginRequest) =>
    authClient.post<TokenResponse>('/auth/login', data),

  refresh: (refreshToken: string) =>
    authClient.post<RefreshTokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    }),

  logout: (data: { refresh_token: string }) =>
    authClient.post('/auth/logout', data, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
    }),

  getCurrentUser: () =>
    authClient.get('/auth/me', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
    }),
};
