# AppSec Review Workbench

A small fullstack workbench for black-box review of [OWASP Juice Shop](https://github.com/juice-shop/juice-shop). It combines OWASP ZAP scanner output with bounded, skill-based business logic investigation. The Skill-Based Agent reasons over sanitized observations; backend code performs guarded HTTP probes.

## Architecture

- **Target Application**: OWASP Juice Shop only (configured server-side).
- **ZAP**: Runs in daemon mode; the backend will drive it through the ZAP API (see `docs/adr/0001-drive-zap-through-api.md`).
- **Backend**: Python, FastAPI, SQLite for review state (`docs/adr/0002-use-sqlite-for-review-state.md`).
- **Frontend**: React + Vite reviewer dashboard with polling (no WebSockets in v1).
- **Agent Reasoning**: NVIDIA NIM when `NVIDIA_API_KEY` is set; mock provider otherwise. Secrets stay on the backend.

Domain language and status names live in `CONTEXT.md`.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

| Service       | URL                        |
|---------------|----------------------------|
| Juice Shop    | http://localhost:3000      |
| ZAP API       | http://localhost:8080      |
| Backend API   | http://localhost:8000      |
| Workbench UI  | http://localhost:5173      |

The dashboard calls `GET /health` and `GET /api/config`. Config exposes the Target Application URL and LLM mode but never API keys.

## Local development

**Backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
pytest
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL=http://localhost:8000` if the API is not on the default host.

## Configuration

See `.env.example` for:

- `TARGET_APPLICATION_URL` — Juice Shop base URL
- `ZAP_API_URL` / `ZAP_API_KEY` — ZAP daemon API
- `DATABASE_URL` — SQLite path for review state
- `LLM_PROVIDER` — `mock` or `nvidia`
- `NVIDIA_API_KEY` — optional; enables NVIDIA NIM

## Trade-offs (issue #0001)

- **Docker Compose** bundles Juice Shop, ZAP, backend, and frontend for a one-command demo.
- **Polling over SSE/WebSockets** keeps the first frontend simple; status updates poll the backend.
- **SQLite** keeps review state local and easy to reset; not aimed at multi-tenant production.
- **Mock LLM** lets the stack run without external API access; real triage lands in a later issue.

## Tests

Backend tests focus on HTTP behavior and guardrails (TDD, vertical slices). Run with `pytest` in `backend/`.

## Further reading

- `docs/PRD.md` — product requirements
- `docs/issues/` — implementation slices
- `docs/adr/` — architecture decisions
