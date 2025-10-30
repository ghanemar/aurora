/**
 * User and Authentication Types
 */

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  role: 'admin' | 'partner';
  is_active: boolean;
  partner_id: string | null;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
}

/**
 * API Response Types
 */

export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
}

/**
 * Auth Context Types
 */

export interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}
