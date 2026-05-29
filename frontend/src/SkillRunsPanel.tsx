import type { SkillRun } from "./api";
import { EmptyState } from "./components/WorkbenchState";

type Props = {
  skillRuns: SkillRun[];
  onSelectFinding?: (findingId: string) => void;
};

export default function SkillRunsPanel({ skillRuns, onSelectFinding }: Props) {
  return (
    <div className="skill-runs">
      <h4>Review Skill runs</h4>
      {skillRuns.length === 0 ? (
        <EmptyState
          title="No Review Skill outcomes yet"
          description="Run a recommended Review Skill from the Review Queue when Agent Triage has Hypotheses."
        />
      ) : (
        <ul className="skill-runs-list">
          {skillRuns.map((run) => (
            <li key={run.id} className="skill-run-card">
              <div className="skill-run-header">
                <span className="skill-run-id">{run.skill_id}</span>
                <span className="skill-run-status">{run.status}</span>
                {run.outcome && (
                  <span className="skill-run-outcome">{run.outcome}</span>
                )}
              </div>
              <p>{run.summary}</p>
              {run.inconclusive_reason && (
                <p className="muted">{run.inconclusive_reason}</p>
              )}
              {run.finding_id && onSelectFinding && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => onSelectFinding(run.finding_id!)}
                >
                  View Finding
                </button>
              )}
              {run.evidence_packets.map((packet) => (
                <div key={packet.id} className="evidence-packet">
                  <h5>{packet.scenario}</h5>
                  <dl>
                    <div>
                      <dt>Actor Context</dt>
                      <dd>{packet.actor_context}</dd>
                    </div>
                    <div>
                      <dt>Expected</dt>
                      <dd>{packet.expected_behavior}</dd>
                    </div>
                    <div>
                      <dt>Observed</dt>
                      <dd>{packet.observed_behavior}</dd>
                    </div>
                    <div>
                      <dt>Request</dt>
                      <dd>
                        {packet.request_method} {packet.request_path}
                      </dd>
                    </div>
                    <div>
                      <dt>Response</dt>
                      <dd>HTTP {packet.response_status}</dd>
                    </div>
                  </dl>
                  {packet.response_excerpt && (
                    <pre className="finding-evidence">
                      {packet.response_excerpt}
                    </pre>
                  )}
                </div>
              ))}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
