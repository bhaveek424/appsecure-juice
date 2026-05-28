# Run ZAP And Normalize Scanner Findings

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Wire Review Runs to OWASP ZAP through the ZAP API. A Review Run should move through the Zapping phase, run spider and active scan work against the configured Target Application, collect ZAP alerts as Scanner Findings, normalize them into the product Finding shape, and expose scanner progress and severity counts to the frontend.

## Acceptance criteria

- [x] Backend starts ZAP spider and active scan work through the ZAP API.
- [x] Review Run status and current step reflect ZAP work.
- [x] ZAP progress is exposed where the API provides it.
- [x] ZAP alerts are normalized into Findings and persisted.
- [x] Raw ZAP alert JSON is not passed straight through to the frontend.
- [x] Findings include source, title, category, severity, endpoint, description, remediation, timestamp, and scanner evidence fields.
- [x] Frontend shows progress, severity counts, and a sortable unified Findings list.
- [x] Backend tests cover ZAP alert normalization and severity mapping.

## Blocked by

- 0002 Create And Poll A Review Run
