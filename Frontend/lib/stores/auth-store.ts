"use client";

import { create } from "zustand";

import * as authApi from "@/lib/api/auth";

function setAccessTokenCookie(token: string | null) {
  if (typeof document === "undefined") return;
  if (!token) {
    document.cookie = "access_token=; path=/; max-age=0; samesite=lax";
    return;
  }
  document.cookie = `access_token=${encodeURIComponent(token)}; path=/; samesite=lax`;
}

type AuthState = {
  accessToken: string | null;
  initialize: () => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  initialize: () => {
    if (typeof window === "undefined") return;
    const token = window.localStorage.getItem("access_token");
    setAccessTokenCookie(token);
    set({ accessToken: token });
  },
  login: async (email: string, password: string) => {
    const token = await authApi.login({ email, password });
    window.localStorage.setItem("access_token", token.access);
    window.localStorage.setItem("refresh_token", token.refresh);
    setAccessTokenCookie(token.access);
    set({ accessToken: token.access });
  },
  logout: () => {
    window.localStorage.removeItem("access_token");
    window.localStorage.removeItem("refresh_token");
    setAccessTokenCookie(null);
    set({ accessToken: null });
  },
}));
