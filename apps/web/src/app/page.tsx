import UploadStudio from "@/components/upload-studio";
import LogoutButton from "@/components/logout-button";

export const dynamic = "force-dynamic";

export default function HomePage() {
  const workspaceId = "00000000-0000-4000-8000-000000000002";
  const email = "Private operator";
  const initial = "C";

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
          <UploadStudio workspaceId={workspaceId} />
          <div className="bottom-note"><span className="shield">✓</span>Your media stays private. Nothing is published automatically.</div>
        </div>
      </section>
    </main>
  );
}
