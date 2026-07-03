"use client";

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";

interface AuthState {
  token: string | null;
  userId: string | null;
  role: string | null;
  email: string | null;
}

interface AuthContextValue {
  auth: AuthState;
  hydrated: boolean;
  setAuth: (auth: AuthState) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  auth: { token: null, userId: null, role: null, email: null },
  hydrated: false,
  setAuth: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuthState] = useState<AuthState>({
    token: null,
    userId: null,
    role: null,
    email: null,
  });
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("auth");
      if (saved) {
        const parsed = JSON.parse(saved);
        setAuthState(parsed);
      }
    } catch {}
    setHydrated(true);
  }, []);

  const setAuth = useCallback((newAuth: AuthState) => {
    setAuthState(newAuth);
    localStorage.setItem("auth", JSON.stringify(newAuth));
  }, []);

  const logout = useCallback(() => {
    const empty = { token: null, userId: null, role: null, email: null };
    setAuthState(empty);
    localStorage.removeItem("auth");
  }, []);

  return (
    <AuthContext.Provider value={{ auth, hydrated, setAuth, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
