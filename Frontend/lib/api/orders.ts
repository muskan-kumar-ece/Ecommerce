import { apiClient } from "@/lib/api/client";
import type { Order } from "@/lib/api/types";

export async function createOrder(payload: {
  total_amount: string;
  status: string;
  payment_status: string;
  tracking_id: string;
}) {
  const { data } = await apiClient.post<Order>(
    "/api/v1/orders/",
    payload,
  );
  return data;
}
