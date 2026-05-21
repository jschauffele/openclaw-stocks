# Deterministic Strategy Architecture

## Foundation Evidence

Current phase: Deterministic Strategy Architecture.

The deterministic strategy architecture foundation is established through completed gates:

- `b43bc3c Strategy: add deterministic strategy library scaffold`
- `a0c81f6 Strategy: harden strategy library metadata validation`
- `6772e68 Strategy: add deterministic regime classifier scaffold`
- `c10d477 Strategy: harden regime classifier validation`

Python 3.12 validation evidence:

- `.venv-312/bin/python --version` reported `Python 3.12.13`
- `.venv-312/bin/python -m pytest test_strategy_library.py` reported `23 passed`
- `.venv-312/bin/python -m pytest test_regime_classifier.py` reported `36 passed`

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

Current boundaries:

- No runtime wiring exists yet.
- No `main.py` integration exists yet.
- No strategy router exists yet.
- No broker, runtime, execution, risk, state, observation, or reporting dependency is approved for strategy metadata.
- Router planning may follow this docs evidence.
- Router code remains unapproved.
- Signal-engine scaffold remains deferred.

The next planned gate after this docs evidence is `STRATEGY_ROUTER_PLANNING`. Router planning must remain read-only until a separate implementation gate is approved.

`.venv-312` is a local-only Python 3.12 validation environment and must remain untracked.
