import { apiClient } from "@/lib/api/client";
import type { AnalyticsSummary } from "@/lib/api/types";

export async function fetchAnalyticsSummary() {
  const { data } = await apiClient.get<AnalyticsSummary>("/admin/analytics/summary/");
  return data;
}
