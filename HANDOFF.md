# HANDOFF.md — OpenClaw Stocks

Written: 2026-04-17. Based on code at `/opt/openclaw-stocks` (branch `integration/data-layer-safe`).

---

## Environment

- **VPS**: DigitalOcean SFO3, Ubuntu 24.04.4
- **Path**: `/opt/openclaw-stocks`
- **Python**: `venv/bin/python3`
- **Alpaca**: Paper endpoint (`https://paper-api.alpaca.markets`)
- **Scheduler**: `openclaw.timer` (systemd, every 15 min) — currently **inactive**
- **Remote**: `git@github.com-openclaw:DickMcGreggor/openclaw-stocks.git`
  - SSH alias `github.com-openclaw` → `~/.ssh/openclaw_deploy` (write-capable key, added 2026-04-17)
  - Old key `openclaw-vps-deploy-key` was read-only; replaced this session

---

## Branch state

Active branch: `integration/data-layer-safe`
Ahead of `origin/main` by ~10 commits. PR URL:
`https://github.com/DickMcGreggor/openclaw-stocks/pull/new/integration/data-layer-safe`

`main` branch exists locally and on origin but has not received this work yet.

---

## File inventory

### Orchestration
| File | Role |
|---|---|
| `main.py` | Entry point. Runs the full pipeline: startup → config validation → market session → data → strategy → signal validation → action proposal → account → duplicate check → risk → reconcile → order → state write → report |
| `config.py` | All env-var config. `OPENCLAW_ENABLED`, `OPENCLAW_DRY_RUN` (default `true`), `OPENCLAW_SYMBOL` (default `AAPL`), `OPENCLAW_QTY` (default `1`), `OPENCLAW_MAX_POSITION_SIZE` (default `5`), `OPENCLAW_DUPLICATE_COOLDOWN_SECONDS` (default `900`) |

### Read layer (pure — no I/O side effects)
| File | Role |
|---|---|
| `strategy_engine.py` | `generate_signal_from_closes(closes)` → momentum signal: `buy` if latest > previous close, else `hold` |
| `decision_engine.py` | `build_action_proposal(symbol, qty, signal_result)` → action dict with `should_submit`, `action`, `reason` |
| `signal_validator.py` | `validate_signal_result(signal_result)` → validates signal/decision against allowed sets `{"buy","hold"}` |
| `data_models.py` | Dataclasses: `HistoricalBarsRequest`, `HistoricalBarsResult`, `Candle` |

### Data layer
| File | Role |
|---|---|
| `alpaca_data_provider.py` | `AlpacaMarketDataProvider` — fetches historical bars from Alpaca data API, handles env key resolution and timeframe fallback |
| `market_data.py` | `get_historical_bars(provider, symbol, timeframe, limit)` — protocol-based wrapper over provider |
| `data_engine.py` | Standalone CLI (`python3 data_engine.py`) for bar inspection; not called by `main.py` |

### Execution layer
| File | Role |
|---|---|
| `execution_engine.py` | `get_market_session_status(client)`, `build_market_order(symbol, qty)`, `submit_market_order(client, order)` |
| `risk_engine.py` | `validate_config(...)`, `risk_check(...)`, `reconcile_position(...)`, `get_existing_position(...)`, `get_open_buy_order_qty(...)` |
| `state_manager.py` | `duplicate_check(symbol, side, qty)`, `write_order_state(state)`, `load_order_state()`, `write_run_report(report)` |
| `reporting.py` | `build_run_report(...)`, `persist_report(...)` — writes `last_run_report.json` |
| `client_factory.py` | `create_trading_client()` → Alpaca `TradingClient` |

### Event logging
| File | Role |
|---|---|
| `event_logger.py` | Module-level singleton. `generate_run_id()` → ISO timestamp run ID. `initialize_event_logger(run_id)` → creates `logs/<run_id>.jsonl`. `log_event(type, stage, status, payload)` → appends with fsync |
| `event_reader.py` | `read_run_events(file_path)`, `read_event_log(file_path)` — read-only consumers of JSONL logs |

