import { apiClient } from "@/lib/api/client";
import type { Product } from "@/lib/api/types";

export async function fetchProducts() {
  const { data } = await apiClient.get<Product[]>("/api/v1/products/");
  return data;
}

export async function fetchProductBySlug(slug: string) {
  const products = await fetchProducts();
  const product = products.find((item) => item.slug === slug);
  if (!product) {
    throw new Error("Product not found");
  }
  return product;
}
