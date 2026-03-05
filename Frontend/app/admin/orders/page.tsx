"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchAdminOrders } from "@/lib/api/orders";
import { ORDER_STATUS_META, PAYMENT_STATUS_META } from "@/lib/order-status";

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

export default function AdminOrdersPage() {
  const [status, setStatus] = useState("");
  const [date, setDate] = useState("");
  const [search, setSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["admin-orders", status, date, search],
    queryFn: () => fetchAdminOrders({ status, date, search }),
  });

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Order Management</h1>
        <p className="text-sm text-slate-500">Monitor and manage customer orders from one dashboard.</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Filters</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            className="h-10 rounded-xl border border-slate-200 px-3 text-sm"
          >
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="shipped">Shipped</option>
            <option value="delivered">Delivered</option>
            <option value="cancelled">Cancelled</option>
            <option value="refunded">Refunded</option>
          </select>
          <Input type="date" value={date} onChange={(event) => setDate(event.target.value)} />
          <Input
            type="text"
            placeholder="Search by order id or user email"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Orders</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={index} className="h-11 w-full" />
              ))}
            </div>
          ) : (
            <table className="min-w-full text-left text-sm">
              <thead className="border-b text-slate-500">
                <tr>
                  <th className="px-2 py-3 font-medium">Order ID</th>
                  <th className="px-2 py-3 font-medium">User Email</th>
                  <th className="px-2 py-3 font-medium">Total</th>
                  <th className="px-2 py-3 font-medium">Payment</th>
                  <th className="px-2 py-3 font-medium">Order Status</th>
                  <th className="px-2 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {data?.map((order) => {
                  const orderMeta = ORDER_STATUS_META[order.status] ?? { label: order.status, variant: "default" as const };
                  const paymentMeta = PAYMENT_STATUS_META[order.payment_status] ?? {
                    label: order.payment_status,
                    variant: "default" as const,
                  };
                  return (
                    <tr key={order.id} className="border-b last:border-0 hover:bg-slate-50">
                      <td className="px-2 py-3">
                        <Link href={`/admin/orders/${order.id}`} className="font-medium text-slate-900 hover:underline">
                          #{order.id}
                        </Link>
                      </td>
                      <td className="px-2 py-3 text-slate-700">{order.user_email}</td>
                      <td className="px-2 py-3 font-medium text-slate-900">{currencyFormatter.format(Number(order.total_amount))}</td>
                      <td className="px-2 py-3">
                        <Badge variant={paymentMeta.variant}>{paymentMeta.label}</Badge>
                      </td>
                      <td className="px-2 py-3">
                        <Badge variant={orderMeta.variant}>{orderMeta.label}</Badge>
                      </td>
                      <td className="px-2 py-3 text-slate-600">{dateFormatter.format(new Date(order.created_at))}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
