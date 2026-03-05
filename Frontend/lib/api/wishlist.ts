import { apiClient } from "@/lib/api/client";
import type { Product, WishlistItem } from "@/lib/api/types";

type RawWishlistItem = Partial<WishlistItem> & {
  product_id?: number;
  product_name?: string;
  price?: string;
  image?: string;
  product_details?: Partial<Product> & { image_url?: string };
};

type WishlistResponse = RawWishlistItem[] | { results?: RawWishlistItem[] };

const WISHLIST_ENDPOINT = "/api/v1/wishlist/";

function normalizeWishlistItem(item: RawWishlistItem): WishlistItem {
  const productId = Number(item.product ?? item.product_id ?? item.product_details?.id ?? 0);
  const productName = item.product_name ?? item.product_details?.name ?? `Product #${productId}`;
  const productPrice = item.product_price ?? item.price ?? item.product_details?.price ?? "0";
  const imageUrl = item.image_url ?? item.image ?? item.product_details?.image_url;

  return {
    id: Number(item.id ?? productId),
    product: productId,
    product_name: String(productName),
    product_price: String(productPrice),
    image_url: imageUrl ? String(imageUrl) : undefined,
    product_details: item.product_details
      ? {
          id: Number(item.product_details.id ?? productId),
          category: Number(item.product_details.category ?? 0),
          category_name: String(item.product_details.category_name ?? ""),
          name: String(item.product_details.name ?? productName),
          slug: String(item.product_details.slug ?? ""),
          description: String(item.product_details.description ?? ""),
          price: String(item.product_details.price ?? productPrice),
          sku: String(item.product_details.sku ?? ""),
          stock_quantity: Number(item.product_details.stock_quantity ?? 0),
          is_refurbished: Boolean(item.product_details.is_refurbished),
          condition_grade: String(item.product_details.condition_grade ?? ""),
          is_active: item.product_details.is_active ?? true,
          created_at: String(item.product_details.created_at ?? new Date(0).toISOString()),
          updated_at: String(item.product_details.updated_at ?? new Date(0).toISOString()),
        }
      : undefined,
    created_at: item.created_at ? String(item.created_at) : undefined,
    updated_at: item.updated_at ? String(item.updated_at) : undefined,
  };
}

export async function fetchWishlist() {
  const { data } = await apiClient.get<WishlistResponse>(WISHLIST_ENDPOINT);
  const items = Array.isArray(data) ? data : data.results ?? [];
  return items.map(normalizeWishlistItem);
}

export async function addToWishlist(productId: number) {
  const { data } = await apiClient.post<RawWishlistItem>(WISHLIST_ENDPOINT, { product: productId });
  return normalizeWishlistItem(data);
}

export async function removeFromWishlist(productId: number) {
  await apiClient.delete(`${WISHLIST_ENDPOINT}${productId}/`);
}
