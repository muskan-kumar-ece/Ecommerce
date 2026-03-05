"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AxiosError } from "axios";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Timeline } from "@/components/ui/timeline";
import { cancelOrder, fetchOrder } from "@/lib/api/orders";
import { retryPayment, verifyRazorpayPayment } from "@/lib/api/payments";
import { fetchProducts } from "@/lib/api/products";
import { ORDER_STATUS_META, PAYMENT_STATUS_META } from "@/lib/order-status";
import { formatOrderNumber } from "@/lib/order-utils";

type OrderDetailsPageProps = {
  params: {
    orderId: string;
  };
};

const ORDER_DATE_LOCALE = "en-IN";
const currencyFormatter = new Intl.NumberFormat(ORDER_DATE_LOCALE, {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});
const dateTimeFormatter = new Intl.DateTimeFormat(ORDER_DATE_LOCALE, {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const toTitleCase = (value: string) =>
  value
    .replaceAll("_", " ")
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

const toNumber = (value: string) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

type RazorpayOptions = {
  key: string;
  amount: number;
  currency: string;
  order_id: string;
  name: string;
  description: string;
  handler: (response: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }) => void;
};

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => { open: () => void };
  }
}

const loadRazorpayScript = async () => {
  if (typeof window === "undefined") return false;
  if (window.Razorpay) return true;
  return new Promise<boolean>((resolve) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

export default function OrderDetailsPage({ params }: OrderDetailsPageProps) {
  const queryClient = useQueryClient();
  const [retryError, setRetryError] = useState<string | null>(null);
  const [retrySuccess, setRetrySuccess] = useState<string | null>(null);
  const orderNumber = formatOrderNumber(params.orderId);
  const { data: order, isLoading } = useQuery({
    queryKey: ["order", params.orderId],
    queryFn: () => fetchOrder(params.orderId),
  });
  const { data: products } = useQuery({
    queryKey: ["products", "for-order-detail", params.orderId],
    queryFn: fetchProducts,
    enabled: Boolean(order),
  });

  const productNameById = new Map((products ?? []).map((product) => [product.id, product.name]));
  const isPaymentConfirmed = order?.payment_status === "paid" || order?.payment_status === "refunded";
  const hasOutForDeliveryEvent = Boolean(
    order?.shipping_events?.some((event) => event.event_type === "out_for_delivery"),
  );
  const isCancellationBlocked = ["shipped", "delivered", "cancelled", "refunded"].includes(order?.status ?? "");
  const timeline = [
    { label: "Order placed", completed: Boolean(order?.created_at), timestamp: order?.created_at },
    {
      label: "Payment confirmed",
      completed: isPaymentConfirmed,
      timestamp: isPaymentConfirmed ? order?.updated_at : null,
    },
    { label: "Shipped", completed: Boolean(order?.shipped_at), timestamp: order?.shipped_at },
    { label: "Out for delivery", completed: hasOutForDeliveryEvent, timestamp: null },
    { label: "Delivered", completed: Boolean(order?.delivered_at), timestamp: order?.delivered_at },
  ];

  const cancelOrderMutation = useMutation({
    mutationFn: () => cancelOrder(params.orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order", params.orderId] });
      queryClient.invalidateQueries({ queryKey: ["my-orders"] });
    },
  });
  const retryMutation = useMutation({
    mutationFn: async () => {
      const session = await retryPayment(params.orderId);
      const isScriptLoaded = await loadRazorpayScript();
      if (!isScriptLoaded || !window.Razorpay) {
        throw new Error("Unable to load payment gateway. Please try again.");
      }
      return session;
    },
    onSuccess: (session) => {
      setRetryError(null);
      const checkout = new window.Razorpay!({
        key: session.key_id,
        amount: session.amount,
        currency: session.currency,
        order_id: session.razorpay_order_id,
        name: "Venopai Commerce",
        description: `Retry payment for ${orderNumber}`,
        handler: async (response) => {
          try {
            await verifyRazorpayPayment(response);
            setRetrySuccess("Payment retry was successful.");
            queryClient.invalidateQueries({ queryKey: ["order", params.orderId] });
            queryClient.invalidateQueries({ queryKey: ["my-orders"] });
          } catch {
            setRetryError("Payment verification failed. Please retry once more.");
          }
        },
      });
      checkout.open();
    },
    onError: (error) => {
      setRetrySuccess(null);
      const apiError = error as AxiosError<{ detail?: string }>;
      if (apiError.response?.data?.detail) {
        setRetryError(apiError.response.data.detail);
        return;
      }
      if (error instanceof Error) {
        setRetryError(error.message);
        return;
      }
      setRetryError("Unable to start payment retry.");
    },
  });

  const handleDownloadInvoice = () => {
    if (!order) return;
    const lineItems = order.items?.map((item) => {
      const productName = productNameById.get(item.product) ?? `Product #${item.product}`;
      return `${productName} | Qty: ${item.quantity} | Price: ${item.price}`;
    }) ?? [];
    const invoiceText = [
      `Invoice - ${orderNumber}`,
      `Order ID: ${order.id}`,
      `Created: ${dateTimeFormatter.format(new Date(order.created_at))}`,
      `Payment Status: ${PAYMENT_STATUS_META[order.payment_status]?.label ?? order.payment_status}`,
      `Order Total: ${currencyFormatter.format(toNumber(order.total_amount))}`,
      `Tracking ID: ${order.tracking_id ?? "Pending assignment"}`,
      "",
      "Items:",
      ...lineItems,
    ].join("\n");

    const blob = new Blob([invoiceText], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `invoice-${order.id}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCancelOrder = () => {
    if (isCancellationBlocked || cancelOrderMutation.isPending) return;
    cancelOrderMutation.mutate();
  };
  const handleRetryPayment = () => {
    if (!order || retryMutation.isPending) return;
    setRetryError(null);
    setRetrySuccess(null);
    retryMutation.mutate();
  };

  return (
    <section className="mx-auto w-full max-w-5xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Order Details</h1>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">Review items, payment and shipping updates for this order.</p>
      </header>

      <Card className="border-neutral-200 shadow-sm dark:border-neutral-800">
        <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <p className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">{orderNumber}</p>
            <p className="text-sm text-neutral-600 dark:text-neutral-300">
              Ordered on {order?.created_at ? dateTimeFormatter.format(new Date(order.created_at)) : "—"}
            </p>
            <div className="flex flex-wrap gap-2">
              <Badge variant={ORDER_STATUS_META[order?.status ?? ""]?.variant ?? "default"}>
                {ORDER_STATUS_META[order?.status ?? ""]?.label ?? order?.status ?? "Unknown"}
              </Badge>
              <Badge variant={PAYMENT_STATUS_META[order?.payment_status ?? ""]?.variant ?? "default"}>
                {PAYMENT_STATUS_META[order?.payment_status ?? ""]?.label ?? order?.payment_status ?? "Unknown"}
              </Badge>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-2 text-sm text-neutral-700 dark:text-neutral-300 sm:text-right">
            <p>
              <span className="text-neutral-500 dark:text-neutral-400">Order Total:</span>{" "}
              <span className="font-semibold">{currencyFormatter.format(toNumber(order?.total_amount ?? "0"))}</span>
            </p>
            <p>
              <span className="text-neutral-500 dark:text-neutral-400">Tracking ID:</span> {order?.tracking_id ?? "Pending assignment"}
            </p>
          </div>
        </CardContent>
      </Card>
      {order?.payment_status === "failed" ? (
        <Alert variant="error">
          <div>
            <AlertTitle>Payment Failed</AlertTitle>
            <AlertDescription>
              Your previous payment attempt failed. You can retry payment for this order up to 3 times.
            </AlertDescription>
          </div>
        </Alert>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="border-neutral-200 shadow-sm dark:border-neutral-800 lg:col-span-2">
          <CardHeader>
            <CardTitle>Products purchased</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            {isLoading ? (
              <p className="text-sm text-neutral-600 dark:text-neutral-300">Loading order items...</p>
            ) : (
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-neutral-200 text-neutral-500 dark:border-neutral-800 dark:text-neutral-400">
                  <tr>
                    <th className="py-2 pr-3 font-medium">Product</th>
                    <th className="py-2 pr-3 font-medium">Quantity</th>
                    <th className="py-2 font-medium">Price</th>
                  </tr>
                </thead>
                <tbody>
                  {(order?.items ?? []).map((item) => (
                    <tr key={item.id} className="border-b border-neutral-100 last:border-0 dark:border-neutral-800">
                      <td className="py-3 pr-3">{productNameById.get(item.product) ?? `Product #${item.product}`}</td>
                      <td className="py-3 pr-3">{item.quantity}</td>
                      <td className="py-3">{currencyFormatter.format(toNumber(item.price))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>

        <Card className="border-neutral-200 shadow-sm dark:border-neutral-800">
          <CardHeader>
            <CardTitle>Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button className="w-full" onClick={handleDownloadInvoice} disabled={!order}>
              Download Invoice
            </Button>
            {order?.payment_status === "failed" ? (
              <Button className="w-full" onClick={handleRetryPayment} disabled={retryMutation.isPending}>
                {retryMutation.isPending ? "Starting Retry..." : "Retry Payment"}
              </Button>
            ) : null}
            <Button
              className="w-full"
              variant="secondary"
              onClick={handleCancelOrder}
              disabled={!order || isCancellationBlocked || cancelOrderMutation.isPending}
            >
              {cancelOrderMutation.isPending ? "Cancelling..." : "Cancel Order"}
            </Button>
            {isCancellationBlocked ? (
              <p className="text-xs text-neutral-500 dark:text-neutral-400">Cancellation is no longer available for this order.</p>
            ) : null}
            {retryError ? <p className="text-xs text-rose-600 dark:text-rose-400">{retryError}</p> : null}
            {retrySuccess ? <p className="text-xs text-emerald-600 dark:text-emerald-400">{retrySuccess}</p> : null}
          </CardContent>
        </Card>
      </div>

      <Card className="border-neutral-200 shadow-sm dark:border-neutral-800">
        <CardHeader>
          <CardTitle>Shipping timeline</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-neutral-600 dark:text-neutral-300">Loading shipping updates...</p>
          ) : (
            <Timeline
              items={timeline}
              formatTimestamp={(value) => dateTimeFormatter.format(new Date(value))}
            />
          )}
        </CardContent>
      </Card>

      {order?.shipping_events && order.shipping_events.length > 0 ? (
        <Card className="border-neutral-200 shadow-sm dark:border-neutral-800">
          <CardHeader>
            <CardTitle>Shipment events</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {order.shipping_events.map((event) => (
              <div key={event.id} className="rounded-md border border-neutral-200 p-3 text-sm dark:border-neutral-800">
                <p className="font-medium text-neutral-900 dark:text-neutral-100">{toTitleCase(event.event_type)}</p>
                <p className="text-neutral-500 dark:text-neutral-400">{dateTimeFormatter.format(new Date(event.timestamp))}</p>
                {event.location ? <p className="text-neutral-600 dark:text-neutral-300">{event.location}</p> : null}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      <div className="flex flex-col gap-3 sm:flex-row">
        <Button asChild variant="secondary">
          <Link href="/account/orders">Back to Orders</Link>
        </Button>
      </div>
    </section>
  );
}
