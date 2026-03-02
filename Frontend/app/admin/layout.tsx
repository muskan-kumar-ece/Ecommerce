import Link from "next/link";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-100">
      <div className="mx-auto grid max-w-7xl gap-4 px-4 py-6 md:grid-cols-[220px_1fr]">
        <aside className="rounded-2xl border border-slate-200 bg-white p-4">
          <h2 className="mb-4 text-lg font-semibold">Admin</h2>
          <nav className="space-y-2 text-sm text-slate-600">
            <Link href="/admin">Dashboard</Link>
            <div className="block">Orders</div>
            <div className="block">Products</div>
            <div className="block">Payments</div>
          </nav>
        </aside>
        <main className="rounded-2xl border border-slate-200 bg-white p-6">{children}</main>
      </div>
    </div>
  );
}
