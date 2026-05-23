# AI Execution Governance

## Purpose

This document defines the token-efficient, zero-drift operating standard for Codex, Cursor, and AI-assisted OpenClaw development.

Use this document as the first retrieval target for future AI work. Prefer it over broad repo scanning.

## Operating Priority

Correctness outranks token savings.

Token efficiency is required, but it must not weaken boundary discipline, validation, source-of-truth alignment, or runtime safety.

## Local Execution Providers

### Source Of Truth

- GitHub `main` remains the source of truth.
- VPS remains runtime, deploy, and log validation only.
- Local AI work is never a new source of truth.

### Codex And Cursor Roles

- `CODEX_LOCAL` is the default local execution provider for AI-assisted work.
- `CURSOR_LOCAL` is equivalent to `CODEX_LOCAL`, not a separate authority.
- Cursor may be used as a temporary local execution provider when Codex limits are reached.
- Cursor must follow the same institutional rules as `CODEX_LOCAL`.
- Only one AI tool may operate on uncommitted work at a time.

### Switching Between Codex And Cursor

Before switching between Codex and Cursor, verify:

```bash
git status --short
git log -1 --oneline
git log origin/main -1 --oneline
```

Before returning to Codex, local `HEAD` and `origin/main` must be aligned, or the uncommitted state must be explicitly summarized.

### Cursor Work Requirements

Cursor gates must use:

- a read-only checkpoint first
- strict file scope
- explicit allowed and disallowed files
- minimal diffs
- no repo-wide scanning unless approved
- validation and classification required

### Cursor Prohibitions

Unless a separate task explicitly approves otherwise, Cursor must not perform VPS, runtime, broker, or live-trading work.

## Default Constraints

Unless a task explicitly approves otherwise:

- do not run `main.py`
- do not use VPS
- do not run broker commands
- do not activate IBKR, TWS, or live runtime paths
- do not run full test suites
- do not edit runtime, broker, execution, risk, observation, JSONL, reporting, state, or config files
- do not edit Python files during docs-only gates
- do not change behavior during planning or evidence gates

## Repo-Scope Discipline

Read the narrowest files needed for the current gate.

Do not do repo-wide scanning unless the task explicitly approves it or the bounded file set is insufficient to answer the request.

Preferred inspection order:

1. current user task
2. relevant freeze or governance doc
3. directly named files
4. directly adjacent tests
5. targeted `rg` for exact symbols only

Avoid speculative exploration.

## Read-Only Checkpoint Rule

Before a new implementation family or runtime boundary change, run a read-only checkpoint.

A read-only checkpoint must determine:

- current source-of-truth HEAD
- relevant approved scope
- files allowed for the next gate
- files that must not be touched
- expected tests
- operational risks
- whether implementation is premature

No code changes may occur during a read-only checkpoint.

## Delta-Prompting Workflow

Use delta prompts instead of reloading the whole project.

Each gate should state:

- current HEAD or known source-of-truth commit
- completed prior gate
- exact allowed files
- exact forbidden files
- exact commands allowed
- expected return format
- classification token

Future AI agents should trust committed governance docs and prior checkpoint summaries unless direct evidence contradicts them.

## Boundary Discipline

Preserve Clean Architecture direction:

- pure strategy metadata stays independent of runtime mechanisms
- report-only metadata must not affect execution behavior
- `reporting.py` remains pass-through unless a separate gate approves otherwise
- `main.py` remains runtime sequencing authority until a separate test-first extraction gate is approved
- JSONL and observation emission remain separate approval gates
- replay-authoritative metadata requires a separate schema/replay gate

Do not move policy into formatting, persistence, broker, observation, or reporting helpers.

## Validation Discipline

Run only the validation named by the task.

Prefer isolated targeted tests over combined bundles when tests inspect process-global state such as `sys.modules`.

Known report metadata validation order:

1. seam tests separately
2. main metadata tests separately

Do not treat raw local `main.py` execution as an approved validation path when broker credentials or runtime dependencies are required.

## Drift Control

Any temporary scaffold, brittle test, deferred boundary, or known limitation must be recorded before moving on.

Use:

- `docs/architecture_drift_risk_register.md` for active and resolved risks
- `docs/architecture_governance_freeze_snapshot.md` for the compact approved state
- `docs/deterministic_strategy_architecture.md` for chronological evidence

If docs disagree, stop and run a read-only governance consolidation checkpoint before implementation.

## Commit And Push Discipline

Commit only files approved by the task.

Before commit:

- inspect `git status --short`
- ensure forbidden files are untouched
- ignore unrelated untracked local-only environments

After push:

- verify local HEAD
- verify `origin/main` HEAD
- report final `git status --short`

## Classification Discipline

Every gate response should end with the requested classification token.

If evidence is incomplete, use the blocked or uncertain classification rather than overstating success.
