# Run Basket And Checkout Skill End-To-End

## Parent

[PRD: AppSec Review Workbench](../PRD.md)

## What to build

Add a Basket And Checkout Review Skill using the established skill runner, actor setup, evidence sanitizer, and Finding path. The skill should perform bounded HTTP-level probes around basket identifiers, quantities, price-sensitive fields, and checkout state, producing Findings only for clear impossible or unauthorized states accepted by the server.

## Acceptance criteria

- [ ] Basket And Checkout Skill can be run for a Review Run.
- [ ] Skill uses existing Actor Context and authenticated HTTP probe infrastructure.
- [ ] Skill tests bounded basket or checkout manipulation scenarios.
- [ ] Skill persists running/completed/failed status and an outcome summary.
- [ ] Evidence Packets are sanitized and attached to any created Business Logic Findings.
- [ ] Inconclusive or rejected manipulations remain skill outcomes, not Findings.
- [ ] Frontend shows the skill in the Review Queue and can display its results.
- [ ] Backend tests cover at least one positive evidence fixture and one inconclusive fixture.

## Blocked by

- 0006 Run Account Boundary Skill End-To-End
