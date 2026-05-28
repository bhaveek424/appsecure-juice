# PRD: AppSec Review Workbench

## Problem Statement

Security reviewers need a small, trustworthy way to review OWASP Juice Shop with both automated scanner coverage and bounded business-logic investigation. A raw OWASP ZAP report is useful for scanner findings, but it does not help a reviewer reason through actor boundaries, checkout behavior, review ownership, or other workflow risks that require application-specific evidence.

The product should help a human reviewer move from automated scanner output and observed application behavior to evidence-backed findings. It should not claim complete Juice Shop coverage, inspect source code, or operate as an uncontrolled autonomous research agent.

## Solution

Build a fullstack AppSec Review Workbench for OWASP Juice Shop. The backend orchestrates a Review Run against the configured Target Application, drives OWASP ZAP through its API, stores normalized review state in SQLite, performs Agent Triage over Observed Output, and runs bounded Review Skills when selected by the reviewer.

The frontend presents a reviewer workbench: start or cancel a Review Run, watch phase-level progress, inspect Hypotheses, run recommended Review Skills, review unified Findings, view Evidence Packets, and assign Review Dispositions.

The Skill-Based Agent uses NVIDIA NIM for Agent Reasoning when an API key is configured, with a mock provider fallback so the stack still runs without external LLM access. Backend code performs all guarded HTTP actions against Juice Shop; the LLM interprets sanitized observations and returns structured hypotheses, skill recommendations, or evidence explanations.

## User Stories

