# Polish Review Workbench UX And Error States

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Tighten the reviewer workbench so it behaves like a coherent product rather than a raw demo. The dashboard should explicitly handle loading, empty, error, disabled, sorting, filtering, and scan-history states across Review Runs, Hypotheses, Review Skills, Findings, and Finding details.

## Acceptance criteria

- [ ] Dashboard has explicit loading states for backend config, scan history, active run, findings, and finding details.
- [ ] Dashboard has explicit empty states for no Review Runs, no Hypotheses, no Findings, and no skill outcomes.
- [ ] Dashboard has visible error states for failed API calls and failed Review Runs.
- [ ] Findings can be sorted by severity.
- [ ] Findings can be filtered by source, severity, or Review Disposition if time permits.
- [ ] Buttons are disabled when actions are invalid or work is active.
- [ ] Scan history switching is clear and does not lose current active-run context.
- [ ] UI uses the glossary language: Review Run, Hypothesis, Review Skill, Finding, Evidence Packet, and Review Disposition.

## Blocked by

- 0004 Review Finding Details And Dispositions
- 0005 Agent Triage With NVIDIA NIM And Mock Fallback
