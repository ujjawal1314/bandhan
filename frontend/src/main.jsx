import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const statusCards = [
  {
    label: "Frontend Running",
    detail: "React + Vite",
    icon: "◇",
    state: "Ready",
  },
  {
    label: "Backend Connected",
    detail: "FastAPI service",
    icon: "↗",
    state: "Checking",
    backend: true,
  },
  {
    label: "Docker Running",
    detail: "Container environment",
    icon: "□",
    state: "Ready",
  },
  {
    label: "PostgreSQL Ready",
    detail: "Database service",
    icon: "○",
    state: "Ready",
  },
];

function App() {
  const [backendReady, setBackendReady] = useState(false);

  useEffect(() => {
    fetch("/api/health")
      .then((response) => response.ok && setBackendReady(true))
      .catch(() => setBackendReady(false));
  }, []);

  return (
    <main className="app-shell">
      <nav className="topbar" aria-label="Primary navigation">
        <a className="brand" href="#home" aria-label="Bandhan home">
          <span className="brand-mark">B</span>
          <span>
            <strong>BANDHAN</strong>
            <small>LOAN MANAGEMENT</small>
          </span>
        </a>
        <span className="review-label">REVIEW 01 · SYSTEM STATUS</span>
      </nav>

      <section className="hero" id="home">
        <p className="eyebrow">LOAN RECOVERY WORKFLOW</p>
        <h1>Bandhan</h1>
        <p className="subtitle">
          Intelligent Loan Recovery Workflow Management System Using AI-Based
          Risk Prediction
        </p>
        <button type="button" className="login-button">Login <span>→</span></button>
      </section>

      <section className="status-section" aria-labelledby="status-heading">
        <div className="section-heading">
          <div>
            <p className="eyebrow">DEPLOYMENT OVERVIEW</p>
            <h2 id="status-heading">System Status</h2>
          </div>
          <span className="live-indicator"><i /> Review environment</span>
        </div>

        <div className="card-grid">
          {statusCards.map((card) => {
            const ready = card.backend ? backendReady : true;
            return (
              <article className="status-card" key={card.label}>
                <div className="card-topline">
                  <span className="card-icon">{card.icon}</span>
                  <span className={ready ? "badge is-ready" : "badge is-pending"}>
                    {card.backend ? (ready ? "Connected" : card.state) : card.state}
                  </span>
                </div>
                <h3>{card.label}</h3>
                <p>{card.detail}</p>
                <div className="status-line"><span className={ready ? "dot" : "dot pending"} /> {ready ? "Operational" : "Waiting for API"}</div>
              </article>
            );
          })}
        </div>
      </section>

      <footer>© 2026 Bandhan · Software Engineering Review 1</footer>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
