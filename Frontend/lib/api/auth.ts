import { apiClient } from "@/lib/api/client";
import type { JwtPair } from "@/lib/api/types";

export async function login(payload: { email: string; password: string }) {
  const { data } = await apiClient.post<JwtPair>("/api/v1/auth/token/", payload);
  return data;
}
