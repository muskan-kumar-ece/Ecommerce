"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchAdminOrder, updateAdminOrderStatus } from "@/lib/api/orders";

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

const dateTimeFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const statusBadgeMap: Record<string, { label: string; variant: "default" | "success" | "warning" | "danger" | "info" }> = {
  pending: { label: "Pending", variant: "warning" },
  confirmed: { label: "Processing", variant: "info" },
  shipped: { label: "Shipped", variant: "info" },
  delivered: { label: "Delivered", variant: "success" },
  cancelled: { label: "Cancelled", variant: "danger" },
  refunded: { label: "Refunded", variant: "default" },
  paid: { label: "Paid", variant: "success" },
};

export default function AdminOrderDetailPage() {
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const orderId = params.id;
  const { data, isLoading } = useQuery({
    queryKey: ["admin-order", orderId],
    queryFn: () => fetchAdminOrder(orderId),
    enabled: Boolean(orderId),
  });
  const { mutate, isPending } = useMutation({
    mutationFn: (payload: { status: string; payment_status?: string }) => updateAdminOrderStatus(orderId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-order", orderId] });
      queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
    },
  });

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Order #{orderId}</h1>
        <p className="text-sm text-slate-500">View order information and update fulfillment status.</p>
      </header>

      <div className="flex flex-wrap gap-2">
        <Button size="sm" onClick={() => mutate({ status: "processing" })} loading={isPending}>
          Mark as Processing
        </Button>
        <Button size="sm" variant="secondary" onClick={() => mutate({ status: "shipped" })} loading={isPending}>
          Mark as Shipped
        </Button>
        <Button size="sm" variant="secondary" onClick={() => mutate({ status: "delivered" })} loading={isPending}>
          Mark as Delivered
        </Button>
        <Button size="sm" variant="danger" onClick={() => mutate({ status: "cancelled" })} loading={isPending}>
          Cancel Order
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => mutate({ status: "refunded", payment_status: "refunded" })}
          loading={isPending}
        >
          Refund Payment
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-52 w-full" />
        </div>
      ) : null}

      {data ? (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">User Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-slate-700">
                <p>
                  <span className="font-medium text-slate-900">Name:</span> {data.user_name}
                </p>
                <p>
                  <span className="font-medium text-slate-900">Email:</span> {data.user_email}
                </p>
                <p>
                  <span className="font-medium text-slate-900">User ID:</span> {data.user}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Payment Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-slate-700">
                <p className="flex items-center gap-2">
                  <span className="font-medium text-slate-900">Payment Status:</span>
                  <Badge variant={statusBadgeMap[data.payment_status]?.variant ?? "default"}>
                    {statusBadgeMap[data.payment_status]?.label ?? data.payment_status}
                  </Badge>
                </p>
                <p>
                  <span className="font-medium text-slate-900">Order Total:</span>{" "}
                  {currencyFormatter.format(Number(data.total_amount))}
                </p>
                <p>
                  <span className="font-medium text-slate-900">Order Status:</span>{" "}
                  {statusBadgeMap[data.status]?.label ?? data.status}
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Shipping Address</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-700">
              {data.shipping_address ? (
                <div className="space-y-1">
                  <p>{data.shipping_address.full_name}</p>
                  <p>{data.shipping_address.phone_number}</p>
                  <p>{data.shipping_address.address_line_1}</p>
                  {data.shipping_address.address_line_2 ? <p>{data.shipping_address.address_line_2}</p> : null}
                  <p>
                    {data.shipping_address.city}, {data.shipping_address.state} {data.shipping_address.postal_code}
                  </p>
                  <p>{data.shipping_address.country}</p>
                </div>
              ) : (
                <p>No shipping address available for this order.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Ordered Products</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b text-slate-500">
                  <tr>
                    <th className="px-2 py-2 font-medium">Product</th>
                    <th className="px-2 py-2 font-medium">Quantity</th>
                    <th className="px-2 py-2 font-medium">Price</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="px-2 py-2">{item.product_name}</td>
                      <td className="px-2 py-2">{item.quantity}</td>
                      <td className="px-2 py-2">{currencyFormatter.format(Number(item.price))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Order Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {data.timeline.length > 0 ? (
                  data.timeline.map((event) => (
                    <li key={event.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                      <p className="font-medium text-slate-900">
                        {event.previous_status || "N/A"} → {event.new_status}
                      </p>
                      <p className="text-slate-600">
                        Payment: {event.previous_payment_status || "N/A"} → {event.new_payment_status}
                      </p>
                      <p className="text-slate-500">
                        {dateTimeFormatter.format(new Date(event.created_at))}
                        {event.changed_by_email ? ` by ${event.changed_by_email}` : ""}
                      </p>
                    </li>
                  ))
                ) : (
                  <li className="rounded-lg border border-slate-200 p-3 text-sm text-slate-600">
                    Order created on {dateTimeFormatter.format(new Date(data.created_at))}
                  </li>
                )}
              </ul>
            </CardContent>
          </Card>

          <Button asChild variant="secondary">
            <Link href="/admin/orders">Back to orders</Link>
          </Button>
        </>
      ) : null}
    </section>
  );
}
