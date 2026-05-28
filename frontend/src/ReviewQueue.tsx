import type { Hypothesis } from "./api";

type Props = {
  hypotheses: Hypothesis[];
};

export default function ReviewQueue({ hypotheses }: Props) {
  if (hypotheses.length === 0) {
    return <p className="muted">No Hypotheses yet. Agent Triage runs after ZAP.</p>;
  }

  return (
    <div className="review-queue">
      <h4>Review Queue</h4>
      <p className="muted queue-lede">
        Hypotheses are speculative leads. Run a recommended Review Skill when ready.
      </p>
      <ul className="hypotheses-list">
        {hypotheses.map((hypothesis) => (
          <li key={hypothesis.id} className="hypothesis-card">
            <div className="hypothesis-header">
              <span className="hypothesis-priority">{hypothesis.priority}</span>
              <span className="hypothesis-skill">
                {hypothesis.recommended_skill_name}
              </span>
            </div>
            <h5>{hypothesis.title}</h5>
            <p>{hypothesis.rationale}</p>
            {hypothesis.source_observations.length > 0 && (
              <p className="hypothesis-sources">
                From:{" "}
                {hypothesis.source_observations
                  .map((source) => source.title)
                  .join(", ")}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
