import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatOrderNumber } from "@/lib/order-utils";

type OrderDetailsPageProps = {
  params: {
    orderId: string;
  };
};

export default function OrderDetailsPage({ params }: OrderDetailsPageProps) {
  const orderNumber = formatOrderNumber(params.orderId);

  return (
    <section className="mx-auto w-full max-w-3xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Order Details</h1>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">View summary and delivery details for your purchase.</p>
      </header>

      <Card className="border-neutral-200 shadow-sm dark:border-neutral-800">
        <CardHeader>
          <CardTitle>{orderNumber}</CardTitle>
          <CardDescription>Detailed line-items and invoice view will appear here.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row">
          <Button asChild>
            <Link href={`/account/orders/${params.orderId}/track`}>Track Order</Link>
          </Button>
          <Button asChild variant="secondary">
            <Link href="/account/orders">Back to Orders</Link>
          </Button>
        </CardContent>
      </Card>
    </section>
  );
}
