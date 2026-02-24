/**
 * Authentication Context
 *
 * Provides auth state (user, tokens) to the entire app.
 * On mount, attempts silent refresh to restore session.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi, clearAccessToken, type AuthUser, type TokenResponse } from '@/lib/auth';

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (...roles: string[]) => boolean;
  updateUser: (user: AuthUser) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Try to restore session on mount via refresh token cookie
  useEffect(() => {
    const tryRestore = async () => {
      try {
        const result = await authApi.refresh();
        if (result) {
          setUser(result.user);
        }
      } catch {
        // No valid session — user needs to log in
      } finally {
        setIsLoading(false);
      }
    };

    tryRestore();
  }, []);

  // Listen for auth:expired events from the API client
  useEffect(() => {
    const handler = () => {
      setUser(null);
      clearAccessToken();
    };

    window.addEventListener('auth:expired', handler);
    return () => window.removeEventListener('auth:expired', handler);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const result: TokenResponse = await authApi.login(username, password);
    setUser(result.user);
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  const hasRole = useCallback((...roles: string[]) => {
    if (!user) return false;
    return roles.includes(user.role);
  }, [user]);

  const updateUser = useCallback((updatedUser: AuthUser) => {
    setUser(updatedUser);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        hasRole,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
