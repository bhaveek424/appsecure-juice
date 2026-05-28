# Document And Verify End-To-End Submission

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Prepare the project for submission. The README should explain the architecture, trade-offs, agent design, setup, limitations, and dependencies. The verification path should prove that a reviewer can run Docker Compose, open the dashboard, start a Review Run, see progress, inspect Findings or Hypotheses, and review evidence.

## Acceptance criteria

- [ ] README explains what the product is and what it is not.
- [ ] README includes an architecture diagram.
- [ ] README explains how to run the full stack end-to-end with `docker compose up`.
- [ ] README explains NVIDIA NIM configuration and mock mode.
- [ ] README explains ZAP API choice, polling choice, SQLite choice, bounded Review Skill choice, and black-box scope.
- [ ] README explains Agent Triage, Hypotheses, Review Skills, Evidence Packets, Findings, and Review Dispositions.
- [ ] README documents limitations and out-of-scope areas.
- [ ] Backend tests for guardrails, normalization, sanitization, dispositions, and mock triage pass.
- [ ] Docker Compose end-to-end path is manually verified.
- [ ] A screenshot or short walkthrough artifact is captured or linked.

## Blocked by

- 0010 Run Recommended Skills And Cancel Active Work
- 0011 Polish Review Workbench UX And Error States
