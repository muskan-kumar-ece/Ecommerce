import { apiClient } from "@/lib/api/client";
import type { Order, OrderItem } from "@/lib/api/types";

export async function createOrder(items: { product_id: number; quantity: number }[]) {
  const { data } = await apiClient.post<Order>(
    "/api/v1/orders/create/",
    { items },
  );
  return data;
}

export async function fetchMyOrders() {
  const { data } = await apiClient.get<Order[]>("/api/v1/orders/my-orders/");
  return data;
}

export async function fetchOrder(id: string) {
  const { data } = await apiClient.get<Order>(`/api/v1/orders/${id}/`);
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
