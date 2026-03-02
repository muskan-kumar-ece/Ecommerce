import { apiClient } from "@/lib/api/client";
import type { ReferralSummary } from "@/lib/api/types";

export async function fetchReferralSummary() {
  const { data } = await apiClient.get<ReferralSummary>("/api/v1/users/referral-summary/");
  return data;
}
