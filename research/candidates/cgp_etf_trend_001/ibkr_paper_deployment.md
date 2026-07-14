# CGP-ETF-TREND-001 — IBKR Paper Deployment Boundary

This document does not authorize execution. It defines the required interface and safety gates if the candidate survives research validation.

## Broker

- Broker: Interactive Brokers.
- Initial environment: paper account only.
- Connectivity: existing repository-controlled IBKR runtime and adapter path.
- Candidate modules must never connect directly to TWS or IB Gateway.
- Candidate modules must never call `placeOrder`, cancel, flatten, retry, or remediate.

## Control-plane separation

1. The candidate computes desired target weights from certified historical or live decision inputs.
2. A separate portfolio-to-order adapter converts target weights to IBKR-qualified contracts and integer/fractional quantities supported by the account.
3. Existing IBKR risk, approval, submit, and reconciliation controls retain sole execution authority.
4. Runtime visibility is evidence only and does not authorize execution.

## Required pre-shadow gates

- research and historical holdout gates passed;
- candidate commit and configuration frozen;
- independent reproduction passed;
- all 14 ETF contracts qualify unambiguously in IBKR;
- exchange, currency, primary listing, and conId recorded;
- account paper status verified;
- no unmanaged positions or open orders;
- target-to-order conversion deterministic;
- cash, buying-power, quantity rounding, and minimum-order behavior tested;
- duplicate-order and reconnect behavior tested;
- no candidate code changes to `broker_factory.py`, `main.py`, or IBKR safety gates.

## Shadow phase

For at least two monthly decision cycles, generate but do not transmit orders. Persist:

- decision timestamp and data cutoff;
- target weights and target dollar values;
- IBKR contract identifiers;
- current positions;
- proposed quantities and order types;
- estimated commissions and slippage;
- all risk blocks and reconciliation results.

Any ambiguity or mismatch fails closed.

## Paper phase

After explicit operator approval, use the existing IBKR paper-only submit workflow. Record:

- order ID and permanent ID;
- submission, acknowledgment, partial-fill, fill, reject, and cancel timestamps;
- fill quantities and prices;
- IBKR commissions;
- target-versus-realized weights;
- end-of-cycle position and cash reconciliation;
- reconnect and duplicate-order evidence.

No automatic retry, resubmit, flatten, or remediation is permitted unless separately authorized by the existing IBKR architecture.

## Shutdown conditions

Immediately stop new orders for:

- live account detection;
- non-paper port or unapproved connection context;
- ambiguous contract qualification;
- stale input data;
- target/order mismatch;
- unresolved open order;
- position or cash reconciliation mismatch;
- duplicate order evidence;
- missing permanent order identity;
- code or configuration hash mismatch;
- actual costs outside the preregistered stress envelope;
- any IBKR state that the current architecture classifies as blocking.

## No-rescue rule

A paper execution problem may be repaired only when it is a mechanical infrastructure defect and the frozen strategy remains unchanged. A change to signal timing, universe, sizing, rebalance logic, order interpretation, or fill assumptions creates a new candidate and a new trial.
