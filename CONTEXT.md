# AppSec Review

This context describes a small application security review system for OWASP Juice Shop. It distinguishes automated scanner output from agent-assisted business logic review.

## Language

**Target Application**:
The running web application being reviewed. In this project, the only valid Target Application is OWASP Juice Shop.
_Avoid_: customer repo, source repository, codebase

**Black-Box Review**:
A review performed by interacting with the running Target Application and its HTTP behavior, without inspecting source code or repository files.
_Avoid_: source-code audit, static analysis

**Skill-Based Agent**:
An LLM-assisted reviewer that follows explicit testing playbooks to investigate business logic behavior in the Target Application.
_Avoid_: repo agent, static analyzer

**Agent Reasoning**:
LLM-generated interpretation of sanitized Observed Output, used to create Hypotheses, recommend Review Skills, and explain evidence. Agent Reasoning does not directly control network access or bypass backend guardrails.
_Avoid_: unrestricted tool use, autonomous browser control

**Review Skill**:
A reusable business-risk playbook used by the Skill-Based Agent, such as account boundary testing, checkout manipulation, coupon abuse, review ownership, or workflow consistency.
_Avoid_: Juice Shop challenge solver, one-off exploit script

**Agent Triage**:
The Skill-Based Agent's lightweight review of Observed Output to produce Hypotheses and recommend which Review Skills should run next.
_Avoid_: full autonomous scan, final verdict

**Review Run**:
One end-to-end attempt to review the Target Application, moving through scanner work, agent triage, optional skill probes, and human review.
_Avoid_: raw scan job

**Review Run Status**:
The current phase of a Review Run. Valid statuses are Queued, Zapping, Triaging, Ready For Skills, Probing, Completed, Failed, and Cancelled.
_Avoid_: generic running state

**Observed Output**:
Evidence produced by the Target Application or scanner during a Black-Box Review, such as HTTP behavior, UI-visible responses, logs surfaced by the review system, or normalized ZAP findings.
_Avoid_: source code, repository context

**Evidence Packet**:
The structured proof attached to a Business Logic Finding, including the Review Skill, tested scenario, actor context, relevant request and response details, expected behavior, observed behavior, and timestamp.
_Avoid_: full raw traffic dump, unsanitized transcript

**Actor Context**:
The identity boundary used during a Black-Box Review, such as Anonymous, User A, or User B. Actor Contexts describe who performed an observed action without exposing session tokens or credentials.
_Avoid_: raw auth token, credential dump

**Business Logic Finding**:
A human-reviewable issue based on workflow behavior, authorization boundaries, or application rules rather than a generic scanner signature.
_Avoid_: raw alert, scanner hit

**Hypothesis**:
A possible business logic risk that appears worth testing but does not yet have enough evidence to be a Finding.
_Avoid_: vulnerability, confirmed issue

**Finding**:
A human-reviewable issue with concrete evidence, severity, description, and remediation guidance. A Finding may originate from ZAP as a Scanner Finding or from a Review Skill as a Business Logic Finding.
_Avoid_: hypothesis, raw alert

**Scanner Finding**:
A normalized issue reported by OWASP ZAP after scanning the Target Application.
_Avoid_: raw ZAP alert

**Review Disposition**:
The human reviewer's classification of a Finding after inspection. Valid dispositions are Unreviewed, True Positive, False Positive, Duplicate, and Needs Investigation.
_Avoid_: agent verdict, final scanner status

## Example Dialogue

Developer: "Should the agent read the business repository?"

Reviewer: "No. This is a Black-Box Review of the Target Application. The Skill-Based Agent may interact with Juice Shop and reason over observed behavior, but it does not inspect source code."

Developer: "Then what counts as a finding?"

Reviewer: "A Scanner Finding comes from ZAP. A Business Logic Finding comes from a skill-driven workflow test and must include evidence a human reviewer can inspect."

Developer: "Can the agent start by reading scan results before it drives its own tests?"

Reviewer: "Yes. The Skill-Based Agent may begin by reasoning over Observed Output, then perform active Black-Box Review steps when a skill needs more evidence."

Developer: "Should skills be named after Juice Shop challenges?"

Reviewer: "No. A Review Skill should describe a reusable business-risk category, even when its probes are tailored to Juice Shop."

Developer: "Does the agent decide whether a vulnerability is real?"

Reviewer: "No. The agent can propose a Finding, but the human reviewer assigns the Review Disposition."

Developer: "Can the agent show speculative risks?"

Reviewer: "Yes, but speculative risks are Hypotheses. They become Findings only after the review system captures concrete evidence."

Developer: "How much proof does a Business Logic Finding need?"

Reviewer: "It needs an Evidence Packet. The packet should show what was tested, who acted, what the application returned, and why the observed behavior differs from the expected behavior."

Developer: "Why do we need two users?"

Reviewer: "Business logic review often depends on Actor Context. User A and User B make account-boundary, basket, order, and review ownership behavior testable."

Developer: "Should all Review Skills run automatically?"

Reviewer: "No. Agent Triage recommends Review Skills from Observed Output, and the human reviewer chooses which skills to run or uses a Run Recommended Skills shortcut."

Developer: "Why not just show running or completed?"

Reviewer: "A Review Run has distinct phases. Zapping, Triaging, Ready For Skills, and Probing tell the reviewer whether scanner work, agent reasoning, or skill execution is currently happening."

Developer: "Does the LLM directly operate the application?"

Reviewer: "No. Backend code performs guarded probes and captures evidence. Agent Reasoning interprets sanitized observations and returns structured recommendations or explanations."
