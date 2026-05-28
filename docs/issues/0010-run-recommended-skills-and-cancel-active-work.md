# Run Recommended Skills And Cancel Active Work

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Add reviewer controls for running all recommended Review Skills and cancelling active work. Cancellation should be best-effort: stop active ZAP work where possible, mark the Review Run Cancelled, and have skill probes check cancellation between steps.

## Acceptance criteria

- [ ] `POST /api/scans/:id/skills/run-recommended` runs recommended skills that are not already complete.
- [ ] Frontend includes a Run Recommended Skills action when Agent Triage has recommendations.
- [ ] `POST /api/scans/:id/cancel` marks an active Review Run Cancelled.
- [ ] Backend attempts to stop active ZAP scans through the ZAP API.
- [ ] Skill probes check cancellation between steps and stop without creating partial Findings.
- [ ] Frontend disables active actions after cancellation and shows Cancelled state.
- [ ] Backend tests cover cancellation state transitions and cancellation during skill execution.

## Blocked by

- 0006 Run Account Boundary Skill End-To-End
