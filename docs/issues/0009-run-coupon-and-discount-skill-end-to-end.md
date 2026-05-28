# Run Coupon And Discount Skill End-To-End

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Add a Coupon And Discount Review Skill using the established skill runner, actor setup, evidence sanitizer, and Finding path. The skill should test bounded discount scenarios only when it has a clear expected rule from visible application behavior or deterministic setup, and it should avoid turning vague discount guesses into Findings.

## Acceptance criteria

- [ ] Coupon And Discount Skill can be run for a Review Run.
- [ ] Skill uses visible or deterministic coupon/discount inputs rather than arbitrary brute force.
- [ ] Skill tests bounded reuse, stacking, or invalid-state scenarios where an expected rule is clear.
- [ ] Skill persists running/completed/failed status and an outcome summary.
- [ ] Evidence Packets include expected discount behavior and observed server behavior.
- [ ] Business Logic Findings are created only when evidence supports a clear discount logic issue.
- [ ] Inconclusive results remain skill outcomes, not Findings.
- [ ] Frontend shows the skill in the Review Queue and can display its results.

## Blocked by

- 0006 Run Account Boundary Skill End-To-End
