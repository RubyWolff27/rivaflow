import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import type { AuthUser } from '../types';
import { authApi } from '../api/auth';
import { getErrorMessage, setAccessToken } from '../api/client';
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

  // On mount, try to obtain a fresh access token via the httpOnly refresh
  // cookie.  This replaces the old localStorage-based token persistence and
  // keeps the access token in memory only.
  useEffect(() => {
    let cancelled = false;
    const bootstrap = async () => {
      try {
        // The refresh endpoint uses the httpOnly cookie automatically
        const refreshRes = await authApi.refresh();
        if (cancelled) return;
        const newToken = refreshRes.data.access_token;
        setAccessToken(newToken);

        // Fetch current user with the fresh token
        const userRes = await authApi.getCurrentUser();
        if (!cancelled) {
          setUser(userRes.data);
        }
      } catch (err) {
        if (!cancelled) {
          logger.debug('No valid refresh cookie — user is not logged in', err);
          setAccessToken(null);
        }
      }
      if (!cancelled) setIsLoading(false);
    };

    bootstrap();
    return () => { cancelled = true; };
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authApi.login({ email, password });
      setAccessToken(response.data.access_token);
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
      setAccessToken(response.data.access_token);
      setUser(response.data.user);
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error));
    }
  };

  const logout = useCallback(() => {
    // Call logout API (fire and forget) — cookie sent automatically
    authApi.logout().catch(err => {
      logger.debug('Logout API call failed (fire-and-forget)', err);
    });

    setAccessToken(null);
    setUser(null);
  }, []);

  // Listen for session-expired events dispatched by the API client
  useEffect(() => {
    const handleSessionExpired = () => {
      logout();
    };
    window.addEventListener('auth:session-expired', handleSessionExpired);
    return () => {
      window.removeEventListener('auth:session-expired', handleSessionExpired);
    };
  }, [logout]);

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
