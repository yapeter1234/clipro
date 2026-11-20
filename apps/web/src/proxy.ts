import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE, verifyOperatorSession } from "@/lib/clipro-auth";

export function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  if (pathname === "/api/auth/login" || pathname === "/api/auth/logout") return NextResponse.next();

  const valid = verifyOperatorSession(request.cookies.get(SESSION_COOKIE)?.value);
  if (pathname === "/login") return valid ? NextResponse.redirect(new URL("/", request.url)) : NextResponse.next();
  if (valid) return NextResponse.next();

  if (pathname.startsWith("/api/")) {
    return NextResponse.json({ detail: "Authentication required." }, {
      status: 401, headers: { "Cache-Control": "no-store" },
    });
  }
  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
