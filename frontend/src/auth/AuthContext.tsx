import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { getCurrentUser, getSetupStatus, login as loginRequest, setupAdmin } from "@/api/auth";
import type { User } from "@/api/types";

import { clearTokens, getAccessToken, setTokens } from "./tokenStorage";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  needsSetup: boolean;
  login: (email: string, password: string) => Promise<void>;
  completeSetup: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);

  const bootstrap = useCallback(async () => {
    setIsLoading(true);
    try {
      const status = await getSetupStatus();
      setNeedsSetup(status.needs_setup);
      if (!status.needs_setup && getAccessToken()) {
        try {
          setUser(await getCurrentUser());
        } catch {
          clearTokens();
          setUser(null);
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await loginRequest(email, password);
    setTokens(tokens.access_token, tokens.refresh_token);
    setUser(await getCurrentUser());
  }, []);

  const completeSetup = useCallback(async (email: string, password: string) => {
    const tokens = await setupAdmin(email, password);
    setTokens(tokens.access_token, tokens.refresh_token);
    setNeedsSetup(false);
    setUser(await getCurrentUser());
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    setUser(await getCurrentUser());
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isLoading, needsSetup, login, completeSetup, logout, refreshUser }),
    [user, isLoading, needsSetup, login, completeSetup, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
