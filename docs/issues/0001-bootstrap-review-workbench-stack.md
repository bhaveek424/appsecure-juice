# Bootstrap Review Workbench Stack

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Create the initial fullstack skeleton for the AppSec Review Workbench. A reviewer should be able to run one command that starts OWASP Juice Shop, OWASP ZAP in daemon mode, the FastAPI backend, and the React frontend. The backend should expose a health endpoint and read configuration for the Target Application, ZAP API, SQLite database, and LLM provider. The frontend should render a basic workbench shell that confirms the backend is reachable and shows the configured Target Application.

## Acceptance criteria

- [ ] `docker compose up` starts Juice Shop, ZAP, backend, and frontend.
- [ ] Juice Shop is reachable from the host and from the backend as the configured Target Application.
- [ ] ZAP runs in daemon mode and is reachable from the backend.
- [ ] Backend exposes a health/config endpoint that does not leak secrets.
- [ ] Frontend renders a basic AppSec Review Workbench shell and shows backend connectivity.
- [ ] `.env.example` documents mock LLM mode and NVIDIA NIM configuration.
- [ ] No real API key or secret is committed.

## Blocked by

None - can start immediately.
