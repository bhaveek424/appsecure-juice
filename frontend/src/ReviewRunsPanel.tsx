import { useCallback, useEffect, useState } from "react";
import {
  cancelReviewRun,
  createScan,
  getScan,
  isActiveReviewRun,
  listScans,
  runRecommendedSkills,
  runReviewSkill,
  type ScanDetail,
  type ScanSummary,
} from "./api";
import {
  EmptyState,
  ErrorBanner,
  LoadingState,
} from "./components/WorkbenchState";
import FindingDetailPanel from "./FindingDetailPanel";
import FindingsList from "./FindingsList";
import ReviewQueue from "./ReviewQueue";
import SkillRunsPanel from "./SkillRunsPanel";
import {
  isFailedReviewRun,
  reviewRunPanelTitle,
  shouldShowActiveRunBanner,
} from "./workbench/reviewRunView";

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
  const [historyLoading, setHistoryLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(
    null,
  );
  const [runningSkillId, setRunningSkillId] = useState<string | null>(null);
  const [runningRecommended, setRunningRecommended] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [followActiveRun, setFollowActiveRun] = useState(true);

  const activeSummary = history.find((run) => isActiveReviewRun(run.status));
  const selectedSummary =
    selectedRunId === null
      ? null
      : history.find((run) => run.id === selectedRunId) ?? null;
  const displayedSummary = selectedSummary ?? activeSummary ?? null;
  const displayedRun = activeDetail ?? displayedSummary ?? null;
  const displayedRunId = activeDetail?.id ?? displayedSummary?.id;
  const skillWorkActive = runningSkillId !== null || runningRecommended;

  const loadRunDetail = useCallback(
    async (runId: string, options?: { showLoading?: boolean }) => {
      const showLoading = options?.showLoading ?? false;
      if (showLoading) {
        setDetailLoading(true);
      }
      try {
        const detail = await getScan(runId);
        setActiveDetail(detail);
        setError(null);
      } catch (loadError) {
        const message =
          loadError instanceof Error ? loadError.message : "Unknown error";
        setError(message);
      } finally {
        if (showLoading) {
          setDetailLoading(false);
        }
      }
    },
    [],
  );

  const refresh = useCallback(
    async (options?: {
      preferredRunId?: string;
      followActive?: boolean;
      showDetailLoading?: boolean;
    }) => {
      const runs = await listScans();
      setHistory(runs);

      const currentActive = runs.find((run) => isActiveReviewRun(run.status));
      const shouldFollow =
        options?.followActive !== undefined
          ? options.followActive
          : followActiveRun;

      let targetId: string | undefined;
      if (shouldFollow && currentActive) {
        targetId = currentActive.id;
        setSelectedRunId(currentActive.id);
        setFollowActiveRun(true);
      } else if (options?.preferredRunId) {
        targetId = options.preferredRunId;
        setSelectedRunId(options.preferredRunId);
      } else if (
        selectedRunId !== null &&
        runs.some((run) => run.id === selectedRunId)
      ) {
        targetId = selectedRunId;
      } else if (currentActive) {
        targetId = currentActive.id;
        setSelectedRunId(currentActive.id);
        setFollowActiveRun(true);
      }

      if (targetId) {
        await loadRunDetail(targetId, {
          showLoading: options?.showDetailLoading ?? false,
        });
      } else {
        setActiveDetail(null);
      }
    },
    [followActiveRun, loadRunDetail, selectedRunId],
  );

  useEffect(() => {
    if (!backendReady) {
      setHistoryLoading(false);
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function load(initial: boolean) {
      try {
        if (initial) {
          setHistoryLoading(true);
        }
        await refresh({ showDetailLoading: initial });
      } catch (loadError) {
        if (!cancelled) {
          const message =
            loadError instanceof Error ? loadError.message : "Unknown error";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          if (initial) {
            setHistoryLoading(false);
          }
          timer = setTimeout(() => load(false), SCAN_POLL_MS);
        }
      }
    }

    load(true);

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
      setFollowActiveRun(true);
      setSelectedRunId(created.id);
      await refresh({
        preferredRunId: created.id,
        followActive: true,
        showDetailLoading: true,
      });
    } catch (startError) {
      const message =
        startError instanceof Error ? startError.message : "Unknown error";
      setError(message);
    } finally {
      setStarting(false);
    }
  }

  async function handleSelectRun(runId: string) {
    setSelectedRunId(runId);
    setFollowActiveRun(runId === activeSummary?.id);
    setSelectedFindingId(null);
    if (activeDetail?.id !== runId) {
      setActiveDetail(null);
    }
    await loadRunDetail(runId, { showLoading: true });
  }

  async function handleBackToActiveRun() {
    if (!activeSummary) {
      return;
    }
    setFollowActiveRun(true);
    setSelectedRunId(activeSummary.id);
    setSelectedFindingId(null);
    if (activeDetail?.id !== activeSummary.id) {
      setActiveDetail(null);
    }
    await loadRunDetail(activeSummary.id, { showLoading: true });
  }

  const startDisabled =
    !backendReady || starting || historyLoading || activeSummary !== null;

  const isFailed = displayedRun ? isFailedReviewRun(displayedRun.status) : false;
  const canRunSkills =
    activeDetail?.status === "Ready For Skills" &&
    !isFailed &&
    displayedRun?.status !== "Cancelled";
  const canCancel =
    displayedRunId !== undefined &&
    displayedRun !== null &&
    isActiveReviewRun(displayedRun.status) &&
    !cancelling &&
    !skillWorkActive;

  const showActiveBanner = shouldShowActiveRunBanner({
    selectedRunId,
    activeRunId: activeSummary?.id,
  });

  async function handleCancelReviewRun() {
    if (!displayedRunId) {
      return;
    }
    setCancelling(true);
    setError(null);
    try {
      await cancelReviewRun(displayedRunId);
      setFollowActiveRun(false);
      setSelectedRunId(displayedRunId);
      await refresh({ preferredRunId: displayedRunId, followActive: false });
    } catch (cancelError) {
      const message =
        cancelError instanceof Error ? cancelError.message : "Unknown error";
      setError(message);
    } finally {
      setCancelling(false);
    }
  }

  async function handleRunRecommendedSkills() {
    if (!displayedRunId) {
      return;
    }
    setRunningRecommended(true);
    setError(null);
    try {
      await runRecommendedSkills(displayedRunId);
      await refresh();
    } catch (runError) {
      const message =
        runError instanceof Error ? runError.message : "Unknown error";
      setError(message);
    } finally {
      setRunningRecommended(false);
    }
  }

  async function handleRunSkill(skillId: string) {
    if (!displayedRunId) {
      return;
    }
    setRunningSkillId(skillId);
    setError(null);
    try {
      await runReviewSkill(displayedRunId, skillId);
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
    <section className="panel review-runs-panel">
      <div className="panel-header">
        <h2>Review Runs</h2>
        <button
          type="button"
          className="primary-button"
          disabled={startDisabled}
          onClick={handleStartScan}
        >
          {starting ? "Starting Review Run…" : "Start Review Run"}
        </button>
      </div>

      {historyLoading && (
        <LoadingState label="Loading Review Run history…" />
      )}
      {error && (
        <ErrorBanner
          title="Review workbench request failed"
          message={error}
        />
      )}

      {!historyLoading && history.length === 0 && !displayedRun && (
        <EmptyState
          title="No Review Runs yet"
          description="Start a Review Run to scan the Target Application, run Agent Triage, and probe recommended Review Skills."
        />
      )}

      {displayedRun && (
        <div
          className={`active-run${
            displayedRun.status === "Cancelled" ? " active-run-cancelled" : ""
          }${isFailed ? " active-run-failed" : ""}`}
        >
          {detailLoading && !activeDetail && (
            <LoadingState label="Loading Review Run detail…" />
          )}

          {activeDetail && (
            <>
              <div className="active-run-header">
                <h3>{reviewRunPanelTitle(displayedRun.status)}</h3>
                {canCancel && (
                  <button
                    type="button"
                    className="danger-button"
                    disabled={cancelling || skillWorkActive}
                    onClick={handleCancelReviewRun}
                  >
                    {cancelling ? "Cancelling…" : "Cancel Review Run"}
                  </button>
                )}
              </div>

              {showActiveBanner && activeSummary && (
                <div className="active-run-context-banner">
                  <p>
                    Viewing Review Run history. Active Review Run is{" "}
                    <strong>{activeSummary.status}</strong> (
                    {activeSummary.current_step}).
                  </p>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={handleBackToActiveRun}
                  >
                    Return to active Review Run
                  </button>
                </div>
              )}

              {isFailed && (
                <ErrorBanner
                  title="Review Run failed"
                  message={
                    displayedRun.current_step ||
                    "This Review Run stopped before completing scanner or Agent Triage work."
                  }
                />
              )}

              {displayedRun.status === "Cancelled" && (
                <p className="cancelled-note muted">
                  Cancellation is best-effort. Active ZAP and Review Skill work
                  stops between steps when possible.
                </p>
              )}

              <dl>
                <div>
                  <dt>Status</dt>
                  <dd
                    className={
                      displayedRun.status === "Cancelled"
                        ? "status-cancelled"
                        : isFailed
                          ? "status-bad"
                          : undefined
                    }
                  >
                    {displayedRun.status}
                  </dd>
                </div>
                <div>
                  <dt>Current step</dt>
                  <dd>{displayedRun.current_step}</dd>
                </div>
                {activeDetail.progress !== null &&
                  activeDetail.progress !== undefined && (
                    <div>
                      <dt>Progress</dt>
                      <dd>
                        <progress max={1} value={activeDetail.progress} />
                        <span>{Math.round(activeDetail.progress * 100)}%</span>
                      </dd>
                    </div>
                  )}
              </dl>

              <ReviewQueue
                hypotheses={activeDetail.hypotheses}
                canRunSkills={canRunSkills}
                runningSkillId={runningSkillId}
                runningRecommended={runningRecommended}
                onRunSkill={handleRunSkill}
                onRunRecommended={handleRunRecommendedSkills}
              />
              <SkillRunsPanel
                skillRuns={activeDetail.skill_runs}
                onSelectFinding={setSelectedFindingId}
              />
              <FindingsList
                findings={activeDetail.findings}
                findingCounts={displayedSummary?.finding_counts}
                onSelectFinding={setSelectedFindingId}
              />
            </>
          )}
        </div>
      )}

      {displayedRunId && selectedFindingId && (
        <FindingDetailPanel
          scanId={displayedRunId}
          findingId={selectedFindingId}
          onClose={() => setSelectedFindingId(null)}
          onUpdated={() => refresh()}
        />
      )}

      <div className="scan-history">
        <h3>Review Run history</h3>
        {history.length === 0 ? (
          <p className="muted">No prior Review Runs.</p>
        ) : (
          <ul>
            {history.map((run) => (
              <li key={run.id}>
                <button
                  type="button"
                  className={`history-run-button${
                    run.id === selectedRunId
                      ? " history-run-button-selected"
                      : ""
                  }${run.id === activeSummary?.id ? " history-run-button-active" : ""}`}
                  onClick={() => handleSelectRun(run.id)}
                >
                  <span className="run-status">
                    {run.status}
                    {run.id === activeSummary?.id && (
                      <span className="run-badge">Active</span>
                    )}
                  </span>
                  <span className="run-step">{run.current_step}</span>
                  <span className="run-time">
                    {formatTimestamp(run.started_at)}
                  </span>
                  <span className="run-findings">
                    {totalFindings(run.finding_counts)} Findings
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
