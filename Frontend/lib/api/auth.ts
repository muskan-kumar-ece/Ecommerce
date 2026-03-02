import { apiClient } from "@/lib/api/client";
import type { JwtPair, User } from "@/lib/api/types";

export async function login(payload: { email: string; password: string }) {
  const { data } = await apiClient.post<JwtPair>("/api/v1/users/login/", payload);
  return data;
}

export async function register(payload: { name: string; email: string; password: string }) {
  const { data } = await apiClient.post<User>("/api/v1/users/register/", payload);
  return data;
}

export async function fetchCurrentUser() {
  const { data } = await apiClient.get<User>("/api/v1/users/profile/");
  return data;
}
