import {
  createContext, useContext, useState, useEffect,
  useCallback, ReactNode
} from 'react';
import api, { setTokens, clearTokens } from '../utils/api';
import { AuthUser, UserRole } from '../types';

interface AuthContextValue {
  user:      AuthUser | null;
  loading:   boolean;
  login:     (email: string, password: string) => Promise<void>;
  logout:    () => void;
  isRole:    (role: UserRole) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function parseJwt(token: string): Record<string, unknown> {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch {
    return {};
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]       = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // Re-hydrate user from stored token on mount
  useEffect(() => {
    const idToken = localStorage.getItem('idToken');
    if (idToken) {
      const claims = parseJwt(idToken);
      const exp = (claims.exp as number) * 1000;
      if (Date.now() < exp) {
        const groups = (claims['cognito:groups'] as string[] | string | undefined) ?? [];
        setUser({
          sub:    claims.sub as string,
          email:  claims.email as string,
          name:   claims.name as string,
          role:   Array.isArray(groups) ? groups[0] : groups,
          groups: (Array.isArray(groups) ? groups : [groups]) as UserRole[],
        });
      } else {
        clearTokens();
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await api.post('/auth/login', { email, password });
    setTokens(data.idToken, data.accessToken, data.refreshToken);
    const claims = parseJwt(data.idToken);
    const groups = (claims['cognito:groups'] as string[] | string | undefined) ?? [];
    setUser({
      sub:    claims.sub as string,
      email:  claims.email as string,
      name:   claims.name as string,
      role:   Array.isArray(groups) ? groups[0] : groups,
      groups: (Array.isArray(groups) ? groups : [groups]) as UserRole[],
    });
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    window.location.href = '/login';
  }, []);

  const isRole = useCallback(
    (role: UserRole) => user?.groups.includes(role) ?? false,
    [user]
  );

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
