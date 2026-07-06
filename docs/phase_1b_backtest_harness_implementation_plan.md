# Phase 1B Backtest / Walk-Forward Harness Implementation Plan

## Classification

Current phase: `PHASE_1_BACKTEST_HARNESS_DESIGN_ACCEPTED_FOR_IMPLEMENTATION_PLANNING`

Current gate: `PHASE_1B_BACKTEST_HARNESS_IMPLEMENTATION_PLANNING`

Starting source-of-truth commit: `436c6e501223bdb32a3942782d67544eec650ba9`

Source design packet: `docs/phase_1_backtest_walk_forward_harness_design_packet.md`

This is a docs-only implementation plan. It does not authorize code implementation, Candidate 002 work, Candidate 001 changes, broker integration, execution simulation, risk sizing, paper trading, live trading, or any non-docs operational change.

## Global Constraints

The harness must consume derived adjusted series, not vendor `adjClose`.

Expected local derived data location: `/Users/openclawcontrol/openclaw-market-data/tiingo/derived/`

Canonical local research data root: `/Users/openclawcontrol/openclaw-market-data`

Market data must remain outside the repository and must not be synced to the VPS.

Current Phase 1 plumbing universe:

- `AAPL`
- `MSFT`
- `NVDA`
- `TSLA`
- `MSTR`
- `PTON`

Any result from this universe must be labeled `NON_GENERALIZABLE_RESEARCH_RESULT`.

Candidate 001 is not predictive-edge validated. It may only be replayed to validate deterministic behavior, architecture safety, routing/evaluator dispatch, no-submit enforcement, and harness correctness.

Candidate 002 remains blocked until the harness exists and Candidate 001 has been replayed through it.

No P&L-first optimization, strategy tuning, risk sizing, execution simulation, broker integration, paper trading, or live trading is allowed in Phase 1B.

Initial return attribution, if introduced, must remain research-only and not broker-realistic.

## Recommended First Code Unit

The first implementation unit should be strictly limited to Phase 1B.1:

- New package/module skeleton if needed
- Config dataclasses or typed structures
- Failure/error enums
- Deterministic hash/serialization helper design if needed
- Unit tests for config validation and failure enums

It must not include data reading, strategy dispatch, report generation, walk-forward evaluation, Candidate 001 replay, or any broker/risk/execution integration.

## Phase 1B.1 - Package Skeleton, Typed Config, Failure Enums, Deterministic Serialization Helpers

### Objective

Create the smallest safe harness foundation: a package/module boundary, typed configuration structures, failure/error enums, and deterministic serialization/hash helper interfaces.

This unit establishes naming, validation, and failure vocabulary before any data is read or strategy logic is dispatched.

### Files likely to be created or modified

Likely new files:

- `backtest_harness/__init__.py`
- `backtest_harness/config.py`
- `backtest_harness/failures.py`
- `backtest_harness/serialization.py`
- `tests/test_backtest_harness_config.py`
- `tests/test_backtest_harness_failures.py`
- `tests/test_backtest_harness_serialization.py`

If the project convention requires another test location, use the existing local test convention without modifying unrelated tests.

### Files explicitly forbidden

- Strategy files, including Candidate 001 files
- Risk files
- Execution files
- Broker/account/order/portfolio/balance files
- Scheduler, systemd, or timer files
- Market data artifacts
- `.gitignore`
- Existing data-layer implementation unless a later gate explicitly authorizes it

### Test requirements

- Config validates the local research data root path as external to the repo.
- Config includes the Phase 1 universe and required `NON_GENERALIZABLE_RESEARCH_RESULT` label.
- Config rejects missing universe labels for Phase 1 universe runs.
- Config rejects broker, execution, paper-trading, or live-trading modes.
- Failure enums include blocking cases for missing derived data, vendor `adjClose` use, duplicate ticker/date rows, missing manifest lineage, non-deterministic output, missing universe label, and train/test overlap.
- Serialization helper tests prove stable canonical JSON/hash output independent of dictionary insertion order.

### Acceptance criteria

