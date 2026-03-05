import { apiClient } from "@/lib/api/client";
import type { Order, OrderItem } from "@/lib/api/types";

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

export async function fetchOrders() {
  const { data } = await apiClient.get<Order[]>("/api/v1/orders/");
  return data;
}

export async function fetchOrderItems() {
  const { data } = await apiClient.get<OrderItem[]>("/api/v1/orders/items/");
  return data;
}
