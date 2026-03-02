import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const metrics = ["Orders", "Revenue", "Pending", "Low Stock"];

export default function AdminDashboardPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Operations Dashboard</h1>
        <p className="text-sm text-slate-500">No adminpanel API endpoints are currently exposed in API_CONTRACT.md.</p>
      </header>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric}>
            <CardHeader>
              <CardTitle className="text-base">{metric}</CardTitle>
            </CardHeader>
            <CardContent className="text-2xl font-semibold text-slate-700">--</CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
