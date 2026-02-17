import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { AuthUser } from '../types';
import { authApi } from '../api/auth';
import { getErrorMessage } from '../api/client';
import { logger } from '../utils/logger';

interface AuthContextType {
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName: string, lastName: string, inviteToken?: string, defaultGym?: string, currentGrade?: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from localStorage on mount
  useEffect(() => {
    let cancelled = false;
    const loadUser = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const response = await authApi.getCurrentUser();
          if (!cancelled) {
            setUser(response.data);
            localStorage.setItem('user', JSON.stringify(response.data));
          }
        } catch (error) {
          if (!cancelled) {
            logger.error('Failed to load user:', error);
            // Clear invalid tokens
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
          }
        }
      }
      if (!cancelled) setIsLoading(false);
    };

    loadUser();
    return () => { cancelled = true; };
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authApi.login({ email, password });
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      setUser(response.data.user);
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error));
    }
  };

  const register = async (
    email: string,
    password: string,
    firstName: string,
    lastName: string,
    inviteToken?: string,
    defaultGym?: string,
    currentGrade?: string,
  ) => {
    try {
      const response = await authApi.register({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        ...(inviteToken ? { invite_token: inviteToken } : {}),
        ...(defaultGym ? { default_gym: defaultGym } : {}),
        ...(currentGrade ? { current_grade: currentGrade } : {}),
      });
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      setUser(response.data.user);
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error));
    }
  };

  // Listen for session-expired events dispatched by the API client
  useEffect(() => {
    const handleSessionExpired = () => {
      logout();
    };
    window.addEventListener('auth:session-expired', handleSessionExpired);
    return () => {
      window.removeEventListener('auth:session-expired', handleSessionExpired);
    };
  });

  const logout = () => {
    // Call logout API (fire and forget) — cookie sent automatically
    authApi.logout().catch(() => {
      // Ignore errors - we're logging out anyway
    });

    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
