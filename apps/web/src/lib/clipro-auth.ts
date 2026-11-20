import { createHash, createHmac, timingSafeEqual } from "node:crypto";

export const SESSION_COOKIE = "clipro_operator_session";
export const OPERATOR_USER_ID = "00000000-0000-4000-8000-000000000001";

type Claims = { sub: string; iss: string; aud: string; iat: number; exp: number };

function secret(name: string): string {
  const value = process.env[name];
  if (!value || value.length < 32) throw new Error(name + " must be configured with at least 32 characters.");
  return value;
}

function signClaims(claims: Claims, key: string): string {
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" }), "utf8").toString("base64url");
  const payload = Buffer.from(JSON.stringify(claims), "utf8").toString("base64url");
  const signingInput = header + "." + payload;
  const signature = createHmac("sha256", key).update(signingInput).digest("base64url");
  return signingInput + "." + signature;
}

function verifyClaims(token: string, key: string, audience: string, subject: string): Claims | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const [encodedHeader, payload, signature] = parts;
    const header = JSON.parse(Buffer.from(encodedHeader, "base64url").toString("utf8")) as { alg?: string; typ?: string };
    if (header.alg !== "HS256" || header.typ !== "JWT") return null;
    const signingInput = encodedHeader + "." + payload;
    const expected = createHmac("sha256", key).update(signingInput).digest();
    const supplied = Buffer.from(signature, "base64url");
    if (supplied.length !== expected.length || !timingSafeEqual(supplied, expected)) return null;
    const claims = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as Claims;
    const now = Math.floor(Date.now() / 1000);
    if (
      claims.sub !== subject || claims.iss !== "clipro-web" || claims.aud !== audience ||
      !Number.isInteger(claims.iat) || !Number.isInteger(claims.exp) ||
      claims.iat > now + 60 || claims.exp <= now
    ) return null;
    return claims;
  } catch {
    return null;
  }
}

export function verifyOperatorPassword(candidate: unknown): boolean {
  const expected = process.env.CLIPRO_OPERATOR_PASSWORD;
  if (typeof candidate !== "string" || !expected || expected.length < 20) return false;
  const expectedDigest = createHash("sha256").update(expected, "utf8").digest();
  const candidateDigest = createHash("sha256").update(candidate, "utf8").digest();
  return timingSafeEqual(candidateDigest, expectedDigest);
}

export function createOperatorSession(): string {
  const now = Math.floor(Date.now() / 1000);
  return signClaims({ sub: "operator", iss: "clipro-web", aud: "clipro-session", iat: now, exp: now + 12 * 60 * 60 }, secret("CLIPRO_SESSION_SECRET"));
}

export function verifyOperatorSession(token: string | undefined | null): boolean {
  if (!token) return false;
  try {
    return verifyClaims(token, secret("CLIPRO_SESSION_SECRET"), "clipro-session", "operator") !== null;
  } catch {
    return false;
  }
}

export function createApiAccessToken(): string {
  const now = Math.floor(Date.now() / 1000);
  return signClaims({
    sub: OPERATOR_USER_ID, iss: "clipro-web", aud: "clipro-api", iat: now, exp: now + 5 * 60,
  }, secret("CLIPRO_API_TOKEN_SECRET"));
}
