# Agent Message Contract

Child agents report to the controller using this shape:

## Result
- Success / partial / blocked / failed

## Observed Facts
- Facts verified by tools or local files

## Actions Taken
- Commands, files changed, services touched

## Files / Artifacts
- Paths created/changed

## Verification
- Checks run and results

## Risks / Assumptions
- What might be wrong or unverified

## Proposed Skill Promotions
- Local skills that may deserve promotion to common/comms
- Do not propose init promotion from child unless Xan explicitly asks

## Remaining Work
- What needs controller/human action

Rules: no secrets, no unverified success claims, no mutation outside assigned scope.
