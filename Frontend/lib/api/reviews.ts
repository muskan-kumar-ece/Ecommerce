import { apiClient } from "@/lib/api/client";
import type { ProductReview } from "@/lib/api/types";

type RawReview = Partial<ProductReview> & {
  user?: string;
  user_display_name?: string;
  username?: string;
  is_mine?: boolean;
  title?: string;
};

function productReviewsEndpoint(productId: number) {
  return `/api/v1/products/${productId}/reviews/`;
}

function normalizeReview(review: RawReview, productId: number): ProductReview {
  return {
    id: Number(review.id ?? 0),
    product: Number(review.product ?? productId),
    user_name: String(review.user_name ?? review.user_display_name ?? review.username ?? review.user ?? "Anonymous"),
    rating: Math.min(5, Math.max(1, Number(review.rating ?? 1))),
    title: String(review.title ?? ""),
    is_mine: review.is_mine ?? false,
    comment: String(review.comment ?? ""),
    created_at: String(review.created_at ?? new Date(0).toISOString()),
    updated_at: review.updated_at ? String(review.updated_at) : undefined,
  };
}

export async function fetchProductReviews(productId: number) {
  const { data } = await apiClient.get<RawReview[] | { results?: RawReview[] }>(productReviewsEndpoint(productId));
  const reviews = Array.isArray(data) ? data : data.results ?? [];
  return reviews.map((review) => normalizeReview(review, productId));
}

export async function createProductReview(productId: number, rating: number, title: string, comment: string) {
  const trimmedTitle = title.trim();
  const trimmedComment = comment.trim();

  if (!trimmedTitle) {
    throw new Error("Title is required.");
  }
  if (!trimmedComment) {
    throw new Error("Comment is required.");
  }
  if (rating < 1 || rating > 5) {
    throw new Error("Rating must be between 1 and 5.");
  }

  const { data } = await apiClient.post<RawReview>("/api/v1/reviews/", {
    product: productId,
    rating,
    title: trimmedTitle,
    comment: trimmedComment,
  });

  return normalizeReview(data, productId);
}

export async function updateProductReview(reviewId: number, productId: number, rating: number, title: string, comment: string) {
  const trimmedTitle = title.trim();
  const trimmedComment = comment.trim();

  if (!trimmedTitle) {
    throw new Error("Title is required.");
  }
  if (!trimmedComment) {
    throw new Error("Comment is required.");
  }
  if (rating < 1 || rating > 5) {
    throw new Error("Rating must be between 1 and 5.");
  }

  const { data } = await apiClient.patch<RawReview>(`/api/v1/reviews/${reviewId}/`, {
    rating,
    title: trimmedTitle,
    comment: trimmedComment,
  });
  return normalizeReview(data, productId);
}

export async function deleteProductReview(reviewId: number) {
  await apiClient.delete(`/api/v1/reviews/${reviewId}/`);
}
