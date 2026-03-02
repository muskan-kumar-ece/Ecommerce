import { apiClient } from "@/lib/api/client";
import type { Cart } from "@/lib/api/types";

export async function fetchCart() {
  const { data } = await apiClient.get<Cart>("/api/v1/orders/cart/");
  return data;
}
