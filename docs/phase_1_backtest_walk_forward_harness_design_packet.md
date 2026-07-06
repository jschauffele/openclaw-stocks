# Phase 1A Backtest / Walk-Forward Harness Design Packet

## 1. Classification

PHASE_1_BACKTEST_HARNESS_DESIGN

Design status: DESIGN_ONLY.

Implementation status: NOT_AUTHORIZED.

This packet defines the required behavior, inputs, guardrails, outputs, and tests for a future Phase 1A backtest / walk-forward harness. It does not authorize harness implementation, strategy changes, Candidate 002 implementation, broker integration, order simulation, or production deployment.

## 2. Locked source-of-truth state

Repository: DickMcGreggor/openclaw-stocks

Local path: `/Users/openclawcontrol/Documents/openclaw-stocks`

Source-of-truth commit: `31c184b73c88ae4ccb3e34750d22e5a1219e33bc`

Current phase: `PHASE_1_DATA_LAYER_COMPLETE`

Current gate: `PHASE_1_BACKTEST_HARNESS_DESIGN`

The design assumes the Phase 1 Tiingo data layer exists, has produced canonical and derived outputs outside the repository, and has completed acceptance with append-stable canonical rows and separate derived adjusted series.

## 3. Purpose

The harness must provide deterministic, local-only, signal-first replay and walk-forward evaluation for OpenClaw strategies against Phase 1 historical research data.

Its first purpose is to prove harness correctness, temporal safety, evaluator routing, and deterministic reporting before any predictive-edge claim or strategy tuning is allowed.

The harness must make it mechanically difficult to leak future information into signals, labels, candidate evaluation, report generation, or split selection.

## 4. Explicit non-goals

The harness must not implement or modify any strategy.

The harness must not implement Candidate 002.

The harness must not change Candidate 001.

The harness must not tune parameters, thresholds, filters, universe membership, or ranking rules before harness correctness is accepted.

The harness must not access broker, account, order, portfolio, balance, or live execution functionality.

The harness must not create production trading recommendations.

The harness must not move market data into the repository.

The harness must not sync market data to the VPS.

The harness must not require VPS research data access.

The harness must not use vendor `adjClose` as an input series.

## 5. Data-source policy

The harness must consume derived adjusted series produced by the Phase 1 data layer.

Expected local derived data location:

`/Users/openclawcontrol/openclaw-market-data/tiingo/derived/`

The harness must not consume Tiingo vendor `adjClose` directly.

The harness must not call Tiingo, broker market-data APIs, account APIs, order APIs, portfolio APIs, or live data providers.

The harness must treat canonical raw OHLCV data and derived adjusted series as local research inputs only. If a future implementation needs canonical data for audit joins, it may read canonical Phase 1 outputs, but signal/evaluation price series must come from the derived adjusted series.

## 6. Data-root policy

Canonical local research data root:

`/Users/openclawcontrol/openclaw-market-data`

Market data must remain outside the repository.

Market data must not be committed, staged, copied into docs, copied into tests, or written under `/Users/openclawcontrol/Documents/openclaw-stocks`.

The harness must reject any data root inside the repository.

The harness must reject any data root under an iCloud-synced or user-documents path unless a later approved gate explicitly changes that policy.

The harness must not require access to the VPS for research data. VPS deployment, if any, is out of scope for this gate.

## 7. Required input dataset

Minimum required input:

- Derived adjusted series under `/Users/openclawcontrol/openclaw-market-data/tiingo/derived/`
- A manifest lineage record tying each derived artifact to its source ingest run
- Ticker/date rows for the Phase 1 plumbing universe
- Deterministic universe declaration for the evaluation run
- Deterministic split specification
- Strategy or evaluator adapter selection that cannot submit orders

Required derived-series fields:

- `date`
- `ticker`
- `computed_adjClose`
- `adjustment_method`
- `adjustment_method_version`
- `source_manifest_id`

Optional provenance may include `ingest_run_id` when present or when recoverable through manifest lineage.

The harness must fail closed if required derived fields are missing.

## 8. Derived adjusted-series reader design

The reader must load derived adjusted series from the local data root only.

The reader must select deterministic artifact inputs. If multiple run-versioned derived files exist for a ticker, the implementation must define and test a deterministic baseline selection policy before use. The recommended initial policy is lexicographically latest `tiingo-*.parquet` per `ticker=<TICKER>/`, matching the Phase 1 current-baseline convention.

The reader must validate:

- Required columns exist
- No vendor `adjClose` column is present or consumed
- No duplicate `(date, ticker)` rows exist after baseline selection
- `source_manifest_id` is present and non-empty
- `ingest_run_id` is preserved when present or recoverable through manifest lineage
- `computed_adjClose` is numeric, finite, and positive for rows used in signal calculation
- Dates are parseable and normalized to session dates
- Tickers are uppercase and match the declared universe

