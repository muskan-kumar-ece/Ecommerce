"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/components/providers/auth-provider";
import { ReviewCard } from "@/components/reviews/review-card";
import { ReviewForm } from "@/components/reviews/review-form";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProductBySlug } from "@/lib/api/products";
import { createProductReview, fetchProductReviews } from "@/lib/api/reviews";

export default function ProductDetailPage({ params }: { params: { slug: string } }) {
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();

  const { data: product, isLoading, isError } = useQuery({
    queryKey: ["product", params.slug],
    queryFn: () => fetchProductBySlug(params.slug),
  });

  const {
    data: reviews = [],
    isLoading: isReviewsLoading,
    isError: isReviewsError,
  } = useQuery({
    queryKey: ["product-reviews", product?.id],
    queryFn: () => fetchProductReviews(product!.id),
    enabled: Boolean(product?.id),
  });

  const reviewMutation = useMutation({
    mutationFn: ({ rating, comment }: { rating: number; comment: string }) =>
      createProductReview(product!.id, rating, comment),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["product-reviews", product?.id] });
    },
  });

  if (isError) return <p className="text-sm text-rose-600">Unable to load product details.</p>;
  if (isLoading || !product) return <p className="text-sm text-slate-500">Loading product...</p>;

  const averageRating =
    reviews.length > 0
      ? (reviews.reduce((total, review) => total + review.rating, 0) / reviews.length).toFixed(1)
      : "0.0";

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>{product.name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-slate-600">{product.description}</p>
          <p className="text-lg font-semibold">₹{product.price}</p>
          <p className="text-sm text-slate-500">SKU: {product.sku}</p>
        </CardContent>
      </Card>

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-50">Customer Reviews</h2>
          <div className="flex items-center gap-2">
            <Badge variant="info">Average: {averageRating} / 5</Badge>
            <Badge>{reviews.length} reviews</Badge>
          </div>
        </div>

        {isReviewsLoading && <p className="text-sm text-neutral-500">Loading reviews...</p>}
        {isReviewsError && <p className="text-sm text-rose-600">Unable to load reviews right now.</p>}
        {!isReviewsLoading && !isReviewsError && reviews.length === 0 && (
          <p className="text-sm text-neutral-500">No reviews yet. Be the first to review this product.</p>
        )}

        {reviews.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2">
            {reviews.map((review) => (
              <ReviewCard
                key={review.id}
                userName={review.user_name}
                rating={review.rating}
                comment={review.comment}
                createdAt={review.created_at}
              />
            ))}
          </div>
        )}

        {accessToken ? (
          <ReviewForm
            onSubmit={async (rating, comment) => {
              await reviewMutation.mutateAsync({ rating, comment });
            }}
            isSubmitting={reviewMutation.isPending}
          />
        ) : (
          <p className="text-sm text-neutral-500">Log in to write a review.</p>
        )}
      </section>
    </div>
  );
}
