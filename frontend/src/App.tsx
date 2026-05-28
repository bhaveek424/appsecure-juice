import { useEffect, useState } from "react";
import "./App.css";

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type BackendConfig = {
  target_application_url: string;
  llm_provider: string;
  llm_configured: boolean;
};

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; healthy: boolean; config: BackendConfig }
  | { kind: "error"; message: string };

export default function App() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [healthRes, configRes] = await Promise.all([
          fetch(`${apiBase}/health`),
          fetch(`${apiBase}/api/config`),
        ]);

        if (!healthRes.ok || !configRes.ok) {
          throw new Error("Backend returned an error");
        }

        const healthy = (await healthRes.json()).status === "ok";
        const config = (await configRes.json()) as BackendConfig;

        if (!cancelled) {
          setState({ kind: "ready", healthy, config });
        }
      } catch (error) {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Unknown error";
          setState({ kind: "error", message });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="workbench">
      <header>
        <p className="eyebrow">Black-Box Review</p>
        <h1>AppSec Review Workbench</h1>
        <p className="lede">
          OWASP Juice Shop review workbench with scanner output and bounded
          business-logic skills.
        </p>
      </header>

      <section className="panel">
        <h2>Backend</h2>
        {state.kind === "loading" && <p>Checking connectivity…</p>}
        {state.kind === "error" && (
          <p className="status-bad">Unreachable — {state.message}</p>
        )}
        {state.kind === "ready" && (
          <>
            <p className={state.healthy ? "status-good" : "status-bad"}>
              {state.healthy ? "Connected" : "Unhealthy"}
            </p>
            <dl>
              <div>
                <dt>Target Application</dt>
                <dd>{state.config.target_application_url}</dd>
              </div>
              <div>
                <dt>LLM provider</dt>
                <dd>
                  {state.config.llm_provider}
                  {state.config.llm_configured ? " (API key set)" : " (mock)"}
                </dd>
              </div>
            </dl>
          </>
        )}
      </section>
    </div>
  );
}
