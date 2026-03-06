"use client";

import { Star } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type ReviewCardProps = {
  userName: string;
  rating: number;
  title: string;
  comment: string;
  createdAt: string;
};

export function ReviewCard({ userName, rating, title, comment, createdAt }: ReviewCardProps) {
  const createdDate = new Date(createdAt);
  const createdDateText = Number.isNaN(createdDate.getTime())
    ? "Unknown date"
    : createdDate.toLocaleDateString("en-IN", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });

  return (
    <Card className="h-full">
      <CardHeader className="space-y-3 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="text-base">{userName}</CardTitle>
          <Badge variant="info">{createdDateText}</Badge>
        </div>
        <div className="flex items-center gap-1" aria-label={`Rating ${rating} out of 5`}>
          {Array.from({ length: 5 }, (_, index) => (
            <Star
              key={index}
              className={cn(
                "h-4 w-4",
                index < rating ? "fill-yellow-500 text-yellow-500" : "text-neutral-300 dark:text-neutral-600",
              )}
            />
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <p className="mb-2 text-sm font-semibold text-neutral-800 dark:text-neutral-100">{title}</p>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">{comment}</p>
      </CardContent>
    </Card>
  );
}
