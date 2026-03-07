import { apiClient } from "@/lib/api/client";
import type { PaginatedResponse, Product } from "@/lib/api/types";

export async function fetchProducts() {
  const { data } = await apiClient.get<PaginatedResponse<Product>>("/api/v1/products/", {
    params: { page_size: 100 },
  });
  return data.results;
}

type ProductListingFilters = {
  search?: string;
  category?: string;
  min_price?: number;
  max_price?: number;
  in_stock?: boolean;
  page?: number;
};

export async function fetchProductListing(filters: ProductListingFilters) {
  const { data } = await apiClient.get<PaginatedResponse<Product>>("/api/v1/products/", {
    params: filters,
  });
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
