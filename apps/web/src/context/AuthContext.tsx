import { createContext, useContext, useState, type ReactNode } from 'react';
import { api, getToken, setToken } from '../api/client';
import type { AuthResponse } from '../api/types';

interface AuthState {
  token: string | null;
  user: AuthResponse['user'] | null;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(getToken());
  const [user, setUser] = useState<AuthResponse['user'] | null>(null);

  const applyAuth = (auth: AuthResponse) => {
    setToken(auth.accessToken);
    setTokenState(auth.accessToken);
    setUser(auth.user);
  };

  const login = async (email: string, password: string) => {
    applyAuth(await api.login(email, password));
  };

  const register = async (name: string, email: string, password: string) => {
    applyAuth(await api.register(name, email, password));
  };

  const logout = () => {
    setToken(null);
    setTokenState(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
