"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProductBySlug } from "@/lib/api/products";

export default function ProductDetailPage({ params }: { params: { slug: string } }) {
  const { data: product, isLoading, isError } = useQuery({
    queryKey: ["product", params.slug],
    queryFn: () => fetchProductBySlug(params.slug),
  });

  if (isError) return <p className="text-sm text-rose-600">Unable to load product details.</p>;
  if (isLoading || !product) return <p className="text-sm text-slate-500">Loading product...</p>;

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