### Infrastructure
| File | Role |
|---|---|
| `utils.py` | `utc_now_iso()`, `parse_iso8601()`, `write_json_atomic()`, `setup_logging()` |
| `guards.py` | **Shim** — re-exports `validate_config`, `duplicate_check`, `get_market_session_status`, `risk_check`, `reconcile_position` from `risk_engine`/`state_manager`. Phase 3 target for deletion |

### State files (not source-controlled)
| File | Role |
|---|---|
| `order_state.json` | Last submitted order record |
| `last_run_report.json` | Last run summary (derived view; event log is authoritative) |
| `last_order.txt` | Legacy duplicate guard |
| `openclaw.log` | Rotating text log |
| `logs/<run_id>.jsonl` | Per-run event log — one file per execution |

### Files that DO NOT EXIST
- `bot_service.py` — referenced in CLAUDE.md design rules as the intended orchestrator. Not yet created. `main.py` currently performs this role directly.

---

## Event type taxonomy

Sampled from `logs/*.jsonl`. Schema version 1. Every event: `schema_version`, `run_id`, `event_id` (evt_NNNN), `event_type`, `stage`, `timestamp_utc`, `status`, `payload`.

| event_type | stage | status values | payload keys |
|---|---|---|---|
| `system` | `startup` | `ok` | `message: "run_started"` |
| `system` | `market_session` | `blocked` | `reason`, `current_time`, `session_open`, `session_close`, `next_open`, `next_close` |
| `strategy` | `signal_evaluation` | `ok` | `signal`, `decision`, `action`, `reason` |
| `risk` | `risk_check` | `ok`, `blocked` | `passed`, `reason`, `symbol`, `qty` |
| `order` | `submission` | `ok` | `symbol`, `qty`, `side`, `status`, `mode` |

Known `market_session` reason values seen in logs: `before_regular_session_open`, `after_regular_session_close`.

**Coverage gap (Phase 3):** Startup event log uses a pre-initialized logger `run_id`; downstream stages (duplicate, reconcile, order) are not yet all emitting events. `order/submission` only appears in paper_submit runs that reach execution.

---

## Recently fixed

### Double run_id drift — fixed 2026-04-17 (commit 876b301)

**Bug:** `main.py` called `generate_run_id()` to initialize the event logger (producing e.g. `run_2026-04-17T21:59:12Z_59b9d5`), then immediately overwrote `run_id` with `str(uuid4())[:8]` (producing e.g. `026e007c`). The JSONL filename and internal `run_id` field used the first ID; `last_run_report.json` and all `logging.info()` lines used the second. Every run emitted mismatched IDs.

**Fix:** Deleted the overwrite line and the now-unused `from uuid import uuid4` import. `generate_run_id()` is the single source of truth. Verified: `last_run_report.json` run_id == `logs/<filename>` == JSONL internal run_id field.

---

## Architecture notes

- **No `bot_service.py`:** CLAUDE.md states "bot_service orchestrates, never decides" but the file does not exist. `main.py` is the de-facto orchestrator. Phase 3 should either create `bot_service.py` and move orchestration there, or update CLAUDE.md.
- **`guards.py` is a shim:** Duplicates function signatures from `risk_engine.py` and `state_manager.py`. It is not imported by `main.py`. Phase 3 target for deletion.
- **`data_engine.py` is a standalone tool:** Has its own `main()` and `parse_args()`. Not called from the trading pipeline.
- **Dry-run default:** `OPENCLAW_DRY_RUN=true` in config but `.env` overrides it to `false` for paper trading. Mode appears as `paper_submit` in run reports when `.env` is active.
- **ALLOWED_SYMBOLS** hardcoded in `config.py`: `["AAPL", "MSFT", "GOOG"]`. Only `AAPL` is traded.

---

## Phase ladder (from CLAUDE.md)

- [x] Phase 0: Reconciliation
- [~] Phase 1: VPS sync, forced-execution test, context docs, run_id fix — **in progress this session**
- [ ] Phase 2: Git becomes source of truth; local Mac becomes dev authority
- [ ] Phase 3: Code fixes (event coverage, timestamp compat, qty×price risk sizing, delete shims)
- [ ] Phase 4: VPS read-only for code
- [ ] Phase 5: Paper shadow (2 weeks of market days)
- [ ] Phase 6: Paper live, qty=1, daily review
- [ ] Phase 7: Monitoring, circuit breaker, runbook
