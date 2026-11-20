"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }), cache: "no-store",
      });
      if (!response.ok) {
        const result = await response.json().catch(() => ({})) as { detail?: string };
        throw new Error(result.detail ?? "Unable to sign in.");
      }
      setPassword("");
      router.replace("/");
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-shell">
      <div className="login-glow" />
      <div className="login-card">
        <div className="brand-lockup login-brand"><div className="brand-mark">C</div><div><div className="brand-name">clipro</div><div className="brand-subtitle">CREATOR STUDIO</div></div></div>
        <div className="eyebrow">PRIVATE OPERATOR ACCESS</div>
        <h1>Welcome <span>back.</span></h1>
        <p className="login-copy">This Clipro workspace is private. Enter your operator password to continue.</p>
        <form onSubmit={signIn} className="login-form">
          <label htmlFor="password">Operator password</label>
          <input id="password" type="password" value={password} onChange={event => setPassword(event.target.value)} placeholder="Enter your password" autoComplete="current-password" required />
          <button type="submit" disabled={busy || !password}>{busy ? "Signing in…" : "Unlock Clipro"} <span>→</span></button>
        </form>
        {error && <div className="notice notice-error">{error}</div>}
        <div className="login-footer"><span className="shield">✓</span>Private access · No public accounts or sign-ups.</div>
      </div>
    </main>
  );
}
