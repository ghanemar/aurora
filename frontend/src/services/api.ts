import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import type { AuthResponse, User, LoginRequest, ApiError } from '../types';

/**
 * API Service Configuration
 *
 * Axios instance configured with:
 * - Base URL from environment
 * - Request interceptor for JWT token
 * - Response interceptor for 401 handling
 */

// Use relative URL for Docker/production (Nginx proxy) or full URL for development
// In Docker, Nginx proxies /api and /health to the backend
// In development, use the full backend URL
const API_URL = import.meta.env.VITE_API_URL || '';

// Create axios instance
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add JWT token to requests
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear storage and redirect to login
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Authentication API
 */

export const authApi = {
  /**
   * Login with username and password
   */
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    // API expects form data for OAuth2 password flow
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await api.post<AuthResponse>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  /**
   * Get current user profile
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/api/v1/auth/me');
    return response.data;
  },

  /**
   * Health check endpoint
   */
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

/**
 * Utility function to check if token is expired
 */
export const isTokenExpired = (): boolean => {
  const token = localStorage.getItem('auth_token');
  if (!token) return true;

  try {
    // JWT structure: header.payload.signature
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expirationTime = payload.exp * 1000; // Convert to milliseconds
    return Date.now() >= expirationTime;
  } catch (error) {
    console.error('Error parsing token:', error);
    return true;
  }
};
