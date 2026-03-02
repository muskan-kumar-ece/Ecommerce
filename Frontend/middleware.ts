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

  if (request.nextUrl.pathname.startsWith("/admin")) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/products/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "text/plain",
        },
        body: "permission-check",
      });

      if (response.status === 401) {
        return redirectToLogin(request);
      }

      if (response.status === 403) {
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
  matcher: ["/cart/:path*", "/checkout/:path*", "/referral/:path*", "/admin/:path*"],
};
