"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const toastVariants = cva(
  "rounded-lg shadow-lg p-4 w-[360px] border flex gap-3 items-start opacity-0 translate-x-full motion-safe:transition-all motion-safe:duration-200 motion-safe:ease-out",
  {
    variants: {
      variant: {
        success:
          "border-green-200 bg-green-50 text-green-800 dark:border-green-800/40 dark:bg-green-900/20 dark:text-green-300",
        error:
          "border-red-200 bg-red-50 text-red-800 dark:border-red-800/40 dark:bg-red-900/20 dark:text-red-300",
        warning:
          "border-yellow-200 bg-yellow-50 text-yellow-800 dark:border-yellow-800/40 dark:bg-yellow-900/20 dark:text-yellow-300",
        info: "border-primary-200 bg-primary-50 text-primary-800 dark:border-primary-800/40 dark:bg-primary-900/20 dark:text-primary-300",
      },
    },
    defaultVariants: {
      variant: "info",
    },
  },
);

export interface ToastProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "title">,
    VariantProps<typeof toastVariants> {
  title?: React.ReactNode;
  description?: React.ReactNode;
  onClose?: () => void;
  exiting?: boolean;
}

const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({ className, variant, title, description, onClose, exiting, ...props }, ref) => {
    const [isVisible, setIsVisible] = React.useState(false);

    React.useEffect(() => {
      const frameId = window.requestAnimationFrame(() => setIsVisible(true));
      return () => window.cancelAnimationFrame(frameId);
    }, []);

    return (
      <div
        ref={ref}
        className={cn(
          toastVariants({ variant }),
          exiting ? "translate-x-full opacity-0" : isVisible && "translate-x-0 opacity-100",
          className,
        )}
        {...props}
      >
        <div className="flex-1 space-y-1">
          {title ? <p className="font-medium leading-none">{title}</p> : null}
          {description ? <p className="text-sm opacity-90">{description}</p> : null}
        </div>
        <button
          type="button"
          aria-label="Close toast"
          className="opacity-70 hover:opacity-100 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current focus-visible:ring-offset-2 ring-offset-background rounded-sm"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  },
);
Toast.displayName = "Toast";

export { Toast, toastVariants };
