import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
  {
    variants: {
      variant: {
        default:
          "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-100",
        success:
          "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
        warning:
          "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
        danger:
          "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
        info: "bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

const dotVariants: Record<string, string> = {
  default: "bg-neutral-500 dark:bg-neutral-400",
  success: "bg-green-500 dark:bg-green-400",
  warning: "bg-yellow-500 dark:bg-yellow-400",
  danger: "bg-red-500 dark:bg-red-400",
  info: "bg-primary-500 dark:bg-primary-400",
};

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, dot = false, children, ...props }, ref) => (
    <span
      ref={ref}
      className={cn(badgeVariants({ variant, className }))}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            "mr-1.5 h-1.5 w-1.5 rounded-full",
            dotVariants[variant ?? "default"],
          )}
        />
      )}
      {children}
    </span>
  ),
);
Badge.displayName = "Badge";

export { Badge, badgeVariants };
