"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { createCheckoutSession } from "@/lib/api/orders";

export default function CheckoutPage() {
  const [message, setMessage] = useState<string | null>(null);

  const onCheckout = async () => {
    try {
      const data = await createCheckoutSession({ payment_method: "razorpay" });
      setMessage(`Order #${data.order_id} created.`);
      if (data.payment_redirect_url) {
        window.location.assign(data.payment_redirect_url);
      }
    } catch {
      setMessage("Checkout failed. Please verify API credentials.");
    }
  };

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle>Checkout</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-slate-600">Proceed with secure payment through backend checkout API.</p>
        <Button onClick={onCheckout}>Place Order</Button>
        {message && <p className="text-sm text-slate-700">{message}</p>}
      </CardContent>
    </Card>
  );
}
