# OpenClaw Architecture

This document is architecture-only.

It describes the current local refactor shape in this repo.
It is not a deployment guide and it does not authorize runtime changes.

## Architecture rule

OpenClaw is being shaped toward a Clean Architecture style layout:

- policy stays near the center
- orchestration coordinates the runtime flow
- infrastructure stays at the edges
- the entrypoint wires dependencies together

## Layer map

### Entry point

Files:

- `run_bot.sh`
- `main.py`

Module role:

- start the runtime
- load settings
- configure logging
- assemble concrete adapters
- invoke the application service

### Application orchestration

Files:

- `bot_service.py`
- `runtime_settings.py`

Module role:

- define runtime-facing settings
- orchestrate the end-to-end bot flow
- coordinate policy and adapter calls
- keep broker SDK details out of the use-case flow

### Policy and use-case logic

Files:

- `strategy_engine.py`
- `decision_engine.py`
- `signal_validator.py`
- `risk_engine.py`
- `state_manager.py`
- `reporting.py`
- `market_data.py`
- `data_models.py`

Module role:

- express deterministic guardrails
- validate signal and decision contracts
- validate and normalize market data requests
- evaluate risk and reconciliation rules
- persist state and reports in a stable shape

### Interface and infrastructure edge

Files:

- `client_factory.py`
- `broker_client.py`
- `broker_models.py`
- `alpaca_broker.py`
- `alpaca_data_provider.py`
- `execution_engine.py`
- `config.py`

Module role:

- define broker-facing contracts
- create and wire concrete broker adapters
- translate Alpaca SDK calls into repo-facing contracts
- fetch market data from external providers
- submit orders and inspect broker session state
- read environment-backed configuration

## Boundaries

The current local refactor uses these boundaries:

### Entrypoint boundary

- `main.py` and `run_bot.sh` start the system and wire dependencies
- they should not own policy logic

### Orchestration boundary

- `bot_service.py` coordinates the runtime sequence
- `runtime_settings.py` provides the runtime-facing settings shape
- orchestration should call policy and edge modules without absorbing their responsibilities

### Policy boundary

- strategy, decision, validation, risk, state, reporting, and market-data domain logic live in the inner layers
- these modules define runtime rules and internal data handling

### Broker boundary

- `broker_client.py` and `broker_models.py` define the broker-facing contract shape
- `alpaca_broker.py` implements Alpaca-specific translation behind that boundary

### External detail boundary

- `alpaca_data_provider.py`, `execution_engine.py`, `client_factory.py`, and `config.py` handle provider access, broker access, adapter wiring, and environment-backed configuration
- these modules belong at the repo edge

## Current local refactor shape

The current local refactor has these important structural characteristics:

- `main.py` is acting as a thinner composition root
- `bot_service.py` centralizes the runtime sequence
- `runtime_settings.py` gives config values a more explicit runtime shape
- `broker_client.py` and `broker_models.py` define broker-facing contracts
- `alpaca_broker.py` isolates Alpaca SDK translation work
- `guards.py` remains legacy compatibility/reference code outside the preferred active structure
