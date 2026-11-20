import { NextResponse, type NextRequest } from "next/server";
import { createApiAccessToken, SESSION_COOKIE, verifyOperatorSession } from "@/lib/clipro-auth";

export const runtime = "nodejs";
type RouteContext = { params: Promise<{ path: string[] }> };
const UUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";

function isAllowedPath(path: string): boolean {
  return path === "api/v1/uploads" ||
    path === "api/v1/uploads/preflight" ||
    path === "api/v1/uploads/sign-request" ||
    path === "api/v1/uploads/finalize" ||
    path === "api/v1/uploads/abort" ||
    new RegExp("^api/v1/uploads/asset/" + UUID + "$", "i").test(path) ||
    new RegExp("^api/v1/jobs/" + UUID + "$", "i").test(path) ||
    new RegExp("^api/v1/jobs/" + UUID + "/dispatch$", "i").test(path) ||
    new RegExp("^api/v1/jobs/assets/" + UUID + "/analyze$", "i").test(path);
}

async function forward(request: NextRequest, context: RouteContext) {
  const origin = request.headers.get("origin");
  if (request.method !== "GET" && (!origin || origin !== new URL(request.url).origin)) {
    return NextResponse.json({ detail: "Request origin rejected." }, { status: 403 });
  }
  if (!verifyOperatorSession(request.cookies.get(SESSION_COOKIE)?.value)) {
    return NextResponse.json({ detail: "Authentication required." }, { status: 401 });
  }

  const { path: segments } = await context.params;
  const path = segments.join("/");
  if (!isAllowedPath(path)) return NextResponse.json({ detail: "API route is not available through this proxy." }, { status: 404 });

  const apiBase = process.env.CLIPRO_API_URL;
  if (!apiBase) return NextResponse.json({ detail: "The Clipro API URL is not configured on the server." }, { status: 503 });

  let target: URL;
  try {
    target = new URL(path, apiBase.endsWith("/") ? apiBase : apiBase + "/");
    target.search = request.nextUrl.search;
  } catch {
    return NextResponse.json({ detail: "The Clipro API URL is invalid." }, { status: 503 });
  }

  let token: string;
  try {
    token = createApiAccessToken();
  } catch {
    return NextResponse.json({ detail: "API token signing is not configured on the server." }, { status: 503 });
  }

  try {
    const body = request.method === "GET" ? undefined : await request.text();
    const upstream = await fetch(target, {
      method: request.method,
      cache: "no-store",
      headers: {
        Authorization: "Bearer " + token,
        ...(body === undefined ? {} : { "Content-Type": request.headers.get("content-type") ?? "application/json" }),
      },
      ...(body === undefined ? {} : { body }),
    });
    return new NextResponse(await upstream.text(), {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") ?? "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return NextResponse.json({ detail: "The Clipro API is temporarily unavailable." }, { status: 502 });
  }
}

export const GET = forward;
export const POST = forward;