- No data files are read.
- No strategy dispatch exists.
- No report generation exists.
- No broker/risk/execution imports are introduced.
- Unit tests pass locally.
- Failure enum names are stable and referenced by tests.

### Stop condition

Stop after the skeleton/config/failure/serialization unit is reviewed.

### Rollback criteria

Rollback this unit if it imports broker/risk/execution modules, reads market data, dispatches a strategy, creates report artifacts, or weakens any Phase 1A design constraint.

## Phase 1B.2 - Derived Adjusted-Series Reader

### Objective

Implement a local-only reader for Phase 1 derived adjusted series. The reader must consume `computed_adjClose` from derived Parquet artifacts and must reject vendor `adjClose` use.

### Files likely to be created or modified

Likely files:

- `backtest_harness/derived_reader.py`
- `tests/test_backtest_harness_derived_reader.py`

Possible supporting files:

- `backtest_harness/config.py`
- `backtest_harness/failures.py`

### Files explicitly forbidden

- Tiingo ingestion code except by separate explicit authorization
- Strategy files
- Risk files
- Execution files
- Broker/account/order/portfolio/balance files
- Market data artifacts under the repo
- Scheduler/systemd/timer files

### Test requirements

- Reader rejects missing derived root.
- Reader rejects any input that exposes or requires vendor `adjClose`.
- Reader rejects duplicate `(ticker, date)` rows.
- Reader rejects missing `source_manifest_id`.
- Reader rejects missing or non-finite `computed_adjClose`.
- Reader validates ticker membership against the declared universe.
- Reader selects deterministic ticker baselines when multiple run-versioned files exist.
- Reader returns copy-isolated data so later mutations do not alter previously produced slices.

Tests should use synthetic temporary Parquet fixtures, not copied market data artifacts.

### Acceptance criteria

- Derived reader reads only local filesystem inputs.
- The reader consumes derived adjusted series, not vendor adjusted-close fields.
- The reader fails closed with typed failure codes.
- No strategy dispatch or report generation is added.
- No external data root is modified.

### Stop condition

Stop after derived-reader behavior and failure handling are reviewed.

### Rollback criteria

Rollback if the reader consumes vendor `adjClose`, reads broker/live APIs, writes market data artifacts, permits duplicate ticker/date rows, or allows missing lineage.

## Phase 1B.3 - Deterministic Walk-Forward Splitter

### Objective

Implement deterministic walk-forward split declarations and validation.

The splitter must define train/test windows before evaluation and mechanically reject overlap or non-forward test windows.

### Files likely to be created or modified

Likely files:

- `backtest_harness/splits.py`
- `tests/test_backtest_harness_splits.py`

Possible supporting files:

- `backtest_harness/config.py`
- `backtest_harness/failures.py`
- `backtest_harness/serialization.py`

### Files explicitly forbidden

- Strategy files
- Risk files
- Execution files
- Broker/account/order/portfolio/balance files
- Scheduler/systemd/timer files
- Market data artifacts

### Test requirements

- Same config produces identical split declarations.
- Train/test overlap fails.
- Test start on or before train end fails.
- Missing split identifiers fail.
- Split declarations include universe, data lineage placeholder/reference, train dates, and test dates.
- Split serialization is deterministic.

### Acceptance criteria

- Splitter is deterministic for fixed config.
- Split validation runs before any strategy dispatch.
- No data leakage from test windows into train windows is possible through split definitions.
- No strategy tuning or performance-aware split selection is introduced.

### Stop condition

Stop after split generation and validation are reviewed.

### Rollback criteria

Rollback if split generation depends on future outcomes, permits overlap, permits missing labels, or starts dispatching strategies.

## Phase 1B.4 - No-Lookahead Signal Dispatch Harness

### Objective

Implement the signal-first dispatch loop that calls evaluators with mechanically time-sliced data only.

This unit must enforce that a signal for date `T` cannot access rows after `T`.

### Files likely to be created or modified

Likely files:

- `backtest_harness/dispatch.py`
- `backtest_harness/signals.py`
- `tests/test_backtest_harness_dispatch.py`
- `tests/test_backtest_harness_no_lookahead.py`

Possible supporting files:

