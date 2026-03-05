import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const alertVariants = cva(
  "relative w-full rounded-lg p-4 text-sm flex gap-3 items-start border-l-4",
  {
    variants: {
      variant: {
        success:
          "border-green-500 bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-300",
        error:
          "border-red-500 bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-300",
        warning:
          "border-yellow-500 bg-yellow-50 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300",
        info: "border-primary-500 bg-primary-50 text-primary-800 dark:bg-primary-900/20 dark:text-primary-300",
      },
    },
    defaultVariants: {
      variant: "info",
    },
  },
);

export interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant, ...props }, ref) => (
    <div
      ref={ref}
      role="alert"
      className={cn(alertVariants({ variant }), className)}
      {...props}
    />
  ),
);
Alert.displayName = "Alert";

const AlertTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5 ref={ref} className={cn("font-medium leading-none tracking-tight", className)} {...props} />
));
AlertTitle.displayName = "AlertTitle";

const AlertDescription = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("text-sm [&_p]:leading-relaxed", className)} {...props} />
));
AlertDescription.displayName = "AlertDescription";

export { Alert, AlertTitle, AlertDescription, alertVariants };
