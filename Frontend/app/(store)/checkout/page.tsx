"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useCart } from "@/components/providers/cart-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createOrder } from "@/lib/api/orders";

const inrFormatter = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });
const formatCurrencyNumber = (value: number) => inrFormatter.format(value);
const toCurrency = (price: string) => {
  const sanitized = price.replace(/[^0-9.]/g, "");
  if ((sanitized.match(/\./g) || []).length > 1) {
    return formatCurrencyNumber(0);
  }
  const value = Number(sanitized);
  return formatCurrencyNumber(Number.isFinite(value) ? value : 0);
};

function CheckoutContent() {
  const { cartItems, totalPrice } = useCart();
  const router = useRouter();
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (cartItems.length === 0) {
    return (
      <Card className="mx-auto max-w-2xl border-neutral-200 shadow-sm">
        <CardHeader>
          <CardTitle>Your cart is empty</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-neutral-600 dark:text-neutral-300">
            Add products to your cart before proceeding to checkout.
          </p>
          <Button asChild variant="secondary">
            <Link href="/">Back to Home</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  const handlePlaceOrder = async () => {
    try {
      setIsPlacingOrder(true);
      setError(null);

      // Convert cart items to the format expected by the API
      const items = cartItems.map((item) => ({
        product_id: item.id,
        quantity: 1, // Each cart item represents 1 quantity in this simple cart
      }));

      // Call the createOrder API
      const order = await createOrder(items);

      // Redirect to order success page
      router.push(`/order-success?order=${order.id}`);
    } catch (err) {
      console.error("Failed to place order:", err);
      setError("Failed to place order. Please try again.");
      setIsPlacingOrder(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-6xl space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Checkout</h1>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">
          Complete your details to review and place your order.
        </p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
        <Card className="border-neutral-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-xl">Customer Information</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label htmlFor="fullName" className="mb-1.5 block text-sm text-neutral-700 dark:text-neutral-300">
                Full Name
              </label>
              <Input id="fullName" placeholder="John Doe" />
            </div>
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm text-neutral-700 dark:text-neutral-300">
                Email
              </label>
              <Input id="email" type="email" placeholder="john@example.com" />
            </div>
            <div>
              <label htmlFor="phone" className="mb-1.5 block text-sm text-neutral-700 dark:text-neutral-300">
                Phone
              </label>
              <Input id="phone" type="tel" placeholder="+91 98765 43210" />
            </div>
            <div className="sm:col-span-2">
              <label htmlFor="address" className="mb-1.5 block text-sm text-neutral-700 dark:text-neutral-300">
                Address
              </label>
              <Input id="address" placeholder="Street address" />
            </div>
            <div>
              <label htmlFor="city" className="mb-1.5 block text-sm text-neutral-700 dark:text-neutral-300">
                City
              </label>
              <Input id="city" placeholder="Mumbai" />
            </div>
            <div>
              <label htmlFor="postalCode" className="mb-1.5 block text-sm text-neutral-700 dark:text-neutral-300">
                Postal Code
              </label>
              <Input id="postalCode" placeholder="400001" />
            </div>
            <div className="sm:col-span-2">
              <label htmlFor="country" className="mb-1.5 block text-sm text-neutral-700 dark:text-neutral-300">
                Country
              </label>
              <Input id="country" placeholder="India" />
            </div>
          </CardContent>
        </Card>

        <Card className="h-fit border-neutral-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-xl">Order Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              {cartItems.map((item) => (
                <div key={item.cartItemId} className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-neutral-800 dark:text-neutral-100">{item.name}</p>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">Quantity: 1</p>
                  </div>
                  <p className="text-sm font-medium text-neutral-800 dark:text-neutral-100">{toCurrency(item.price)}</p>
                </div>
              ))}
            </div>
            <div className="border-t border-neutral-200 pt-4 dark:border-neutral-800">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-sm text-neutral-600 dark:text-neutral-300">Total</span>
                <span className="font-semibold text-neutral-900 dark:text-neutral-100">{formatCurrencyNumber(totalPrice)}</span>
              </div>
              {error && (
                <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-600 dark:bg-red-950/30 dark:text-red-400">
                  {error}
                </div>
              )}
              <Button 
                type="button" 
                fullWidth 
                onClick={handlePlaceOrder}
                disabled={isPlacingOrder}
              >
                {isPlacingOrder ? "Placing Order..." : "Place Order"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function CheckoutPage() {
  return <CheckoutContent />;
}
