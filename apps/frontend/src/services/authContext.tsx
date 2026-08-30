import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthState } from '../types';

interface AuthContextType extends AuthState {
  login: (token: string, role: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    token: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    // Check for existing token on mount
    const storedToken = localStorage.getItem('access_token');
    if (storedToken) {
      try {
        // Parse JWT payload (base64)
        const payloadBase64 = storedToken.split('.')[1];
        const payloadDecoded = JSON.parse(atob(payloadBase64));
        
        // Check expiration
        const currentTime = Math.floor(Date.now() / 1000);
        if (payloadDecoded.exp < currentTime) {
          localStorage.removeItem('access_token');
          setAuthState({ isAuthenticated: false, user: null, token: null, loading: false, error: 'Session expired' });
        } else {
          const user: User = {
            email: payloadDecoded.sub,
            role: payloadDecoded.role || 'operator',
          };
          setAuthState({ isAuthenticated: true, user, token: storedToken, loading: false, error: null });
        }
      } catch (err) {
        localStorage.removeItem('access_token');
        setAuthState({ isAuthenticated: false, user: null, token: null, loading: false, error: 'Invalid session' });
      }
    } else {
      setAuthState({ isAuthenticated: false, user: null, token: null, loading: false, error: null });
    }
  }, []);

  const login = (token: string, role: string) => {
    localStorage.setItem('access_token', token);
    try {
      const payloadBase64 = token.split('.')[1];
      const payloadDecoded = JSON.parse(atob(payloadBase64));
      const user: User = {
        email: payloadDecoded.sub,
        role: role,
      };
      setAuthState({ isAuthenticated: true, user, token, loading: false, error: null });
    } catch (err) {
      console.error('Failed to parse token on login', err);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setAuthState({ isAuthenticated: false, user: null, token: null, loading: false, error: null });
    // Force a reload to clear all active states and websockets
    window.location.href = '/';
  };

  return (
    <AuthContext.Provider value={{ ...authState, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
