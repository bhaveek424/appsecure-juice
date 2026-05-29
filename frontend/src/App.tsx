import { useEffect, useState } from "react";
import {
  fetchConfig,
  fetchHealth,
  type BackendConfig,
  type HealthResponse,
} from "./api";
import { LoadingState } from "./components/WorkbenchState";
import ReviewRunsPanel from "./ReviewRunsPanel";
import "./App.css";

const HEALTH_POLL_MS = 3_000;

type LoadState =
  | { kind: "loading" }
  | {
      kind: "ready";
      health: HealthResponse;
      config: BackendConfig;
      waitingForDependencies: boolean;
    }
  | { kind: "error"; message: string };

export default function App() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    let config: BackendConfig | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        if (!config) {
          config = await fetchConfig();
        }
        const health = await fetchHealth();
        if (cancelled) {
          return;
        }

        const waitingForDependencies = health.status !== "ok";
        setState({ kind: "ready", health, config, waitingForDependencies });

        if (waitingForDependencies) {
          timer = setTimeout(poll, HEALTH_POLL_MS);
        }
      } catch (error) {
        if (cancelled) {
          return;
        }
        const message =
          error instanceof Error ? error.message : "Unknown error";
        setState({ kind: "error", message });
        timer = setTimeout(poll, HEALTH_POLL_MS);
      }
    }

    poll();

    return () => {
      cancelled = true;
      if (timer !== undefined) {
        clearTimeout(timer);
      }
    };
  }, []);

  const backendReady =
    state.kind === "ready" && state.health.status === "ok";

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
        {state.kind === "loading" && (
          <LoadingState label="Loading backend configuration…" />
        )}
        {state.kind === "error" && (
          <p className="status-bad" role="alert">
            Backend unreachable — {state.message}. Retrying…
          </p>
        )}
        {state.kind === "ready" && (
          <>
            <p
              className={
                state.health.status === "ok" ? "status-good" : "status-bad"
              }
            >
              {state.health.status === "ok"
                ? "Connected"
                : state.waitingForDependencies
                  ? "Starting dependencies…"
                  : "Degraded — check dependencies"}
            </p>
            <dl>
              <div>
                <dt>Target Application</dt>
                <dd>{state.config.target_application_url}</dd>
              </div>
              <div>
                <dt>Juice Shop reachable</dt>
                <dd>
                  {state.health.dependencies.target_application.reachable
                    ? "Yes"
                    : "No"}
                </dd>
              </div>
              <div>
                <dt>ZAP reachable</dt>
                <dd>
                  {state.health.dependencies.zap.reachable ? "Yes" : "No"}
                </dd>
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

      {state.kind === "ready" && (
        <ReviewRunsPanel backendReady={backendReady} />
      )}
    </div>
  );
}
