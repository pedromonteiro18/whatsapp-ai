import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { AuthState } from '@/types/auth';
import { getCurrentUser, logout as logoutAPI } from '@/services/auth';

interface AuthContextType extends AuthState {
  login: (token: string, phone: string) => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_TOKEN_KEY = 'auth_token';
const USER_PHONE_KEY = 'user_phone';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    userPhone: null,
    token: null,
  });
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async (): Promise<void> => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      const phone = localStorage.getItem(USER_PHONE_KEY);

      if (!token || !phone) {
        setAuthState({
          isAuthenticated: false,
          userPhone: null,
          token: null,
        });
        return;
      }

      // Verify token with backend
      try {
        const response = await getCurrentUser(token);

        // Token is valid
        setAuthState({
          isAuthenticated: true,
          userPhone: response.phone_number,
          token,
        });
      } catch (error) {
        // Token is invalid, clear storage
        console.error('Token validation failed:', error);
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(USER_PHONE_KEY);
        setAuthState({
          isAuthenticated: false,
          userPhone: null,
          token: null,
        });
      }
    } catch (error) {
      console.error('Error checking authentication:', error);
      setAuthState({
        isAuthenticated: false,
        userPhone: null,
        token: null,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const login = (token: string, phone: string): void => {
    // Store in localStorage
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(USER_PHONE_KEY, phone);

    // Update state
    setAuthState({
      isAuthenticated: true,
      userPhone: phone,
      token,
    });
  };

  const logout = async (): Promise<void> => {
    try {
      // Call logout API if we have a token
      if (authState.token) {
        try {
          await logoutAPI(authState.token);
        } catch (error) {
          // Log error but continue with logout
          console.error('Error calling logout API:', error);
        }
      }
    } finally {
      // Always clear local state and storage
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(USER_PHONE_KEY);

      setAuthState({
        isAuthenticated: false,
        userPhone: null,
        token: null,
      });
    }
  };

  const value: AuthContextType = {
    ...authState,
    login,
    logout,
    checkAuth,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
