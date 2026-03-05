 "use client";

import Link from "next/link";
import { CheckCircle } from "lucide-react";
import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function OrderSuccessPage() {
  const orderNumber = useMemo(
    () => `VN-${Math.floor(10000 + Math.random() * 90000)}`,
    [],
  );

  return (
    <div className="flex min-h-[calc(100vh-14rem)] items-center justify-center">
      <Card className="w-full max-w-xl border-neutral-200 shadow-xl shadow-neutral-200/40 dark:border-neutral-700 dark:shadow-black/20">
        <CardHeader className="items-center space-y-4 text-center">
          <CheckCircle className="h-16 w-16 text-emerald-500" aria-hidden="true" />
          <CardTitle className="text-3xl">Order Confirmed</CardTitle>
          <CardDescription className="max-w-md text-base text-neutral-600 dark:text-neutral-300">
            Thank you for your purchase. We&apos;ve received your order and will
            send an update as soon as it ships.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 text-center">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-neutral-500 dark:text-neutral-400">
            Order Number
          </p>
          <p className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
            {orderNumber}
          </p>
          <Button asChild size="lg" className="w-full sm:w-auto">
            <Link href="/">Continue Shopping</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
