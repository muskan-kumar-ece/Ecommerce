"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Timeline } from "@/components/ui/timeline";
import { fetchOrder } from "@/lib/api/orders";
import { formatOrderNumber } from "@/lib/order-utils";

type OrderDetailsPageProps = {
  params: {
    orderId: string;
  };
};

const ORDER_DATE_LOCALE = "en-IN";
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

export default function OrderDetailsPage({ params }: OrderDetailsPageProps) {
  const orderNumber = formatOrderNumber(params.orderId);
  const { data: order, isLoading } = useQuery({
    queryKey: ["order", params.orderId],
    queryFn: () => fetchOrder(params.orderId),
  });

  const hasOutForDeliveryEvent = Boolean(
    order?.shipping_events?.some((event) => event.event_type === "out_for_delivery"),
  );
  const isPaymentConfirmed = order?.payment_status === "paid" || order?.payment_status === "refunded";
  const timeline = [
    { label: "Order placed", completed: Boolean(order?.created_at), time: order?.created_at },
    {
      label: "Payment confirmed",
      completed: isPaymentConfirmed,
      time: isPaymentConfirmed ? order?.updated_at : null,
    },
    { label: "Shipped", completed: Boolean(order?.shipped_at), time: order?.shipped_at },
    { label: "Out for delivery", completed: hasOutForDeliveryEvent, time: null },
    { label: "Delivered", completed: Boolean(order?.delivered_at), time: order?.delivered_at },
  ];

  return (
    <section className="mx-auto w-full max-w-3xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Order Details</h1>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">View summary and delivery details for your purchase.</p>
      </header>

      <Card className="border-neutral-200 shadow-sm dark:border-neutral-800">
        <CardHeader>
          <CardTitle>{orderNumber}</CardTitle>
          <CardDescription>Shipping timeline</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-neutral-600 dark:text-neutral-300">Loading order details...</p>
          ) : (
            <Timeline
              items={timeline.map((step) => ({ ...step, timestamp: step.time }))}
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

      <Card className="border-neutral-200 shadow-sm dark:border-neutral-800">
        <CardHeader>
          <CardTitle>Tracking details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm text-neutral-700 dark:text-neutral-300">
          <p>Tracking ID: {order?.tracking_id ?? "Pending assignment"}</p>
          <p>Provider: {order?.shipping_provider ?? "Pending assignment"}</p>
        </CardContent>
      </Card>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Button asChild>
          <Link href={`/account/orders/${params.orderId}/track`}>Track Order</Link>
        </Button>
        <Button asChild variant="secondary">
          <Link href="/account/orders">Back to Orders</Link>
        </Button>
      </div>
    </section>
  );
}
