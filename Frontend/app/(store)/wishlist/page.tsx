"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/components/providers/auth-provider";
import { useCart } from "@/components/providers/cart-context";
import { WishlistCard } from "@/components/wishlist/wishlist-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchWishlist, removeFromWishlist } from "@/lib/api/wishlist";
import type { WishlistItem } from "@/lib/api/types";

export default function WishlistPage() {
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();
  const { addToCart } = useCart();

  const { data: wishlist = [], isLoading, isError } = useQuery({
    queryKey: ["wishlist"],
    queryFn: fetchWishlist,
    enabled: Boolean(accessToken),
  });

  const removeMutation = useMutation({
    mutationFn: (productId: number) => removeFromWishlist(productId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    },
  });

  const handleMoveToCart = async (item: WishlistItem) => {
    addToCart({
      id: item.product_details?.id ?? item.product,
      name: item.product_details?.name ?? item.product_name ?? `Product #${item.product}`,
      price: item.product_details?.price ?? item.product_price ?? "0",
    });
    await removeMutation.mutateAsync(item.product);
  };

  if (!accessToken) {
    return (
      <section className="mx-auto flex max-w-2xl flex-col items-center gap-4 py-16 text-center">
        <Badge variant="warning">Wishlist</Badge>
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Your Wishlist</h1>
        <p className="text-neutral-600 dark:text-neutral-300">Please login to view your saved products.</p>
        <Button asChild>
          <Link href="/login">Go to Login</Link>
        </Button>
      </section>
    );
  }

  if (isError) return <p className="text-sm text-rose-600">Unable to load wishlist.</p>;
  if (isLoading) return <p className="text-sm text-slate-500">Loading wishlist...</p>;

  if (wishlist.length === 0) {
    return (
      <section className="mx-auto flex max-w-2xl flex-col items-center gap-4 py-16 text-center">
        <Badge variant="info">Wishlist</Badge>
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Your Wishlist</h1>
        <p className="text-neutral-600 dark:text-neutral-300">You have no saved products yet</p>
        <Button asChild>
          <Link href="/">Continue Shopping</Link>
        </Button>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Your Wishlist</h1>
        <Badge>{wishlist.length} saved</Badge>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {wishlist.map((item) => (
          <WishlistCard
            key={`${item.id}-${item.product}`}
            item={item}
            onRemove={(productId) => removeMutation.mutate(productId)}
            onMoveToCart={handleMoveToCart}
            isRemoving={removeMutation.isPending}
          />
        ))}
      </div>
    </section>
  );
}
