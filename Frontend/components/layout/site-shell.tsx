import Link from "next/link";

export function SiteShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-neutral-200/70 bg-white/80 backdrop-blur dark:border-neutral-700/70 dark:bg-neutral-900/80">
        <div className="mx-auto flex h-16 max-w-[1280px] items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="text-lg font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">
            Venopai
          </Link>
          <nav className="flex items-center gap-5 text-sm text-neutral-600 dark:text-neutral-300">
            <Link href="/">Products</Link>
            <Link href="/cart">Cart</Link>
            <Link href="/checkout">Checkout</Link>
            <Link href="/referral">Referral</Link>
            <Link href="/admin">Admin</Link>
            <Link href="/login">Login</Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1280px] px-4 py-8 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
