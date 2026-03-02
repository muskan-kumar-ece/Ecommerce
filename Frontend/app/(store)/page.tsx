"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProducts } from "@/lib/api/products";

export default function ProductListingPage() {
  const { data: products = [], isLoading, isError } = useQuery({
    queryKey: ["products"],
    queryFn: fetchProducts,
  });

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Discover Products</h1>
        <p className="text-slate-500">Curated premium inventory from live APIs.</p>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Loading products...</p>}
      {isError && <p className="text-sm text-rose-600">Unable to load products from API.</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((product) => (
          <Card key={product.id}>
            <CardHeader>
              <CardTitle className="line-clamp-1">{product.name}</CardTitle>
              <CardDescription>SKU: {product.sku}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="line-clamp-2 text-sm text-slate-600">{product.description}</p>
              <div className="flex items-center justify-between">
                <p className="text-lg font-semibold">₹{product.price}</p>
                <Link href={`/products/${product.slug}`} className="text-sm font-medium text-slate-700 underline-offset-4 hover:underline">
                  View
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {!isLoading && !isError && products.length === 0 && (
        <Card>
          <CardContent className="p-6 text-sm text-slate-600">No products found from the API.</CardContent>
        </Card>
      )}
    </section>
  );
}
