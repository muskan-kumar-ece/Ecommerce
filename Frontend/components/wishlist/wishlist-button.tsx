"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Heart } from "lucide-react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { addToWishlist, fetchWishlist, removeFromWishlist } from "@/lib/api/wishlist";
import { cn } from "@/lib/utils";

type WishlistButtonProps = {
  productId: number;
  className?: string;
};

export function WishlistButton({ productId, className }: WishlistButtonProps) {
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();

  const { data: wishlist = [] } = useQuery({
    queryKey: ["wishlist"],
    queryFn: fetchWishlist,
    enabled: Boolean(accessToken),
  });

  const isWishlisted = wishlist.some((item) => item.product === productId || item.product_details?.id === productId);

  const addMutation = useMutation({
    mutationFn: () => addToWishlist(productId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    },
  });

  const removeMutation = useMutation({
    mutationFn: () => removeFromWishlist(productId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    },
  });

  const isPending = addMutation.isPending || removeMutation.isPending;

  if (!accessToken) {
    return (
      <Button asChild variant="outline" className={cn("w-full sm:w-auto", className)}>
        <Link href="/login" className="flex items-center gap-2">
          <Heart className="h-4 w-4" />
          Login to save
        </Link>
      </Button>
    );
  }

  return (
    <Button
      type="button"
      variant={isWishlisted ? "secondary" : "outline"}
      loading={isPending}
      onClick={() => {
        if (isWishlisted) {
          removeMutation.mutate();
          return;
        }
        addMutation.mutate();
      }}
      className={cn("w-full sm:w-auto", className)}
      iconLeft={<Heart className={cn("h-4 w-4", isWishlisted && "fill-current")} />}
    >
      {isWishlisted ? "Saved" : "Save to wishlist"}
    </Button>
  );
}
