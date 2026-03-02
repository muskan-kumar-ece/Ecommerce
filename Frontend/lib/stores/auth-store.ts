"use client";

import { create } from "zustand";

import * as authApi from "@/lib/api/auth";

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
    set({ accessToken: window.localStorage.getItem("access_token") });
  },
  login: async (email: string, password: string) => {
    const token = await authApi.login({ email, password });
    window.localStorage.setItem("access_token", token.access);
    window.localStorage.setItem("refresh_token", token.refresh);
    set({ accessToken: token.access });
  },
  logout: () => {
    window.localStorage.removeItem("access_token");
    window.localStorage.removeItem("refresh_token");
    set({ accessToken: null });
  },
}));
