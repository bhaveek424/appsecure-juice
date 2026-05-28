import { useCallback, useEffect, useState } from "react";
import {
  createScan,
  getScan,
  isActiveReviewRun,
  listScans,
  runReviewSkill,
  type ScanDetail,
  type ScanSummary,
} from "./api";
import FindingDetailPanel from "./FindingDetailPanel";
import FindingsList from "./FindingsList";
import ReviewQueue from "./ReviewQueue";
import SkillRunsPanel from "./SkillRunsPanel";

const SCAN_POLL_MS = 3_000;

type Props = {
  backendReady: boolean;
};

function formatTimestamp(value: string | null): string {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleString();
}

function totalFindings(counts: ScanSummary["finding_counts"]): number {
  return (
    counts.critical +
    counts.high +
    counts.medium +
    counts.low +
    counts.informational
  );
}

export default function ReviewRunsPanel({ backendReady }: Props) {
  const [history, setHistory] = useState<ScanSummary[]>([]);
  const [activeDetail, setActiveDetail] = useState<ScanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(
    null,
  );
  const [runningSkillId, setRunningSkillId] = useState<string | null>(null);

  const activeSummary = history.find((run) => isActiveReviewRun(run.status));
  const activeRun = activeDetail ?? activeSummary ?? null;
  const activeScanId = activeDetail?.id ?? activeSummary?.id;

  const refresh = useCallback(async () => {
    const runs = await listScans();
    setHistory(runs);

    const activeSummary = runs.find((run) => isActiveReviewRun(run.status));
    if (activeSummary) {
      const detail = await getScan(activeSummary.id);
      setActiveDetail(detail);
    } else {
      setActiveDetail(null);
    }
  }, []);

  useEffect(() => {
    if (!backendReady) {
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function load() {
      try {
        await refresh();
        if (!cancelled) {
          setError(null);
        }
      } catch (loadError) {
        if (!cancelled) {
          const message =
            loadError instanceof Error ? loadError.message : "Unknown error";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
          timer = setTimeout(load, SCAN_POLL_MS);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
      if (timer !== undefined) {
        clearTimeout(timer);
      }
    };
  }, [backendReady, refresh]);

  async function handleStartScan() {
    setStarting(true);
    setError(null);
    try {
      const created = await createScan();
      const detail = await getScan(created.id);
      setActiveDetail(detail);
      await refresh();
    } catch (startError) {
      const message =
        startError instanceof Error ? startError.message : "Unknown error";
      setError(message);
    } finally {
      setStarting(false);
    }
  }

  const startDisabled =
    !backendReady || starting || activeRun !== null;

  const canRunSkills = activeDetail?.status === "Ready For Skills";

  async function handleRunSkill(skillId: string) {
    if (!activeScanId) {
      return;
    }
    setRunningSkillId(skillId);
    setError(null);
    try {
      await runReviewSkill(activeScanId, skillId);
      await refresh();
    } catch (runError) {
      const message =
        runError instanceof Error ? runError.message : "Unknown error";
      setError(message);
    } finally {
      setRunningSkillId(null);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Review Runs</h2>
        <button
          type="button"
          className="primary-button"
          disabled={startDisabled}
          onClick={handleStartScan}
        >
          {starting ? "Starting…" : "Start Review Run"}
        </button>
      </div>

      {loading && <p>Loading Review Runs…</p>}
      {error && <p className="status-bad">{error}</p>}

      {activeRun && (
        <div className="active-run">
          <h3>Active Review Run</h3>
          <dl>
            <div>
              <dt>Status</dt>
              <dd>{activeRun.status}</dd>
            </div>
            <div>
              <dt>Current step</dt>
              <dd>{activeRun.current_step}</dd>
            </div>
            {activeDetail?.progress !== null &&
              activeDetail?.progress !== undefined && (
              <div>
                <dt>Progress</dt>
                <dd>
                  <progress
                    max={1}
                    value={activeDetail.progress}
                  />
                  <span>{Math.round(activeDetail.progress * 100)}%</span>
                </dd>
              </div>
            )}
          </dl>
          {activeDetail && activeDetail.hypotheses.length > 0 && (
            <ReviewQueue
              hypotheses={activeDetail.hypotheses}
              canRunSkills={canRunSkills}
              runningSkillId={runningSkillId}
              onRunSkill={handleRunSkill}
            />
          )}
          {activeDetail && activeDetail.skill_runs.length > 0 && (
            <SkillRunsPanel
              skillRuns={activeDetail.skill_runs}
              onSelectFinding={setSelectedFindingId}
            />
          )}
          {activeDetail && activeDetail.findings.length > 0 && (
            <FindingsList
              findings={activeDetail.findings}
              findingCounts={activeSummary?.finding_counts}
              onSelectFinding={setSelectedFindingId}
            />
          )}
        </div>
      )}

      {activeScanId && selectedFindingId && (
        <FindingDetailPanel
          scanId={activeScanId}
          findingId={selectedFindingId}
          onClose={() => setSelectedFindingId(null)}
          onUpdated={refresh}
        />
      )}

      <div className="scan-history">
        <h3>History</h3>
        {history.length === 0 ? (
          <p className="muted">No Review Runs yet.</p>
        ) : (
          <ul>
            {history.map((run) => (
              <li key={run.id}>
                <span className="run-status">{run.status}</span>
                <span className="run-step">{run.current_step}</span>
                <span className="run-time">{formatTimestamp(run.started_at)}</span>
                <span className="run-findings">
                  {totalFindings(run.finding_counts)} findings
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
