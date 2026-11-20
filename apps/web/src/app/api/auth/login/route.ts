import { NextResponse, type NextRequest } from "next/server";
import { createOperatorSession, SESSION_COOKIE, verifyOperatorPassword } from "@/lib/clipro-auth";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const origin = request.headers.get("origin");
  if (!origin || origin !== new URL(request.url).origin) {
    return NextResponse.json({ detail: "Request origin rejected." }, { status: 403 });
  }

  let password: unknown;
  try {
    const body = await request.json() as { password?: unknown };
    password = body.password;
  } catch {
    return NextResponse.json({ detail: "Invalid sign-in request." }, { status: 400 });
  }

  if (!verifyOperatorPassword(password)) {
    return NextResponse.json({ detail: "Invalid password." }, { status: 401, headers: { "Cache-Control": "no-store" } });
  }

  let session: string;
  try {
    session = createOperatorSession();
  } catch {
    return NextResponse.json({ detail: "Private access is not configured on the server." }, { status: 503 });
  }

  const response = NextResponse.json({ ok: true }, { headers: { "Cache-Control": "no-store" } });
  response.cookies.set(SESSION_COOKIE, session, {
    httpOnly: true, secure: process.env.NODE_ENV === "production",
    sameSite: "lax", path: "/", maxAge: 12 * 60 * 60,
  });
  return response;
}
