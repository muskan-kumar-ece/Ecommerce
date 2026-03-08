import { apiClient } from "@/lib/api/client";
import type { AdminAnalyticsDashboard, AnalyticsSummary } from "@/lib/api/types";

export async function fetchAnalyticsSummary() {
  const { data } = await apiClient.get<AnalyticsSummary>("/api/v1/admin/analytics/summary/");
  return data;
}

export async function fetchAdminDashboardAnalytics() {
  const { data } = await apiClient.get<AdminAnalyticsDashboard>("/api/v1/admin/analytics/");
  return data;
}
