# Controlled Evolution Doctrine

## Purpose

This document defines how OpenClaw may improve over time. It is doctrine only.
It does not approve runtime changes, strategy changes, parameter changes,
portfolio allocation changes, execution activation, evaluation infrastructure,
or autonomous optimization.

OpenClaw improves through evidence, replay, evaluation, governed approval, and
controlled promotion, not live self-modification.

## Production Runtime

The production runtime must remain deterministic, versioned, and reproducible.

Production behavior should be explainable from:

- Versioned source code.
- Versioned configuration.
- Recorded inputs.
- Recorded portfolio and broker-visible state.
- Deterministic signal outputs.
- Deterministic reconciliation decisions.
- Deterministic execution gating decisions.

The same approved production version, given the same inputs and state, should
produce the same decisions. Runtime behavior must not change because a live
model, agent, optimizer, or strategy mutates itself during operation.

## Offline Research and Evaluation

Research and evaluation may explore alternatives offline.

Offline work may compare strategies, parameters, allocation rules, ranking
methods, replay outcomes, and risk controls. It may use historical data,
recorded production observations, simulation, paper evaluation, or other
approved research inputs.

Offline evaluation is not production authority. A researched alternative must
not affect live behavior until it is reviewed, approved, versioned, and promoted
through a controlled process.

## No Live Self-Modifying Strategies

Production strategies must not modify their own logic while live.

A live strategy may evaluate current inputs according to approved code and
configuration, but it must not rewrite its rules, introduce new decision logic,
change its objective, or alter its own implementation during runtime.

Strategy evolution requires evidence and promotion, not live mutation.

## No Live Autonomous Parameter Mutation

Production parameters must not be autonomously changed by the live runtime.

This includes thresholds, weights, caps, sizing values, ranking coefficients,
strategy eligibility settings, risk budgets, and execution-related parameters.

Parameter changes require replay, evaluation, approval, and promotion. A live
system may observe that a parameter appears suboptimal, but it must not mutate
that parameter in production without governed approval.

## No Live AI Execution Authority

AI must not have live execution authority.

An AI system may not independently approve, create, resize, route, cancel, sell,
rebalance, or otherwise mutate broker-facing production behavior. It may not
convert advice into execution permission.

Execution permission remains a governed system boundary and must be granted only
through approved deterministic runtime paths.

## Strategy Change Requirements

Strategy changes require evidence and promotion.

Before a strategy change can affect production, it should have:

- A clear hypothesis or defect rationale.
- Offline replay or evaluation evidence.
- Comparison against the current approved behavior.
- Risk and boundary review.
- Versioned implementation.
- Approval for promotion.
- A rollback or deactivation plan when appropriate.

No strategy change is production-approved merely because it performs well in one
observation, one market condition, or one ad hoc manual review.

## Parameter Change Requirements

Parameter changes require replay, evaluation, and promotion.

Before a parameter change can affect production, it should have:

- The current parameter value and proposed value.
- The reason for the proposed change.
- Replay or evaluation evidence.
- Sensitivity analysis where appropriate.
- Impact on risk, exposure, ranking, allocation, or execution boundaries.
- Approval for promotion.
- Versioned configuration.

Parameter changes should be treated as governed behavior changes, not casual
runtime tuning.

## Portfolio Allocation Change Requirements

Portfolio allocation changes require governance approval.

Changes to allocation rules, exposure budgets, cap hierarchy, ranking
arbitration, adaptive sizing, sell behavior, rebalance behavior, or
portfolio-construction objectives can materially change system behavior.

Such changes require explicit approval before implementation or production use.
They must not be smuggled into strategy logic, reconciliation logic, execution
logic, AI advice, or runtime visibility tooling.

## AI Role

AI may advise, evaluate, compare, and recommend. AI may not mutate production
runtime.

Approved AI uses may include:

- Summarizing runtime observations.
- Comparing replay results.
- Identifying candidate improvements.
- Drafting hypotheses.
- Reviewing governance implications.
- Producing reports for human review.
- Recommending future experiments.

Non-approved AI uses include:

- Changing production strategy code.
- Changing production parameters.
- Approving execution.
- Creating broker-facing actions.
- Rebalancing the portfolio.
- Overriding deterministic risk controls.
- Mutating live configuration or runtime state.

AI can support governance. It cannot replace governance.

## Future Improvement Path

OpenClaw's improvement path is:

1. Observe.
2. Record.
3. Replay.
4. Evaluate.
5. Approve.
6. Promote.

Observation identifies behavior. Recording preserves inputs, state, decisions,
and outcomes. Replay reproduces the behavior under controlled conditions.
Evaluation compares alternatives. Approval determines whether a change is
allowed. Promotion moves the approved change into a versioned production path.

This sequence prevents live experimentation from becoming uncontrolled
production behavior.

## Deferred Implementation

Implementation remains deferred unless a future phase explicitly opens
evaluation infrastructure.

This doctrine does not approve:

- Replay infrastructure.
- Experiment tracking.
- Offline optimizer implementation.
- Strategy promotion tooling.
- Parameter promotion tooling.
- Portfolio allocation engines.
- AI-controlled runtime mutation.
- Live adaptive optimization.

Those capabilities may be considered later, but only through an explicit phase
that defines scope, authority, data requirements, audit requirements, and
promotion controls.

Until then, OpenClaw remains governed by deterministic production behavior and
controlled, documented evolution.
