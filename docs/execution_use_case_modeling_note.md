# Broker-Agnostic Execution Use-Case Modeling Note

## Purpose

This note defines the first broker-agnostic execution request, outcome, and use-case contract.

The first execution use case accepts already-approved trade intent only. Strategy, risk, duplicate protection, and broker-state eligibility policy remain outside this boundary.

## ExecutionRequest

`ExecutionRequest` should represent a prevalidated trade intent with these fields:

- `run_id`
- `broker_name`
- `mode`
- `symbol`
- `side`
- `qty`
- `order_type`
- `trigger_source`
- `strategy_reason`
- `signal`
- `decision`

It must not contain native broker order payloads, IBKR contracts, Alpaca request objects, or runtime visibility state.

## ExecutionOutcome

`ExecutionOutcome` should represent the broker-agnostic result of attempting or simulating execution:

- `result`
- `reason`
- `mode`
- `broker_name`
- `order_status`
- `submit_state`
- `reconciliation_status`
- `manual_review_required`
- `terminal_for_run`
- `reconciliation_ambiguous`
- `filled_qty`
- `working_qty`
- `notes`
- `raw_submit_result`
- `raw_reconciliation_result`

The outcome should be suitable for existing report and event fields without exposing native broker mechanics as policy.

## First Use-Case Contract

The first use-case contract should be:

```python
execute_prevalidated_market_order(
    request,
    broker,
    reconciliation_workflow=None,
    clock=None,
) -> ExecutionOutcome
```

This use case coordinates order preparation, dry-run handling, paper-submit handling, uncertain-submit reconciliation, and structured outcome mapping.

It explicitly excludes:

- strategy generation
- risk policy
- duplicate protection
- broker-state eligibility policy
- runtime visibility enforcement
- retry or resubmit policy
- cancel, flatten, or remediation behavior

## Adapter Boundary

Broker adapters provide mechanics only:

- build broker-specific order payloads
- submit when instructed by the use case
- normalize broker responses
- provide broker read snapshots needed by reconciliation

Adapters must not authorize execution or own retry, remediation, or manual-review policy.

## Activation Boundary

Fake-broker use-case testing must precede IBKR activation.

`broker_factory.py` changes and IBKR production activation remain deferred until the use-case boundary is tested with fakes and separately reviewed for paper-only IBKR execution.
