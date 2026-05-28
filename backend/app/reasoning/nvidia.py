import json
import re

import httpx

from app.config import get_settings
from app.domain.review_skill import REVIEW_SKILL_NAMES, ReviewSkillId
from app.reasoning.types import (
    SanitizedObservation,
    SourceObservationRef,
    TriageHypothesisResult,
)


class HttpNvidiaNimReasoningClient:
    _CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
    _MODEL = "meta/llama-3.1-8b-instruct"

    def triage(
        self, observations: list[SanitizedObservation]
    ) -> list[TriageHypothesisResult]:
        if not observations:
            return []

        settings = get_settings()
        api_key = settings.nvidia_api_key
        if api_key is None:
            raise RuntimeError("NVIDIA API key is required for NVIDIA NIM triage")

        prompt = _build_prompt(observations)
        payload = {
            "model": self._MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AppSec triage assistant. Return JSON only: "
                        '{"hypotheses":[{"title":"...","rationale":"...","recommended_skill_id":"account-boundary|basket-and-checkout|review-ownership|coupon-and-discount","priority":"High|Medium|Low","source_finding_ids":["..."]}]}'
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }
        headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(self._CHAT_URL, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()

        content = body["choices"][0]["message"]["content"]
        return _parse_response(content, observations)


def _build_prompt(observations: list[SanitizedObservation]) -> str:
    lines = ["Sanitized scanner observations:"]
    for observation in observations:
        lines.append(
            f"- id={observation.finding_id} title={observation.title} "
            f"severity={observation.severity} endpoint={observation.endpoint}"
        )
    lines.append(
        "Recommend business-logic Review Skills as hypotheses, not confirmed vulnerabilities."
    )
    return "\n".join(lines)


def _parse_response(
    content: str,
    observations: list[SanitizedObservation],
) -> list[TriageHypothesisResult]:
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if match is None:
        raise ValueError("NVIDIA NIM response did not include JSON")

    payload = json.loads(match.group())
    observation_by_id = {observation.finding_id: observation for observation in observations}
    results: list[TriageHypothesisResult] = []

    for item in payload.get("hypotheses", []):
        skill_id = item.get("recommended_skill_id", ReviewSkillId.ACCOUNT_BOUNDARY)
        try:
            skill = ReviewSkillId(skill_id)
        except ValueError:
            skill = ReviewSkillId.ACCOUNT_BOUNDARY

        refs: list[SourceObservationRef] = []
        for finding_id in item.get("source_finding_ids", []):
            observation = observation_by_id.get(finding_id)
            if observation is None:
                continue
            refs.append(
                SourceObservationRef(
                    finding_id=observation.finding_id,
                    title=observation.title,
                    severity=observation.severity,
                )
            )
        if not refs and observations:
            observation = observations[0]
            refs = [
                SourceObservationRef(
                    finding_id=observation.finding_id,
                    title=observation.title,
                    severity=observation.severity,
                )
            ]

        results.append(
            TriageHypothesisResult(
                title=item["title"],
                rationale=item["rationale"],
                recommended_skill_id=skill.value,
                recommended_skill_name=REVIEW_SKILL_NAMES[skill],
                priority=item.get("priority", "Medium"),
                source_observations=refs,
            )
        )

    return results
