# Run Review Ownership Skill End-To-End

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Add a Review Ownership Review Skill using the established skill runner, actor setup, evidence sanitizer, and Finding path. The skill should create or identify a review under User A and test whether User B can edit, delete, or otherwise affect that review, creating a Finding only when ownership boundaries are violated.

## Acceptance criteria

- [ ] Review Ownership Skill can be run for a Review Run.
- [ ] Skill creates or identifies a User A review in Juice Shop.
- [ ] Skill attempts bounded cross-actor operations as User B.
- [ ] Skill persists running/completed/failed status and an outcome summary.
- [ ] Evidence Packets compare expected ownership enforcement against observed behavior.
- [ ] Business Logic Findings are created only when cross-user review ownership bypass evidence exists.
- [ ] Frontend shows the skill in the Review Queue and can display its results.
- [ ] Backend tests cover evidence-gated Finding creation and inconclusive outcome handling.

## Blocked by

- 0006 Run Account Boundary Skill End-To-End
