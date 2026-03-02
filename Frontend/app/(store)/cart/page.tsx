"use client";

import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCart } from "@/lib/api/cart";
import type { Cart } from "@/lib/api/types";

export default function CartPage() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCart().then(setCart).catch(() => setError("Unable to load cart."));
  }, []);

  if (error) return <p className="text-sm text-rose-600">{error}</p>;
  if (!cart) return <p className="text-sm text-slate-500">Loading cart...</p>;

  return (
    <section className="space-y-4">
      <h1 className="text-3xl font-semibold tracking-tight">Cart</h1>
      <div className="space-y-3">
        {cart.items.map((item) => (
          <Card key={item.id}>
            <CardHeader>
              <CardTitle className="text-base">{item.product.name}</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <p className="text-sm text-slate-600">Qty: {item.quantity}</p>
              <p className="font-semibold">₹{item.product.price}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
