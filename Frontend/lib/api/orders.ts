import { apiClient } from "@/lib/api/client";

export async function createCheckoutSession(payload: { payment_method: string }) {
  const { data } = await apiClient.post<{ order_id: number; payment_redirect_url?: string }>(
    "/api/v1/orders/checkout/",
    payload,
  );
  return data;
}
