import { apiClient } from "@/lib/api/client";
import type { AdminOrderDetail, AdminOrderListItem, Order, OrderItem } from "@/lib/api/types";

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

type AdminOrdersFilters = {
  status?: string;
  date?: string;
  search?: string;
};

export async function fetchAdminOrders(filters: AdminOrdersFilters) {
  const { data } = await apiClient.get<AdminOrderListItem[]>("/admin/orders/", {
    params: filters,
  });
  return data;
}

export async function fetchAdminOrder(id: string) {
  const { data } = await apiClient.get<AdminOrderDetail>(`/admin/orders/${id}/`);
  return data;
}

export async function updateAdminOrderStatus(
  id: string,
  payload: { status: string; payment_status?: string; note?: string },
) {
  const { data } = await apiClient.post<AdminOrderDetail>(`/admin/orders/${id}/status/`, payload);
  return data;
}
