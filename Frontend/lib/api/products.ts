import { apiClient } from "@/lib/api/client";
import type { ApiListResponse, Product } from "@/lib/api/types";

export async function fetchProducts() {
  const { data } = await apiClient.get<ApiListResponse<Product>>("/api/v1/products/products/");
  return data.results;
}

export async function fetchProductBySlug(slug: string) {
  const { data } = await apiClient.get<Product>(`/api/v1/products/products/${slug}/`);
  return data;
}
