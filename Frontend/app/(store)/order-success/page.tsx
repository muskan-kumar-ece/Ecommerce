import Link from "next/link";
import { CheckCircle } from "lucide-react";
import { randomInt } from "crypto";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type OrderSuccessPageProps = {
  searchParams?: {
    order?: string;
  };
};

const orderPattern = /^VN-\d{5}$/;

export default function OrderSuccessPage({ searchParams }: OrderSuccessPageProps) {
  const requestedOrder = searchParams?.order ?? "";
  const orderNumber = orderPattern.test(requestedOrder)
    ? requestedOrder
    : `VN-${randomInt(0, 100000).toString().padStart(5, "0")}`;

  return (
    <div className="flex min-h-[calc(100vh-14rem)] items-center justify-center">
      <Card className="w-full max-w-xl border-neutral-200 shadow-xl shadow-neutral-200/40 dark:border-neutral-700 dark:shadow-black/20">
        <CardHeader className="items-center space-y-4 text-center">
          <CheckCircle className="h-16 w-16 text-emerald-500" aria-hidden="true" />
          <CardTitle className="text-3xl">Order Confirmed</CardTitle>
          <CardDescription className="max-w-md text-base text-neutral-600 dark:text-neutral-300">
            Your order has been placed successfully. We&apos;ll start preparing it
            right away.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="border-t border-neutral-200 pt-6 dark:border-neutral-800">
            <dl className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <dt className="text-sm text-neutral-600 dark:text-neutral-300">Order Number</dt>
                <dd className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">{orderNumber}</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-sm text-neutral-600 dark:text-neutral-300">Estimated Delivery</dt>
                <dd className="text-sm font-medium text-neutral-900 dark:text-neutral-100">3–5 business days</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-sm text-neutral-600 dark:text-neutral-300">Payment Status</dt>
                <dd className="text-sm font-medium text-emerald-600 dark:text-emerald-400">Paid</dd>
              </div>
            </dl>
          </div>

          <div className="border-t border-neutral-200 pt-6 text-sm text-neutral-600 dark:border-neutral-800 dark:text-neutral-300">
            We&apos;ve sent a confirmation email with your order details.
          </div>

          <div className="border-t border-neutral-200 pt-6 dark:border-neutral-800">
            <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
              <Button asChild size="lg" className="w-full transition-transform hover:-translate-y-0.5 sm:w-auto">
                <Link href="/">Continue Shopping</Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="secondary"
                className="w-full transition-transform hover:-translate-y-0.5 sm:w-auto"
              >
                <Link href="/account/orders">View Orders</Link>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
