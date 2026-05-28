# Agent Triage With NVIDIA NIM And Mock Fallback

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Add Agent Triage after ZAP has produced Observed Output. The backend should call a reasoning client that supports NVIDIA NIM when configured and a mock provider when no API key is available. Agent Triage should create Hypotheses and recommended Review Skills without presenting speculative risks as Findings.

## Acceptance criteria

- [x] Backend has a provider-isolated reasoning client with NVIDIA NIM and mock implementations.
- [x] LLM provider configuration is backend-only and does not expose secrets to the frontend.
- [x] Review Run transitions from Zapping to Triaging and then Ready For Skills.
- [x] Agent Triage reads sanitized Observed Output and stores Hypotheses.
- [x] Hypotheses include title, rationale, recommended skill, confidence or priority, and source observations.
- [x] Frontend shows a Review Queue with hypotheses and recommended Review Skills.
- [x] Mock provider produces deterministic hypotheses for local/demo use.
- [x] Backend tests cover mock triage output shape.

## Blocked by

- 0003 Run ZAP And Normalize Scanner Findings
