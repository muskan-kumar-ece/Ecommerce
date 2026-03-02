import { SiteShell } from "@/components/layout/site-shell";

export default function StoreLayout({ children }: { children: React.ReactNode }) {
  return <SiteShell>{children}</SiteShell>;
}
