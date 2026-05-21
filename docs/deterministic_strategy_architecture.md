# Deterministic Strategy Architecture

## Foundation Evidence

Current phase: Deterministic Strategy Architecture.

The deterministic strategy architecture foundation is established through two completed gates:

- `b43bc3c Strategy: add deterministic strategy library scaffold`
- `a0c81f6 Strategy: harden strategy library metadata validation`

Python 3.12 validation evidence:

- `.venv-312/bin/python --version` reported `Python 3.12.13`
- `.venv-312/bin/python -m pytest test_strategy_library.py` reported `23 passed`

`strategy_library.py` is a pure inner-policy metadata module. It follows the Clean Architecture Chapter 20 and Chapter 22 boundary: business rules and entities remain pure, dependencies point inward, and inner policy does not depend on outer mechanisms.

`test_strategy_library.py` validates strategy catalog behavior under Python 3.12. The tests cover stable strategy identity, immutable catalog data, duplicate rejection, validation hardening, lookup behavior, and forbidden outer-mechanism imports.

The current strategy metadata does not create broker, runtime, execution, risk, state, reporting, observation, or configuration authority. `execution_authority` remains `False`, and `broker_compatibility` remains empty.

`close_momentum_v1` is metadata only. It records the existing close-momentum strategy shape and observable fields, but it does not add new strategy behavior, routing, execution authority, broker compatibility, or runtime activation.

Current boundaries:

- No runtime wiring exists yet.
- No `main.py` integration exists yet.
- No regime classifier exists yet.
- No strategy router exists yet.
- No broker, runtime, execution, risk, state, observation, or reporting dependency is approved for strategy metadata.

The next planned code gate after this docs evidence is `REGIME_CLASSIFIER_SCAFFOLD`. Before regime code is added, the allowed regime IDs and deterministic classification rules must be defined.

`.venv-312` is a local-only Python 3.12 validation environment and must remain untracked.
