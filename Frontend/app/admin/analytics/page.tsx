"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchAnalyticsSummary } from "@/lib/api/analytics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
});

const integerFormatter = new Intl.NumberFormat("en-IN");

function toNumber(value: string) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export default function AdminAnalyticsDashboardPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["admin-analytics-summary"],
    queryFn: fetchAnalyticsSummary,
  });

  const chartData = useMemo(() => {
    if (!data) return [];

    const todayRevenue = toNumber(data.today_revenue);
    const total7DayRevenue = toNumber(data.last_7_days_revenue);
    const previousSixTotal = Math.max(total7DayRevenue - todayRevenue, 0);
    const averagePreviousDay = previousSixTotal / 6;

    return [
      { label: "D-6", value: averagePreviousDay },
      { label: "D-5", value: averagePreviousDay },
      { label: "D-4", value: averagePreviousDay },
      { label: "D-3", value: averagePreviousDay },
      { label: "D-2", value: averagePreviousDay },
      { label: "D-1", value: averagePreviousDay },
      { label: "Today", value: todayRevenue },
    ];
  }, [data]);

  const maxRevenue = Math.max(...chartData.map((item) => item.value), 1);

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Admin Analytics Dashboard</h1>
        <p className="text-sm text-slate-500">High-level business metrics for orders, revenue, and refunds.</p>
      </header>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {Array.from({ length: 5 }).map((_, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle className="text-base">Loading...</CardTitle>
              </CardHeader>
              <CardContent className="h-8 animate-pulse rounded bg-slate-100" />
            </Card>
          ))}
        </div>
      ) : null}

      {isError ? (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-base text-red-700">Could not load analytics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-red-700">{error instanceof Error ? error.message : "Unknown error"}</p>
            <Button onClick={() => refetch()} disabled={isFetching}>
              {isFetching ? "Retrying..." : "Retry"}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {!isLoading && !isError && data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Total Revenue</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-800">
                {currencyFormatter.format(toNumber(data.total_revenue))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Total Orders</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-800">
                {integerFormatter.format(data.total_orders)}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Refund Rate</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-800">{data.refund_rate_percent}%</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Today Revenue</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-800">
                {currencyFormatter.format(toNumber(data.today_revenue))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">7 Day Revenue</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-800">
                {currencyFormatter.format(toNumber(data.last_7_days_revenue))}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Revenue (Last 7 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex h-64 items-end gap-3 rounded-xl bg-slate-50 p-4">
                {chartData.map((item) => {
                  const heightPercent = (item.value / maxRevenue) * 100;
                  return (
                    <div key={item.label} className="flex min-w-0 flex-1 flex-col items-center gap-2">
                      <div className="text-xs text-slate-500">{currencyFormatter.format(item.value)}</div>
                      <div className="flex h-44 w-full items-end">
                        <div
                          className="w-full rounded-t-md bg-slate-900"
                          style={{ height: `${Math.max(heightPercent, 8)}%` }}
                        />
                      </div>
                      <div className="text-xs text-slate-500">{item.label}</div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </>
      ) : null}
    </section>
  );
}
