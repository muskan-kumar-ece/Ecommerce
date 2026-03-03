"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, ShieldCheck, Truck, RotateCcw } from "lucide-react";

import { CartDrawer } from "@/components/layout/cart-drawer";
import { CartProvider, type CartProduct, useCart } from "@/components/providers/cart-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const featuredProducts = [
  { id: 1, name: "Aurora Smartwatch", price: "₹7,499", description: "Precision tracking with an elegant titanium finish." },
  { id: 2, name: "Luma Wireless Earbuds", price: "₹4,299", description: "Immersive sound tuned for all-day comfort and clarity." },
  { id: 3, name: "Nimbus Travel Backpack", price: "₹3,899", description: "Minimal silhouette with premium weather-resistant fabric." },
  { id: 4, name: "Quartz Desk Lamp", price: "₹2,199", description: "Soft ambient lighting with modern touch controls." },
];

function ProductCard({
  product,
  onAdded,
}: {
  product: CartProduct & { description: string };
  onAdded: () => void;
}) {
  const { addToCart } = useCart();

  return (
    <Card className="transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
      <CardContent className="p-0">
        <div className="aspect-square rounded-t-lg bg-neutral-100 dark:bg-neutral-800" />
      </CardContent>
      <CardHeader>
        <CardTitle>{product.name}</CardTitle>
        <data value={product.price.replace(/[^\d]/g, "")} className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
          {product.price}
        </data>
      </CardHeader>
      <CardContent className="space-y-4">
        <CardDescription className="text-sm text-neutral-600 dark:text-neutral-300">{product.description}</CardDescription>
        <Button
          type="button"
          onClick={() => {
            addToCart(product);
            onAdded();
          }}
          className="w-full motion-safe:transition-all motion-safe:duration-200 motion-safe:hover:scale-[1.02] motion-safe:hover:shadow-lg"
        >
          Add to Cart
        </Button>
      </CardContent>
    </Card>
  );
}

function StorefrontContent() {
  const [isCartOpen, setIsCartOpen] = useState(false);
  const { totalItems } = useCart();

  return (
    <>
      <CartDrawer open={isCartOpen} onClose={() => setIsCartOpen(false)} />
      <div className="bg-gradient-to-b from-primary-50 via-white to-white dark:from-neutral-900 dark:via-neutral-950 dark:to-neutral-950">
      <section className="relative mx-auto flex min-h-[60vh] w-full max-w-6xl flex-col items-center justify-center overflow-hidden px-4 py-24 text-center">
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary-200/40 blur-3xl dark:bg-primary-900/20" />
        <div className="max-w-3xl space-y-6">
          <h1 className="text-4xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100 sm:text-5xl">
            Premium essentials designed for modern living.
          </h1>
          <p className="text-lg text-neutral-600 dark:text-neutral-300">
            Discover curated products that blend craftsmanship, performance, and timeless design.
          </p>
          <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button asChild size="lg">
              <Link href="#featured-products">
                Shop Collection <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button type="button" size="lg" variant="secondary" onClick={() => setIsCartOpen(true)}>
              Cart ({totalItems})
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/referral">Explore Benefits</Link>
            </Button>
          </div>
          <p className="text-sm text-neutral-500 dark:text-neutral-400">Free shipping over ₹999</p>
        </div>
      </section>
      <section className="border-y border-neutral-200/70 bg-neutral-50 py-6 dark:border-neutral-800/70 dark:bg-neutral-900">
        <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 text-center sm:grid-cols-3">
          <div>
            <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">4.8/5 Rating</p>
            <p className="text-sm text-neutral-600 dark:text-neutral-300">Trusted by shoppers</p>
          </div>
          <div>
            <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">50K+ Orders</p>
            <p className="text-sm text-neutral-600 dark:text-neutral-300">Delivered nationwide</p>
          </div>
          <div>
            <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">100% Secure</p>
            <p className="text-sm text-neutral-600 dark:text-neutral-300">Encrypted checkout</p>
          </div>
        </div>
      </section>

      <section id="featured-products" className="mx-auto w-full max-w-6xl border-t border-neutral-200/70 px-4 py-20 dark:border-neutral-800/70">
        <h2 className="mb-8 text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Featured Products</h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {featuredProducts.map((product) => (
            <ProductCard key={product.id} product={product} onAdded={() => setIsCartOpen(true)} />
          ))}
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl border-t border-neutral-200/70 px-4 py-20 dark:border-neutral-800/70">
        <h2 className="mb-8 text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Why shop with us</h2>
        <div className="grid gap-6 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-primary-500" />
                Secure Payments
              </CardTitle>
              <CardDescription>Encrypted checkout with trusted payment partners for complete peace of mind.</CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Truck className="h-5 w-5 text-primary-500" />
                Fast Delivery
              </CardTitle>
              <CardDescription>Quick dispatch and reliable shipping to keep your experience effortless.</CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <RotateCcw className="h-5 w-5 text-primary-500" />
                Easy Returns
              </CardTitle>
              <CardDescription>Simple return process with responsive support whenever you need assistance.</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      <footer className="border-t border-neutral-200 px-4 py-8 text-center text-sm text-neutral-500 dark:border-neutral-800 dark:text-neutral-400">
        © {new Date().getFullYear()} Venopai Commerce. Crafted for a premium shopping experience.
      </footer>
      </div>
    </>
  );
}

export default function ProductListingPage() {
  return (
    <CartProvider>
      <StorefrontContent />
    </CartProvider>
  );
}
