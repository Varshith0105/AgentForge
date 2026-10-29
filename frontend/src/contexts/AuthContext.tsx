import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types/api';
import { api } from '../services/api';
import { wsClient } from '../services/websocket';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  register: (name: string, email: string, pass: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('agentforge_token');
      if (token) {
        try {
          const profile = await api.auth.me();
          setUser(profile);
          wsClient.connect();
        } catch {
          localStorage.removeItem('agentforge_token');
          localStorage.removeItem('agentforge_refresh_token');
        }
      }
      setIsLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email: string, pass: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', pass);
    const tokens = await api.auth.login(formData);
    localStorage.setItem('agentforge_token', tokens.access_token);
    localStorage.setItem('agentforge_refresh_token', tokens.refresh_token);

    const profile = await api.auth.me();
    setUser(profile);
    wsClient.connect();
  };

  const register = async (name: string, email: string, pass: string) => {
    await api.auth.register({ name, email, password: pass });
    await login(email, pass);
  };

  const logout = () => {
    api.auth.logout().catch(() => {});
    localStorage.removeItem('agentforge_token');
    localStorage.removeItem('agentforge_refresh_token');
    setUser(null);
    wsClient.disconnect();
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
