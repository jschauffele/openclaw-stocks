# OpenClaw Stocks Roadmap

## Current Phase

The system is in a strict no-drift confidence-day window.

Status:
- Stable VPS runtime on `main` is the operational source of truth.
- Day 10 passed.
- One more confidence day (Day 11) is pending.
- No runtime-affecting changes are allowed until that confidence day is complete.

## Immediate Next Step

Run one more confidence day exactly as-is.

That means:
- no code changes
- no VPS changes
- no deployment
- no `.env` changes
- no service or timer changes
- observation and validation only

## Allowed Work Before Day 11 Completes

Allowed work is limited to documentation and planning only:
- architecture clarification
- boundary clarification
- README clarity improvements
- operator/runbook wording cleanup
- planning documents
- explicit phase-boundary documentation

## Not Allowed Before Day 11 Completes

Do not:
- modify runtime behavior
- edit active-path files
- deploy local refactor work
- change stable VPS `main`
- change dry-run behavior
- change validated execution order
- change service, timer, or environment configuration
- begin Phase 2 code cleanup
- treat local refactor work as deploy-ready
- assume local, GitHub, and VPS are synchronized without verification

## Source Of Truth During This Window

Use the stable VPS runtime behavior as the source of truth for confidence-day evaluation.

Do not let local refactor progress change the confidence-day story.

## Decision Deferred Until After Day 11

After the next confidence day completes, evaluate one of these paths:

Option A:
- enable paper order submission
- disable `dry_run`
- monitor actual paper-order behavior

Option B:
- remain in `dry_run`
- continue observation
- continue strategy refinement
- gather more confidence first

Do not choose between Option A and Option B yet.
