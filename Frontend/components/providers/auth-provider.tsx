"use client";

import { useEffect } from "react";

import { useAuthStore } from "@/lib/stores/auth-store";

type AuthContextValue = {
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const initialize = useAuthStore((state) => state.initialize);

  useEffect(() => {
    initialize();
  }, [initialize]);

  return <>{children}</>;
}

export const useAuth = (): AuthContextValue => useAuthStore((state) => state);
