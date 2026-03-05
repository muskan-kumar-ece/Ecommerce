"use client";

import { useState } from "react";
import { Star } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type ReviewFormProps = {
  onSubmit: (rating: number, comment: string) => Promise<void>;
  isSubmitting?: boolean;
};

export function ReviewForm({ onSubmit, isSubmitting = false }: ReviewFormProps) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedComment = comment.trim();

    if (rating < 1 || rating > 5) {
      setError("Please select a rating between 1 and 5.");
      return;
    }
    if (!trimmedComment) {
      setError("Please enter a review comment.");
      return;
    }

    setError(null);

    try {
      await onSubmit(rating, trimmedComment);
      setComment("");
      setRating(5);
    } catch {
      setError("Unable to submit review. Please try again.");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Write a review</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <p className="text-sm font-medium text-neutral-700 dark:text-neutral-200">Your rating</p>
            <div className="flex items-center gap-1">
              {Array.from({ length: 5 }, (_, index) => {
                const value = index + 1;
                return (
                  <button
                    key={value}
                    type="button"
                    className="rounded-md p-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 ring-offset-background"
                    onClick={() => setRating(value)}
                    aria-label={`Set ${value} star rating`}
                  >
                    <Star
                      className={cn(
                        "h-5 w-5 transition-colors",
                        value <= rating ? "fill-yellow-500 text-yellow-500" : "text-neutral-300 dark:text-neutral-600",
                      )}
                    />
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="review-comment" className="text-sm font-medium text-neutral-700 dark:text-neutral-200">
              Your review
            </label>
            <textarea
              id="review-comment"
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              placeholder="Share your experience with this product..."
              rows={4}
              maxLength={1000}
              className="w-full rounded-xl border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 shadow-sm transition-colors placeholder:text-neutral-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 ring-offset-background dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 dark:placeholder:text-neutral-500"
            />
          </div>

          {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

          <Button type="submit" loading={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Submit review"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
