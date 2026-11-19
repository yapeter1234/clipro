import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { createClient } from "@/lib/supabase/server";
import UploadStudio from "@/components/upload-studio";
import LogoutButton from "@/components/logout-button";

export const dynamic = "force-dynamic";

function ConfigurationMessage() {
  return (
    <main className="setup-screen"><div className="setup-card">
      <div className="brand-lockup"><div className="brand-mark">C</div><div><div className="brand-name">clipro</div><div className="brand-subtitle">CREATOR STUDIO</div></div></div>
      <div className="eyebrow">FIRST-TIME SETUP</div>
      <h1>Connect your workspace.</h1>
      <p>Set the Supabase project URL and publishable key in the web app environment, apply the Clipro database migration, then reload this page.</p>
      <a className="text-link" href="https://supabase.com/dashboard">Open Supabase dashboard ↗</a>
    </div></main>
  );
}

export default async function HomePage() {
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY) return <ConfigurationMessage />;

  const supabase = await createClient();
  const auth = await supabase.auth.getUser();
  if (auth.error || !auth.data.user) redirect("/login");

  const membership = await supabase
    .from("workspace_memberships")
    .select("workspace_id, role, created_at")
    .eq("user_id", auth.data.user.id)
    .order("created_at", { ascending: true })
    .limit(1);

  const workspaceId = membership.data?.[0]?.workspace_id as string | undefined;
  const email = auth.data.user.email ?? "Signed in";
  const initial = (email[0] ?? "U").toUpperCase();

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup"><div className="brand-mark">C</div><div><div className="brand-name">clipro</div><div className="brand-subtitle">CREATOR STUDIO</div></div></div>
        <div className="workspace-chip"><span className="workspace-dot" /><span>Personal workspace</span><span className="workspace-chevron">⌄</span></div>
        <div className="nav-label">WORKSPACE</div>
        <nav className="side-nav">
          <a className="nav-item active" href="#new-upload"><span className="nav-icon">＋</span>New project</a>
          <a className="nav-item muted" href="#recent"><span className="nav-icon">▤</span>Media library</a>
          <a className="nav-item muted" href="#campaign"><span className="nav-icon">◈</span>Campaigns</a>
        </nav>
        <div className="sidebar-bottom">
          <div className="plan-card"><div className="plan-title">Your editing workspace</div><div className="plan-description">Upload a clip to start your first AI-assisted edit.</div></div>
          <div className="user-row"><div className="avatar">{initial}</div><div className="user-copy"><div className="user-email">{email}</div><div className="user-role">Workspace owner</div></div><LogoutButton /></div>
        </div>
      </aside>
      <section className="main-panel">
        <header className="topbar"><div className="breadcrumbs"><span>Workspace</span><span className="crumb-separator">/</span><strong>New project</strong></div><div className="topbar-right"><span className="status-indicator"><i />MANUAL REVIEW ENABLED</span><span className="user-avatar-small">{initial}</span></div></header>
        <div className="page-content">
          <div className="page-heading"><div><div className="eyebrow">SOURCE INTAKE · M1</div><h1>Turn footage into <span>standout clips.</span></h1><p className="page-intro">Bring in a stream clip or an authorized video. Clipro validates it before analysis and editing.</p></div><div className="heading-step"><span className="step-number">01</span><span>New source</span><span className="step-line" /><span className="step-number future">02</span><span className="future">AI edit</span></div></div>
          {membership.error || !workspaceId ? <div className="notice notice-warning"><strong>Workspace setup required</strong><p>{membership.error?.message ?? "No workspace membership was found. Apply the Clipro Supabase migration, then sign out and sign in again."}</p></div> : <UploadStudio workspaceId={workspaceId} />}
          <div className="bottom-note"><span className="shield">✓</span>Your media stays private. Nothing is published automatically.</div>
        </div>
      </section>
    </main>
  );
}
