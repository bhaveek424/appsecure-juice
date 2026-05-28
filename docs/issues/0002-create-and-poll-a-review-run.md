# Create And Poll A Review Run

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Implement the first end-to-end Review Run path. A reviewer can start a Review Run against the configured Target Application, the backend persists it in SQLite, the frontend polls for status, and the reviewer can see current and past Review Runs. The backend must reject arbitrary targets and enforce one active Review Run at a time.

## Acceptance criteria

- [ ] `POST /api/scans` creates a Review Run and returns its id immediately.
- [ ] The backend rejects any requested target that does not exactly match the configured Target Application after normalization.
- [ ] Starting a second active Review Run returns `409 Conflict` with the active run id.
- [ ] `GET /api/scans` lists Review Runs with id, status, start time, completion time, current step, and finding counts.
- [ ] `GET /api/scans/:id` returns status, progress, current step, and empty collections for findings, hypotheses, and skill runs.
- [ ] Frontend can start a Review Run, disables Start while a run is active, polls the active run, and shows scan history.
- [ ] Backend tests cover target guardrail and one-active-run behavior.

## Blocked by

- 0001 Bootstrap Review Workbench Stack
