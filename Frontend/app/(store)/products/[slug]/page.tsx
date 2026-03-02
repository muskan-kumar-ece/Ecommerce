"use client";

import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProductBySlug } from "@/lib/api/products";
import type { Product } from "@/lib/api/types";

export default function ProductDetailPage({ params }: { params: { slug: string } }) {
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProductBySlug(params.slug)
      .then(setProduct)
      .catch(() => setError("Unable to load product details."));
  }, [params.slug]);

  if (error) return <p className="text-sm text-rose-600">{error}</p>;
  if (!product) return <p className="text-sm text-slate-500">Loading product...</p>;

  return (
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
  );
}
