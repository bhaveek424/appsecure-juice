import { useEffect, useState } from "react";
import {
  getFindingDetail,
  REVIEW_DISPOSITIONS,
  updateFindingDisposition,
  type FindingDetail,
  type ReviewDisposition,
} from "./api";
import { ErrorBanner, LoadingState } from "./components/WorkbenchState";

type Props = {
  scanId: string;
  findingId: string;
  onClose: () => void;
  onUpdated: () => void;
};

export default function FindingDetailPanel({
  scanId,
  findingId,
  onClose,
  onUpdated,
}: Props) {
  const [detail, setDetail] = useState<FindingDetail | null>(null);
  const [disposition, setDisposition] = useState<ReviewDisposition>("Unreviewed");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const finding = await getFindingDetail(scanId, findingId);
        if (!cancelled) {
          setDetail(finding);
          setDisposition(finding.disposition);
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
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [scanId, findingId]);

  async function handleSave() {
    if (!detail) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const saved = await updateFindingDisposition(findingId, disposition);
      setDetail({ ...detail, disposition: saved.disposition });
      setDisposition(saved.disposition);
      onUpdated();
    } catch (saveError) {
      const message =
        saveError instanceof Error ? saveError.message : "Unknown error";
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="panel finding-detail-panel">
      <div className="panel-header">
        <h2>Finding detail</h2>
        <button type="button" className="secondary-button" onClick={onClose}>
          Close
        </button>
      </div>

      {loading && <LoadingState label="Loading Finding detail…" />}
      {error && (
        <ErrorBanner title="Could not load Finding detail" message={error} />
      )}

      {detail && !loading && (
        <>
          <dl>
            <div>
              <dt>Source</dt>
              <dd>{detail.source}</dd>
            </div>
            <div>
              <dt>Severity</dt>
              <dd>{detail.severity}</dd>
            </div>
            <div>
              <dt>Title</dt>
              <dd>{detail.title}</dd>
            </div>
            <div>
              <dt>Endpoint</dt>
              <dd>{detail.endpoint}</dd>
            </div>
            <div>
              <dt>Review Disposition</dt>
              <dd className="disposition-controls">
                <select
                  value={disposition}
                  disabled={saving}
                  onChange={(event) =>
                    setDisposition(event.target.value as ReviewDisposition)
                  }
                >
                  {REVIEW_DISPOSITIONS.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="primary-button"
                  disabled={saving || disposition === detail.disposition}
                  onClick={handleSave}
                >
                  {saving ? "Saving Review Disposition…" : "Save Review Disposition"}
                </button>
              </dd>
            </div>
          </dl>

          {detail.business_logic && (
            <div className="scanner-detail">
              <h3>Evidence Packet</h3>
              <dl>
                <div>
                  <dt>Review Skill</dt>
                  <dd>{detail.business_logic.skill_id}</dd>
                </div>
                <div>
                  <dt>Scenario</dt>
                  <dd>{detail.business_logic.scenario}</dd>
                </div>
                <div>
                  <dt>Actor Context</dt>
                  <dd>{detail.business_logic.actor_context}</dd>
                </div>
                <div>
                  <dt>Expected behavior</dt>
                  <dd>{detail.business_logic.expected_behavior}</dd>
                </div>
                <div>
                  <dt>Observed behavior</dt>
                  <dd>{detail.business_logic.observed_behavior}</dd>
                </div>
                <div>
                  <dt>Request</dt>
                  <dd>
                    {detail.business_logic.request_method}{" "}
                    {detail.business_logic.request_path}
                  </dd>
                </div>
                <div>
                  <dt>Response status</dt>
                  <dd>{detail.business_logic.response_status}</dd>
                </div>
                <div>
                  <dt>Reasoning summary</dt>
                  <dd>{detail.business_logic.reasoning_summary}</dd>
                </div>
              </dl>
              {detail.business_logic.response_excerpt && (
                <pre className="finding-evidence">
                  {detail.business_logic.response_excerpt}
                </pre>
              )}
            </div>
          )}

          {detail.scanner && (
            <div className="scanner-detail">
              <h3>Scanner Finding evidence</h3>
              <dl>
                <div>
                  <dt>Alert</dt>
                  <dd>{detail.scanner.alert}</dd>
                </div>
                <div>
                  <dt>Confidence</dt>
                  <dd>{detail.scanner.confidence ?? "—"}</dd>
                </div>
                <div>
                  <dt>Description</dt>
                  <dd>{detail.scanner.description}</dd>
                </div>
                <div>
                  <dt>Remediation</dt>
                  <dd>{detail.scanner.remediation}</dd>
                </div>
              </dl>
              {detail.scanner.evidence_excerpt && (
                <pre className="finding-evidence">
                  {detail.scanner.evidence_excerpt}
                </pre>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
}
