import { apiClient } from "@/lib/api/client";

export type RazorpayOrder = {
  payment_id: number;
  razorpay_order_id: string;
  amount: number;
  currency: string;
  key_id: string;
};

export async function createRazorpayOrder(payload: { order_id: number; idempotency_key: string }) {
  const { data } = await apiClient.post<RazorpayOrder>("/api/v1/payments/create-order/", payload);
  return data;
}
