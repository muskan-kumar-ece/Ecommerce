"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCart } from "@/lib/api/cart";

export default function CartPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["cart"],
    queryFn: fetchCart,
  });

  if (isError) return <p className="text-sm text-rose-600">Unable to load cart.</p>;
  if (isLoading || !data) return <p className="text-sm text-slate-500">Loading cart...</p>;

  return (
    <section className="space-y-4">
      <h1 className="text-3xl font-semibold tracking-tight">Cart</h1>
      <div className="space-y-3">
        {data.items.map((item) => (
          <Card key={item.id}>
            <CardHeader>
              <CardTitle className="text-base">{item.product_details?.name ?? `Product #${item.product}`}</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <p className="text-sm text-slate-600">Qty: {item.quantity}</p>
              <p className="font-semibold">₹{item.product_details?.price ?? "--"}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