1. As a reviewer, I want to start a Review Run from the dashboard, so that I can begin reviewing the configured Juice Shop instance without CLI steps.
2. As a reviewer, I want the product to reject any target other than the configured Juice Shop instance, so that the workbench cannot become an unintended network scanner.
3. As a reviewer, I want to see the configured Target Application clearly, so that I know what is being reviewed.
4. As a reviewer, I want the Start Scan action disabled while a Review Run is active, so that I do not accidentally start conflicting scans.
5. As a reviewer, I want to see whether a Review Run is Queued, Zapping, Triaging, Ready For Skills, Probing, Completed, Failed, or Cancelled, so that I understand what the system is doing.
6. As a reviewer, I want a current step label during a Review Run, so that progress is understandable even when exact progress is not available.
7. As a reviewer, I want ZAP-specific progress where available, so that I can distinguish spider progress from active scan progress.
8. As a reviewer, I want the frontend to poll for progress, so that the dashboard updates without requiring a complex live transport.
9. As a reviewer, I want to cancel an active Review Run, so that I can stop long-running or mistaken work.
10. As a reviewer, I want cancellation to be visibly best-effort, so that I understand some backend work may stop between steps rather than instantly.
11. As a reviewer, I want past Review Runs listed, so that I can return to previous findings and dispositions.
12. As a reviewer, I want past Review Runs to show status, start time, completion time, and finding counts, so that I can quickly choose the right run.
13. As a reviewer, I want OWASP ZAP findings normalized into the product's Finding shape, so that I do not have to interpret raw ZAP alert JSON.
14. As a reviewer, I want scanner findings and business logic findings in one unified list, so that I have a single review queue.
15. As a reviewer, I want each Finding to show its source, so that I know whether it came from ZAP or a Review Skill.
16. As a reviewer, I want Findings sorted by severity, so that I can inspect the most serious issues first.
17. As a reviewer, I want severity normalized to Critical, High, Medium, Low, and Informational, so that findings from different sources are comparable.
18. As a reviewer, I want finding counts by severity, so that I can summarize the Review Run at a glance.
19. As a reviewer, I want empty states, loading states, and error states, so that the dashboard remains understandable before and during review work.
20. As a reviewer, I want to open a Finding detail view, so that I can inspect the supporting evidence.
21. As a reviewer, I want ZAP finding details to include title, category, severity, endpoint, description, remediation, confidence, and evidence excerpt, so that scanner output is human-readable.
22. As a reviewer, I want business logic findings to include an Evidence Packet, so that I can verify what was tested and what was observed.
23. As a reviewer, I want an Evidence Packet to include the Review Skill, scenario, Actor Context, expected behavior, observed behavior, relevant request details, response status, response excerpt, reasoning summary, and timestamp, so that the finding is reviewable.
24. As a reviewer, I want auth tokens and cookies excluded from Evidence Packets, so that evidence can be inspected safely.
25. As a reviewer, I want to classify Findings as Unreviewed, True Positive, False Positive, Duplicate, or Needs Investigation, so that my review decisions persist.
26. As a reviewer, I want Review Dispositions persisted across restarts, so that I can continue a review later.
27. As a reviewer, I want Agent Triage to analyze Observed Output after ZAP produces enough results, so that I get business-logic leads without manually reading every scanner result.
28. As a reviewer, I want Agent Triage to produce Hypotheses rather than confirmed vulnerabilities, so that speculative risks are not presented as evidence-backed Findings.
29. As a reviewer, I want each Hypothesis to explain why a Review Skill is recommended, so that I can decide whether to run it.
30. As a reviewer, I want to run one selected Review Skill, so that I can investigate a specific business-risk area.
31. As a reviewer, I want to run all recommended Review Skills, so that I can quickly execute the agent's suggested path.
32. As a reviewer, I want Review Skill runs to show their status and outcome, so that I can tell which investigations are complete.
33. As a reviewer, I want Review Skills to create Findings only when evidence is concrete, so that the findings list remains credible.
34. As a reviewer, I want inconclusive skill results to remain notes or skill outcomes rather than findings, so that uncertainty is represented honestly.
35. As a reviewer, I want an Account Boundary Skill, so that I can test whether User A can access or alter User B's account-adjacent data.
36. As a reviewer, I want a Basket And Checkout Skill, so that I can test whether basket, quantity, price, or checkout state can be manipulated.
37. As a reviewer, I want a Review Ownership Skill, so that I can test whether one user can affect another user's product review.
38. As a reviewer, I want a Coupon And Discount Skill, so that I can test discount reuse, stacking, or invalid-state behavior when a clear expected rule is available.
39. As a reviewer, I want the system to create or reuse User A and User B during a Review Run, so that actor-boundary tests have meaningful identities.
40. As a reviewer, I want the agent to use HTTP-level probes before browser automation, so that evidence is stable and easy to inspect.
41. As a reviewer, I want ZAP to scan the public surface while authenticated workflow checks are handled by Review Skills, so that each tool is used where it is strongest.
42. As a reviewer, I want the app to run without an LLM key in mock mode, so that I can still evaluate the stack end-to-end.
43. As a reviewer, I want NVIDIA NIM support when an API key is present, so that Agent Reasoning can use a real LLM provider.
44. As a reviewer, I want the frontend never to receive the LLM API key, so that secrets remain backend-only.
45. As a developer, I want the ZAP integration isolated behind a small adapter, so that scanner orchestration can be tested and changed without touching the rest of the app.
46. As a developer, I want the LLM provider isolated behind a reasoning interface, so that NVIDIA NIM can be swapped or mocked without rewriting Review Skills.
47. As a developer, I want Review Skills to be bounded with explicit allowed actions and stop conditions, so that agentic behavior remains predictable.
48. As a developer, I want normalized schemas for Hypotheses, Findings, Evidence Packets, Review Runs, and Skill Runs, so that frontend and backend share clear contracts.
49. As a developer, I want backend tests around guardrails and normalization, so that the highest-risk behavior is protected.
50. As a reviewer, I want a README that explains architecture and trade-offs, so that I can understand why the product is built this way.

## Implementation Decisions

