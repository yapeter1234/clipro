import UploadStudio from "@/components/upload-studio";

export const dynamic = "force-dynamic";

export default function HomePage() {
  const workspaceId = "00000000-0000-4000-8000-000000000002";

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup"><div className="brand-mark">C</div><div><div className="brand-name">clipro</div><div className="brand-subtitle">CREATOR STUDIO</div></div></div>
        <div className="workspace-chip"><span className="workspace-dot" /><span>Public prototype workspace</span><span className="workspace-chevron">⌄</span></div>
        <div className="nav-label">WORKSPACE</div>
        <nav className="side-nav">
          <a className="nav-item active" href="#new-upload"><span className="nav-icon">＋</span>New project</a>
          <a className="nav-item muted" href="#recent"><span className="nav-icon">▤</span>Media library</a>
          <a className="nav-item muted" href="#campaign"><span className="nav-icon">◈</span>Campaigns</a>
        </nav>
        <div className="sidebar-bottom">
          <div className="plan-card"><div className="plan-title">Try AI-assisted clipping</div><div className="plan-description">Upload a video to validate it and discover potential highlights.</div></div>
          <div className="user-row"><div className="avatar">P</div><div className="user-copy"><div className="user-email">Public prototype</div><div className="user-role">Shared workspace</div></div></div>
        </div>
      </aside>
      <section className="main-panel">
        <header className="topbar"><div className="breadcrumbs"><span>Workspace</span><span className="crumb-separator">/</span><strong>New project</strong></div><div className="topbar-right"><span className="status-indicator"><i />MANUAL REVIEW ENABLED</span><span className="user-avatar-small">P</span></div></header>
        <div className="page-content">
          <div className="page-heading"><div><div className="eyebrow">SOURCE INTAKE · PUBLIC PROTOTYPE</div><h1>Turn footage into <span>standout clips.</span></h1><p className="page-intro">Upload a video you have permission to edit. Clipro validates it and identifies promising moments for short-form clips.</p></div><div className="heading-step"><span className="step-number">01</span><span>New source</span><span className="step-line" /><span className="step-number future">02</span><span className="future">AI edit</span></div></div>
          <UploadStudio workspaceId={workspaceId} />
          <div className="bottom-note"><span className="shield">ℹ</span>Public prototype: uploads are processed in a shared workspace. Review your video before publishing.</div>
        </div>
      </section>
    </main>
  );
}
