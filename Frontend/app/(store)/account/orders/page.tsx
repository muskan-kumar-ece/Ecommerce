"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchOrderItems, fetchOrders } from "@/lib/api/orders";
import { formatOrderNumber } from "@/lib/order-utils";

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

const dateFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const toNumber = (value: string) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

const getStatusMeta = (status: string) => {
  if (status === "delivered") return { label: "Delivered", variant: "success" as const };
  if (status === "shipped") return { label: "Shipped", variant: "info" as const };
  return { label: "Processing", variant: "warning" as const };
};

export default function OrdersPage() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["orders", "with-item-counts"],
    queryFn: async () => {
      const [orders, orderItems] = await Promise.all([fetchOrders(), fetchOrderItems()]);
      const itemCountByOrder = orderItems.reduce<Record<number, number>>((counts, item) => {
        counts[item.order] = (counts[item.order] ?? 0) + item.quantity;
        return counts;
      }, {});

      return orders.map((order) => {
        return {
          ...order,
          itemCount: itemCountByOrder[order.id] ?? 0,
          orderNumber: formatOrderNumber(order.id, order.tracking_id),
          statusMeta: getStatusMeta(order.status),
        };
      });
    },
  });

  return (
    <section className="mx-auto w-full max-w-5xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Your Orders</h1>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">Review past purchases and stay updated on delivery progress.</p>
      </header>

      {isLoading ? (
        <Card className="border-neutral-200 shadow-sm dark:border-neutral-800">
          <CardHeader>
            <CardTitle className="text-base">Loading your orders...</CardTitle>
          </CardHeader>
        </Card>
      ) : null}

      {isError ? (
        <Card className="border-rose-200 bg-rose-50/60 shadow-sm dark:border-rose-900/40 dark:bg-rose-900/10">
          <CardHeader>
            <CardTitle className="text-base text-rose-700 dark:text-rose-300">Unable to load your orders</CardTitle>
          </CardHeader>
          <CardContent>
            <Button variant="secondary" onClick={() => refetch()} disabled={isFetching}>
              {isFetching ? "Retrying..." : "Try Again"}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {data && data.length === 0 ? (
        <Card className="border-neutral-200 shadow-sm dark:border-neutral-800">
          <CardHeader>
            <CardTitle className="text-xl">You have no orders yet</CardTitle>
            <CardDescription>Explore premium products and place your first order today.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href="/">Start Shopping</Link>
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {data && data.length > 0 ? (
        <div className="space-y-4">
          {data.map((order) => (
            <Card key={order.id} className="border-neutral-200 shadow-sm transition-shadow hover:shadow-md dark:border-neutral-800">
              <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-xl text-neutral-900 dark:text-neutral-100">{order.orderNumber}</CardTitle>
                  <CardDescription>Ordered on {dateFormatter.format(new Date(order.created_at))}</CardDescription>
                </div>
                <Badge variant={order.statusMeta.variant} dot>
                  {order.statusMeta.label}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="grid gap-3 text-sm text-neutral-700 dark:text-neutral-300 sm:grid-cols-2">
                  <p>
                    <span className="text-neutral-500 dark:text-neutral-400">Total Amount:</span>{" "}
                    <span className="font-semibold text-neutral-900 dark:text-neutral-100">
                      {currencyFormatter.format(toNumber(order.total_amount))}
                    </span>
                  </p>
                  <p>
                    <span className="text-neutral-500 dark:text-neutral-400">Number of Items:</span>{" "}
                    <span className="font-semibold text-neutral-900 dark:text-neutral-100">{order.itemCount}</span>
                  </p>
                </div>
                <div className="flex flex-col gap-3 sm:flex-row">
                  <Button asChild>
                    <Link href={`/account/orders/${order.id}`}>View Order Details</Link>
                  </Button>
                  <Button asChild variant="secondary">
                    <Link href={`/account/orders/${order.id}/track`}>Track Order</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : null}
    </section>
  );
}
