# Deterministic Strategy Architecture

## Foundation Evidence

Current phase: Deterministic Strategy Architecture.

The deterministic strategy architecture foundation is established through completed gates:

- `b43bc3c Strategy: add deterministic strategy library scaffold`
- `a0c81f6 Strategy: harden strategy library metadata validation`
- `6772e68 Strategy: add deterministic regime classifier scaffold`
- `c10d477 Strategy: harden regime classifier validation`
- `c6d32a3 Strategy: add deterministic strategy router scaffold`
- `2abbc7e Strategy: harden strategy router validation`
- `75d60b3 Strategy: add deterministic strategy integration scaffold`
- `9b5ee1b Strategy: harden strategy integration validation`

Python 3.12 validation evidence:

- `.venv-312/bin/python --version` reported `Python 3.12.13`
- `.venv-312/bin/python -m pytest test_strategy_library.py` reported `23 passed`
- `.venv-312/bin/python -m pytest test_regime_classifier.py` reported `36 passed`
- `.venv-312/bin/python -m pytest test_strategy_router.py` reported `31 passed`
- `.venv-312/bin/python -m pytest test_strategy_integration.py` reported `24 passed`

`strategy_library.py` is a pure inner-policy metadata module. It follows the Clean Architecture Chapter 20 and Chapter 22 boundary: business rules and entities remain pure, dependencies point inward, and inner policy does not depend on outer mechanisms.

`test_strategy_library.py` validates strategy catalog behavior under Python 3.12. The tests cover stable strategy identity, immutable catalog data, duplicate rejection, validation hardening, lookup behavior, and forbidden outer-mechanism imports.

The current strategy metadata does not create broker, runtime, execution, risk, state, reporting, observation, or configuration authority. `execution_authority` remains `False`, and `broker_compatibility` remains empty.

`close_momentum_v1` is metadata only. It records the existing close-momentum strategy shape and observable fields, but it does not add new strategy behavior, routing, execution authority, broker compatibility, or runtime activation.

## Regime Classifier Evidence

`regime_classifier.py` is a pure deterministic inner-policy module. It uses frozen input and result dataclasses with dependency-free primitive values and no side effects.

Allowed regime IDs:

- `insufficient_data`
- `volatile`
- `uptrend`
- `downtrend`
- `sideways`
- `unknown`

`unknown` is reserved only for explicit result construction. It is not an invalid-input fallback. Invalid input raises `ValueError`.

The regime classifier does not route strategies, generate signals, size risk, submit orders, cancel orders, flatten positions, or perform remediation. It does not touch broker, runtime, config, state, observation, reporting, execution, risk, market data, file, environment, network, or VPS behavior.

`test_regime_classifier.py` validates deterministic regime classification under Python 3.12, including frozen dataclasses, allowed regime IDs, validation hardening, invalid input behavior, import isolation, and absence of execution, broker, order, routing, or strategy-selection fields.

## Strategy Router Evidence

`strategy_router.py` is a pure deterministic inner-policy module. It consumes `StrategyDefinition` and `RegimeClassificationResult` only, and it selects eligible strategy metadata only.

The router preserves catalog order for deterministic selection. It filters out execution-authorized metadata, broker-compatible metadata, non-active metadata, and metadata whose `allowed_regimes` do not include the current regime. Empty `allowed_regimes` remains metadata-level regime-agnostic.

The router validates routing evidence invariants, including evidence tuple shape, nonblank string strategy IDs, duplicate evidence IDs, eligible/rejected overlap, and selected-strategy consistency.

The router does not run strategies, generate signals, size risk, submit orders, cancel orders, flatten positions, or perform remediation. It does not touch broker, runtime, config, state, observation, reporting, execution, risk, market data, file, environment, network, or VPS behavior.

`test_strategy_router.py` validates deterministic router behavior under Python 3.12, including catalog-order selection, eligibility filtering, result evidence invariants, import isolation, and absence of signal, action, order, broker, execution, risk, runtime, state, observation, or reporting fields.

## Strategy Integration Evidence

`strategy_integration.py` is a pure deterministic orchestration/use-case-style module:

- Module: `strategy_integration.py`
- Tests: `test_strategy_integration.py`
- Purpose: connect `strategy_library`, `regime_classifier`, and `strategy_router` without runtime integration.

The integration input model contains dependency-free values only:

- `closes` tuple
- optional `lookback`
- optional `min_trend_percent`
- optional `volatility_percent`

The integration processing steps are deterministic and metadata-only:

1. Build the default strategy catalog.
2. Classify the regime from closes and thresholds.
3. Route eligible strategy metadata from the regime result.

The integration output model is a frozen metadata-only integration result with:

- `regime_id`
- `selected_strategy_id`
- routing reason
- `eligible_strategy_ids`
- `rejected_strategy_ids`
- no execution fields

Explicit integration boundaries:

- No signal generation.
- No strategy execution.
- No broker behavior.
- No runtime, config, risk, state, observation, or reporting behavior.
- No `main.py` integration.
- No order, action, submit, cancel, flatten, or remediation fields.
- No `strategy_engine.py` integration.
- No `signal_validator.py` integration.

`test_strategy_integration.py` validates deterministic orchestration under Python 3.12, including default catalog construction, regime classification, metadata routing, threshold propagation, input/result invariant hardening, import isolation, no file/env/network side effects, and absence of signal, action, order, broker, execution, risk, runtime, state, observation, or reporting fields.

Runtime integration planning may follow this docs evidence. Runtime integration code remains unapproved. Signal-engine scaffold remains deferred.

## Runtime Integration Planning

Runtime integration planning is docs-only. `main.py` remains untouched.

No runtime wiring is approved. No runtime code is approved.

The first future runtime seam must be metadata-only and non-executing. Future code may read already-available closes only and may call `evaluate_strategy_integration()`. Future output must be metadata-only strategy architecture evidence.

Explicit runtime integration boundaries:

- No signal generation.
- No strategy execution.
- No broker behavior.
- No risk sizing.
- No order actions.
- No submit, cancel, flatten, or remediation.
- No state writes.
- No observation or reporting changes.
- `strategy_engine.py` remains unchanged.
- `signal_validator.py` remains unchanged.
- IBKR runtime activation remains deferred.
- Broker submission remains deferred.

Any future runtime integration code gate requires separate approval.

Current boundaries:

- No runtime wiring exists yet.
- No `main.py` integration exists yet.
- No broker, runtime, execution, risk, state, observation, or reporting dependency is approved for strategy metadata.
- Runtime integration code remains unapproved.
- Signal-engine scaffold remains deferred.

The next planned gate after this docs evidence is `RUNTIME_INTEGRATION_PLANNING`. Runtime planning must remain read-only until a separate implementation gate is approved.

`.venv-312` is a local-only Python 3.12 validation environment and must remain untracked.
