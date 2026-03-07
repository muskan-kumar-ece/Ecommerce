"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useCart } from "@/components/providers/cart-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createOrder } from "@/lib/api/orders";
import { createRazorpayOrder, verifyRazorpayPayment } from "@/lib/api/payments";

const inrFormatter = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });
const formatCurrencyNumber = (value: number) => inrFormatter.format(value);

type RazorpaySuccessPayload = {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
};

type RazorpayFailurePayload = {
  error?: {
    description?: string;
  };
};

type RazorpayCheckoutOptions = {
  key: string;
  amount: number;
  currency: string;
  order_id: string;
  name: string;
  description: string;
  prefill?: {
    name?: string;
    email?: string;
  };
  modal?: {
    ondismiss?: () => void;
  };
  handler: (response: RazorpaySuccessPayload) => void | Promise<void>;
};

type RazorpayCheckoutInstance = {
  open: () => void;
  on: (event: "payment.failed", handler: (response: RazorpayFailurePayload) => void) => void;
};

const loadRazorpayScript = async () => {
  if (typeof window === "undefined") {
    return false;
  }
  const razorpayWindow = window as Window & {
    Razorpay?: new (options: RazorpayCheckoutOptions) => RazorpayCheckoutInstance;
  };
  if (razorpayWindow.Razorpay) {
    return true;
  }

  return new Promise<boolean>((resolve) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

function CheckoutContent() {
  const { cartItems, totalPrice } = useCart();
  const router = useRouter();
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");

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
    const trimmedName = fullName.trim();
    const trimmedEmail = email.trim();
    if (!trimmedName || !trimmedEmail) {
      setError("Please provide your name and email to continue with payment.");
      return;
    }

    try {
      setIsPlacingOrder(true);
      setError(null);

      // Aggregate cart items by product ID and calculate quantities
      const itemsMap = new Map<number, number>();
      for (const item of cartItems) {
        const currentQty = itemsMap.get(item.id) || 0;
        itemsMap.set(item.id, currentQty + 1);
      }

      // Convert to API format
      const items = Array.from(itemsMap.entries()).map(([product_id, quantity]) => ({
        product_id,
        quantity,
      }));

      // Call the createOrder API
      const order = await createOrder(items);

      const scriptLoaded = await loadRazorpayScript();
      const Razorpay = (window as Window & {
        Razorpay?: new (options: RazorpayCheckoutOptions) => RazorpayCheckoutInstance;
      }).Razorpay;
      if (!scriptLoaded || !Razorpay) {
        setError("Unable to load payment gateway. Please try again.");
        setIsPlacingOrder(false);
        return;
      }

      const idempotencyKey = `checkout-${order.id}`;
      const paymentSession = await createRazorpayOrder({
        order_id: order.id,
        idempotency_key: idempotencyKey,
      });

      const checkout = new Razorpay({
        key: paymentSession.key_id,
        amount: paymentSession.amount,
        currency: paymentSession.currency,
        order_id: paymentSession.razorpay_order_id,
        name: "Venopai Commerce",
        description: `Payment for order #${order.id}`,
        prefill: {
          name: trimmedName,
          email: trimmedEmail,
        },
        modal: {
          ondismiss: () => {
            setError("Payment was cancelled. You can retry checkout.");
            setIsPlacingOrder(false);
          },
        },
        handler: async (response) => {
          try {
            await verifyRazorpayPayment({
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_signature: response.razorpay_signature,
            });
            router.push(`/order-success?order_id=${order.id}`);
          } catch (verifyError) {
            console.error("Payment verification failed:", verifyError);
            setError(`Payment verification failed for order #${order.id}. Please contact support if amount was debited.`);
            setIsPlacingOrder(false);
          }
        },
      });

      checkout.on("payment.failed", (response) => {
        setError(response.error?.description ?? "Payment failed. Please try again.");
        setIsPlacingOrder(false);
      });
      checkout.open();
    } catch (err) {
      console.error("Failed to place order:", err);
      setError("Checkout failed. Please try again.");
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
              <Input id="fullName" placeholder="John Doe" value={fullName} onChange={(event) => setFullName(event.target.value)} />
            </div>
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm text-neutral-700 dark:text-neutral-300">
                Email
              </label>
              <Input id="email" type="email" placeholder="john@example.com" value={email} onChange={(event) => setEmail(event.target.value)} />
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
              {(() => {
                // Group cart items by product and show quantity
                const itemsMap = new Map<number, { name: string; price: string; quantity: number }>();
                for (const item of cartItems) {
                  const existing = itemsMap.get(item.id);
                  if (existing) {
                    existing.quantity += 1;
                  } else {
                    itemsMap.set(item.id, { name: item.name, price: item.price, quantity: 1 });
                  }
                }
                return Array.from(itemsMap.entries()).map(([productId, item]) => {
                  // Parse the price and calculate total for this line item
                  const sanitized = item.price.replace(/[^0-9.]/g, "");
                  const unitPrice = Number(sanitized) || 0;
                  const lineTotal = unitPrice * item.quantity;
                  
                  return (
                    <div key={productId} className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-neutral-800 dark:text-neutral-100">{item.name}</p>
                        <p className="text-xs text-neutral-500 dark:text-neutral-400">Quantity: {item.quantity}</p>
                      </div>
                      <p className="text-sm font-medium text-neutral-800 dark:text-neutral-100">{formatCurrencyNumber(lineTotal)}</p>
                    </div>
                  );
                });
              })()}
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
                {isPlacingOrder ? "Processing Payment..." : "Pay with Razorpay"}
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