- Build a monorepo with separate backend and frontend applications plus Docker Compose wiring for Juice Shop, ZAP, backend, and frontend.
- Use Python, FastAPI, Pydantic, SQLAlchemy, SQLite, and httpx for the backend.
- Use React with Vite for the frontend.
- Run OWASP ZAP in daemon mode and drive it through the ZAP API.
- Use polling rather than Server-Sent Events or WebSocket for Review Run status updates.
- Persist review state in SQLite, including Review Runs, Hypotheses, Findings, Evidence Packets, Skill Runs, and Review Dispositions.
- Allow only one active Review Run at a time.
- Reject scan requests for any target other than the configured Juice Shop Target Application.
- Keep target configuration backend-owned. The frontend should display the target but not invite arbitrary target entry.
- Use statuses: Queued, Zapping, Triaging, Ready For Skills, Probing, Completed, Failed, and Cancelled.
- Keep cancellation best-effort. The backend should mark the run Cancelled, attempt to stop active ZAP work, and have Review Skills check cancellation between steps.
- Normalize all ZAP alerts into the shared Finding shape. Do not pass raw ZAP alert JSON to the frontend.
- Use a unified Findings list with source-specific detail sections.
- Normalize severity to Critical, High, Medium, Low, and Informational.
- Include Review Dispositions: Unreviewed, True Positive, False Positive, Duplicate, and Needs Investigation.
- Distinguish Hypotheses from Findings. Hypotheses are testable risks; Findings require evidence.
- Require Evidence Packets for Business Logic Findings.
- Sanitize Evidence Packets before storage and display, especially auth headers, cookies, and tokens.
- Build Agent Triage as a lightweight reasoning step that reviews Observed Output and recommends Review Skills.
- Use bounded Review Skills instead of an open-ended autonomous research agent.
- Implement initial Review Skills for account boundaries, basket and checkout manipulation, review ownership, and coupon or discount behavior.
- Postpone broad workflow consistency testing until the narrower skills are stable.
- Use HTTP/API probes for initial Review Skills. Browser automation is optional later for flows that cannot be exercised cleanly through HTTP.
- Seed or reuse two normal users, User A and User B, during a Review Run.
- Run ZAP unauthenticated initially. Use authenticated actor-specific probes in Review Skills.
- Use NVIDIA NIM for LLM-backed Agent Reasoning when configured.
- Provide a mock LLM provider so Docker Compose can run without an API key.
- Keep LLM access backend-only. The frontend must never receive provider secrets.
- Use Agent Reasoning for triage, skill recommendation, evidence interpretation, and remediation drafting when scanner guidance is unavailable.
- Do not let the LLM directly control arbitrary network access. Backend code owns guarded actions and target restrictions.
- Build deep backend modules around:
  - Review Run orchestration
  - ZAP adapter
  - Finding normalization
  - Evidence sanitization
  - Review Skill execution
  - LLM reasoning client
  - Persistence repositories
- Build frontend modules around:
  - Review Run header and progress
  - Scan history
  - Hypothesis and skill recommendation queue
  - Unified findings list
  - Finding detail and disposition controls
- The README should explain black-box scope, ZAP API choice, polling choice, SQLite choice, bounded-agent choice, NVIDIA NIM configuration, mock mode, and limitations.

## Testing Decisions

- Backend tests should focus on external behavior and product guardrails, not private implementation details.
- Test that scan requests against non-configured targets are rejected.
- Test that a second active Review Run cannot be started while one is already active.
- Test ZAP alert normalization into the shared Finding shape.
- Test ZAP severity mapping into the normalized severity model.
- Test Evidence Packet sanitization removes cookies, bearer tokens, and other sensitive headers.
- Test Review Disposition updates persist.
- Test mock Agent Triage returns structured Hypotheses and recommended Review Skills.
- Test Review Skill outputs create Findings only when an Evidence Packet is present.
- Test cancellation transitions an active Review Run to Cancelled and prevents additional skill steps.
- Frontend tests are lower priority. Manual verification and a short screenshot or walkthrough are sufficient unless time remains.
- End-to-end verification should use Docker Compose to bring up Juice Shop, ZAP, backend, and frontend, then start a Review Run from the dashboard and inspect emerging findings.

## Out of Scope

- Inspecting source code or repository files from Juice Shop or any business application.
- Complete Juice Shop challenge coverage.
- Fully autonomous vulnerability discovery.
- A general-purpose source-code auditing agent.
- Multi-target scanning.
- Multi-tenant review workflows.
- Authentication, user management, and reviewer accounts for the dashboard.
- Production deployment, Kubernetes, CI/CD, or cloud hosting.
- Authenticated ZAP scanning with login scripts and ZAP contexts.
- Comprehensive browser automation for all user flows.
- Polished visual design beyond a clean, readable reviewer workbench.
- UI test coverage beyond optional smoke checks.

## Further Notes

- This product should be framed as a human review workbench, not as a magic scanner.
- ZAP is responsible for scanner findings; the Skill-Based Agent is responsible for bounded business-logic investigation.
- Agent outputs are advisory until backed by Evidence Packets and reviewed by a human.
- The README is part of the deliverable and should be treated as seriously as the code because the assignment values reasoning and trade-off decisions.
- A screenshot or short recording should show the dashboard starting a Review Run, showing progress, listing findings or hypotheses, and opening a finding or evidence detail.
