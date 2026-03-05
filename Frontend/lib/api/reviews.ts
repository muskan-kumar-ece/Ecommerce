import { apiClient } from "@/lib/api/client";
import type { ProductReview } from "@/lib/api/types";

type RawReview = Partial<ProductReview> & {
  user?: string;
  user_display_name?: string;
  username?: string;
};

function reviewsEndpoint(productId: number) {
  return `/api/v1/products/${productId}/reviews/`;
}

function normalizeReview(review: RawReview, productId: number): ProductReview {
  return {
    id: Number(review.id ?? 0),
    product: Number(review.product ?? productId),
    user_name: String(review.user_name ?? review.user_display_name ?? review.username ?? review.user ?? "Anonymous"),
    rating: Math.min(5, Math.max(1, Number(review.rating ?? 1))),
    comment: String(review.comment ?? ""),
    created_at: String(review.created_at ?? new Date(0).toISOString()),
    updated_at: review.updated_at ? String(review.updated_at) : undefined,
  };
}

export async function fetchProductReviews(productId: number) {
  const { data } = await apiClient.get<RawReview[] | { results?: RawReview[] }>(reviewsEndpoint(productId));
  const reviews = Array.isArray(data) ? data : data.results ?? [];
  return reviews.map((review) => normalizeReview(review, productId));
}

export async function createProductReview(productId: number, rating: number, comment: string) {
  const trimmedComment = comment.trim();

  if (!trimmedComment) {
    throw new Error("Comment is required.");
  }
  if (rating < 1 || rating > 5) {
    throw new Error("Rating must be between 1 and 5.");
  }

  const { data } = await apiClient.post<RawReview>(reviewsEndpoint(productId), {
    rating,
    comment: trimmedComment,
  });

  return normalizeReview(data, productId);
}
