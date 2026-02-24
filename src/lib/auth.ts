/**
 * Authentication Types & API Client
 *
 * Handles token storage, login/logout API calls, and token refresh logic.
 * Access tokens are stored in memory (not localStorage) for security.
 * Refresh tokens are handled via httpOnly cookies by the backend.
 */

export interface AuthUser {
  id: number;
  username: string;
  email: string | null;
  role: 'admin' | 'trader' | 'viewer';
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

// ────────────── In-Memory Token Store ──────────────

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function clearAccessToken(): void {
  accessToken = null;
}

/**
 * Check if a JWT is expired (with 30s buffer).
 */
export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expiry = payload.exp * 1000; // Convert to ms
    return Date.now() > expiry - 30_000; // 30s buffer
  } catch {
    return true;
  }
}

// ────────────── Auth API Calls ──────────────

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const authApi = {
  /**
   * Login with username/password.
   * Sets the access token in memory and refresh token via cookie.
   */
  async login(username: string, password: string): Promise<TokenResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Send/receive cookies
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Login failed');
    }

    const data: TokenResponse = await response.json();
    setAccessToken(data.access_token);
    return data;
  },

  /**
   * Logout — revokes refresh token and clears access token.
   */
  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch {
      // Best effort — clear token even if API fails
    }
    clearAccessToken();
  },

  /**
   * Refresh access token using the refresh cookie.
   * Called automatically when a request gets 401.
   */
  async refresh(): Promise<TokenResponse | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        clearAccessToken();
        return null;
      }

      const data: TokenResponse = await response.json();
      setAccessToken(data.access_token);
      return data;
    } catch {
      clearAccessToken();
      return null;
    }
  },

  /**
   * Get current user profile.
   */
  async getMe(): Promise<AuthUser> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error('Not authenticated');
    }

    return response.json();
  },

  /**
   * Change own password.
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/auth/me/password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAccessToken()}`,
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to change password' }));
      throw new Error(error.detail || 'Failed to change password');
    }
  },

  /**
   * Update own profile (e.g. email).
   */
  async updateProfile(data: { email?: string }): Promise<AuthUser> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAccessToken()}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to update profile' }));
      throw new Error(error.detail || 'Failed to update profile');
    }

    return response.json();
  },

  /**
   * Self-register a new account.
   */
  async register(username: string, password: string, email?: string, role?: string): Promise<TokenResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password, email: email || undefined, role: role || undefined }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
      // FastAPI 422 returns detail as an array of validation errors
      if (Array.isArray(error.detail)) {
        const messages = error.detail.map((e: any) => e.msg?.replace('Value error, ', '') || e.message || 'Validation error');
        throw new Error(messages.join('. '));
      }
      throw new Error(error.detail || 'Registration failed');
    }

    const data: TokenResponse = await response.json();
    setAccessToken(data.access_token);
    return data;
  },

  /**
   * Check if self-registration is enabled (public).
   */
  async checkRegistrationStatus(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/registration-status`);
      if (!response.ok) return false;
      const data = await response.json();
      return data.enabled;
    } catch {
      return false;
    }
  },
};
