"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchProductListing } from "@/lib/api/products";

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

export default function ProductsPage() {
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [minPriceInput, setMinPriceInput] = useState("");
  const [maxPriceInput, setMaxPriceInput] = useState("");
  const [inStockOnly, setInStockOnly] = useState(false);
  const [page, setPage] = useState(1);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const minPrice = useMemo(() => {
    const value = Number(minPriceInput);
    return Number.isFinite(value) && minPriceInput !== "" ? value : undefined;
  }, [minPriceInput]);

  const maxPrice = useMemo(() => {
    const value = Number(maxPriceInput);
    return Number.isFinite(value) && maxPriceInput !== "" ? value : undefined;
  }, [maxPriceInput]);

  const {
    data: listing,
    isLoading,
    isError,
    isFetching,
  } = useQuery({
    queryKey: ["products", "listing", { search, category, minPrice, maxPrice, inStockOnly, page }],
    queryFn: () =>
      fetchProductListing({
        search: search || undefined,
        category: category || undefined,
        min_price: minPrice,
        max_price: maxPrice,
        in_stock: inStockOnly || undefined,
        page,
      }),
  });

  const hasPrevious = Boolean(listing?.previous);
  const hasNext = Boolean(listing?.next);
  const products = listing?.results ?? [];

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Browse Products</h1>
        <p className="text-sm text-slate-500">Search and filter products to quickly find what you need.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        <aside className="space-y-4 rounded-xl border border-slate-200 bg-white p-4">
          <div className="space-y-2">
            <label htmlFor="product-search" className="text-sm font-medium text-slate-700">
              Search
            </label>
            <Input
              id="product-search"
              placeholder="Search by name..."
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="product-category" className="text-sm font-medium text-slate-700">
              Category
            </label>
            <Input
              id="product-category"
              placeholder="e.g. electronics"
              value={category}
              onChange={(event) => {
                setCategory(event.target.value);
                setPage(1);
              }}
            />
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-700">Price range</p>
            <div className="grid grid-cols-2 gap-2">
              <Input
                type="number"
                min={0}
                placeholder="Min"
                value={minPriceInput}
                onChange={(event) => {
                  setMinPriceInput(event.target.value);
                  setPage(1);
                }}
              />
              <Input
                type="number"
                min={0}
                placeholder="Max"
                value={maxPriceInput}
                onChange={(event) => {
                  setMaxPriceInput(event.target.value);
                  setPage(1);
                }}
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={inStockOnly}
              onChange={(event) => {
                setInStockOnly(event.target.checked);
                setPage(1);
              }}
            />
            In stock only
          </label>
        </aside>

        <div className="space-y-4">
          {isLoading ? <p className="text-sm text-slate-500">Loading products...</p> : null}
          {isError ? <p className="text-sm text-rose-600">Unable to load products. Please retry.</p> : null}
          {!isLoading && !isError && products.length === 0 ? (
            <p className="text-sm text-slate-500">No products found for the selected filters.</p>
          ) : null}

          {products.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {products.map((product) => (
                <Card key={product.id}>
                  <CardHeader>
                    <CardTitle className="text-base">
                      <Link href={`/products/${product.slug}`} className="hover:underline">
                        {product.name}
                      </Link>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <p className="line-clamp-2 text-sm text-slate-600">{product.description}</p>
                    <p className="text-sm text-slate-500">{product.category_name}</p>
                    <p className="font-semibold text-slate-900">
                      {currencyFormatter.format(Number(product.price) || 0)}
                    </p>
                    <p className="text-xs text-slate-500">{product.stock_quantity > 0 ? "In stock" : "Out of stock"}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : null}

          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">{listing ? `${listing.count} total products` : ""}</p>
            <div className="flex items-center gap-2">
              <Button type="button" variant="outline" disabled={!hasPrevious || isFetching} onClick={() => setPage((current) => Math.max(1, current - 1))}>
                Previous
              </Button>
              <span className="text-sm text-slate-600">Page {page}</span>
              <Button type="button" variant="outline" disabled={!hasNext || isFetching} onClick={() => setPage((current) => current + 1)}>
                Next
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
