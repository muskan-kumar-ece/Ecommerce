"use client";

import { createContext, useContext, useMemo, useState } from "react";

import * as authApi from "@/lib/api/auth";

type AuthContextValue = {
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const value = useMemo(
    () => ({
      accessToken,
      login: async (email: string, password: string) => {
        const token = await authApi.login({ email, password });
        window.localStorage.setItem("access_token", token.access);
        window.localStorage.setItem("refresh_token", token.refresh);
        setAccessToken(token.access);
      },
      logout: () => {
        window.localStorage.removeItem("access_token");
        window.localStorage.removeItem("refresh_token");
        setAccessToken(null);
      },
    }),
    [accessToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
