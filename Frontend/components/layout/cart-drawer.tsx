"use client";

import { Button } from "@/components/ui/button";
import { useCart } from "@/components/providers/cart-context";

const inrFormatter = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });

function formatINR(value: number) {
  return inrFormatter.format(value);
}

export function CartDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { cartItems, removeFromCart, totalPrice } = useCart();

  return (
    <div className={`fixed inset-0 z-50 ${open ? "pointer-events-auto" : "pointer-events-none"}`}>
      <button
        type="button"
        aria-label="Close cart"
        onClick={onClose}
        className={`absolute inset-0 bg-black/30 transition-opacity duration-300 ${open ? "opacity-100" : "opacity-0"}`}
      />
      <aside
        className={`absolute right-0 top-0 flex h-full w-80 flex-col bg-white p-6 shadow-2xl transition-transform duration-300 dark:bg-neutral-950 ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">Your Cart</h3>
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto">
          {cartItems.length === 0 ? (
            <p className="text-sm text-neutral-500 dark:text-neutral-400">Your cart is empty.</p>
          ) : (
            cartItems.map((item) => (
              <div
                key={item.cartItemId}
                className="rounded-xl border border-neutral-200 p-3 dark:border-neutral-800"
              >
                <p className="font-medium text-neutral-900 dark:text-neutral-100">{item.name}</p>
                <p className="text-sm text-neutral-600 dark:text-neutral-300">{item.price}</p>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="mt-2 px-0 text-neutral-600 hover:bg-transparent hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-neutral-100"
                  onClick={() => removeFromCart(item.cartItemId)}
                >
                  Remove
                </Button>
              </div>
            ))
          )}
        </div>

        <div className="mt-6 border-t border-neutral-200 pt-4 dark:border-neutral-800">
          <div className="mb-4 flex items-center justify-between text-sm">
            <span className="text-neutral-600 dark:text-neutral-300">Total</span>
            <span className="font-semibold text-neutral-900 dark:text-neutral-100">{formatINR(totalPrice)}</span>
          </div>
          <Button type="button" className="w-full" disabled>
            Checkout
          </Button>
        </div>
      </aside>
    </div>
  );
}
