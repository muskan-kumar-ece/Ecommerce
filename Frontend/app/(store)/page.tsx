import Link from "next/link";
import { ArrowRight, ShieldCheck, Truck, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const featuredProducts = [
  { id: 1, name: "Aurora Smartwatch", price: "₹7,499", description: "Precision tracking with an elegant titanium finish." },
  { id: 2, name: "Luma Wireless Earbuds", price: "₹4,299", description: "Immersive sound tuned for all-day comfort and clarity." },
  { id: 3, name: "Nimbus Travel Backpack", price: "₹3,899", description: "Minimal silhouette with premium weather-resistant fabric." },
  { id: 4, name: "Quartz Desk Lamp", price: "₹2,199", description: "Soft ambient lighting with modern touch controls." },
];

function ProductCard({ name, price, description }: { name: string; price: string; description: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{name}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex items-center justify-between">
        <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">{price}</p>
      </CardContent>
    </Card>
  );
}

export default function ProductListingPage() {
  return (
    <div className="bg-gradient-to-b from-primary-50 via-white to-white dark:from-neutral-900 dark:via-neutral-950 dark:to-neutral-950">
      <section className="mx-auto flex min-h-[60vh] w-full max-w-6xl flex-col items-center justify-center px-4 py-20 text-center">
        <div className="max-w-3xl space-y-6">
          <h1 className="text-4xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100 sm:text-5xl">
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
            <Button asChild size="lg" variant="outline">
              <Link href="/referral">Explore Benefits</Link>
            </Button>
          </div>
        </div>
      </section>

      <section id="featured-products" className="mx-auto w-full max-w-6xl px-4 py-16">
        <h2 className="mb-8 text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Featured Products</h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {featuredProducts.map((product) => (
            <ProductCard key={product.id} name={product.name} price={product.price} description={product.description} />
          ))}
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-4 py-16">
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
  );
}
