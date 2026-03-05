"use client";

import { ShoppingCart, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { WishlistItem } from "@/lib/api/types";

type WishlistCardProps = {
  item: WishlistItem;
  onRemove: (productId: number) => void;
  onMoveToCart: (item: WishlistItem) => void;
  isRemoving?: boolean;
};

export function WishlistCard({ item, onRemove, onMoveToCart, isRemoving = false }: WishlistCardProps) {
  const productName = item.product_details?.name ?? item.product_name ?? `Product #${item.product}`;
  const productPrice = item.product_details?.price ?? item.product_price ?? "0";

  return (
    <Card className="h-full">
      <CardContent className="p-0">
        <div
          className="flex aspect-[4/3] items-center justify-center rounded-t-lg bg-neutral-100 bg-cover bg-center text-sm text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400"
          style={item.image_url ? { backgroundImage: `url(${item.image_url})` } : undefined}
          role="img"
          aria-label={productName}
        >
          {!item.image_url && "Product image"}
        </div>
      </CardContent>
      <CardHeader className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="text-base">{productName}</CardTitle>
          <Badge variant="info">Saved</Badge>
        </div>
        <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">₹{productPrice}</p>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 sm:flex-row">
        <Button
          type="button"
          variant="secondary"
          className="flex-1"
          iconLeft={<ShoppingCart className="h-4 w-4" />}
          onClick={() => onMoveToCart(item)}
        >
          Move to cart
        </Button>
        <Button
          type="button"
          variant="ghost"
          className="flex-1"
          iconLeft={<Trash2 className="h-4 w-4" />}
          onClick={() => onRemove(item.product)}
          loading={isRemoving}
        >
          Remove
        </Button>
      </CardContent>
    </Card>
  );
}
