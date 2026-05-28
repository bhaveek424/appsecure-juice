from app.reasoning.mock import MockReasoningClient
from app.reasoning.types import SanitizedObservation


def test_mock_triage_returns_structured_hypotheses():
    client = MockReasoningClient()
    observations = [
        SanitizedObservation(
            finding_id="finding-1",
            title="Cross Site Scripting",
            severity="High",
            category="Injection",
            endpoint="http://juice-shop:3000/#/search",
            source="Scanner",
        )
    ]

    hypotheses = client.triage(observations)

    assert len(hypotheses) >= 1
    hypothesis = hypotheses[0]
    assert hypothesis.title
    assert hypothesis.rationale
    assert hypothesis.recommended_skill_id
    assert hypothesis.recommended_skill_name
    assert hypothesis.priority
    assert len(hypothesis.source_observations) >= 1
    source = hypothesis.source_observations[0]
    assert source.finding_id == "finding-1"
    assert source.title == "Cross Site Scripting"


def test_mock_triage_is_deterministic():
    client = MockReasoningClient()
    observations = [
        SanitizedObservation(
            finding_id="finding-1",
            title="Cross Site Scripting",
            severity="High",
            category="Injection",
            endpoint="http://juice-shop:3000/#/search",
            source="Scanner",
        )
    ]

    first = client.triage(observations)
    second = client.triage(observations)

    assert [h.model_dump() for h in first] == [h.model_dump() for h in second]
