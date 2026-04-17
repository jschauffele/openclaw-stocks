# CLAUDE.md — OpenClaw Stocks

## Canonical environment
Path: /opt/openclaw-stocks on DigitalOcean VPS (Ubuntu 24.04.4, SFO3). This is the only runtime authority. Do not trust any local Mac mirror until Phase 2 completes and git becomes the source of truth.

## What this is
Single-operator paper-trading bot on Alpaca paper endpoint. One run per scheduler tick (every 15 min via openclaw.timer). Each run: guard → data → strategy → account → duplicate → risk → reconcile → decision → submit → log. Event-sourced: one JSONL per run in logs/<run_id>.jsonl.

## Design rules
Paper only, killswitch gated (OPENCLAW_ENABLED). Deterministic, strictly staged, no skipping. Read/write separation: strategy, decision, signal_validator are pure. bot_service orchestrates, never decides. Event log is source of truth; order_state.json and last_run_report.json are derived views.

## Anti-goals
Never place a live (non-paper) trade. Never bypass the market-session guard. Never add I/O to the read layer. Never edit .py files on the VPS after Phase 2. Never commit .env or credentials. Never skip phases.

## Phase ladder
- [x] Phase 0: Reconciliation, HANDOFF.md written.
- [ ] Phase 1: VPS Claude Code sync, forced-execution test, commit context docs.
- [ ] Phase 2: Git becomes source of truth. Local Mac becomes dev authority.
- [ ] Phase 3: Code fixes — main.py wiring test, event coverage test, timestamp additive compat, qty*latest_close risk sizing, delete shims.
- [ ] Phase 4: Deployment discipline — VPS read-only for code.
- [ ] Phase 5: Paper shadow for 2 weeks of market days.
- [ ] Phase 6: Paper live, qty=1, daily review.
- [ ] Phase 7: Monitoring, circuit breaker, runbook.

## Operator protocol
Every assistant session starts by reading this file, HANDOFF.md, and the most recent logs/*.jsonl. Memory lives in the repo, not in the model. Concise, direct, copy/paste-ready commands. No micro-check loops. Commands in code blocks, expected output in prose. Institutional: controlled, minimal, deterministic.
