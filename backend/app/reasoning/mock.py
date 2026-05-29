from app.domain.review_skill import REVIEW_SKILL_NAMES, ReviewSkillId
from app.reasoning.types import (
    SanitizedObservation,
    SourceObservationRef,
    TriageHypothesisResult,
)


class MockReasoningClient:
    def triage(
        self, observations: list[SanitizedObservation]
    ) -> list[TriageHypothesisResult]:
        if not observations:
            return []

        refs = [
            SourceObservationRef(
                finding_id=observation.finding_id,
                title=observation.title,
                severity=observation.severity,
            )
            for observation in observations
        ]
        primary = observations[0]

        return [
            TriageHypothesisResult(
                title="Session-scoped workflows may lack actor isolation",
                rationale=(
                    f"Scanner observed '{primary.title}' on {primary.endpoint}. "
                    "Test whether User A can reach or alter User B account-adjacent data."
                ),
                recommended_skill_id=ReviewSkillId.ACCOUNT_BOUNDARY,
                recommended_skill_name=REVIEW_SKILL_NAMES[
                    ReviewSkillId.ACCOUNT_BOUNDARY
                ],
                priority="High",
                source_observations=refs,
            ),
            TriageHypothesisResult(
                title="Cart or checkout state may accept unintended manipulation",
                rationale=(
                    f"Observed {primary.severity} issue '{primary.title}' suggests "
                    "client-visible workflow fields should be probed for basket abuse."
                ),
                recommended_skill_id=ReviewSkillId.BASKET_AND_CHECKOUT,
                recommended_skill_name=REVIEW_SKILL_NAMES[
                    ReviewSkillId.BASKET_AND_CHECKOUT
                ],
                priority="Medium",
                source_observations=refs[:1],
            ),
            TriageHypothesisResult(
                title="Product reviews may not enforce ownership boundaries",
                rationale=(
                    "Juice Shop review flows often mix public reads with per-user writes. "
                    "Verify User B cannot edit or delete User A reviews."
                ),
                recommended_skill_id=ReviewSkillId.REVIEW_OWNERSHIP,
                recommended_skill_name=REVIEW_SKILL_NAMES[
                    ReviewSkillId.REVIEW_OWNERSHIP
                ],
                priority="Medium",
                source_observations=refs[:1],
            ),
            TriageHypothesisResult(
                title="Coupon reuse or cross-account discount application may be possible",
                rationale=(
                    "Promotional endpoints should enforce one-time redemption and "
                    "basket ownership. Probe bounded reuse and cross-actor coupon flows."
                ),
                recommended_skill_id=ReviewSkillId.COUPON_AND_DISCOUNT,
                recommended_skill_name=REVIEW_SKILL_NAMES[
                    ReviewSkillId.COUPON_AND_DISCOUNT
                ],
                priority="Medium",
                source_observations=refs[:1],
            ),
        ]
