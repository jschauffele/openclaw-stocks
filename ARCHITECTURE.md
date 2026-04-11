# OpenClaw Architecture

This repo is being shaped toward a Clean Architecture style layout:

- policies and decisions stay in the center
- infrastructure stays at the edges
- the entrypoint wires dependencies together but should not contain business rules

## Current layer map

### Entry point
- `run_bot.sh`
- `main.py`

Responsibilities:
- start the runtime
- load settings
- configure logging
- assemble concrete adapters
- invoke the application service

### Application orchestration
- `bot_service.py`
- `runtime_settings.py`

Responsibilities:
- define the runtime settings object
- orchestrate the end-to-end bot flow
- coordinate policies and adapters without owning broker SDK details

### Policy and use-case logic
- `strategy_engine.py`
- `decision_engine.py`
- `signal_validator.py`
- `risk_engine.py`
- `state_manager.py`
- `reporting.py`
- `market_data.py`
- `data_models.py`

Responsibilities:
- express deterministic guardrails
- validate signal and decision contracts
- validate and normalize market data requests
- evaluate risk and reconciliation rules
- persist state and reports in a stable shape

### Infrastructure adapters
- `client_factory.py`
- `alpaca_data_provider.py`
- `execution_engine.py`
- `config.py`

Responsibilities:
- connect to Alpaca SDK clients
- translate provider requests into Alpaca calls
- submit orders and inspect broker session state
- read environment-backed configuration

## Why this structure helps

This layout is better for institutional-grade operation because it makes three things clearer:

1. What the bot decides
The policy layer contains signal, risk, and guardrail rules.

2. How the bot talks to the outside world
The infrastructure layer owns Alpaca, environment loading, and external IO.

3. Where to change things safely
- strategy changes should mostly live in strategy and decision modules
- guardrail changes should mostly live in risk/state/reporting modules
- broker or deployment changes should mostly live in factories and adapters

## Current architectural improvements

- `main.py` is now a thin composition root instead of the orchestration brain
- runtime configuration is wrapped in `RuntimeSettings`
- the application flow lives in `OpenClawBot`
- reports can now be built from explicit runtime settings instead of only config globals
- broker-facing calls now move through `BrokerClient` and normalized broker models
- Alpaca SDK details are isolated in `alpaca_broker.py` and the edge factory path
- the active runtime path is now covered by focused automated tests for orchestration, risk/reconciliation, and market-data retry behavior

## Legacy status

- `guards.py` is a legacy compatibility/reference module and is not part of the active runtime path
- new runtime behavior should not be added to `guards.py`
- cleanup in the current phase should favor protecting the active path with tests instead of rewriting legacy modules

## Next recommended architectural steps

1. Keep expanding tests around deterministic guardrails before further cleanup
2. Continue only small reporting/state seam improvements that do not change validated runtime behavior
3. Leave `guards.py` documented as legacy until after the current stability phase
4. Store richer run outcomes for strategy review and promotion decisions
5. Separate strategy experimentation from execution deployment even more clearly
