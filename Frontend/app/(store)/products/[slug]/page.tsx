"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/components/providers/auth-provider";
import { ReviewCard } from "@/components/reviews/review-card";
import { ReviewForm } from "@/components/reviews/review-form";
import { WishlistButton } from "@/components/wishlist/wishlist-button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProductBySlug } from "@/lib/api/products";
import { createProductReview, fetchProductReviews, updateProductReview } from "@/lib/api/reviews";

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
    mutationFn: ({ rating, title, comment }: { rating: number; title: string; comment: string }) => {
      const existingReview = reviews.find((review) => review.is_mine);
      if (existingReview) {
        return updateProductReview(existingReview.id, product!.id, rating, title, comment);
      }
      return createProductReview(product!.id, rating, title, comment);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["product-reviews", product?.id] });
      await queryClient.invalidateQueries({ queryKey: ["product", params.slug] });
    },
  });

  if (isError) return <p className="text-sm text-rose-600">Unable to load product details.</p>;
  if (isLoading || !product) return <p className="text-sm text-slate-500">Loading product...</p>;

  const averageRating = Number(product.average_rating ?? 0).toFixed(1);
  const reviewsCount = product.reviews_count ?? reviews.length;
  const myReview = reviews.find((review) => review.is_mine);

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
          <WishlistButton productId={product.id} />
        </CardContent>
      </Card>

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-50">Customer Reviews</h2>
          <div className="flex items-center gap-2">
            <Badge variant="info">Average: {averageRating} / 5</Badge>
            <Badge>{reviewsCount} reviews</Badge>
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
                title={review.title}
                comment={review.comment}
                createdAt={review.created_at}
              />
            ))}
          </div>
        )}

        {accessToken ? (
          <ReviewForm
            onSubmit={async (rating, title, comment) => {
              await reviewMutation.mutateAsync({ rating, title, comment });
            }}
            isSubmitting={reviewMutation.isPending}
            initialRating={myReview?.rating ?? 5}
            initialTitle={myReview?.title ?? ""}
            initialComment={myReview?.comment ?? ""}
            mode={myReview ? "edit" : "create"}
          />
        ) : (
          <p className="text-sm text-neutral-500">Log in to write a review.</p>
        )}
      </section>
    </div>
  );
}
