import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatOrderNumber } from "@/lib/order-utils";

type TrackOrderPageProps = {
  params: {
    orderId: string;
  };
};

export default function TrackOrderPage({ params }: TrackOrderPageProps) {
  const orderNumber = formatOrderNumber(params.orderId);

  return (
    <section className="mx-auto w-full max-w-3xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">Track Order</h1>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">Latest shipment updates for {orderNumber}.</p>
      </header>

      <Card className="border-neutral-200 shadow-sm dark:border-neutral-800">
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <CardTitle>{orderNumber}</CardTitle>
            <CardDescription>Shipment timeline integration will appear here.</CardDescription>
          </div>
          <Badge variant="info" dot>
            In Transit
          </Badge>
        </CardHeader>
        <CardContent>
          <Button asChild variant="secondary">
            <Link href="/account/orders">Back to Orders</Link>
          </Button>
        </CardContent>
      </Card>
    </section>
  );
}
