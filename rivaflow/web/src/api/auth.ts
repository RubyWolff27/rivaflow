import axios from 'axios';
import { getAccessToken } from './_client';

// API base URL - use environment variable if set, otherwise default to versioned path
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

// Create a separate axios instance for auth (no interceptors to avoid circular dependencies)
const authClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  invite_token?: string;
  default_gym?: string;
  current_grade?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
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

  refresh: () =>
    authClient.post<RefreshTokenResponse>('/auth/refresh'),

  logout: () =>
    authClient.post('/auth/logout', null, {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    }),

  getCurrentUser: () =>
    authClient.get('/auth/me', {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    }),

  forgotPassword: (email: string) =>
    authClient.post('/auth/forgot-password', { email }),

  resetPassword: (token: string, newPassword: string) =>
    authClient.post('/auth/reset-password', { token, new_password: newPassword }),
};
