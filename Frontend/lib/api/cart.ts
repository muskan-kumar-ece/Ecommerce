import { apiClient } from "@/lib/api/client";
import type { Cart, CartItem, Product } from "@/lib/api/types";

export type CartItemWithProduct = CartItem & {
  product_details?: Product;
};

export type CartView = {
  cart: Cart | null;
  items: CartItemWithProduct[];
};

export async function fetchCart() {
  const [{ data: carts }, { data: cartItems }, { data: products }] = await Promise.all([
    apiClient.get<Cart[]>("/api/v1/orders/carts/"),
    apiClient.get<CartItem[]>("/api/v1/orders/cart-items/"),
    apiClient.get<Product[]>("/api/v1/products/"),
  ]);

  const activeCart = carts.find((cart) => cart.is_active) ?? null;
  const productsById = new Map(products.map((product) => [product.id, product]));
  const items = activeCart
    ? cartItems.filter((item) => item.cart === activeCart.id).map((item) => ({
        ...item,
        product_details: productsById.get(item.product),
      }))
    : [];

  return { cart: activeCart, items };
}
