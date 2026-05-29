import type { Hypothesis } from "./api";
import { EmptyState } from "./components/WorkbenchState";

const RUNNABLE_SKILLS: Record<string, string> = {
  "account-boundary": "Run Account Boundary Review Skill",
  "basket-and-checkout": "Run Basket And Checkout Review Skill",
  "review-ownership": "Run Review Ownership Review Skill",
  "coupon-and-discount": "Run Coupon And Discount Review Skill",
};

type Props = {
  hypotheses: Hypothesis[];
  canRunSkills?: boolean;
  runningSkillId?: string | null;
  runningRecommended?: boolean;
  onRunSkill?: (skillId: string) => void;
  onRunRecommended?: () => void;
};

export default function ReviewQueue({
  hypotheses,
  canRunSkills = false,
  runningSkillId = null,
  runningRecommended = false,
  onRunSkill,
  onRunRecommended,
}: Props) {
  const skillWorkActive = runningSkillId !== null || runningRecommended;

  return (
    <div className="review-queue">
      <h4>Review Queue</h4>
      <p className="muted queue-lede">
        Hypotheses are speculative leads from Agent Triage. Run a recommended
        Review Skill when you are ready to collect Evidence Packets.
      </p>
      {hypotheses.length === 0 ? (
        <EmptyState
          title="No Hypotheses yet"
          description="Agent Triage creates Hypotheses after the scanner phase completes for this Review Run."
        />
      ) : (
        <>
          {canRunSkills && onRunRecommended && (
            <button
              type="button"
              className="primary-button queue-run-recommended"
              disabled={skillWorkActive}
              onClick={onRunRecommended}
            >
              {runningRecommended
                ? "Running recommended Review Skills…"
                : "Run Recommended Review Skills"}
            </button>
          )}
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
                    From Findings:{" "}
                    {hypothesis.source_observations
                      .map((source) => source.title)
                      .join(", ")}
                  </p>
                )}
                {canRunSkills &&
                  onRunSkill &&
                  RUNNABLE_SKILLS[hypothesis.recommended_skill_id] && (
                    <button
                      type="button"
                      className="primary-button"
                      disabled={skillWorkActive}
                      onClick={() => onRunSkill(hypothesis.recommended_skill_id)}
                    >
                      {runningSkillId === hypothesis.recommended_skill_id
                        ? "Running Review Skill…"
                        : RUNNABLE_SKILLS[hypothesis.recommended_skill_id]}
                    </button>
                  )}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
