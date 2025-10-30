import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { authApi, isTokenExpired } from '../services/api';
import type { User, AuthContextType } from '../types';

/**
 * Authentication Context
 *
 * Provides:
 * - User state and authentication status
 * - Login/logout functions
 * - Token persistence with localStorage
 * - Automatic token expiration handling
 */

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  /**
   * Initialize auth state from localStorage on mount
   */
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('auth_token');
      const storedUser = localStorage.getItem('user');

      if (storedToken && storedUser && !isTokenExpired()) {
        try {
          // Validate token by fetching current user
          const currentUser = await authApi.getCurrentUser();
          setToken(storedToken);
          setUser(currentUser);
          localStorage.setItem('user', JSON.stringify(currentUser)); // Update user data
        } catch (error) {
          console.error('Token validation failed:', error);
          // Clear invalid token
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
        }
      } else {
        // Clear expired token
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
      }

      setLoading(false);
    };

    initAuth();
  }, []);

  /**
   * Login function
   */
  const login = async (username: string, password: string): Promise<void> => {
    try {
      // Get token from API
      const authResponse = await authApi.login({ username, password });
      const { access_token } = authResponse;

      // Store token
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);

      // Fetch user profile
      const currentUser = await authApi.getCurrentUser();
      localStorage.setItem('user', JSON.stringify(currentUser));
      setUser(currentUser);
    } catch (error) {
      // Clear any partial state
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      setToken(null);
      setUser(null);
      throw error;
    }
  };

  /**
   * Logout function
   */
  const logout = (): void => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  /**
   * Check token expiration periodically (every 5 minutes)
   */
  useEffect(() => {
    if (!token) return;

    const checkTokenExpiration = () => {
      if (isTokenExpired()) {
        console.log('Token expired - logging out');
        logout();
      }
    };

    // Check immediately
    checkTokenExpiration();

    // Check every 5 minutes
    const interval = setInterval(checkTokenExpiration, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [token]);

  const value: AuthContextType = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated: !!token && !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * useAuth hook for accessing auth context
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
