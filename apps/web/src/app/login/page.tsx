"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function requestMagicLink(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const supabase = createClient();
      const result = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: window.location.origin + "/auth/callback" },
      });
      if (result.error) throw result.error;
      setMessage("Check your inbox for the secure sign-in link.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to send the sign-in link.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-shell">
      <div className="login-glow" />
      <div className="login-card">
        <div className="brand-lockup login-brand"><div className="brand-mark">C</div><div><div className="brand-name">clipro</div><div className="brand-subtitle">CREATOR STUDIO</div></div></div>
        <div className="eyebrow">YOUR EDITING WORKSPACE</div>
        <h1>Make every moment <span>count.</span></h1>
        <p className="login-copy">Sign in to manage your sources, campaigns and AI-assisted edits.</p>
        <form onSubmit={requestMagicLink} className="login-form">
          <label htmlFor="email">Email address</label>
          <input id="email" type="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" required />
          <button type="submit" disabled={busy}>{busy ? "Sending link…" : "Continue with email"} <span>→</span></button>
        </form>
        {message && <div className="notice notice-success">{message}</div>}
        {error && <div className="notice notice-error">{error}</div>}
        <div className="login-footer"><span className="shield">✓</span>Secure, passwordless sign-in powered by Supabase.</div>
      </div>
    </main>
  );
}
