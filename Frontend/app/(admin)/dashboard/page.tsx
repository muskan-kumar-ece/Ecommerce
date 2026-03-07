"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchAdminDashboardAnalytics } from "@/lib/api/analytics";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ORDER_STATUS_META } from "@/lib/order-status";

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

const integerFormatter = new Intl.NumberFormat("en-IN");

const dateFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

function formatStatusLabel(status: string) {
  return status
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export default function AdminDashboardPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["admin-dashboard-analytics"],
    queryFn: fetchAdminDashboardAnalytics,
  });

  return (
    <section className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Admin Dashboard</h1>
        <p className="text-sm text-slate-500">Real-time overview of revenue, orders, users, and recent activity.</p>
      </header>

      {isLoading ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="text-base">
                    <Skeleton className="h-4 w-28" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-32" />
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  <Skeleton className="h-4 w-32" />
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {Array.from({ length: 5 }).map((_, index) => (
                  <Skeleton key={index} className="h-10 w-full" />
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  <Skeleton className="h-4 w-36" />
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {Array.from({ length: 6 }).map((_, index) => (
                  <Skeleton key={index} className="h-10 w-full" />
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      ) : null}

      {isError ? (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-base text-red-700">Unable to load dashboard analytics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-red-700">{error instanceof Error ? error.message : "Unknown error occurred."}</p>
            <Button onClick={() => refetch()} disabled={isFetching}>
              {isFetching ? "Retrying..." : "Retry"}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {!isLoading && !isError && data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Total Revenue</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-900">
                {currencyFormatter.format(Number(data.total_revenue))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Total Orders</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-900">
                {integerFormatter.format(data.total_orders)}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Total Users</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-900">
                {integerFormatter.format(data.total_users)}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Top Products</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b text-slate-500">
                    <tr>
                      <th className="px-2 py-3 font-medium">Product Name</th>
                      <th className="px-2 py-3 font-medium">Units Sold</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_products.map((product) => (
                      <tr key={product.product_id} className="border-b last:border-0">
                        <td className="px-2 py-3 text-slate-800">{product.name}</td>
                        <td className="px-2 py-3 font-medium text-slate-900">{integerFormatter.format(product.total_sold)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Orders</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b text-slate-500">
                    <tr>
                      <th className="px-2 py-3 font-medium">Order ID</th>
                      <th className="px-2 py-3 font-medium">Customer Email</th>
                      <th className="px-2 py-3 font-medium">Amount</th>
                      <th className="px-2 py-3 font-medium">Status</th>
                      <th className="px-2 py-3 font-medium">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_orders.map((order) => {
                      const statusMeta = ORDER_STATUS_META[order.status] ?? {
                        label: formatStatusLabel(order.status),
                        variant: "default" as const,
                      };
                      return (
                        <tr key={order.order_id} className="border-b last:border-0">
                          <td className="px-2 py-3 font-medium text-slate-900">#{order.order_id}</td>
                          <td className="px-2 py-3 text-slate-700">{order.user_email}</td>
                          <td className="px-2 py-3 font-medium text-slate-900">
                            {currencyFormatter.format(Number(order.total_amount))}
                          </td>
                          <td className="px-2 py-3">
                            <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>
                          </td>
                          <td className="px-2 py-3 text-slate-600">{dateFormatter.format(new Date(order.created_at))}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </div>
        </>
      ) : null}
    </section>
  );
}