The reader must return an immutable or copy-isolated frame to downstream evaluators so later test mutations cannot alter already-produced prior signals.

## 9. Current Phase 1 universe policy

Current Phase 1 plumbing universe:

- `AAPL`
- `MSFT`
- `NVDA`
- `TSLA`
- `MSTR`
- `PTON`

Every result from this universe must be labeled:

`NON_GENERALIZABLE_RESEARCH_RESULT`

This universe is for plumbing validation only. It is not a valid research universe for predictive-edge conclusions.

## 10. Survivorship-bias policy

The current Phase 1 universe is not generalizable and is not survivorship-controlled.

The harness must place `NON_GENERALIZABLE_RESEARCH_RESULT` in every report, metrics artifact, manifest, and summary generated from the current Phase 1 universe.

The harness must block report finalization if the required non-generalizable label is missing.

Any future survivorship-controlled universe must be separately designed, reviewed, and accepted before predictive-edge claims can be considered.

## 11. Time semantics

All input rows must be interpreted as daily session data.

Signals for session `T` may only use data available at or before the close of session `T` if the design models next-session action, or at or before session `T-1` if the design models same-open action. The first implementation must choose one execution timing convention and encode it mechanically.

Recommended initial convention:

- Features are computed through session `T`
- Signals are timestamped at session `T`
- Any research-only forward return label begins after `T`
- No feature for signal `T` may read any row with date greater than `T`

The harness must use explicit date cutoffs rather than relying on dataframe ordering conventions.

## 12. Strategy/evaluator interface

The harness must call strategies through a no-submit evaluator interface.

The interface must pass only:

- Historical data truncated to the current evaluation timestamp
- The current ticker universe
- Deterministic configuration
- Read-only metadata needed for routing and reporting

The interface must not expose:

- Broker clients
- Account state
- Order submission methods
- Portfolio balances
- Live market data providers
- Full future datasets

Evaluator dispatch must be explicit and auditable. A run manifest must record which evaluator or strategy adapter was invoked.

## 13. Candidate 001 handling

Candidate 001 is validated only for:

- Deterministic behavior
- Architecture safety
- Routing/evaluator dispatch
- No-submit enforcement
- Compatibility with derived adjusted series
- Temporal guardrail compliance

Candidate 001 is not predictive-edge validated.

Candidate 001 replay through this harness is a harness correctness exercise, not a claim that Candidate 001 has alpha or production readiness.

## 14. Candidate 002 blocked status

Candidate 002 remains blocked.

Candidate 002 must not be implemented, tuned, evaluated, or promoted until:

- The Phase 1A harness exists
- Harness correctness has been accepted
- Candidate 001 has been replayed through the harness
- Candidate 001 replay artifacts have passed deterministic output and no-lookahead checks

## 15. Walk-forward split rules

Walk-forward splits must be deterministic and declared before evaluation.

Each split must include:

- Train start date
- Train end date
- Test start date
- Test end date
- Universe declaration
- Derived data manifest lineage
- Split identifier

Train and test windows must not overlap.

Test windows must occur strictly after their corresponding train windows.

No split may be generated from future performance outcomes.

The split generator must be deterministic for a fixed dataset, date range, and configuration.

## 16. No-lookahead guardrails

No-lookahead protection must be mechanical, not convention-based.

Required guardrails:

- The evaluator must provide each strategy call a time-sliced view ending at the evaluation date.
- The strategy must not receive the full dataset object.
- Forward labels or return windows must be computed in a separate post-signal phase.
- Feature computation must assert that every input row date is less than or equal to the signal date.
- Report aggregation must join realized research labels to precomputed signals by immutable signal identifiers.
- Train/test split validation must fail on overlap before strategy dispatch.
- Future-row mutation/removal tests must prove prior signals are unchanged.
- Leaky fixture tests must prove intentionally future-dependent inputs fail.

Any implementation path that relies on developer discipline instead of enforced slicing and assertions must be rejected.

## 17. Signal-first evaluation metrics

The harness must be signal-first, not P&L-first.

Required initial metrics:

- Signal count by ticker and split
- Signal timestamp coverage
- Duplicate signal detection
- Missing signal timestamp detection
- Deterministic signal hash
- Direction or class distribution, if applicable
- Forward-label availability rate, research-only
- Hit-rate style directional agreement, research-only
- Rank correlation or bucket monotonicity, research-only if ranking exists
- Turnover proxy based on signal changes, research-only

Metrics must make clear whether they evaluate signal formation, label association, or research-only return attribution.

No broker-realistic P&L, fill simulation, slippage model, margin model, position sizing model, or portfolio optimizer is authorized in this gate.

## 18. Limited research return attribution

Initial return attribution may be described only as research-only and not broker-realistic.

Allowed research-only attribution examples:

- Next-session adjusted close to adjusted close return
- Fixed-horizon adjusted close return
- Directional agreement between signal and forward adjusted return

