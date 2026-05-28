# Run Account Boundary Skill End-To-End

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Implement the first bounded Review Skill. The Account Boundary Skill should create or reuse User A and User B, authenticate them against Juice Shop, perform HTTP-level probes for cross-actor access or mutation of account-adjacent data, sanitize captured evidence, and create a Business Logic Finding only when an Evidence Packet supports the claim.

## Acceptance criteria

- [x] Backend can create or reuse User A and User B for a Review Run.
- [x] Actor Context is represented as Anonymous, User A, or User B without exposing credentials or tokens.
- [x] `POST /api/scans/:id/skills/:skill_id/run` can start the Account Boundary Skill.
- [x] Skill run status and outcome are persisted.
- [x] Skill probes capture sanitized request/response evidence.
- [x] Evidence Packets include skill, scenario, actor context, expected behavior, observed behavior, request details, response status, response excerpt, reasoning summary, and timestamp.
- [x] Business Logic Findings are created only when evidence supports an authorization or boundary issue.
- [x] Inconclusive results are stored as skill outcomes, not Findings.
- [x] Frontend can run the skill and view resulting skill status, finding, or inconclusive outcome.
- [x] Backend tests cover evidence sanitization and evidence-gated finding creation.

## Blocked by

- 0005 Agent Triage With NVIDIA NIM And Mock Fallback