- `backtest_harness/failures.py`
- `backtest_harness/serialization.py`

### Files explicitly forbidden

- Candidate 001 strategy changes
- Candidate 002 files
- Risk sizing files
- Execution simulation files
- Broker/account/order/portfolio/balance files
- Scheduler/systemd/timer files

### Test requirements

- Strategy/evaluator receives data truncated through the signal date.
- Strategy/evaluator never receives the full future dataset object.
- Future-row mutation does not change prior signals.
- Future-row removal does not change prior signals.
- Intentionally leaky fixtures fail.
- Dispatch records evaluator identity.
- Dispatch enforces no-submit behavior through interface boundaries or test doubles.

### Acceptance criteria

- Harness is signal-first and produces signals independent of future rows.
- No P&L-first optimization is introduced.
- No risk sizing, execution simulation, paper trading, live trading, or broker integration exists.
- Candidate 001 is not changed.

### Stop condition

Stop after no-lookahead dispatch and leak tests are reviewed.

### Rollback criteria

Rollback if dispatch exposes future rows, imports broker/order functionality, allows submit behavior, modifies Candidate 001, or introduces P&L-first optimization.

## Phase 1B.5 - Deterministic Report Artifacts and Output Hashes

### Objective

Implement deterministic report artifacts for harness runs and output hashes for repeated-run comparison.

Reports must be signal-first and must label Phase 1 universe results as `NON_GENERALIZABLE_RESEARCH_RESULT`.

### Files likely to be created or modified

Likely files:

- `backtest_harness/reporting.py`
- `backtest_harness/artifacts.py`
- `tests/test_backtest_harness_reporting.py`
- `tests/test_backtest_harness_output_hashes.py`

Possible supporting files:

- `backtest_harness/serialization.py`
- `backtest_harness/failures.py`

### Files explicitly forbidden

- Existing production reporting files unless separately authorized
- Strategy files
- Risk files
- Execution files
- Broker/account/order/portfolio/balance files
- Scheduler/systemd/timer files
- Market data artifacts

### Test requirements

- Repeated identical runs produce identical deterministic output hashes.
- Report hashes exclude wall-clock-only fields.
- Report finalization fails when `NON_GENERALIZABLE_RESEARCH_RESULT` is missing.
- Reports include source commit, data root, universe, split identifiers, evaluator identifier, lineage references, and deterministic config hash.
- Reports do not include secrets, Tiingo tokens, broker credentials, account identifiers, or raw market data dumps.
- Research-only attribution, if present, is labeled `RESEARCH_ONLY_NOT_BROKER_REALISTIC`.

### Acceptance criteria

- Reports are deterministic and hashable.
- Missing universe label blocks finalization.
- Reports remain research-only and signal-first.
- No broker-realistic P&L, slippage, fills, risk sizing, or execution simulation is introduced.

### Stop condition

Stop after deterministic reporting and hash tests are reviewed.

### Rollback criteria

Rollback if output is non-deterministic, labels are optional, secrets can appear in artifacts, or reports become broker-realistic P&L outputs.

## Phase 1B.6 - Candidate 001 Replay Adapter

### Objective

Add a no-submit adapter that can replay Candidate 001 through the harness for architecture and determinism validation only.

Candidate 001 must not be modified and must not be predictive-edge validated.

### Files likely to be created or modified

Likely files:

- `backtest_harness/candidate_001_adapter.py`
- `tests/test_backtest_harness_candidate_001_adapter.py`

Possible supporting files:

- `backtest_harness/dispatch.py`
- `backtest_harness/signals.py`
- `backtest_harness/failures.py`

### Files explicitly forbidden

- Candidate 001 strategy source files
- Candidate 002 files
- Risk files
- Execution files
- Broker/account/order/portfolio/balance files
- Scheduler/systemd/timer files

### Test requirements

- Candidate 001 replay adapter cannot submit orders.
- Adapter records routing/evaluator dispatch.
- Adapter produces deterministic signals for identical time-sliced inputs.
- Adapter does not import or access broker/account/order/portfolio/balance functionality.
- Adapter labels outputs from the Phase 1 universe `NON_GENERALIZABLE_RESEARCH_RESULT`.
- Adapter report states Candidate 001 is not predictive-edge validated.

