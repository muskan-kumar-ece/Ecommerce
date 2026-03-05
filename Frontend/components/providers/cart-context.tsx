"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";

export type CartProduct = {
  id: number;
  name: string;
  price: string;
};

export type CartItem = CartProduct & {
  cartItemId: string;
};

type CartContextValue = {
  cartItems: CartItem[];
  addToCart: (product: CartProduct) => void;
  removeFromCart: (id: string) => void;
  totalItems: number;
  totalPrice: number;
};

const CartContext = createContext<CartContextValue | undefined>(undefined);
let cartItemFallbackCounter = 0;

function parsePrice(price: string) {
  const sanitized = price.replace(/[^0-9.]/g, "");
  if ((sanitized.match(/\./g) || []).length > 1) {
    return 0;
  }
  const [whole, fraction] = sanitized.split(".");
  const normalized = fraction !== undefined ? `${whole}.${fraction}` : whole;
  return Number(normalized) || 0;
}

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [cartItems, setCartItems] = useState<CartItem[]>([]);

  const addToCart = useCallback((product: CartProduct) => {
    const cartItemId =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${product.id}-${Date.now()}-${++cartItemFallbackCounter}`;
    setCartItems((prev) => [...prev, { ...product, cartItemId }]);
  }, []);

  const removeFromCart = useCallback((id: string) => {
    setCartItems((prev) => {
      const index = prev.findIndex((item) => item.cartItemId === id);
      if (index < 0) return prev;
      return [...prev.slice(0, index), ...prev.slice(index + 1)];
    });
  }, []);

  const value = useMemo(
    () => ({
      cartItems,
      addToCart,
      removeFromCart,
      totalItems: cartItems.length,
      totalPrice: cartItems.reduce((sum, item) => sum + parsePrice(item.price), 0),
    }),
    [addToCart, cartItems, removeFromCart],
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}
