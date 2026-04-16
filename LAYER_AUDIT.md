# OpenClaw Layer Audit

This document is architecture-only.

It records the current boundary classification for the local refactor branch.
Its purpose is to show what is clean, what is transitional, what is edge detail, and where leaks still exist.

## Audit scope

Current branch:

- `codex/insufficient-market-data-fix`

Audited files:

- `main.py`
- `bot_service.py`
- `runtime_settings.py`
- `broker_client.py`
- `broker_models.py`
- `alpaca_broker.py`
- `client_factory.py`
- `execution_engine.py`
- `risk_engine.py`
- `state_manager.py`
- `reporting.py`
- `config.py`
- `market_data.py`
- `data_models.py`
- `strategy_engine.py`
- `decision_engine.py`
- `guards.py`

## Classification

### Cleanest core candidates

- `bot_service.py`
- `broker_client.py`
- `broker_models.py`
- `market_data.py`
- `data_models.py`
- `strategy_engine.py`
- `decision_engine.py`

Why they are in this group:

- mostly framework-free
- focused on policy, contracts, or internal models
- not directly shaped by Alpaca SDK objects

### Transitional modules

- `main.py`
- `runtime_settings.py`
- `execution_engine.py`
- `risk_engine.py`
- `state_manager.py`
- `reporting.py`

Why they are in this group:

- they are part of the active refactor direction
- they still carry boundary cleanup work
- some still depend on config globals or mixed legacy paths

### Edge and detail modules

- `client_factory.py`
- `alpaca_broker.py`
- `alpaca_data_provider.py`
- `config.py`

Why they are in this group:

- they deal directly with external SDKs, provider calls, or environment-backed configuration
- they belong at the repo edge, not at the policy center

### Legacy compatibility modules

- `guards.py`

Why it is in this group:

- it is stale legacy compatibility/reference code
- no active imports were found in the current runtime path

## Confirmed leaks

### `runtime_settings.py`

Leak:

- imports from `config.py`

Effect:

- config ownership is still upstream-global rather than fully isolated

### `state_manager.py`

Leak:

- imports from `config.py`

Effect:

- persistence paths and cooldown config are still pulled from globals

### `reporting.py`

Leaks:

- imports from `config.py`
- contains both settings-based and legacy config-backed reporting paths

Effect:

- reporting is partly migrated but not yet fully centered on explicit runtime contracts

### `client_factory.py`

Leaks:

- imports `alpaca_broker.py`
- imports Alpaca credentials from `config.py`

Effect:

- acceptable for an edge factory
- should remain outside policy/core concerns

## Confirmed boundary improvement

### `risk_engine.py`

Current status:

- direct Alpaca SDK and `APIError` imports were removed in the local refactor

Why it matters:

- reconciliation and risk logic now talks to the broker port instead of Alpaca-shaped SDK calls

## Audit summary

Strongest areas:

- broker contracts
- market data contracts
- internal data models
- signal and decision policy
- orchestration direction

Main remaining issues:

- config globals still leak into policy-adjacent modules
- reporting still carries mixed current and legacy paths
- persistence and reporting seams are not yet fully explicit

## What this document covers

Use `LAYER_AUDIT.md` for:

- boundary classification
- leak tracking
- clean versus transitional versus legacy status

Use `ARCHITECTURE.md` for:

- the layer map
- the current local refactor shape
- module-group responsibilities
