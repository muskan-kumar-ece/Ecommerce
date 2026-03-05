import { apiClient } from "@/lib/api/client";

export type RazorpayOrder = {
  payment_id: number;
  razorpay_order_id: string;
  amount: number;
  currency: string;
  key_id: string;
  retry_attempt?: number;
};

export async function createRazorpayOrder(payload: { order_id: number; idempotency_key: string }) {
  const { data } = await apiClient.post<RazorpayOrder>("/api/v1/payments/create-order/", payload);
  return data;
}

export async function retryPayment(orderId: string) {
  const { data } = await apiClient.post<RazorpayOrder>(`/api/v1/payments/retry/${orderId}/`);
  return data;
}

export async function verifyRazorpayPayment(payload: {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}) {
  const { data } = await apiClient.post<{ detail: string }>("/api/v1/payments/verify/", payload);
  return data;
}
