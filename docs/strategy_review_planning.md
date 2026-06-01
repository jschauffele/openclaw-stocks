# Strategy Review Planning

## Purpose

This document defines a docs-only planning gate for the next possible non-metadata OpenClaw strategy phase.

It does not approve implementation, trading behavior changes, live trading, IBKR/runtime work, broker work, JSONL emission, observation emission, risk changes, order behavior, or reporting behavior changes.

## Current State

Current strategy behavior remains unchanged.

Current report metadata work is complete and stopped.

Strategy development requires a separate review gate before code.

Any future strategy change must preserve deterministic behavior. AI may advise during planning and review, but AI must not execute trades, override deterministic rules, bypass policy, or become runtime authority.

Strategy, risk, execution, broker, and runtime boundaries remain separate.

No signal, action, risk, order, broker, runtime, JSONL, observation, or reporting behavior changes are approved by this document.

Runtime orchestration extraction remains deferred until concrete pressure appears.

Replay authority remains deferred.

JSONL and observation strategy expansion remain deferred.

VPS validation is not needed for this docs-only phase.

## Strategy/Risk Roadmap Rebase

Strategy/risk remains governance-only. This roadmap rebase does not approve
strategy behavior changes, risk behavior changes, evaluation, promotion,
broker/API work, IBKR action, or live trading.

Current production strategy state:

- Production strategy behavior remains the existing close-based momentum path.
- `close_momentum_v1` remains the default strategy catalog entry.
- Strategy metadata has no execution authority and no broker compatibility
  authority.
- Regime classifier, strategy router, and strategy integration scaffolds remain
  deterministic metadata/control-plane scaffolds only.

Current production risk state:

- Risk behavior remains hard-cap enforcement through reconciliation and risk
  checks.
- Saturated BUY proposals may remain visible as strategy demand while
  reconciliation blocks projected exposure above `max_position_size`.
- No automatic sell, trim, rebalance, dynamic sizing, portfolio construction,
  allocation arbitration, short or hedge behavior, adaptive optimization, or
  strategy promotion is approved.

Broad 3-close evidence continuation is closed unless a sharper hypothesis or
defect rationale is opened. Future treasury-proxy/MSTR, portfolio
construction, regime routing, short/hedge, and multi-strategy work remain
future architecture only.

Any future strategy/risk implementation requires:

- Explicit hypothesis or defect rationale.
- Deterministic acceptance criteria and fixtures.
- Strategy ID compatibility or new strategy ID decision.
- Replay-grade input and state package contracts.
- Evaluation and attribution framework.
- Promotion workflow with approval, monitoring, and rollback criteria.
- As-of feature availability contract.
- Portfolio/risk state contract before allocation, ranking, resize,
  suppression, trim, exit, or rebalance logic.
- Risk review for cap, sizing, allocation, sell, hedge, or short behavior.
- Proof-boundary separation between signal, allocation, risk, reconciliation,
  execution permission, and broker execution.

## Possible Next Strategy Surfaces

### Controlled Improvement Of Current 3-Close Momentum Strategy

Surface type:

- Strategy

Status:

- Safe now for docs-only review.
- Deferred for implementation.

Missing evidence/input:

- Clear target behavior for improving the current close-momentum rule.
- Historical examples or acceptance criteria showing why the current 3-close rule should change.
- Deterministic comparison criteria that do not depend on AI discretion.
- Explicit decision on whether the current strategy ID remains compatible or a new strategy ID is required.

Required future gate before implementation:

- Strategy behavior review gate defining exact deterministic rule changes, expected fixtures, backward-compatibility impact, and targeted tests.

### Regime-Classifier Planning

Surface type:

- Strategy

Status:

- Safe now for docs-only review.
- Deferred for implementation.

Missing evidence/input:

- Concrete regime definitions to add or adjust.
- Threshold rationale and examples for any new or changed regime behavior.
- Deterministic fixture set covering boundary cases.
- Decision on whether existing regime IDs remain stable.

Required future gate before implementation:

- Regime classifier planning gate defining exact classification changes, allowed regime IDs, validation cases, and import/side-effect boundaries.

### Deterministic Strategy-Router Planning

Surface type:

- Strategy

Status:

- Safe now for docs-only review.
- Deferred for implementation.

Missing evidence/input:

- Concrete routing objective.
- Strategy catalog changes, if any.
- Deterministic tie-break and rejection evidence requirements.
- Expected behavior when no strategy is eligible.

Required future gate before implementation:

- Strategy router planning gate defining catalog/routing changes, deterministic ordering, evidence fields, and targeted tests.

### Treasury-Proxy/MSTR-Style Strategy Research Planning

Surface type:

- Documentation
- Strategy research

Status:

- Safe now for docs-only research planning.
- Deferred for implementation.

Missing evidence/input:

- Reference material defining the thesis, instruments, constraints, and time horizon.
- Explicit decision on whether this is research-only, paper-trading-only, or a future strategy candidate.
- Deterministic data inputs and evaluation metrics.
- Boundary decision separating strategy research from risk sizing and broker execution.

Required future gate before implementation:

- Research review gate with user-provided source material, deterministic assumptions, allowed instruments, prohibited live behavior, and criteria for whether the research may become a strategy candidate.

### IBKR Strategy-Readiness Boundary Planning

Surface type:

- Broker
- Runtime
- Documentation

Status:

- Deferred.

Missing evidence/input:

- Explicit approval to resume IBKR or broker-boundary work.
- Current IBKR runtime objective.
- Paper/live boundary decision.
- Required local or VPS validation scope.

Required future gate before implementation:

- Separate broker/runtime boundary checkpoint. This must define allowed commands, forbidden live behavior, environment, validation path, and rollback/safety constraints before any IBKR work.

### Paper-Trading Validation Criteria Planning

Surface type:

- Documentation
- Runtime validation planning

Status:

- Safe now for docs-only planning.
- Deferred for runtime execution.

Missing evidence/input:

- Exact paper-trading success criteria.
- Required reports, logs, and observations to inspect.
- Decision on whether validation is local-only or VPS runtime/log validation.
- Explicit list of allowed commands and forbidden broker/live paths.

Required future gate before implementation:

- Runtime validation planning gate defining paper-trading validation criteria, allowed environment, allowed commands, artifacts to inspect, and safety boundaries.

## Recommended Next Step

The 3-close stronger trend confirmation evidence phase is closed for now. Do not continue collecting more 3-close evidence under the current hypothesis.

Return to higher-value OpenClaw roadmap work unless a new, sharper strategy hypothesis is explicitly defined. Future strategy research should avoid over-investing in close-only 3-candle confirmation unless paired with a clearer discriminating feature or regime filter.

If no concrete strategy objective is available, pause strategy implementation work. Do not advance to runtime, broker, replay, JSONL, observation, or IBKR work from this document.
