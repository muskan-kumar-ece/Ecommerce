"use client";

import * as React from "react";

import { Toast } from "@/components/ui/toast";
import { useToast } from "@/components/ui/use-toast";

function ToastProvider() {
  const { toasts, dismiss } = useToast();

  return (
    <div
      aria-live="polite"
      className="fixed top-4 right-4 z-50 flex flex-col gap-3 pointer-events-none"
    >
      {toasts.map((item) => (
        <Toast
          key={item.id}
          variant={item.variant}
          title={item.title}
          description={item.description}
          onClose={() => dismiss(item.id)}
          className="pointer-events-auto"
        />
      ))}
    </div>
  );
}

export { ToastProvider };
