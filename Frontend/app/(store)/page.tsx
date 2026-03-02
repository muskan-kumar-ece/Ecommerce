"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchProducts } from "@/lib/api/products";
import type { Product } from "@/lib/api/types";

export default function ProductListingPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setError("Unable to load products from API."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Discover Products</h1>
        <p className="text-slate-500">Curated premium inventory from live APIs.</p>
      </div>

      {loading && <p className="text-sm text-slate-500">Loading products...</p>}
      {error && <p className="text-sm text-rose-600">{error}</p>}

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

      {!loading && !error && products.length === 0 && (
        <Card>
          <CardContent className="p-6 text-sm text-slate-600">No products found from the API.</CardContent>
        </Card>
      )}
    </section>
  );
}