### Acceptance criteria

- Candidate 001 is replayable through the no-submit harness.
- Candidate 001 source remains unchanged.
- Replay validates deterministic behavior and architecture safety only.
- Candidate 002 remains blocked.

### Stop condition

Stop after Candidate 001 replay adapter artifacts and tests are reviewed.

### Rollback criteria

Rollback if Candidate 001 source changes, any submit path is reachable, broker/order modules are imported, or replay output is described as predictive-edge validation.

## Phase 1B.7 - Local Acceptance Test Suite

### Objective

Create the local acceptance suite that validates the full Phase 1B harness behavior on synthetic fixtures and, where explicitly authorized, local derived data.

### Files likely to be created or modified

Likely files:

- `tests/test_backtest_harness_acceptance.py`
- `tests/test_backtest_harness_end_to_end_determinism.py`

Possible supporting files:

- Existing `backtest_harness/*` files created in earlier Phase 1B units

### Files explicitly forbidden

- Strategy source changes
- Risk files
- Execution files
- Broker/account/order/portfolio/balance files
- Scheduler/systemd/timer files
- Market data artifacts committed to the repo
- `.gitignore`

### Test requirements

- Full local run uses derived adjusted series rather than vendor `adjClose`.
- Missing derived data fails closed.
- Duplicate ticker/date rows fail closed.
- Missing manifest lineage fails closed.
- Missing universe label fails closed.
- Train/test overlap fails closed.
- Future-row mutation and removal do not alter prior signals.
- Leaky fixtures fail.
- Repeated runs produce matching deterministic output hashes.
- Candidate 001 replay remains no-submit.
- Candidate 002 remains blocked.

### Acceptance criteria

- Acceptance tests pass locally.
- No market data is added to the repository.
- No broker/risk/execution functionality is accessed.
- Harness correctness is established before any strategy tuning.

### Stop condition

Stop after local acceptance evidence is reviewed.

### Rollback criteria

Rollback if tests require live services, committed market data, broker access, order access, or strategy tuning.

## Phase 1B.8 - VPS Validation Gate

### Objective

Define a VPS validation gate that confirms the harness does not require VPS research data access and does not attempt live, paper, broker, account, order, portfolio, balance, risk-sizing, or execution behavior.

This gate is validation-only. It must not sync market data to the VPS.

### Files likely to be created or modified

Likely files:

- `docs/phase_1b_vps_validation_gate.md`

Possible test additions only if separately authorized:

- A local-only preflight test proving data-root absence on VPS fails closed without side effects

### Files explicitly forbidden

- Market data artifacts
- Broker/account/order/portfolio/balance files
- Risk files
- Execution files
- Scheduler/systemd/timer files
- Strategy files
- VPS deployment scripts unless separately authorized

### Test requirements

- Harness must fail closed when local research data root is unavailable.
- Failure must not try to fetch Tiingo data.
- Failure must not access broker/account/order/portfolio/balance functionality.
- Failure must not create market data artifacts in the repo.
- Validation confirms no VPS research data requirement.

### Acceptance criteria

- VPS gate documents that research data remains local-only.
- No market data is synced to VPS.
- No paper/live trading path is enabled.
- Candidate 002 remains blocked unless and until the full prior sequence is accepted.

### Stop condition

Stop after the VPS validation gate is reviewed.

### Rollback criteria

Rollback if the gate requires market-data sync to VPS, opens broker connectivity, enables paper/live trading, or changes scheduler/systemd/timer behavior.

## Phase 1B Completion Criteria

Phase 1B is complete only when all implementation units have passed review in order, local acceptance tests pass, deterministic output hashes match across repeated runs, Candidate 001 has been replayed through the harness without submit access, and every Phase 1 universe result is labeled `NON_GENERALIZABLE_RESEARCH_RESULT`.

Completion of Phase 1B does not validate Candidate 001 predictive edge and does not unblock Candidate 002 automatically. Candidate 002 requires a separate authorization gate after the harness exists and Candidate 001 replay artifacts have been reviewed.
