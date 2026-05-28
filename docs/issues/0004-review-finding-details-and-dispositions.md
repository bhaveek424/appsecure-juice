# Review Finding Details And Dispositions

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Add the reviewer workflow for inspecting a Finding and assigning a Review Disposition. The detail view should show source-specific evidence and remediation. Disposition updates should persist and be reflected in scan history and the findings list.

## Acceptance criteria

- [x] `GET /api/scans/:id/findings/:finding_id` returns full Finding detail.
- [x] `PATCH /api/findings/:id/disposition` persists one of Unreviewed, True Positive, False Positive, Duplicate, or Needs Investigation.
- [x] Frontend opens a Finding detail view from the unified Findings list.
- [x] ZAP Finding details include alert metadata, description, remediation, confidence, and evidence excerpt.
- [x] Frontend allows changing Review Disposition and reflects the saved value after refresh.
- [x] Backend tests cover disposition persistence and invalid disposition rejection.

## Blocked by

- 0003 Run ZAP And Normalize Scanner Findings
