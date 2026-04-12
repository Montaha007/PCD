import AppSidebar from "../components/AppSidebar";
import "./Profile.css";

export default function AppSection({ title, description }) {
  return (
    <div className="wellness-shell">
      <AppSidebar />
      <main className="wellness-content">
        <section className="section-panel">
          <p className="section-chip">Workspace</p>
          <h1 className="section-title-main">{title}</h1>
          <p className="section-copy">{description}</p>

          <div className="section-grid">
            <article className="section-card">
              <h2>Overview</h2>
              <p>
                This area is ready for your {title.toLowerCase()} widgets. The sidebar is now
                in place so you can add each feature block step by step.
              </p>
            </article>
            <article className="section-card">
              <h2>Next Step</h2>
              <p>
                Connect the API and place your charts, logs, and actions here while preserving
                the same visual style across the app.
              </p>
            </article>
          </div>
        </section>
      </main>
    </div>
  );
}
