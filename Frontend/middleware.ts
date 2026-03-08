import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function redirectToLogin(request: NextRequest) {
  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("next", request.nextUrl.pathname);
  return NextResponse.redirect(loginUrl);
}

export async function middleware(request: NextRequest) {
  const token = request.cookies.get("access_token")?.value;

  if (!token) {
    return redirectToLogin(request);
  }

  const requiresAdminAccess =
    request.nextUrl.pathname.startsWith("/admin") || request.nextUrl.pathname.startsWith("/dashboard");

  if (requiresAdminAccess) {
    try {
      // Use the dedicated read-only /users/me/ endpoint to check staff status.
      // This avoids the previous approach of making a write (POST) request to
      // the products endpoint, which was semantically incorrect and fragile.
      const response = await fetch(`${API_BASE_URL}/api/v1/users/me/`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        return redirectToLogin(request);
      }

      if (!response.ok) {
        // Unexpected error – deny access rather than silently allow
        return NextResponse.redirect(new URL("/", request.url));
      }

      const user = await response.json() as { is_staff?: boolean };
      if (!user.is_staff) {
        return NextResponse.redirect(new URL("/", request.url));
      }
    } catch (error) {
      console.error("Admin route staff check failed", error);
      return NextResponse.redirect(new URL("/", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/cart/:path*", "/checkout/:path*", "/referral/:path*", "/admin/:path*", "/dashboard/:path*"],
};
