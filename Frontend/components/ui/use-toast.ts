"use client";

import * as React from "react";

export type ToastVariant = "success" | "error" | "warning" | "info";

export interface ToastInput {
  title?: React.ReactNode;
  description?: React.ReactNode;
  variant?: ToastVariant;
}

export interface ToastItem extends ToastInput {
  id: string;
}

interface ToastState {
  toasts: ToastItem[];
}

const TOAST_LIMIT = 4;
const TOAST_DURATION = 4000;

let count = 0;
let memoryState: ToastState = { toasts: [] };
const listeners = new Set<(state: ToastState) => void>();

function emit(state: ToastState) {
  memoryState = state;
  listeners.forEach((listener) => listener(memoryState));
}

function dismiss(id: string) {
  emit({
    toasts: memoryState.toasts.filter((toast) => toast.id !== id),
  });
}

function toast({ title, description, variant = "info" }: ToastInput) {
  const id = `${++count}`;

  emit({
    toasts: [{ id, title, description, variant }, ...memoryState.toasts].slice(0, TOAST_LIMIT),
  });

  window.setTimeout(() => dismiss(id), TOAST_DURATION);
  return id;
}

function useToast() {
  const [state, setState] = React.useState<ToastState>(memoryState);

  React.useEffect(() => {
    listeners.add(setState);
    return () => {
      listeners.delete(setState);
    };
  }, []);

  return {
    ...state,
    toast,
    dismiss,
  };
}

export { useToast, toast, dismiss };
