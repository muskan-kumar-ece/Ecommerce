import { SiteShell } from "@/components/layout/site-shell";
import { CartProvider } from "@/components/providers/cart-context";

export default function StoreLayout({ children }: { children: React.ReactNode }) {
  return (
    <CartProvider>
      <SiteShell>{children}</SiteShell>
    </CartProvider>
  );
}
