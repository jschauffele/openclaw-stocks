# OpenClaw Stocks Roadmap

This document is planning-only.

It defines the current local-repo documentation posture after successful paper-mode validation.
It does not authorize runtime changes, deployment, or production workflow changes.

## Current posture

- stable runtime behavior has already been validated in paper mode
- VPS runtime and deployment workflow remain out of scope for this cleanup pass
- local work is limited to documentation and architecture clarification unless a new change window is explicitly opened
- code cleanup, staging, commits, and deployment are not part of this task

## Documentation structure

Use each root document for one purpose only.

### Runtime-adjacent

These documents describe the validated runtime path or operator-facing checks.
They should be treated cautiously and should not be casually rewritten during local doc cleanup.

- `README.md`: high-level entry point and runtime-adjacent quick reference
- `BUILD_STATUS.md`: runtime status snapshot and validated controls summary
- `MARKET_OPEN_CHECKLIST.md`: operator runbook for market-session readiness

### Architecture-only

These documents explain the local refactor shape and boundary discipline.

- `ARCHITECTURE.md`: current layer map and clean-architecture intent
- `LAYER_AUDIT.md`: current leak audit and boundary classification

### Planning-only

These documents explain what should happen later, not what should be changed immediately.

- `ROADMAP.md`: current cleanup posture, scope limits, and safe cleanup order
- `PHASE_1_2_BLUEPRINT.md`: near-term planning backlog and sequencing
- `COMPATIBILITY_CLEANUP_PLAN.md`: staged plan for legacy-path cleanup
- `FULL_BLUEPRINT.md`: long-range platform doctrine and phase map

## Current cleanup goal

The goal of the current local cleanup pass is to make the documentation easier to navigate without changing runtime meaning.

That means:

- clarify which docs describe runtime reality
- clarify which docs are planning-only
- reduce overlap between architecture docs and planning docs
- leave VPS and deployment guidance untouched unless a later task explicitly reopens that work

## Safe cleanup order

Follow this order to minimize risk:

1. update planning-only docs that contain outdated phase framing
2. align architecture-only docs so they describe the local refactor consistently
3. trim duplicate planning language across the blueprint documents
4. review runtime-adjacent docs last, and only for wording drift that does not alter operator instructions

## What to avoid

Do not:

- change runtime behavior
- edit code files during documentation cleanup
- rewrite deployment instructions as part of a structure cleanup
- mix local refactor planning with production promotion decisions
- stage, commit, or deploy anything from this cleanup pass

## Current next-step logic

If a future task is documentation-only:

1. classify the target file first
2. prefer planning-only files before architecture-only files
3. avoid runtime-adjacent files unless the wording is clearly stale and the change is purely descriptive

If a future task needs code or deployment changes:

- stop this documentation-only workflow
- open a separate task with explicit approval for that kind of work
