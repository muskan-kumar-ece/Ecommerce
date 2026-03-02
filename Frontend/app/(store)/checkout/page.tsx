"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { createOrder } from "@/lib/api/orders";
import { createRazorpayOrder } from "@/lib/api/payments";

export default function CheckoutPage() {
  const [message, setMessage] = useState<string | null>(null);

  const checkoutMutation = useMutation({
    mutationFn: async () => {
      const order = await createOrder({
        total_amount: "1.00",
        status: "pending",
        payment_status: "pending",
        tracking_id: `TRACK-${Date.now()}`,
      });
      const payment = await createRazorpayOrder({
        order_id: order.id,
        idempotency_key: `${order.id}-${Date.now()}`,
      });
      return { order, payment };
    },
    onSuccess: ({ order, payment }) => {
      setMessage(`Order #${order.id} created. Razorpay order: ${payment.razorpay_order_id}`);
    },
    onError: () => {
      setMessage("Checkout failed. Please verify API credentials.");
    },
  });

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle>Checkout</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-slate-600">Proceed with secure payment through backend checkout API.</p>
        <Button onClick={() => checkoutMutation.mutate()} disabled={checkoutMutation.isPending}>
          {checkoutMutation.isPending ? "Processing..." : "Place Order"}
        </Button>
        {message && <p className="text-sm text-slate-700">{message}</p>}
      </CardContent>
    </Card>
  );
}