Required label:

`RESEARCH_ONLY_NOT_BROKER_REALISTIC`

The attribution must not account for fills, spreads, liquidity, borrow, fees, taxes, partial fills, halts, margin, portfolio constraints, or order timing realism.

Research-only attribution must not be used to approve live trading.

## 19. Deterministic output artifacts

A completed harness run must produce deterministic artifacts for identical inputs and configuration.

Required artifact classes:

- Run manifest
- Input dataset manifest summary
- Universe declaration
- Split declaration
- Signal output
- Signal hash
- Metrics report
- Guardrail report
- Failure report if the run fails closed

Artifacts must include:

- Source-of-truth commit
- Data root path
- Derived data artifact lineage
- Universe label
- Evaluator identifier
- Split identifiers
- Deterministic run configuration hash
- Deterministic output hash

Artifacts must not include secrets, Tiingo tokens, broker credentials, account identifiers, or market data payload dumps.

## 20. Determinism requirements

For identical code, inputs, data artifacts, universe, splits, evaluator, and configuration, the harness must produce byte-stable or canonicalized-equivalent outputs.

Required determinism controls:

- Stable sort order by `ticker`, `date`, and deterministic signal id
- Stable JSON serialization for report hashes
- Explicit timezone/date normalization
- No wall-clock timestamps in deterministic report hashes
- No random behavior unless seeded and recorded
- No dependency on filesystem iteration order
- No dependency on dataframe row order after joins

The test suite must compare deterministic output hashes across repeated runs.

## 21. Failure-mode catalog

The harness must fail closed for:

- Missing derived data
- Attempted vendor `adjClose` use
- Duplicate `(ticker, date)` rows
- Missing manifest lineage
- Non-deterministic output
- Missing `NON_GENERALIZABLE_RESEARCH_RESULT` label for the Phase 1 universe
- Train/test overlap
- Test window not strictly after train window
- Strategy adapter attempting to access broker/account/order/portfolio functionality
- Signal generation receiving rows after the signal date
- Leaky fixture acceptance
- Missing or non-finite `computed_adjClose`
- Universe mismatch between config and data
- Missing deterministic split declaration
- Missing source-of-truth commit in artifacts
- Missing evaluator identifier in artifacts
- Missing no-submit enforcement report

Failures must produce a failure report unless producing that report would risk writing secrets or invalid data into the repository.

## 22. Test plan

Required tests:

- Derived reader rejects missing derived root.
- Derived reader rejects vendor `adjClose` consumption.
- Derived reader rejects duplicate `(ticker, date)` rows.
- Derived reader rejects missing `source_manifest_id`.
- Derived reader rejects missing or non-finite `computed_adjClose`.
- Derived reader selects deterministic ticker baselines.
- Phase 1 universe reports include `NON_GENERALIZABLE_RESEARCH_RESULT`.
- Report finalization fails when the required universe label is missing.
- Walk-forward split validation rejects train/test overlap.
- Walk-forward split validation rejects test windows that do not occur strictly after train windows.
- Strategy dispatch receives only time-sliced data through the signal date.
- Future-row mutation does not change prior signals.
- Future-row removal does not change prior signals.
- Leaky fixtures that depend on future rows fail.
- Forward labels are computed only after signals are frozen.
- Candidate 001 replay cannot submit orders.
- Candidate 001 replay records evaluator dispatch.
- Repeated runs produce identical deterministic output hashes.
- Report hashes exclude wall-clock-only fields.
- Research-only attribution is labeled `RESEARCH_ONLY_NOT_BROKER_REALISTIC`.
- Missing manifest lineage blocks the run.

Test fixtures must be synthetic or derived from approved local Phase 1 artifacts without copying market data into the repository.

## 23. Acceptance criteria

The future harness implementation may be accepted only when:

- It reads derived adjusted series rather than vendor `adjClose`.
- It uses `/Users/openclawcontrol/openclaw-market-data` as the local research data root.
- It does not move market data into the repository.
- It does not require VPS research data access.
- It labels Phase 1 universe outputs `NON_GENERALIZABLE_RESEARCH_RESULT`.
- It mechanically enforces no-lookahead slicing and assertions.
- It blocks train/test overlap.
- It blocks duplicate `(ticker, date)` rows.
- It blocks missing manifest lineage.
- It blocks vendor `adjClose` use.
- It blocks non-deterministic outputs.
- It blocks missing universe labels.
- It can replay Candidate 001 without order submission.
- It produces deterministic output hashes for repeated identical runs.
- It keeps return attribution research-only and not broker-realistic.
- It does not tune any strategy before harness correctness is accepted.

## 24. Stop condition

Stop after this design packet is reviewed.

Staging, committing, pushing, merging, backtest harness implementation, Candidate 002 implementation, Candidate 001 modification, strategy tuning, broker integration, and production execution work remain NOT_AUTHORIZED.
