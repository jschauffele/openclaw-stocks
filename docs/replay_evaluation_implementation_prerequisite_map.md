# Replay/Evaluation Implementation Prerequisite Map

## Purpose

This map source-controls the implementation order, prerequisites, candidate
files, forbidden actions, stop conditions, and non-authority boundaries for the
replay/evaluation authority chain before any code phase begins.

This map does not approve implementation. The replay/evaluation authority
phase is closed at the governance and boundary level only. Implementation
remains unapproved.

This docs map does not approve tests, code, constants, types, modules, package
creation, runtime capture, storage, hashing, evaluation, promotion, broker
work, execution permission, or live trading.

## Required Implementation Order

The required implementation order is:

1. Manifest schema vocabulary/types.
2. Deterministic serialization and canonical byte generation.
3. Hash algorithm/version and integrity status vocabulary.
4. Package identity and package layout rules.
5. Manifest generation.
6. Section/package hash computation.
7. Integrity validation.
8. Storage root/path/lifecycle/finalization/immutability.
9. Runtime source-reference and source-artifact authority.
10. Runtime artifact discovery/capture.
11. Replay package creation.
12. Evaluation metric/attribution/experiment registry prerequisites.
13. Promotion workflow prerequisites.

No implementation unit may imply broker authority, execution permission, or
live trading. Any unit requiring filesystem reads or writes must wait for a
separate filesystem/storage authority gate. Any unit requiring runtime
artifacts must wait for a separate runtime capture/source artifact gate. Any
unit requiring broker/API/TWS/Alpaca/IBKR access is outside this map and
requires a separate broker/runtime gate.

JSONL remains chronology evidence only. Mapper completeness is not complete
replay package authority. Evaluation output is not promotion. Broker-visible
evidence is not broker authority.

## Unit 1: Manifest Schema Vocabulary/Types

- Current authority status: docs-rebased and test-guarded; implementation is
  unapproved.
- Implementation readiness: first eventual code candidate only after this map
  is recorded and guarded.
- Prerequisite dependencies: manifest schema authority contract, current mapper
  boundary, current boundary guard.
- Candidate files: `tools/replay/package_schema.py` or future
  `tools/replay/manifest_schema.py`; tests in `tests/test_offline_replay_mapper.py`
  or a separately approved manifest-schema test file.
- Forbidden files/actions: no `main.py`, broker modules, runtime modules,
  filesystem writers, manifest builders, serializers, hash modules, storage
  modules, runtime capture modules, evaluation modules, or promotion modules.
- Required tests: positive vocabulary/type tests and negative boundary tests
  proving no manifest generation, package creation, serialization, hashing,
  storage, runtime capture, evaluation, promotion, broker authority, execution
  permission, or live trading authority.
- Stop conditions: any need to generate manifests, create packages, serialize,
  hash, store, capture runtime artifacts, evaluate, promote, touch broker/API,
  or imply live trading.
- Non-authority boundaries: pure in-memory vocabulary/types only.
- Filesystem access allowed: no.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 2: Deterministic Serialization And Canonical Bytes

- Current authority status: docs-rebased and test-guarded; implementation is
  unapproved.
- Implementation readiness: blocked until manifest vocabulary and serializer
  input model are stable.
- Prerequisite dependencies: manifest schema vocabulary/types, serializer input
  eligibility, canonical JSON scope, absent/null/not_applicable semantics,
  timestamp and numeric rules.
- Candidate files: future `tools/replay/canonical_json.py`,
  `tools/replay/canonical_bytes.py`, or serialization-specific tests.
- Forbidden files/actions: no manifest generation, package creation, hash
  computation, storage, runtime capture, evaluation, promotion, broker/API
  access, or runtime mutation.
- Required tests: canonical ordering, chronology preservation, unsupported type
  fail-closed behavior, and non-authority boundary tests.
- Stop conditions: unstable input vocabulary, ambiguous floats, ambiguous
  timestamp precision, undefined absent/null/not_applicable semantics, or any
  implied downstream authority.
- Non-authority boundaries: serializer output cannot become manifest authority,
  package authority, hash authority, storage authority, runtime capture
  authority, evaluation authority, promotion authority, broker authority,
  execution permission, or live trading authority.
- Filesystem access allowed: no.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 3: Hash Algorithm/Version And Integrity Status Vocabulary

- Current authority status: docs-rebased and test-guarded; implementation is
  unapproved.
- Implementation readiness: blocked until canonical byte authority exists.
- Prerequisite dependencies: deterministic serialization, canonical byte input,
  manifest schema scope, section status semantics, provenance and redaction
  vocabulary.
- Candidate files: future `tools/replay/hashing.py`,
  `tools/replay/integrity.py`, or integrity-specific tests.
- Forbidden files/actions: no hash computation if the scope is vocabulary only,
  no integrity validation, no package creation, no storage, no runtime capture,
  no evaluation, no promotion, no broker/API access.
- Required tests: hash algorithm/version vocabulary tests, integrity status
  vocabulary tests, and boundary tests proving no computed hashes or validators
  exist unless separately approved.
- Stop conditions: missing canonical bytes, unknown hash algorithm/version,
  undefined integrity statuses, missing provenance/redaction semantics, or
  implied package completeness.
- Non-authority boundaries: placeholder hash fields cannot imply computed hash
  authority or package completeness.
- Filesystem access allowed: no.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 4: Package Identity And Package Layout Rules

- Current authority status: docs-rebased and test-guarded; implementation is
  unapproved.
- Implementation readiness: blocked until manifest vocabulary and section
  status semantics exist.
- Prerequisite dependencies: canonical run_id rules, governed package_id rules,
  manifest schema vocabulary, section identity/status vocabulary.
- Candidate files: future `tools/replay/package_layout.py` or
  package-identity tests.
- Forbidden files/actions: no package directories, filesystem writes, manifest
  generation, package creation, storage, runtime capture, evaluation,
  promotion, or broker/API access.
- Required tests: package identity and layout rule tests plus boundaries proving
  no directories or packages are created.
- Stop conditions: ambiguous package identity, mixed run_id, unknown source
  references, or need for filesystem paths before storage authority.
- Non-authority boundaries: layout rules are not package creation authority and
  not complete replay package authority.
- Filesystem access allowed: no.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 5: Manifest Generation

- Current authority status: docs authority exists; implementation is
  unapproved.
- Implementation readiness: blocked until schema vocabulary and input
  eligibility exist.
- Prerequisite dependencies: manifest schema vocabulary/types, package identity
  rules, section status semantics, provenance/redaction fields.
- Candidate files: future `tools/replay/manifest_builder.py` and
  manifest-generation tests.
- Forbidden files/actions: no filesystem writes, package creation, hashing,
  storage, runtime capture, evaluation, promotion, broker/API access, or live
  trading.
- Required tests: in-memory manifest object generation, required/optional field
  handling, fail-closed malformed inputs, and downstream non-authority tests.
- Stop conditions: missing schema vocabulary, missing provenance/redaction
  status, mixed run_id, unknown source references, or need to write files.
- Non-authority boundaries: manifest output is not package creation, package
  completeness, storage, finalization, evaluation, promotion, broker authority,
  execution permission, or live trading authority.
- Filesystem access allowed: no.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 6: Section/Package Hash Computation

- Current authority status: docs authority exists; implementation is
  unapproved.
- Implementation readiness: blocked until canonical bytes, hash
  algorithm/version, manifest generation, and section scopes exist.
- Prerequisite dependencies: units 2, 3, and 5.
- Candidate files: future hash computation module and hash computation tests.
- Forbidden files/actions: no filesystem writes, storage finalization, runtime
  capture, package creation, evaluation, promotion, broker/API access, or live
  trading.
- Required tests: section hash, manifest hash, package hash distinction; mixed
  run_id fail-closed behavior; missing provenance/redaction fail-closed
  behavior; no package completeness authority.
- Stop conditions: missing canonical bytes, missing section scope, unknown hash
  version, sensitive data exposure, mixed run_id, or undefined redaction state.
- Non-authority boundaries: hash output cannot create manifest authority,
  package authority, package completeness, storage authority, finalization
  authority, runtime capture authority, evaluation authority, promotion
  authority, broker authority, execution permission, or live trading authority.
- Filesystem access allowed: no.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 7: Integrity Validation

- Current authority status: docs authority exists; implementation is
  unapproved.
- Implementation readiness: blocked until hash computation, provenance,
  redaction, source references, and run_id alignment rules exist.
- Prerequisite dependencies: units 3 and 6 plus source/provenance semantics.
- Candidate files: future integrity validation module and integrity validation
  tests.
- Forbidden files/actions: no storage/finalization, package creation, runtime
  capture, evaluation, promotion, broker/API access, or live trading.
- Required tests: mismatch fail-closed behavior, missing hash fail-closed
  behavior, provenance/redaction/source-reference failure cases, and no storage
  authority.
- Stop conditions: missing hashes, mismatches, mixed run_id, missing
  provenance, missing/invalid redaction status, unknown source references, or
  sensitive data exposure.
- Non-authority boundaries: validation result is not storage authority,
  finalization authority, package creation authority, evaluation authority,
  promotion authority, broker authority, execution permission, or live trading
  authority.
- Filesystem access allowed: no.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 8: Storage Root/Path/Lifecycle/Finalization/Immutability

- Current authority status: docs-rebased and test-guarded; implementation is
  unapproved.
- Implementation readiness: metadata-only in-memory scope ready after units 4
  and 7; finalized persistence scope remains blocked until unit 11 and a
  separate filesystem/storage/finalization gate exist.
- Prerequisite dependencies: units 4 and 7 for metadata-only in-memory scope;
  unit 11 additionally required for finalized persistence scope only.
- Candidate files: future storage lifecycle module and storage tests, only
  after a separate filesystem/storage gate.
- Forbidden files/actions: no filesystem reads or writes before that separate
  gate, no package directories, no runtime capture, no evaluation, no
  promotion, no broker/API access.
- Required tests: root/path authority, lifecycle states, no-overwrite finalized
  evidence, correction/invalidation/supersession lineage, and fail-closed
  path/root behavior.
- Stop conditions: unknown root, missing path authority, attempted overwrite,
  missing integrity validation, mixed run_id, missing provenance, missing or
  invalid redaction status, unknown source references, or sensitive data
  exposure.
- Non-authority boundaries: storage output cannot create package completeness,
  runtime capture, evaluation, promotion, broker authority, execution
  permission, or live trading authority.
- Filesystem access allowed: no until a separate filesystem/storage authority
  gate approves it.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 9: Runtime Source-Reference And Source-Artifact Authority

- Current authority status: docs-rebased and test-guarded; implementation is
  unapproved.
- Implementation readiness: blocked until storage, package, provenance, and
  redaction semantics are stable.
- Prerequisite dependencies: package layout, source-reference vocabulary,
  redaction/provenance semantics, storage/finalization boundaries.
- Candidate files: future source-reference/source-artifact module and tests.
- Forbidden files/actions: no runtime artifact discovery, no source path
  ingestion, no artifact copying, no filesystem reads/writes, no package
  creation, no broker/API access.
- Required tests: source reference vocabulary, absent/not-applicable
  declarations, redaction/provenance requirements, and no file access.
- Stop conditions: unknown source references, missing provenance, missing or
  invalid redaction status, source path ambiguity, or need to inspect runtime
  artifacts.
- Non-authority boundaries: source references are not runtime capture, package
  creation, storage, evaluation, promotion, broker authority, execution
  permission, or live trading authority.
- Filesystem access allowed: no.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 10: Runtime Artifact Discovery/Capture

- Current authority status: vocabulary-only scope validated
  (tools/replay/runtime_artifact_discovery.py exists and is test-guarded);
  actual runtime capture (tools/replay/runtime_capture.py,
  tools/replay/runtime_artifacts.py, tools/replay/source_path_ingestion.py)
  remains unapproved and requires a separate runtime capture authority gate
  before those files may exist.
- Implementation readiness: vocabulary-only scope (runtime_artifact_discovery.py)
  validated as no-op; actual capture scope blocked until source-reference
  authority, source path authority, redaction, storage, and package creation
  exist and a separate runtime capture/source-artifact gate is opened (see
  Post-Unit-11 Prerequisite Chain section below).
- Prerequisite dependencies: units 8, 9, and 11 plus terminal completion and
  strict run_id alignment rules.
- Candidate files: future `tools/replay/runtime_capture.py` and runtime capture
  tests, only after a separate runtime capture/source artifact gate.
- Forbidden files/actions: no runtime logs or artifacts before approval, no
  ungoverned filesystem reads/writes, no broker/API calls, no `main.py`, no
  timer mutation, no signal remediation.
- Required tests: source path authority, discovery scope, stale/missing/mixed
  run_id fail-closed behavior, redaction/provenance enforcement, and
  non-authority boundaries.
- Stop conditions: missing terminal completion, stale/missing/malformed
  artifacts, mixed run_id, unknown source references, missing provenance,
  missing/invalid redaction status, sensitive data exposure, or implied package
  creation.
- Non-authority boundaries: runtime capture is not package creation, storage
  finalization, evaluation, promotion, broker authority, execution permission,
  or live trading authority.
- Filesystem access allowed: no until separate runtime capture/source artifact
  and filesystem gates approve it.
- Runtime artifact access allowed: no until a separate runtime capture/source
  artifact gate approves it.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 11: Replay Package Creation

- Current authority status: docs-rebased and test-guarded; implementation is
  unapproved.
- Implementation readiness: blocked until manifest generation, serialization,
  hashing/integrity, package layout, and storage/finalization contracts exist
  for the target scope.
- Prerequisite dependencies: units 4, 5, 6, 7, and storage/finalization scope
  for persisted/finalized packages.
- Candidate files: future package creation module and package creation tests.
- Forbidden files/actions: no runtime artifact ingestion unless runtime capture
  is separately approved, no filesystem writes unless storage is separately
  approved, no evaluation, no promotion, no broker/API access, no live trading.
- Required tests: draft-only assembly if approved, package identity alignment,
  provenance/redaction checks, completeness prerequisites, and no downstream
  authority.
- Stop conditions: missing run_id, mixed run_id, stale/malformed artifacts,
  missing terminal completion for runtime-derived inputs, missing provenance,
  missing/invalid redaction status, unknown source references, sensitive data
  exposure, ambiguous package identity, or implied runtime capture/storage.
- Non-authority boundaries: package creation output cannot create evaluation,
  promotion, broker authority, execution permission, or live trading authority.
- Filesystem access allowed: no unless a separate storage/filesystem gate
  approves it.
- Runtime artifact access allowed: no unless a separate runtime capture/source
  artifact gate approves it.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 12: Evaluation Metric/Attribution/Experiment Registry Prerequisites

- Current authority status: docs-rebased and test-guarded; implementation is
  unapproved.
- Implementation readiness: blocked until complete authoritative replay
  packages and finalized immutable evidence exist for trusted scoring.
- Prerequisite dependencies: complete replay package authority, finalized
  immutable package evidence, metric vocabulary/versioning, attribution
  vocabulary/versioning, experiment identifier/registry authority, package-set
  inclusion/exclusion rules, reproducibility rules, candidate identity and
  parameter versioning.
- Candidate files: future evaluation vocabulary/registry modules and tests,
  after a separate evaluation prerequisite gate.
- Forbidden files/actions: no strategy promotion, no broker/API access, no
  runtime mutation, no order actions, no live trading.
- Required tests: metric vocabulary, attribution vocabulary, experiment
  identifier/registry boundaries, fail-closed package eligibility, and
  evaluation-output non-authority.
- Stop conditions: incomplete, mutable, stale, untrusted, mixed-run,
  unhashable, unfinalized, non-authoritative, provenance-defective,
  redaction-defective, or invalidated replay packages.
- Non-authority boundaries: evaluation reports, metrics, comparisons, and
  recommendations do not create promotion authority, broker authority,
  execution permission, or live trading authority.
- Filesystem access allowed: no unless a separate evaluation artifact/storage
  gate approves it.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Unit 13: Promotion Workflow Prerequisites

- Current authority status: docs-rebased and test-guarded; implementation is
  unapproved.
- Implementation readiness: blocked until evaluation, metrics, attribution,
  experiment registry, approval, monitoring, rollback, rejection, and
  production deployment gates exist.
- Prerequisite dependencies: unit 12 plus explicit promotion workflow
  governance.
- Candidate files: future promotion workflow docs/tests/modules only after a
  separate promotion gate.
- Forbidden files/actions: no broker/API access, no runtime mutation, no order
  submission/cancellation/flattening/selling, no signal remediation, no live
  trading approval.
- Required tests: explicit approval gate behavior, rollback/rejection
  boundaries, monitoring/deployment separation, and no broker/live authority.
- Stop conditions: implied automatic promotion from score/report/AI
  recommendation/shadow output/paper result, missing approval workflow, missing
  rollback, missing monitoring, broker/API dependency, or execution/live
  implication.
- Non-authority boundaries: promotion workflow output does not create broker
  authority, execution permission, or live trading authority.
- Filesystem access allowed: no unless separately approved.
- Runtime artifact access allowed: no.
- Broker/API access allowed: no.
- Execution/live trading authority allowed: no.

## Post-Unit-11 Prerequisite Chain To Unit 12

Units 1 through 11 have been validated as pure in-memory vocabulary,
metadata, and draft package creation only. Unit 12 (evaluation
metric/attribution/experiment registry prerequisites) is blocked until the
following gates are opened in order. No gate in this chain may be skipped.

### Gate A: Runtime Capture Authority Gate

Required before: tools/replay/runtime_capture.py,
tools/replay/runtime_artifacts.py, tools/replay/source_path_ingestion.py may
exist.

This gate requires a separate operator-approved runtime/VPS authority decision
and explicit filesystem/source-artifact authority grant. It cannot be opened
from the local Mac dev lane alone.

Prerequisites for this gate (blocked until source-reference authority, source
path authority, redaction, storage, and package creation exist):
- All of units 8, 9, and 11 in-memory vocabulary scopes are validated.
- Explicit source-reference authority exists (source_artifacts.py validated).
- Explicit runtime artifact discovery vocabulary exists
  (runtime_artifact_discovery.py validated).
- A separate filesystem/source-artifact authority grant is recorded in
  source-controlled docs.
- A separate operator-approved VPS/runtime gate is recorded.

Required behaviors this gate must define:
- Strict run_id alignment: every captured artifact run_id must match the
  canonical_run_id; mixed run_id must fail closed.
- Terminal completion: a run must have a terminal completion event before its
  artifacts are capture-eligible.
- Stale artifacts must fail closed.
- Missing artifacts without explicit absent or not-applicable declarations
  must fail closed.
- Malformed artifacts must fail closed.
- Unknown source references must fail closed.
- Missing provenance must fail closed.
- Missing or invalid redaction status must fail closed.
- Sensitive data exposure must stop capture.
- No broker/API/TWS/Alpaca/IBKR access.
- No main.py calls, timer mutation, or signal remediation.

Non-authority boundaries:
- Runtime capture output is not package completeness authority.
- Runtime capture output is not finalized immutable evidence.
- Runtime capture output is not evaluation authority.
- Runtime capture output is not promotion authority.
- Runtime capture output is not broker authority.
- Runtime capture output is not execution permission.
- Runtime capture output is not paper trading approval.
- Runtime capture output is not live trading authority.

### Gate B: Package Writer And Package Persistence Authority Gate

Required before: tools/replay/package_writer.py,
tools/replay/package_persistence.py may exist.

This gate requires explicit filesystem write authority and a separate
storage/finalization gate. It cannot be opened from the local Mac dev lane
alone without a separate filesystem write authority grant.

Prerequisites for this gate:
- Gate A (runtime capture authority) must be complete.
- Filesystem write authority must be explicitly granted in source-controlled
  docs.
- Storage and finalization authority (unit 8, filesystem_storage_authority.py,
  storage_implementation.py) must be stable.
- Package layout (unit 4) and package identity rules must be stable.
- Manifest generation (unit 5), hash computation (unit 6), integrity
  validation (unit 7) must be stable.

Non-authority boundaries:
- Package writer output is not evaluation authority.
- Package writer output is not promotion authority.
- Package writer output is not broker authority or execution permission.

### Gate C: Complete Replay Package Authority

Required before: any module may claim complete replay package authority or
produce finalized immutable replay package evidence.

Prerequisites for this gate:
- Gate B (package writer/persistence) must be complete.
- Actual on-disk replay packages must exist with known hashes and
  source-controlled provenance.
- No-overwrite finalization semantics must be enforced.
- Immutability markers must be present for finalized packages.

### Gate D: Evaluation Prerequisite Governance Gate

Required before: Unit 12 may be opened.

This is the "separate evaluation prerequisite gate" required by Unit 12.

Prerequisites for this gate:
- Gate C (complete replay package authority) must be complete.
- Finalized immutable evidence must exist.
- Metric vocabulary and versioning must be governed and source-controlled.
- Attribution vocabulary and versioning must be governed.
- Experiment identifier and registry authority must be governed.
- Package-set inclusion/exclusion rules must be governed.
- Reproducibility rules must be governed.
- Candidate strategy identity and parameter versioning must be governed.
- Baseline versus candidate comparison rules must be governed.
- As-of feature availability and decision-time evidence rules must be governed.

Non-authority boundaries (carried forward from Unit 12 map):
- Evaluation reports, metrics, comparisons, and recommendations do not create
  promotion authority.
- Evaluation output must remain separate from strategy promotion.
- Evaluation output is not broker authority, execution permission, paper
  trading approval, or live trading authority.

## Operator Approval Record: Runtime Capture Authority Path

### Phase 2 VPS/Git Alignment Confirmation

The operator confirmed Phase 2 VPS/Git alignment on 2026-06-10:

- VPS repo: /opt/openclaw-stocks
- VPS HEAD: 3ba1d52eeb3eb3291fe3c2477478b2ed0275365c
- GitHub/main: 3ba1d52eeb3eb3291fe3c2477478b2ed0275365c
- Phase 2 authority check result: PHASE2_VPS_AUTHORITY_CHECK_PASS

This is a governance record only. It does not authorize runtime capture
implementation, source path ingestion, artifact reads, or any downstream
authority.

### Governance Approval Scope

This approval records the future-authorized path only. It does not approve:

- runtime_capture.py, runtime_artifacts.py, or source_path_ingestion.py
  (all remain forbidden until a separate implementation gate)
- source_references.py or source_paths.py
  (both now exist and are test-guarded as of commit
  c00b6567f8349b82e311d8b37abd9b7ebb7290bd; this does not approve runtime
  capture, source path ingestion, or any downstream authority)
- file_reader.py extension to VPS runtime artifact paths
  (validated for governed replay evidence reads only; cannot independently
  authorize VPS runtime artifact capture)
- any filesystem-backed package implementation, storage finalization,
  immutability enforcement, evaluation, promotion, broker/API access,
  execution permission, paper trading, or live trading authority

### Future-Approved VPS Artifact Path Families (Governance Only)

The following artifact path families are recorded for future governance
reference. No artifact in these families may be read until a subsequent
file-reader authority extension code gate is opened after Gate A is complete.
Gate A is now complete (both A1 and A2 recorded). Actual runtime artifact
reads remain blocked until the file-reader authority extension code gate and
any required VPS execution gate are separately opened:

- logs/<run_id>.jsonl — canonical JSONL event log per run
- last_run_report.json — derived operational summary; matched to JSONL run_id
- order_state.json — operational state evidence; requires explicit provenance
  or explicit absent declaration
- observations — only if later explicitly source-referenced and
  run_id-governed; not approved without a separate observations gate
- runtime visibility evidence — only if later explicitly source-referenced or
  declared absent/not-applicable; not approved without a separate gate

### Required Future Capture Artifact Rules

Every artifact captured in any future runtime capture gate must have:

- Canonical run_id alignment: artifact internal run_id must match the
  canonical_run_id derived from the JSONL filename; mixed run_id fails closed.
- Terminal completion evidence: the run must have a terminal completion event
  before any artifact in that run is capture-eligible.
- Source reference identity: each artifact must be bound to a known, governed
  source reference name.
- Source path identity: each artifact must be bound to an explicitly governed
  source path; ungoverned path discovery is forbidden.
- Provenance: explicit and recorded per artifact.
- Redaction status: explicit and valid per artifact.
- Fail-closed behavior for: stale artifact, missing artifact without
  absent/not-applicable declaration, malformed artifact, mixed run_id,
  unknown source reference, missing provenance, missing or invalid redaction
  status, and sensitive data exposure.

### Runtime Capture Non-Authority Boundaries

Runtime capture output, when later implemented, cannot create:

- Package completeness authority
- Finalized immutable evidence
- Evaluation authority
- Promotion authority
- Broker/API authority
- Execution permission
- Paper trading approval
- Live trading authority

### Unit 12 Remaining Blockers

Unit 12 (evaluation metric/attribution/experiment registry prerequisites)
remains blocked until all of the following are complete:

1. ~~Source-reference and source-path authority modules (source_references.py,
   source_paths.py) are created and validated.~~
   **COMPLETE as of commit c00b6567f8349b82e311d8b37abd9b7ebb7290bd.**
   tools/replay/source_references.py, tools/replay/source_paths.py, and
   tools/replay/verify_vocabulary_boundaries.py all exist and are
   test-guarded. tests/test_vocabulary_boundary_verifier.py provides 16 tests
   covering pass/fail paths and boundary vocabulary allowances.
   verify_vocabulary_boundaries.py is the permanent source-controlled
   deterministic verifier for source-reference/source-path vocabulary
   boundaries; it uses AST parsing and fixed text checks and does not read
   runtime artifacts, resolve paths, or perform runtime capture.
   This completion does not authorize: runtime capture, runtime artifact reads,
   source path ingestion, file path ingestion, package writing, package
   persistence, complete replay package authority, finalized immutable
   evidence, evaluation authority, promotion authority, broker/API authority,
   execution permission, paper trading approval, or live trading authority.
2. Runtime capture authority (runtime_capture.py, runtime_artifacts.py,
   source_path_ingestion.py) is implemented and validated under Gate A.
   Gate A required two governance records:
   (a) filesystem/source-artifact authority grant — **COMPLETE as A1** (see
   Gate A Record A1 section below);
   (b) operator-approved VPS/runtime gate — **COMPLETE as A2** (see Gate A
   Record A2 section below).
   **Gate A is now complete as a prerequisite authority record.** Unit 12
   remains blocked. runtime_capture.py, runtime_artifacts.py, and
   source_path_ingestion.py remain forbidden until separate in-memory contract
   module gates are opened after Gate A.
3. Package writer and package persistence authority (package_writer.py,
   package_persistence.py) is implemented and validated under Gate B.
4. Complete replay package authority exists with actual on-disk packages
   (Gate C).
5. Finalized immutable evidence exists.
6. Evaluation prerequisite governance is complete (Gate D).

No gate in this chain may be skipped. This operator approval record does not
advance the chain; it records the pre-conditions that must be met.

## Gate A Record A1: Filesystem/Source-Artifact Authority Grant

### A1 Status

Recorded as a docs-only governance record on 2026-06-11. This is record A1
of the two records required to open Gate A. Gate A remains incomplete until
A2 is separately operator-approved and recorded.

### A1 Gate Prerequisite Chain Status

- Source-reference/source-path vocabulary: **COMPLETE**
  (source_references.py, source_paths.py, verify_vocabulary_boundaries.py)
- Vocabulary boundary verifier: **COMPLETE**
  (tests/test_vocabulary_boundary_verifier.py, 16 tests)
- A1 filesystem/source-artifact authority record: **COMPLETE** (this record)
- A2 operator VPS/runtime gate: **COMPLETE** (see Gate A Record A2 below)
- Gate A: **COMPLETE** (both A1 and A2 recorded)
- Unit 12: **BLOCKED** (Gates B, C, D not started)

### A1 Approved VPS Artifact Root

The approved VPS artifact root for governed runtime artifact reads is:

```
/opt/openclaw-stocks
```

This root applies only to the OpenClaw VPS at the path established in Phase 2.
No other filesystem root is approved by this record.

### A1 Approved Flag

`allow_absolute_artifact_root: True` is approved only for governed VPS
artifact paths under `/opt/openclaw-stocks`. It is not approved for arbitrary
absolute paths, local Mac paths, or any path outside this root.

### A1 Authorized Path Families

The only A1-authorized path families are:

- `logs/<run_id>.jsonl` — canonical JSONL event log per run
- `last_run_report.json` — derived operational summary; matched to JSONL run_id
- `order_state.json` — operational state evidence; requires explicit provenance
  or explicit absent/not-applicable declaration

The following path families remain not authorized by A1 and require a
separate gate before they may be read:

- observations — requires a separate observations gate
- runtime visibility evidence — requires a separate gate

### A1 Non-Authorization Statement

A1 alone does not authorize actual VPS artifact reads. Actual governed VPS
runtime artifact reads remain blocked until A2 is separately recorded and
Gate A is complete.

A1 alone does not authorize these modules to exist:

- tools/replay/runtime_capture.py
- tools/replay/runtime_artifacts.py
- tools/replay/source_path_ingestion.py
- tools/replay/runtime_artifact_file_reader.py
- tools/replay/approved_file_reads.py
- tools/replay/package_writer.py
- tools/replay/package_persistence.py

A1 does not authorize:

- Runtime capture
- Source path ingestion
- Arbitrary file path ingestion
- Artifact discovery beyond existing metadata-only vocabulary
- Artifact copying
- Package writing or package persistence
- Complete replay package authority
- Finalized immutable evidence
- Evaluation authority
- Promotion authority
- Broker/API authority
- Strategy/risk/execution behavior
- Config/credential/systemd/deployment changes
- Paper trading approval
- Live trading authority

### A2 Requirements — Now Satisfied

A2 has been recorded (see Gate A Record A2 section below). Gate A is complete.

## Gate A Record A2: Operator VPS/Runtime Semantics Authority Grant

### A2 Status

Recorded as a docs-only governance record on 2026-06-11. This is record A2
of the two records required to open Gate A. With A1 and A2 both recorded,
Gate A is complete as a prerequisite authority record. Gate A completion does
not open Gates B, C, or D. Unit 12 remains blocked.

### A2 Gate Prerequisite Chain Status

- Source-reference/source-path vocabulary: **COMPLETE**
- Vocabulary boundary verifier: **COMPLETE**
- A1 filesystem/source-artifact authority record: **COMPLETE**
- A2 operator VPS/runtime gate: **COMPLETE** (this record)
- Gate A: **COMPLETE** (both A1 and A2 recorded)
- Gate B (package writer/persistence): **COMPLETE** (as docs-only prerequisite
  authority record, see Gate B Record B1 below)
- Gate C (complete replay package authority): **NOT STARTED**
- Gate D (evaluation prerequisite governance): **NOT STARTED**
- Unit 12: **BLOCKED** (Gates C and D not started)

### A2 Terminal Event Binding Rule

A terminal runtime event is defined as exactly one JSONL event where:

- `event_type == "system"` AND
- `stage == "completion"`

This is a source-controlled runtime fact derived from `event_logger.py` and
`main.py`. Every execution path in `main.py` converges on exactly one
`log_event("system", "completion", <status>, {...})` call. No run can reach
a second completion event in normal flow.

Fail-closed rules for terminal events:

- A run with zero terminal completion events must fail closed.
- A run with duplicate terminal completion events must fail closed.
- A run with malformed, ambiguous, mixed-run, stale, or non-aligned terminal
  metadata must fail closed.
- The terminal completion event `run_id` must match the JSONL filename stem.

### A2 Completion-Status Eligibility Policy

The following operator policy governs which completion statuses are
capture-eligible:

- `status == "ok"` — **capture-eligible**, subject to standard fail-closed
  alignment guards. Represents paper order submitted or dry run completed.
- `status == "blocked"` — **capture-eligible**, subject to standard
  fail-closed alignment guards. Blocked completions represent normal
  controlled runtime outcomes in paper trading operation (killswitch,
  market session, duplicate, risk, reconciliation checks, etc.).
- `status == "error"` — **not eligible** for governed runtime capture
  packages, replay evaluation evidence, promotion evidence, or success
  evidence. Error completions represent diagnostic terminal states. A later
  explicit diagnostic authority gate may separately authorize error-run
  capture; no such gate exists yet.

All eligibility determinations remain subject to: canonical run_id alignment,
terminal completion event presence, provenance, redaction status, and all
other fail-closed guards defined in Gate A and the runtime capture authority
contract.

### A2 run_id Format and JSONL Path Binding

The source-controlled run_id format (from `event_logger.generate_run_id()`):

```
run_YYYY-MM-DDTHH:MM:SSZ_XXXXXX
```

Where `XXXXXX` is the six-character lowercase hex suffix produced by
`secrets.token_hex(3)`. Example shape: `run_2026-05-29T19:45:04Z_8b7033`.

JSONL path binding rules:

- The canonical JSONL path family is `logs/{run_id}.jsonl`.
- The VPS artifact root (from A1) is `/opt/openclaw-stocks`.
- The canonical VPS JSONL path is `/opt/openclaw-stocks/logs/{run_id}.jsonl`.
- The JSONL filename stem must equal the canonical run_id.
- Every event line in the JSONL must carry the same `run_id` field value.
- The terminal completion event `run_id` field must match the JSONL filename
  stem.
- Mixed `run_id` values within a single JSONL file must fail closed.

### A2 last_run_report.json Binding

- `last_run_report.json` is eligible only if its `run_id` field matches the
  canonical JSONL filename stem and the JSONL internal `run_id`.
- `last_run_report.json` is not independently authoritative without
  JSONL/run_id alignment.
- A stale report file (run_id mismatch or absent) must fail closed.
- A2 does not authorize `last_run_report.json` reads; reads remain blocked
  until the file-reader authority extension code gate is opened.

### A2 order_state.json Authority Boundary

- `order_state.json` does not independently establish canonical run_id
  authority unless a later governed capture or file-reader authority extension
  explicitly binds it to a run.
- `order_state.json` must not be treated as run-aligned promotion or
  evaluation evidence from A2 alone.
- A2 does not authorize `order_state.json` reads.

### A2 In-Memory Module Eligibility Statement

After Gate A is complete, the following modules may become eligible in later
separate gates as local in-memory contract modules only, subject to each gate
meeting its own prerequisites:

- `tools/replay/runtime_capture.py`
- `tools/replay/runtime_artifacts.py`
- `tools/replay/source_path_ingestion.py`

These modules are not approved for implementation in this gate. They remain
forbidden until their respective in-memory contract module gates are opened.

### A2 Non-Authorization Statement

A2 does not authorize:

- VPS commands or VPS runtime execution
- Runtime capture execution
- Runtime artifact reads or runtime log reads
- Source path ingestion or arbitrary file path ingestion
- Artifact discovery beyond existing metadata-only vocabulary
- Artifact copying
- Package creation, package directories, or filesystem-backed package
  persistence
- Immutable evidence creation
- Storage or finalization implementation
- Evaluation, attribution engine, or experiment registry implementation
- Promotion workflow
- Broker/API/TWS/Alpaca/IBKR behavior
- Strategy, risk, or execution behavior changes
- Config, credential, `.env`, systemd, scheduler, or deployment changes
- Paper trading approval or live trading approval
- Order submission, order cancellation, cleanup, flatten, or sell
- Broker remediation

## Gate B Record B1: Filesystem Write Authority Grant

### B1 Status

Recorded as a docs-only governance record on 2026-06-11. This is the
filesystem write authority record required before package_writer.py and
package_persistence.py may exist. Gate B is complete as a prerequisite
authority record.

Gate B completion does not authorize package_writer.py or
package_persistence.py to be implemented. It does not authorize filesystem
writes, package directory creation, runtime capture, runtime artifact reads,
storage or finalization implementation, evaluation, promotion, VPS action,
broker/API work, or trading of any kind.

### B1 Gate Prerequisite Chain Status

- Source-reference/source-path vocabulary: **COMPLETE**
- Vocabulary boundary verifier: **COMPLETE**
- Gate A (runtime capture authority — both A1 and A2): **COMPLETE**
- B1 filesystem write authority record: **COMPLETE** (this record)
- Gate B: **COMPLETE** (as a docs-only prerequisite authority record)
- Gate C (complete replay package authority): **NOT STARTED**
- Gate D (evaluation prerequisite governance): **NOT STARTED**
- Unit 12: **BLOCKED** (Gates C and D not started)

### B1 Filesystem Write Authority Scope

Gate B authorizes the docs-level recording of filesystem write authority
boundaries only. It does not itself authorize writes. It does not implement
package_writer.py or package_persistence.py. Future implementation gates
may use this authority only if they separately implement and validate:

- Fail-closed path containment
- Deterministic package layout
- Manifest schema
- Deterministic serialization
- Hashing and integrity validation
- Redaction
- Provenance
- Storage and finalization
- Non-overwrite behavior

### B1 Governed Storage Root Label

The governed storage root label is `"replay_packages"`. This label is
source-controlled in test fixtures (tests/test_offline_replay_mapper.py).
The relative package path family is `"replay_packages/{run_id}"`, where
`{run_id}` is the canonical run_id format defined in Gate A Record A2.

The absolute VPS path follows from Gate A Record A1 (VPS artifact root
`/opt/openclaw-stocks`): the intended absolute VPS package output root is
`/opt/openclaw-stocks/replay_packages`. The absolute path binding is not
yet source-controlled in docs. Future package implementation remains blocked
until a later implementation gate explicitly confirms and records the
absolute VPS package output root and governs path containment relative to it.

No other storage root, absolute path, or path outside the governed root is
approved by this record.

### B1 Absolute VPS Package Output Root (Implementation Gate Record)

Recorded by gate IMPLEMENT_PACKAGE_WRITER_PERSISTENCE (2026-06-11).

- Governed storage root label: `replay_packages`
- Relative package path family: `replay_packages/{run_id}`
- Absolute VPS package output root: `/opt/openclaw-stocks/replay_packages`

The absolute VPS root is recorded as package-output authority metadata only.
`APPROVED_VPS_PACKAGE_ROOT_PATH = "/opt/openclaw-stocks/replay_packages"` is
source-controlled in `tools/replay/package_writer.py`.

This local implementation gate does not authorize real VPS writes. VPS package
writes require a separate VPS execution gate. Gate C (complete replay package
authority), Gate D (evaluation prerequisite governance), and Unit 12 remain
blocked and are not authorized by this implementation gate.

### B1 Fail-Closed Path Authority Rules

Path authority is fail-closed:

- No absolute path writes unless the absolute root is explicitly
  source-controlled and operator-approved.
- No writes outside the governed package output root.
- No path traversal.
- No symlink traversal.
- No arbitrary file path writes.
- No writes to runtime logs.
- No writes to broker files.
- No writes to config, credentials, `.env`, systemd, scheduler, deployment,
  Git metadata, source files, or tests.
- No writes to VPS paths from a local dev gate.
- No package path may be derived from untrusted runtime input without
  validation and canonicalization.

### B1 Authorized Future Write Operations

After future implementation gates separately approve them:

- Create a new governed package directory or staging directory under the
  governed package output root only.
- Write new package files under the governed package root only.
- Write manifest and integrity files under governed package layout only.
- Finalize by deterministic, fail-closed operation only if the
  storage/finalization authority later approves it.

### B1 Explicitly Forbidden Write Operations

The following operations are forbidden and must not be implemented under
this record or any gate that cites only this record as its authority:

- Delete
- Overwrite finalized packages
- Mutate finalized packages
- Append to finalized evidence
- Write outside the governed package root
- `chmod`/`chown` or permission mutation unless separately approved
- Arbitrary `mkdir`
- Arbitrary copy
- Arbitrary rename outside finalization rules
- Shell execution
- Network access
- Broker/API activity
- Credential access
- Runtime activation

### B1 Package Writer / Package Persistence Eligibility

After Gate B is complete as a docs-only authority record, package_writer.py
and package_persistence.py may become eligible only in later separate
implementation gates. Those gates must be explicit and may not be inferred
from Gate B.

package_writer.py is not approved for implementation in this gate.
package_persistence.py is not approved for implementation in this gate.
Future guards protecting these modules must not be flipped in this gate.

### B1 Runtime Capture / Runtime Artifacts / Source Path Ingestion Status

Gate A made runtime_capture.py, runtime_artifacts.py, and
source_path_ingestion.py eligible only for future in-memory contract module
consideration. Gate B does not implement them.

Runtime capture remains blocked until package layout, package creation,
manifest schema, deterministic serialization, hashing/integrity, redaction,
provenance, storage, and finalization authority are separately promoted.

Runtime artifact reads remain blocked until a later file-reader authority
extension and any required VPS/runtime gate are separately opened.

### B1 Gate C and Gate D Status

- Gate C remains **NOT STARTED** and blocked until complete replay package
  authority exists with actual governed package structure.
- Gate D remains **NOT STARTED** and blocked until evaluation prerequisite
  governance is separately recorded.
- Unit 12 remains **BLOCKED** until the Gate B, Gate C, and Gate D chain is
  complete and separately validated.

### B1 Non-Authorization Statement

Gate B does not authorize:

- package_writer.py implementation
- package_persistence.py implementation
- runtime_capture.py implementation
- runtime_artifacts.py implementation
- source_path_ingestion.py implementation
- Future guard flips
- Package directory creation
- Package file creation
- Filesystem-backed package persistence
- Immutable evidence creation
- Storage or finalization implementation
- Runtime capture execution
- Runtime artifact reads or runtime log reads
- Source path ingestion or arbitrary file path ingestion
- Artifact copying
- Evaluation implementation
- Attribution engine or experiment registry implementation
- Promotion workflow
- VPS commands or VPS runtime execution
- Broker/API/TWS/Alpaca/IBKR behavior
- Strategy, risk, or execution behavior changes
- Config, credential, `.env`, systemd, scheduler, or deployment changes
- Paper trading approval or live trading approval
- Order submission, order cancellation, cleanup, flatten, or sell
- Broker remediation

## Gate C Record C1: Complete Replay Package Authority Governance Record

### C1 Status

Recorded as a docs-only governance record on 2026-06-11. This is the
complete replay package authority governance record required before any
Gate C implementation lane may be considered.

C1 is **COMPLETE** as a governance record only. C1 does not mark Gate C
complete. Gate C remains **INCOMPLETE** until later separate
implementation/evidence gates prove actual governed on-disk replay package
authority. Gate D remains **NOT STARTED**. Unit 12 remains **BLOCKED**.

C1 does not implement Gate C. It does not create package files or
directories, write packages, perform runtime capture, read real VPS runtime
artifacts, or approve evaluation, promotion, broker/API work,
strategy/risk/execution changes, paper trading, or live trading.

### C1 Gate Prerequisite Chain Status

- Source-reference/source-path vocabulary: **COMPLETE**
- Vocabulary boundary verifier: **COMPLETE**
- Gate A (runtime capture authority — both A1 and A2): **COMPLETE**
- Gate B (package writer/persistence — B1 plus
  IMPLEMENT_PACKAGE_WRITER_PERSISTENCE): **COMPLETE**
- C1 complete replay package authority governance record: **COMPLETE**
  (this record, governance record only)
- Gate C (complete replay package authority): **INCOMPLETE** (C1 recorded;
  implementation and production on-disk evidence gates not opened)
- Gate D (evaluation prerequisite governance): **NOT STARTED**
- Unit 12: **BLOCKED** (Gate C incomplete, Gate D not started)

### C1 Gate C Ambiguity Resolution (Operator Policy)

The Gate C discovery lane identified an ambiguity in the Gate C requirement
"actual on-disk replay packages must exist." The operator resolves it as
follows:

- tmp_path synthetic package roots are acceptable for local implementation
  tests and deterministic validation of package mechanics and test contracts.
- tmp_path synthetic package roots do not satisfy production Gate C
  completion.
- Production Gate C completion requires actual governed on-disk replay
  packages with known hashes, source-controlled provenance, enforced
  no-overwrite finalization, and immutability markers.
- Real VPS package writes to `/opt/openclaw-stocks/replay_packages` require a
  later explicit VPS execution gate.
- No local Claude/Codex implementation lane may write real VPS packages.
- No local Claude/Codex implementation lane may treat tmp_path package
  evidence as production Gate C evidence.

Governance authority, local implementation tests, production package
evidence, and VPS execution authority remain distinct. None of the four may
be inferred from another.

### C1 Complete Replay Package Authority Contract

Complete replay package authority requires all of the following:

- Canonical run_id (Gate A Record A2 format and JSONL path binding).
- Terminal completion eligibility under the A2 completion-status policy
  (`ok` and `blocked` eligible; `error` not eligible).
- Runtime artifact discovery result.
- Source artifact authority.
- Source path ingestion result.
- Runtime artifact metadata.
- Approved file-read result.
- Package layout.
- Manifest schema.
- Deterministic serialization.
- Hash computation.
- Integrity validation.
- Redaction status.
- Provenance.
- Package writer result.
- Package persistence result.
- Storage/finalization status.
- Known written bytes.
- Content hash.
- Section hashes, if applicable.
- No-overwrite finalization enforcement.
- Immutability marker presence.
- Absent/not_applicable declarations for optional artifacts.
- Fail-closed handling for stale, malformed, mixed-run, ambiguous, sensitive,
  or missing package evidence.

Any package evidence missing one or more of these requirements must fail
closed and cannot be classified as a complete replay package.

### C1 package_completeness.py Boundary

Existing `tools/replay/package_completeness.py` remains metadata-only and
does not itself satisfy production Gate C. Its authority vocabulary is
explicitly `complete_replay_package_authority_metadata_only`, its authority
boundary forbids actual filesystem reads and writes, and its storage
validation accepts metadata-only storage results only.

package_completeness.py may remain a prerequisite contributor to a future
Gate C implementation, but it cannot alone prove actual on-disk complete
replay package authority. Its metadata-only boundary must not be weakened by
C1 or by any gate that cites only C1 as its authority.

### C1 Future Gate C Implementation Path (Identified, Not Opened)

After C1, a later separate implementation gate may define and validate
complete replay package authority machinery. C1 identifies but does not open
the likely future implementation scope:

- A complete replay package authority module, if needed. No module name is
  source-controlled yet; any proposed name is a future implementation
  candidate only and must avoid the guarded future module names
  `package_creator.py`, `manifest_writer.py`, and `manifest_generator.py`,
  which remain test-guarded as non-existent.
- On-disk package evidence binding.
- Written-byte hash verification against manifest hash records.
- Finalized lifecycle verification.
- Immutability marker verification.
- Package writer/persistence result binding.
- Manifest/hash/integrity binding.
- tmp_path-only implementation tests.

That future implementation gate must be explicit and may not be inferred
from C1. Local implementation tests validate mechanics only; they do not
create production Gate C evidence.

### C1 Future VPS Execution Path (Identified, Not Opened)

Even after local Gate C implementation tests pass, real VPS package writes
remain blocked until a separate explicit VPS execution gate authorizes them.
That future VPS execution gate must verify, at minimum:

- VPS repo alignment.
- Clean VPS tree.
- venv Python.
- Filesystem root state.
- Package output root path.
- No runtime/service instability.
- No broker/API/trading authority.
- Explicit operator approval for the bounded package-writing action.
- Post-write package hash/provenance/finalization evidence.

C1 does not open that VPS execution gate.

### C1 order_state.json Boundary

`order_state.json` remains blocked for reads and writes until a later
explicit binding gate. `read_order_state(...)` and
`write_order_state_artifact(...)` remain fail-closed. Gate C must not infer
order_state authority from C1, from package completeness, or from any
package evidence.

### C1 Gate D and Unit 12 Status

- Gate D remains **NOT STARTED**.
- Gate D requires Gate C completion plus finalized immutable evidence plus
  separate evaluation prerequisite governance.
- Unit 12 remains **BLOCKED** after C1.
- No evaluation, attribution engine, experiment registry, promotion
  workflow, or metric authority is approved by C1.

### C1 Non-Authorization Statement

C1 does not authorize:

- Complete replay package implementation
- Real VPS package writes
- Real VPS runtime artifact reads
- Runtime capture execution
- Package creation outside tmp_path tests
- Package directories outside tmp_path tests
- Filesystem-backed package persistence outside later approved gates
- Immutable production evidence creation
- Evaluation implementation
- Attribution engine implementation
- Experiment registry implementation
- Promotion workflow
- Broker/API/TWS/Alpaca/IBKR behavior
- Strategy behavior changes
- Risk behavior changes
- Execution behavior changes
- Config changes
- Credential changes
- `.env` changes
- systemd changes
- Scheduler changes
- Deployment changes
- Paper trading approval
- Live trading approval
- Order submission
- Order cancellation
- Cleanup
- Flatten
- Sell
- Broker remediation

## Gate C Record C2: VPS Execution Authority Contract

### C2 Status

Recorded as a docs-only governance record on 2026-06-11. This is the bounded
VPS execution authority contract, recorded now that the package execution
orchestrator interface is source-controlled and the future command shape is
nameable.

C2 is **COMPLETE** as a governance contract record only. C2 does not mark
production Gate C complete, does not approve immediate VPS execution, does not
implement VPS mode, and does not open Gate D or Unit 12.

C2 did not imply that the `package_execution_orchestrator` CLI already
performed VPS package execution when this contract was first recorded. At that
point, the source-controlled command shape was nameable, but `vps` mode
deferred and refused real execution: both `execute_package_orchestration(...)`
and `main(...)` failed closed in `vps` mode. Later source-controlled CLI
behavior requires `--authorize-vps-package-write` for any explicitly
operator-authorized bounded package write; without that flag the CLI still
defers and performs no package write.

### C2 Gate Prerequisite Chain Status

- Source-reference/source-path vocabulary: **COMPLETE**
- Vocabulary boundary verifier: **COMPLETE**
- Gate A (runtime capture authority — A1 and A2): **COMPLETE**
- Gate B (package writer/persistence — B1 plus implementation): **COMPLETE**
- C1 (complete replay package authority governance record): **COMPLETE**
- Local complete package authority module: **IMPLEMENTED**
- Package execution orchestrator, terminal completion evaluator, last_run_report
  alignment checker: **IMPLEMENTED**
- C2 VPS execution authority contract: **COMPLETE** (this record, governance
  contract only)
- Gate C (complete replay package authority): **INCOMPLETE** (production
  completion not recorded; bounded VPS execution evidence does not exist)
- Gate D (evaluation prerequisite governance): **NOT STARTED**
- Unit 12: **BLOCKED** (production Gate C incomplete, Gate D not started)

### C2 Future Bounded VPS Command Shape

The current bounded VPS package-execution command shape for a future separately
authorized package write is:

```
python -m tools.replay.package_execution_orchestrator --run-id <run_id> --execution-mode vps --authorize-vps-package-write
```

The earlier unflagged command shape remains source-controlled as
`PACKAGE_EXECUTION_VPS_COMMAND_CANDIDATE` in
`tools/replay/package_execution_orchestrator.py`, but current CLI behavior
requires `--authorize-vps-package-write` for any explicitly operator-authorized
bounded package write. Without that flag, the CLI defers and performs no
package write.

Actual execution remains blocked until all of the following occur in order:

- A future eligible regular-session timer run exists.
- The operator explicitly authorizes governed package capture for one known
  `run_id`.
- The governed capture command includes `--authorize-vps-package-write`.
- All D13, run_id alignment, report alignment, no-overwrite, root/path, and
  non-authority guards pass.

### C2 Governed Roots

The exact governed roots for future VPS execution are:

- Artifact root: `/opt/openclaw-stocks`
- Package output root: `/opt/openclaw-stocks/replay_packages`
- Package directory family: `/opt/openclaw-stocks/replay_packages/{run_id}`

Approved artifact families (read-only, governed):

- `logs/{run_id}.jsonl` — canonical JSONL event log per run
- `last_run_report.json` — derived operational summary, matched to JSONL run_id

Blocked artifact:

- `order_state.json` — reads, writes, and complete-package binding remain
  fail-closed pending a later explicit binding gate.

No other artifact family may be read or bound without a later explicit gate.

### C2 Eligible-Run Selection Rule

- The `run_id` must be explicitly supplied by the operator.
- The `run_id` must correspond to `logs/{run_id}.jsonl`.
- The JSONL filename stem must match the canonical `run_id`.
- Every JSONL line carrying `run_id`/`canonical_run_id` must match the canonical
  `run_id`.
- Terminal completion status must be derived from JSONL bytes by
  `terminal_completion_evaluator`, not hand-asserted.
- Exactly one event with `event_type == "system"` and `stage == "completion"`
  must exist.
- Terminal status `ok` is eligible.
- Terminal status `blocked` is eligible, subject to existing fail-closed
  alignment guards.
- Terminal status `error` is diagnostic only and not package-eligible.
- Zero, duplicate, malformed, missing, unknown, mixed-run, stale, or ambiguous
  completion evidence fails closed.

### C2 last_run_report Alignment Rule

- `last_run_report.json` must be parsed from bytes by
  `last_run_report_alignment`.
- The report `run_id`/`canonical_run_id` must match the canonical `run_id` and
  the JSONL filename stem.
- A stale report (run_id mismatch or absent) fails closed.
- The report status must not contradict the JSONL-derived terminal status.
- A report `error` status fails closed.
- Missing optional provenance in `last_run_report.json` may be recorded as
  `not_present` metadata, but cannot be treated as production provenance unless
  separately provided by the package evidence chain.

### C2 Future VPS Execution Evidence Requirements

A future bounded VPS execution gate must produce and preserve:

- VPS repo alignment at the expected commit.
- Clean VPS tree before and after.
- venv Python validation.
- Verifier pass.
- Test suite pass.
- Package output root state before execution.
- No pre-existing package directory for the selected `run_id` unless explicitly
  handled by a no-overwrite / fail-closed policy.
- JSONL read evidence from the approved file-reader path.
- `last_run_report.json` read evidence from the approved file-reader path.
- Terminal completion evaluation result derived from JSONL bytes.
- `last_run_report` alignment result derived from bytes.
- Manifest evidence.
- Deterministic serialization evidence.
- Hash computation evidence.
- Integrity validation evidence.
- Package writer result.
- Package persistence result.
- Complete package authority result.
- Written package path.
- Written artifact sha256 digests.
- Post-write re-read hash verification.
- Finalized lifecycle status.
- No-overwrite finalization evidence.
- Immutability marker.
- Provenance.
- Redaction status.
- Explicit absent/not_applicable declarations for optional artifacts.
- No order_state binding.
- A final machine-readable execution evidence report.

### C2 Required Future Implementation Before Execution

Before a real VPS execution gate may run, a later local implementation gate
must enable the current orchestrator's `vps` mode to:

- Read `logs/{run_id}.jsonl` via
  `runtime_artifact_file_reader.read_jsonl_event_stream`.
- Read `last_run_report.json` via
  `runtime_artifact_file_reader.read_last_run_report`.
- Pin `artifact_root_path` exactly to `/opt/openclaw-stocks`.
- Pin `package_root_path` exactly to `/opt/openclaw-stocks/replay_packages`.
- Reject all non-source-controlled roots in `vps` mode.
- Write only under `/opt/openclaw-stocks/replay_packages/{run_id}`.
- Reject pre-existing finalized package directories unless a later explicit
  no-overwrite-safe policy allows otherwise.
- Produce a machine-readable evidence report.
- Continue to reject `order_state.json`.
- Continue to return `production_gate_c_complete=False` from code, because
  production Gate C completion is recorded by governance after evidence review,
  not self-declared by code.

### C2 Production Gate C Completion Rule

- Production Gate C remains **INCOMPLETE** after C2.
- Production Gate C can only be completed by a later docs-only completion record
  after bounded VPS execution evidence exists and is reviewed.
- Code must not self-declare production Gate C completion.
- `complete_package_authority.py` and `package_execution_orchestrator.py` must
  continue to keep `production_gate_c_complete=False`.

### C2 Gate D and Unit 12 Status

- Gate D remains **NOT STARTED**.
- Gate D requires production Gate C completion plus finalized immutable evidence
  plus separate evaluation prerequisite governance.
- Unit 12 remains **BLOCKED** after C2.
- No evaluation, attribution engine, experiment registry, promotion workflow,
  metric authority, broker/API behavior, strategy/risk/execution behavior,
  paper trading, or live trading is approved by C2.

### C2 Non-Authorization Statement

C2 does not authorize:

- Immediate VPS execution
- Real VPS runtime artifact reads
- Real VPS package writes
- Runtime capture execution
- order_state.json reads
- order_state.json writes
- order_state.json binding
- Source path ingestion against the real filesystem
- Arbitrary file path ingestion
- Artifact discovery outside approved families
- Package creation outside later approved gates
- Filesystem-backed package persistence outside later approved gates
- Immutable production evidence creation
- Production Gate C completion
- Gate D
- Unit 12
- Evaluation implementation
- Attribution engine implementation
- Experiment registry implementation
- Promotion workflow
- Broker/API/TWS/Alpaca/IBKR behavior
- Strategy behavior changes
- Risk behavior changes
- Execution behavior changes
- Config changes
- Credential changes
- `.env` changes
- systemd changes
- Scheduler changes
- Deployment changes
- Paper trading approval
- Live trading approval
- Order submission
- Order cancellation
- Cleanup
- Flatten
- Sell
- Broker remediation

## Gate C Completion Record: Governed VPS Replay-Package Evidence

### Completion Status

Recorded as a docs-only completion record on 2026-06-12. This record completes
the Gate C production replay-package evidence path under the completion rule
established by Gate C Record C1 and Gate C Record C2:

> Production Gate C can only be completed by a later docs-only completion record
> after bounded VPS execution evidence exists and is reviewed.

That precondition is now satisfied: bounded VPS package execution and the
subsequent package evidence review both classified PASS for a single governed
run. Accordingly, Gate C (complete replay package authority) is classified
**COMPLETE** for the production replay-package evidence path, evidenced by the
governed on-disk package recorded below.

This record is append-only governance evidence. The earlier chain-status
sections in this map (Gate A Record A2, Gate B Record B1, Gate C Record C1, and
Gate C Record C2) recorded Gate C as INCOMPLETE; those statements were accurate
when written and are retained as historical record. This completion record
supersedes that status for the production replay-package evidence path only.

### Reviewed Evidence

- `run_id`: `run_2026-06-12T13:00:11Z_68d0b9`
- Package directory (VPS runtime evidence):
  `/opt/openclaw-stocks/replay_packages/run_2026-06-12T13:00:11Z_68d0b9`
- Package artifact:
  `/opt/openclaw-stocks/replay_packages/run_2026-06-12T13:00:11Z_68d0b9/manifest.json`
- Manifest sha256:
  `9b11c013d3b4a309541cd42ab74181eb11dd1e6ae10256ec86e71df093e23358`
- JSONL source:
  `/opt/openclaw-stocks/logs/run_2026-06-12T13:00:11Z_68d0b9.jsonl`
- JSONL line count: 4
- Terminal stage: `completion`
- Terminal status: `blocked` (capture-eligible under Gate A Record A2)
- Terminal reason: `before_regular_session_open` (an approved safe
  market-session guard reason)
- `last_run_report.json` still matched the package run during evidence review:
  true
- `trading_authority`: false
- `broker_api_authority`: false
- `order_state_binding`: false
- `production_gate_c_complete` in package output: false (code never
  self-declares; completion is recorded here in governance, not by code)

### What This Completion Means

- The end-to-end governed path produced an actual on-disk complete replay
  package with a known hash, finalized no-overwrite lifecycle, an immutability
  marker, terminal-completion eligibility derived from JSONL bytes, and
  `last_run_report.json` alignment, and that package passed evidence review.
- This satisfies the Gate C Record C1 prerequisites for production Gate C
  completion for the evidenced run.

### Prerequisite Chain Status After This Record

- Gate A (runtime capture authority — A1 and A2): **COMPLETE**
- Gate B (package writer/persistence — B1 plus implementation): **COMPLETE**
- C1 (complete replay package authority governance record): **COMPLETE**
- C2 (VPS execution authority contract): **COMPLETE**
- Gate C (complete replay package authority): **COMPLETE** (production
  replay-package evidence path; this record)
- Gate D (evaluation prerequisite governance): **NOT STARTED**
- Unit 12: **BLOCKED**

### Explicit Non-Authorizations

This completion record does not approve or authorize:

- Gate D, or the opening of any evaluation prerequisite governance work
- Unit 12, evaluation, attribution engine, experiment registry, metric
  authority, or promotion workflow
- Broker activation or any broker/API authority
- Alpaca, IBKR, or TWS work
- Cleanup, flatten, sell, cancel, order submission, order cancellation, or
  broker remediation
- Strategy, risk, or execution behavior changes
- systemd, scheduler, runtime activation, `.env`, or credential changes
- Paper trading approval or live trading approval

Gate D remains NOT STARTED and additionally requires its own evaluation
prerequisite governance (metric/attribution/experiment-registry vocabulary,
package-set inclusion rules, reproducibility rules, and baseline/candidate
comparison rules) beyond Gate C completion. Unit 12 remains BLOCKED until the
Gate D chain is opened and completed.

### VPS Evidence Custody

The VPS `/opt/openclaw-stocks/replay_packages` directory and its contents are
runtime evidence that lives on the VPS. They must not be committed to Git from
the VPS or anywhere else. This completion record commits no package artifact, no
package directory, and no manifest bytes; it records only the reviewed evidence
metadata above. No replay package was created locally for this record.

## Gate D Record D1: Evaluation Prerequisite Governance Contract

### D1 Status

Recorded as a docs-only governance record on 2026-06-12. This is the evaluation
prerequisite governance contract that opens Gate D **only at the governance
level**. It is the source-controlled basis required by the
`### Gate D: Evaluation Prerequisite Governance Gate` section above and by the
`## Evaluation and Promotion Authority Contract` in
`docs/evaluation_infrastructure_architecture.md`.

D1 is **COMPLETE** as a docs-only prerequisite governance contract record only.
D1 does not start Gate D implementation, does not create any evaluation,
metric, attribution, experiment-registry, scoring, or promotion code, and does
not open Unit 12.

Gate D implementation remains **NOT STARTED**. Unit 12 remains **BLOCKED**.
This record is append-only governance evidence; it does not rewrite the prior
chain-status history recorded in the A2, B1, C1, C2, and Gate C completion
records.

### D1 Prerequisite Chain Status

- Gate A (runtime capture authority — A1 and A2): **COMPLETE**
- Gate B (package writer/persistence — B1 plus implementation): **COMPLETE**
- C1 (complete replay package authority governance record): **COMPLETE**
- C2 (VPS execution authority contract): **COMPLETE**
- Gate C (complete replay package authority — production evidence path):
  **COMPLETE**
- D1 (evaluation prerequisite governance contract): **COMPLETE** (this record,
  governance contract only)
- Gate D (evaluation prerequisite governance): **NOT STARTED**
- Unit 12: **BLOCKED**

### D1 Evidence Basis

Gate C completion produced one finalized, immutable, governed on-disk replay
package (recorded in the Gate C Completion Record). This is a **thin** immutable
evidence set:

- It is sufficient for evaluation prerequisite **governance planning** (defining
  vocabulary, versioning, and fail-closed rules), which does not consume or
  score packages.
- It is **insufficient for real scoring**: the single package is a `blocked`,
  market-closed run with no strategy decision or trade to evaluate and no
  baseline-versus-candidate pair. Authoritative evaluation execution must wait
  for a richer finalized immutable evidence set across real decision runs,
  approved by a later separate gate.

### D1 Ordered Prerequisite Chain

Gate D prerequisite governance must be source-controlled in this order; no item
may be skipped, and each is its own later lane:

1. Metric vocabulary and versioning governance.
2. Attribution vocabulary and versioning governance.
3. Experiment identifier and registry authority governance.
4. Package-set inclusion/exclusion rules.
5. Reproducibility rules.
6. Candidate strategy identity and parameter versioning.
7. Baseline-versus-candidate comparison rules.
8. As-of feature availability and decision-time evidence rules.

The first implementation lane after D1, if and when separately approved, is the
smallest unit: metric vocabulary and versioning, as a pure in-memory,
test-guarded module with no scoring, no filesystem access, and no downstream
authority. D1 does not approve that implementation.

### D1 Fail-Closed Requirements

Authoritative evaluation must fail closed for any replay package evidence that
is incomplete, mutable, stale, mixed-run, unfinalized, unhashable, hash-
mismatched, provenance-defective, redaction-defective, non-authoritative,
invalidated, or otherwise unapproved. Draft or incomplete packages may support
only exploratory, non-authoritative reports if a later gate explicitly approves
that use; they may never be treated as authoritative evaluation evidence.

### D1 Evaluation Output Non-Authority

Evaluation reports, metrics, comparisons, attributions, and recommendations:

- Do not create promotion authority and must remain separate from strategy
  promotion.
- Do not create broker authority, execution permission, paper trading approval,
  or live trading authority.
- Do not mutate runtime state and do not change strategy, risk, allocation,
  sizing, sell, trim, rebalance, hedge, short, order, broker, or execution
  behavior.

### D1 Non-Authorization Statement

D1 does not authorize:

- Gate D implementation
- Unit 12
- Evaluation, metric, attribution, experiment-registry, scoring, or comparison
  implementation
- Promotion workflow or strategy promotion
- Broker/API/TWS/Alpaca/IBKR behavior
- Strategy, risk, or execution behavior changes
- systemd, scheduler, or runtime activation changes
- `.env` or credential changes
- Cleanup, flatten, sell, cancel, order submission, order cancellation, or
  broker remediation
- Paper trading approval
- Live trading approval

## Gate D Record D2: Metric Vocabulary And Versioning Unit

### D2 Status

Recorded on 2026-06-12. This is the first Gate D implementation unit ordered by
Gate D Record D1: metric vocabulary and versioning governance. It is
**IMPLEMENTED** as a pure in-memory, test-guarded vocabulary module:
`tools/replay/metric_vocabulary.py`.

The module defines governed metric identifiers and a deterministic metric
vocabulary version (`METRIC_VOCABULARY_VERSION`), and exposes pure validation
helpers (`validate_metric_identifier_set`, `validate_metric_vocabulary_record`,
`is_known_metric_identifier`) that fail closed for unknown identifiers, missing
or unsupported versions, duplicate identifiers, malformed records, and
authority-bearing fields. It computes no scores, reads no files, reads no replay
packages, and carries no evaluation-execution, attribution, experiment-registry,
package-set, promotion, broker, strategy, risk, execution, paper-trading, or
live-trading authority.

### D2 Chain Status

- D1 (evaluation prerequisite governance contract): **COMPLETE**
- D2 (metric vocabulary + versioning unit): **IMPLEMENTED** (this record)
- Remaining Gate D prerequisite units (attribution vocabulary, experiment
  identifier/registry, package-set inclusion/exclusion, reproducibility,
  candidate identity/parameter versioning, baseline-vs-candidate comparison,
  as-of feature availability): **NOT STARTED**
- Gate D (evaluation prerequisite governance): **NOT STARTED** (implementation
  of the full prerequisite chain is incomplete; this unit is the first of eight)
- Unit 12: **BLOCKED**

D2 does not complete Gate D and does not approve evaluation execution,
attribution, experiment registry, package-set selection, reproducibility logic,
baseline-vs-candidate comparison, as-of feature logic, scoring, strategy
promotion, Unit 12, broker/API work, or any execution/paper/live trading
authority.

## Gate D Record D3: Attribution Vocabulary And Versioning Unit

### D3 Status

Recorded on 2026-06-12. This is the second Gate D implementation unit ordered by
Gate D Record D1: attribution vocabulary and versioning governance, following
the metric vocabulary unit (D2). It is **IMPLEMENTED** as a pure in-memory,
test-guarded vocabulary module: `tools/replay/attribution_vocabulary.py`.

The module defines governed attribution cause identifiers and a deterministic
attribution vocabulary version (`ATTRIBUTION_VOCABULARY_VERSION`), and exposes
pure validation helpers (`validate_attribution_identifier_set`,
`validate_attribution_vocabulary_record`, `is_known_attribution_identifier`)
that fail closed for unknown identifiers, missing or unsupported versions,
duplicate identifiers, empty sets, malformed records, and authority-bearing
fields. It performs no attribution computation, computes no scores, reads no
files, reads no replay packages, and carries no evaluation-execution,
experiment-registry, package-set, reproducibility, baseline-vs-candidate,
as-of, promotion, broker, strategy, risk, execution, paper-trading, or
live-trading authority.

### D3 Chain Status

- D1 (evaluation prerequisite governance contract): **COMPLETE**
- D2 (metric vocabulary + versioning unit): **IMPLEMENTED**
- D3 (attribution vocabulary + versioning unit): **IMPLEMENTED** (this record)
- Remaining Gate D prerequisite units (experiment identifier/registry,
  package-set inclusion/exclusion, reproducibility, candidate identity/parameter
  versioning, baseline-vs-candidate comparison, as-of feature availability):
  **NOT STARTED**
- Gate D (evaluation prerequisite governance): **NOT STARTED** (implementation
  of the full prerequisite chain is incomplete; this is the second of eight
  units)
- Unit 12: **BLOCKED**

D3 does not complete Gate D and does not approve attribution execution,
evaluation execution, experiment registry, package-set selection,
reproducibility logic, baseline-vs-candidate comparison, as-of feature logic,
scoring, strategy promotion, Unit 12, broker/API work, or any execution/paper/
live trading authority.

## Gate D Record D4: Experiment Identifier And Registry Authority Unit

### D4 Status

Recorded on 2026-06-12. This is the third Gate D implementation unit ordered by
Gate D Record D1: experiment identifier and registry authority governance,
following metric (D2) and attribution (D3) vocabulary. It is **IMPLEMENTED** as
a pure in-memory, test-guarded module: `tools/replay/experiment_registry.py`.

The module defines deterministic experiment identifier shape rules
(`EXPERIMENT_ID_PREFIX`, bounded charset, length, and traversal/order_state
rejection), a deterministic registry version and authority
(`EXPERIMENT_REGISTRY_VERSION`, `EXPERIMENT_REGISTRY_AUTHORITY`), and pure
validation helpers (`is_valid_experiment_identifier`,
`validate_experiment_identifier`, `validate_experiment_registry_record`,
`validate_experiment_registry_record_set`). It fails closed for missing or
malformed identifiers, missing or unsupported versions, missing or unknown
registry authority, unknown experiment status, missing experiment scope,
mutable registry records, missing immutability markers, duplicate experiment
identifiers, empty sets, malformed records, and authority-bearing fields. It
runs no experiments, persists no registry, computes no scores, performs no
attribution or evaluation execution, reads no files or replay packages, and
carries no package-set, reproducibility, baseline-vs-candidate, as-of,
promotion, broker, strategy, risk, execution, paper-trading, or live-trading
authority.

### D4 Chain Status

- D1 (evaluation prerequisite governance contract): **COMPLETE**
- D2 (metric vocabulary + versioning unit): **IMPLEMENTED**
- D3 (attribution vocabulary + versioning unit): **IMPLEMENTED**
- D4 (experiment identifier + registry authority unit): **IMPLEMENTED** (this
  record)
- Remaining Gate D prerequisite units (package-set inclusion/exclusion,
  reproducibility, candidate identity/parameter versioning, baseline-vs-candidate
  comparison, as-of feature availability): **NOT STARTED**
- Gate D (evaluation prerequisite governance): **NOT STARTED** (implementation
  of the full prerequisite chain is incomplete; this is the third of eight
  units)
- Unit 12: **BLOCKED**

D4 does not complete Gate D and does not approve experiment execution, registry
persistence, evaluation execution, attribution execution, package-set
selection, reproducibility logic, baseline-vs-candidate comparison, as-of
feature logic, scoring, strategy promotion, Unit 12, broker/API work, or any
execution/paper/live trading authority.

## Gate D Record D5: Package-Set Inclusion/Exclusion Rules Unit

### D5 Status

Recorded on 2026-06-12. This is the fourth Gate D implementation unit ordered by
Gate D Record D1: package-set inclusion/exclusion rules governance, following
metric (D2), attribution (D3), and experiment registry (D4). It is
**IMPLEMENTED** as a pure in-memory, test-guarded module:
`tools/replay/package_set_governance.py`.

The module defines deterministic inclusion rule identifiers, exclusion rule
identifiers, and a governed package-set version
(`PACKAGE_SET_GOVERNANCE_VERSION`), and exposes pure validators
(`is_known_inclusion_rule`, `is_known_exclusion_rule`,
`is_known_package_set_rule`, `validate_package_set_rule_record`,
`validate_package_set_governance_record`). It fails closed for missing or
unsupported versions, unknown or duplicate rule identifiers, unknown rule kinds
or rule-kind mismatches, empty inclusion or exclusion rule sets, conflicting
include/exclude declarations, empty package reference sets, missing
immutable-evidence markers, mutable-package markers, missing finalization
markers, malformed records, and authority-bearing fields. It reads no replay
packages, discovers no packages, selects no packages, touches no filesystem,
and carries no scoring, attribution-execution, experiment-execution,
evaluation-execution, reproducibility, baseline-vs-candidate, as-of, promotion,
broker, strategy, risk, execution, paper-trading, or live-trading authority.

### D5 Chain Status

- D1 (evaluation prerequisite governance contract): **COMPLETE**
- D2 (metric vocabulary + versioning unit): **IMPLEMENTED**
- D3 (attribution vocabulary + versioning unit): **IMPLEMENTED**
- D4 (experiment identifier + registry authority unit): **IMPLEMENTED**
- D5 (package-set inclusion/exclusion rules unit): **IMPLEMENTED** (this record)
- Remaining Gate D prerequisite units (reproducibility, candidate
  identity/parameter versioning, baseline-vs-candidate comparison, as-of feature
  availability): **NOT STARTED**
- Gate D (evaluation prerequisite governance): **NOT STARTED** (implementation
  of the full prerequisite chain is incomplete; this is the fourth of eight
  units)
- Unit 12: **BLOCKED**

D5 does not complete Gate D and does not approve package reading, package
discovery, package selection execution, scoring, attribution execution,
experiment execution, evaluation execution, reproducibility logic,
baseline-vs-candidate comparison, as-of feature logic, strategy promotion,
Unit 12, broker/API work, or any execution/paper/live trading authority.

## Gate D Record D6: Reproducibility Rules Unit

### D6 Status

Recorded on 2026-06-12. This is the fifth Gate D implementation unit ordered by
Gate D Record D1: reproducibility rules governance, following metric (D2),
attribution (D3), experiment registry (D4), and package-set (D5). It is
**IMPLEMENTED** as a pure in-memory, test-guarded module:
`tools/replay/reproducibility_governance.py`.

The module defines deterministic reproducibility rule identifiers (pinned commit
identity, deterministic vocabulary versions, canonical serialization,
hash-verified inputs, immutable evidence, stable ordering, environment-
independent comparison), a governed reproducibility version
(`REPRODUCIBILITY_GOVERNANCE_VERSION`), and pure validators
(`is_known_reproducibility_rule`, `validate_reproducibility_rule_record`,
`validate_reproducibility_governance_record`). It fails closed for missing or
unsupported versions, unknown or duplicate rule identifiers, empty rule sets,
malformed records, missing pinned-commit/canonical-serialization/hash-
verification/immutable-evidence/stable-ordering/environment-independent-
comparison declarations, mutable-input markers, nondeterministic-order markers,
environment-dependent markers, and authority-bearing fields. It runs no replay,
runs no evaluation, reads no packages, discovers no packages, selects no
packages, touches no filesystem, and carries no scoring, attribution-execution,
experiment-execution, baseline-vs-candidate, as-of, promotion, broker, strategy,
risk, execution, paper-trading, or live-trading authority.

### D6 Chain Status

- D1 (evaluation prerequisite governance contract): **COMPLETE**
- D2 (metric vocabulary + versioning unit): **IMPLEMENTED**
- D3 (attribution vocabulary + versioning unit): **IMPLEMENTED**
- D4 (experiment identifier + registry authority unit): **IMPLEMENTED**
- D5 (package-set inclusion/exclusion rules unit): **IMPLEMENTED**
- D6 (reproducibility rules unit): **IMPLEMENTED** (this record)
- Remaining Gate D prerequisite units (candidate identity/parameter versioning,
  baseline-vs-candidate comparison, as-of feature availability): **NOT STARTED**
- Gate D (evaluation prerequisite governance): **NOT STARTED** (implementation
  of the full prerequisite chain is incomplete; this is the fifth of eight
  units)
- Unit 12: **BLOCKED**

D6 does not complete Gate D and does not approve replay execution, evaluation
execution, package reading, package discovery, package selection execution,
scoring, attribution execution, experiment execution, baseline-vs-candidate
comparison, as-of feature logic, strategy promotion, Unit 12, broker/API work,
or any execution/paper/live trading authority.

## Gate D Record D7: Candidate Strategy Identity And Parameter Versioning Unit

### D7 Status

Recorded on 2026-06-12. This is the sixth Gate D implementation unit ordered by
Gate D Record D1: candidate strategy identity + parameter versioning
governance, following metric (D2), attribution (D3), experiment registry (D4),
package-set (D5), and reproducibility (D6). It is **IMPLEMENTED** as a pure
in-memory, test-guarded module: `tools/replay/candidate_strategy_governance.py`.

The module defines deterministic candidate strategy identity/version rules and
candidate parameter-set identity/version rules (namespaced `cand_strategy_` and
`cand_paramset_`, strictly distinct from approved production identity), a
governed version (`CANDIDATE_STRATEGY_GOVERNANCE_VERSION`), and pure validators
(`is_valid_candidate_strategy_identifier`, `is_valid_parameter_set_identifier`,
`validate_candidate_strategy_record`, `validate_parameter_set_record`,
`validate_candidate_strategy_record_set`, `validate_parameter_set_record_set`).
It fails closed for missing or unsupported versions, malformed strategy or
parameter-set identifiers, missing strategy or parameter-set versions, missing
candidate markers, production/approved/live markers, mutable parameter markers,
missing immutability declarations, duplicate identifiers, empty record sets,
malformed records, and authority-bearing fields. It carries no strategy
behavior, signal generation, risk logic, execution logic, replay or evaluation
execution, package reading, package discovery, package selection, scoring,
attribution/experiment execution, baseline-vs-candidate comparison, as-of logic,
promotion, broker, strategy/risk/execution, paper-trading, or live-trading
authority.

### D7 Chain Status

- D1 (evaluation prerequisite governance contract): **COMPLETE**
- D2 (metric vocabulary + versioning unit): **IMPLEMENTED**
- D3 (attribution vocabulary + versioning unit): **IMPLEMENTED**
- D4 (experiment identifier + registry authority unit): **IMPLEMENTED**
- D5 (package-set inclusion/exclusion rules unit): **IMPLEMENTED**
- D6 (reproducibility rules unit): **IMPLEMENTED**
- D7 (candidate strategy identity + parameter versioning unit): **IMPLEMENTED**
  (this record)
- Remaining Gate D prerequisite units (baseline-vs-candidate comparison, as-of
  feature availability): **NOT STARTED**
- Gate D (evaluation prerequisite governance): **NOT STARTED** (implementation
  of the full prerequisite chain is incomplete; this is the sixth of eight
  units)
- Unit 12: **BLOCKED**

D7 does not complete Gate D and does not approve strategy behavior, signal
generation, risk logic, execution logic, replay execution, evaluation
execution, package reading, package discovery, package selection execution,
scoring, attribution execution, experiment execution, baseline-vs-candidate
comparison, as-of feature logic, strategy promotion, Unit 12, broker/API work,
or any execution/paper/live trading authority.

## Gate D Record D8: Baseline-vs-Candidate Comparison Rules Unit

### D8 Status

Recorded on 2026-06-12. This is the seventh Gate D implementation unit ordered
by Gate D Record D1: baseline-vs-candidate comparison rules governance,
following metric (D2), attribution (D3), experiment registry (D4), package-set
(D5), reproducibility (D6), and candidate strategy (D7). It is **IMPLEMENTED**
as a pure in-memory, test-guarded module:
`tools/replay/baseline_candidate_comparison_governance.py`.

The module defines deterministic comparison rule identifiers, baseline strategy
and parameter-set identity rules (namespaced `baseline_*`, distinct from the
candidate `cand_*` namespace), candidate identity pairing rules (composed with
the Unit 6 candidate identity validators), a governed version
(`COMPARISON_GOVERNANCE_VERSION`), and pure validators
(`is_known_comparison_rule`, `is_valid_baseline_strategy_identifier`,
`is_valid_baseline_parameter_set_identifier`, `validate_comparison_rule_record`,
`validate_baseline_candidate_pairing_record`). It requires baseline records to
be baseline-marked (and not candidate-marked), candidate records to be
candidate-marked (and not production/approved/live-marked), and both to declare
matching run scope, immutable evidence, reproducibility, strategy identity and
version, and parameter-set identity and version. It fails closed for missing or
unsupported versions, unknown or duplicate rule identifiers, empty rule sets,
malformed baseline or candidate identifiers, missing baseline or candidate
markers, candidate markers on baseline records, production/approved/live markers
on candidate records, mismatched run scope, mutable evidence markers, missing
immutability or reproducibility declarations, missing strategy or parameter-set
versions, malformed records, and authority-bearing fields. It executes no
comparison, computes no scores, runs no strategy/signal/risk/execution/replay/
evaluation logic, reads/discovers/selects no packages, touches no filesystem,
and carries no attribution-execution, experiment-execution, as-of, promotion,
broker, strategy/risk/execution, paper-trading, or live-trading authority.

### D8 Chain Status

- D1 (evaluation prerequisite governance contract): **COMPLETE**
- D2 (metric vocabulary + versioning unit): **IMPLEMENTED**
- D3 (attribution vocabulary + versioning unit): **IMPLEMENTED**
- D4 (experiment identifier + registry authority unit): **IMPLEMENTED**
- D5 (package-set inclusion/exclusion rules unit): **IMPLEMENTED**
- D6 (reproducibility rules unit): **IMPLEMENTED**
- D7 (candidate strategy identity + parameter versioning unit): **IMPLEMENTED**
- D8 (baseline-vs-candidate comparison rules unit): **IMPLEMENTED** (this record)
- Remaining Gate D prerequisite unit (as-of feature availability and
  decision-time evidence rules): **NOT STARTED**
- Gate D (evaluation prerequisite governance): **NOT STARTED** (implementation
  of the full prerequisite chain is incomplete; this is the seventh of eight
  units)
- Unit 12: **BLOCKED**

D8 does not complete Gate D and does not approve comparison execution, scoring,
strategy behavior, signal generation, risk logic, execution logic, replay
execution, evaluation execution, package reading, package discovery, package
selection execution, attribution execution, experiment execution, as-of feature
logic, strategy promotion, Unit 12, broker/API work, or any execution/paper/
live trading authority.

## Gate D Record D9: As-Of Feature Availability And Decision-Time Evidence Unit

### D9 Status

Recorded on 2026-06-12. This is the eighth and final Gate D implementation unit
ordered by Gate D Record D1: as-of feature availability + decision-time evidence
rules governance, following metric (D2) through baseline-vs-candidate comparison
(D8). It is **IMPLEMENTED** as a pure in-memory, test-guarded module:
`tools/replay/asof_evidence_governance.py`.

The module defines deterministic as-of evidence, decision-time evidence, and
feature availability rule identifiers, a governed version
(`ASOF_GOVERNANCE_VERSION`), and pure validators (`is_known_asof_evidence_rule`,
`is_known_decision_time_rule`, `is_known_feature_availability_rule`,
`is_known_asof_rule`, `validate_asof_rule_record`,
`validate_asof_evidence_record`). It enforces the no-look-ahead rule —
`available_at_timestamp <= decision_timestamp` — over caller-supplied canonical
UTC ISO-8601 timestamps, and requires decision-timestamp, availability-timestamp
(and, where present, observation-timestamp) declarations, an explicit
no-look-ahead declaration, an immutable evidence marker, and a reproducibility
declaration. It fails closed for missing or unsupported versions, unknown or
duplicate rule identifiers, empty rule sets, malformed records, missing decision
or availability timestamps, malformed timestamps, evidence availability after
decision time, post-decision observation, future-dated / post-decision / leaked
/ mutable evidence markers, missing no-look-ahead / immutability /
reproducibility declarations, and authority-bearing fields. It computes no as-of
features, generates no features, executes no comparison, computes no scores,
runs no strategy/signal/risk/execution/replay/evaluation logic, reads/discovers/
selects no packages, touches no filesystem, and carries no attribution-execution,
experiment-execution, promotion, broker, strategy/risk/execution, paper-trading,
or live-trading authority.

### D9 Chain Status

- D1 (evaluation prerequisite governance contract): **COMPLETE**
- D2 (metric vocabulary + versioning unit): **IMPLEMENTED**
- D3 (attribution vocabulary + versioning unit): **IMPLEMENTED**
- D4 (experiment identifier + registry authority unit): **IMPLEMENTED**
- D5 (package-set inclusion/exclusion rules unit): **IMPLEMENTED**
- D6 (reproducibility rules unit): **IMPLEMENTED**
- D7 (candidate strategy identity + parameter versioning unit): **IMPLEMENTED**
- D8 (baseline-vs-candidate comparison rules unit): **IMPLEMENTED**
- D9 (as-of feature availability + decision-time evidence unit): **IMPLEMENTED**
  (this record; the eighth and final Gate D prerequisite-governance unit)
- Gate D (evaluation prerequisite governance): **NOT STARTED** (all eight
  prerequisite-governance units are now implemented as pure in-memory vocabulary;
  overall Gate D completion, finalized immutable evidence-set sufficiency, and
  any evaluation/scoring engine remain separate later gates and are not opened
  here)
- Unit 12: **BLOCKED**

D9 does not complete Gate D and does not approve as-of computation execution,
feature generation, comparison execution, scoring, strategy behavior, signal
generation, risk logic, execution logic, replay execution, evaluation execution,
package reading, package discovery, package selection execution, attribution
execution, experiment execution, strategy promotion, Unit 12, broker/API work,
or any execution/paper/live trading authority.

## Gate D Record D10: Prerequisite Governance Completion Record

### D10 Status

Recorded as a docs-only governance record on 2026-06-12. This record completes
the Gate D **prerequisite-governance chain** and nothing else.

The Gate D prerequisite-governance chain is **COMPLETE**: Gate D Record D1 (the
prerequisite governance contract) plus the eight ordered prerequisite-governance
units D2 through D9 cover, in order, the full D1 prerequisite-governance list.
Each unit is a pure in-memory, test-guarded vocabulary/governance module with a
deterministic version, fail-closed validators, and a no-downstream-authority
boundary.

This record is append-only governance evidence. It does not rewrite the prior
D1–D9 records, and it does not contradict them: the prior records' statement
that "Gate D (evaluation prerequisite governance): **NOT STARTED**" refers to
overall Gate D implementation and evaluation execution, which remain unopened.
D10 records only that the prerequisite-governance chain is complete.

### D10 Prerequisite Coverage

- Gate C (complete replay package authority): **COMPLETE** (see the Gate C
  Completion Record).
- At least one finalized, immutable, governed on-disk replay package exists
  (`run_2026-06-12T13:00:11Z_68d0b9`, recorded in the Gate C Completion Record).
- Metric vocabulary + versioning governance: **COMPLETE** (D2,
  `tools/replay/metric_vocabulary.py`).
- Attribution vocabulary + versioning governance: **COMPLETE** (D3,
  `tools/replay/attribution_vocabulary.py`).
- Experiment identifier + registry authority governance: **COMPLETE** (D4,
  `tools/replay/experiment_registry.py`).
- Package-set inclusion/exclusion rules governance: **COMPLETE** (D5,
  `tools/replay/package_set_governance.py`).
- Reproducibility rules governance: **COMPLETE** (D6,
  `tools/replay/reproducibility_governance.py`).
- Candidate strategy identity + parameter versioning governance: **COMPLETE**
  (D7, `tools/replay/candidate_strategy_governance.py`).
- Baseline-vs-candidate comparison rules governance: **COMPLETE** (D8,
  `tools/replay/baseline_candidate_comparison_governance.py`).
- As-of feature availability + decision-time evidence rules governance:
  **COMPLETE** (D9, `tools/replay/asof_evidence_governance.py`).

### D10 Evidence Sufficiency Is Separate

The prerequisite list requires that finalized immutable evidence *exists*, which
is met. Whether the finalized immutable evidence *set* is rich enough to support
trustworthy scoring or baseline-vs-candidate evaluation is a **separate decision
that D10 does not make and does not approve**. As recorded in D1, the current
evidence set is thin (a single `blocked`, market-closed run with no decision or
trade and no baseline-vs-candidate pair) and is insufficient for real scoring.
Evidence-set sufficiency remains a later, separately governed decision.

### D10 Chain Status

- Gate C (complete replay package authority — production evidence path):
  **COMPLETE**
- Gate D prerequisite-governance chain (D1 through D9): **COMPLETE** (this
  record)
- Gate D (evaluation prerequisite governance): **NOT STARTED** — overall Gate D
  implementation and evaluation execution remain unopened; only the
  prerequisite-governance chain is complete.
- Evidence-set sufficiency for scoring: **NOT DECIDED / NOT APPROVED**
- Unit 12: **BLOCKED**

### D10 Non-Authorization Statement

D10 does not authorize:

- Evaluation or scoring execution
- Evidence-sufficiency approval for scoring
- Unit 12
- Promotion authority or strategy promotion
- Broker/API/TWS/Alpaca/IBKR authority
- Strategy, risk, or execution behavior changes (production behavior is
  unchanged)
- Attribution, experiment, comparison, or as-of computation execution
- Package reading, package discovery, or package selection execution
- systemd, scheduler, runtime activation, `.env`, or credential changes
- Cleanup, flatten, sell, cancel, order submission, order cancellation, or
  broker remediation
- Paper trading approval or live trading approval

Unit 12 remains BLOCKED until, at minimum, an evidence-set sufficiency decision
and a separately governed evaluation-execution gate are recorded. No such gate
is opened here.

## Gate D Record D11: Evidence-Set Sufficiency Decision

### D11 Status

Recorded as a docs-only governance record on 2026-06-12. This record makes the
evidence-set sufficiency decision that Gate D Record D10 explicitly deferred. It
decides nothing else.

Finalized immutable governed replay-package evidence **exists**, but the current
evidence set is **INSUFFICIENT** for trustworthy baseline-vs-candidate
evaluation/scoring. This decision is consistent with the thin-evidence note in
Gate D Record D1 and the deferral in Gate D Record D10. It is append-only and
does not rewrite the prior D1–D10 records.

### D11 Current Evidence Set

- The current set consists of **one thin governed package** from `run_id`
  `run_2026-06-12T13:00:11Z_68d0b9`, recorded in the Gate C Completion Record.
- That package is **market-closed**: terminal reason `before_regular_session_open`,
  terminal status `blocked` — a pre-regular-session run with no strategy decision
  and no trade.
- The current set **lacks multiple finalized immutable packages** (only one
  exists).
- The current set **lacks regular-session decision opportunities** (the lone run
  is market-closed before the regular session opens).
- The current set **lacks meaningful decision diversity** (no BUY/HOLD/SELL or
  substantive blocked-reason variety; a single blocked, market-closed run).
- The current set **lacks a baseline package**.
- The current set **lacks a candidate package**.
- The current set **lacks a baseline-vs-candidate pair** (a comparison cannot be
  formed).

### D11 Decision

- Evidence sufficiency for scoring: **NOT MET**.
- Evaluation/scoring execution: **BLOCKED**.
- Unit 12: **BLOCKED**.
- Promotion authority: **UNAPPROVED**.
- Broker/API/Alpaca/IBKR/TWS authority: **UNAPPROVED**.
- Strategy/risk/execution behavior: **UNCHANGED** (no production behavior change).
- Paper trading and live trading: **UNAPPROVED**.

### D11 Minimum Sufficiency Criteria

Before any evaluation/scoring lane may open, the finalized immutable governed
evidence set must satisfy, at minimum:

- Multiple finalized immutable governed packages (not a single thin package).
- Regular-session decision opportunities (not only market-closed blocked runs).
- Meaningful decision diversity where applicable (BUY/HOLD/SELL or substantive
  blocked-reason variety).
- Baseline and candidate package pairing compatibility (a baseline-marked and a
  candidate-marked package with matching run scope, per Unit 7 governance).
- Package-set inclusion/exclusion compatibility (finalized-immutable,
  run_id-aligned, hash-verified, terminal-completion-eligible; excluding
  draft/incomplete, mutable, stale, mixed-run-id, unhashable/hash-mismatch,
  invalidated, and error-terminal packages, per Unit 4 governance).
- Reproducibility declarations (pinned commit, canonical serialization,
  hash-verified inputs, immutable evidence, stable ordering,
  environment-independent comparison, per Unit 5 governance).
- As-of decision-time compliance (`available_at_timestamp <= decision_timestamp`;
  no future-dated, post-decision, or leaked evidence, per Unit 8 governance).
- Deterministic metric and attribution vocabulary compatibility (per Unit 1 and
  Unit 2 governance).
- No package mutation, no hash mismatch, no mixed `run_id`, and no future or
  leaked evidence.

### D11 Recommended Next Lane

The next later lane is an **evidence-expansion / additional governed package
capture plan** — capturing multiple finalized immutable governed packages over
real regular-session decision runs through the existing bounded VPS
package-execution path until the minimum sufficiency criteria are met. That lane
is a planned operational evidence lane and is **not** evaluation execution: it
does not score, evaluate, compare, promote, or open Unit 12.

### D11 Non-Authorization Statement

D11 does not authorize evaluation or scoring execution, evidence capture
execution, package creation, Unit 12, promotion authority, broker/API/TWS/Alpaca/
IBKR authority, strategy/risk/execution behavior changes, attribution/experiment/
comparison/as-of computation execution, package reading/discovery/selection,
systemd/scheduler/runtime-activation/`.env`/credential changes, cleanup, flatten,
sell, cancel, order submission, order cancellation, broker remediation, paper
trading approval, or live trading approval. Unit 12 remains BLOCKED until the
minimum sufficiency criteria are met and a separately governed evaluation-execution
gate is recorded; no such gate is opened here.

## Gate D Record D12: Evidence-Expansion / Governed Package Capture Plan

### D12 Status

Recorded as a docs-only governance record on 2026-06-12. This record source-
controls the evidence-expansion / governed package capture plan that follows the
Gate D Record D11 sufficiency decision. It plans capture targets only; it
captures nothing, scores nothing, and approves no execution.

- Current evidence remains **INSUFFICIENT** for trustworthy baseline-vs-candidate
  scoring (per D11).
- The D11 minimum sufficiency criteria remain **controlling**; D12 operationalizes
  them as capture targets and does not relax them.
- The immediate next objective is **evidence expansion, not evaluation
  execution**.
- Production baseline package capture alone **cannot satisfy full
  baseline-vs-candidate sufficiency**.
- A **separate governed candidate-evidence mechanism is required** before a
  baseline-vs-candidate pair can exist; that mechanism does not yet exist and is
  a distinct future gate beyond package capture (and is not evaluation
  execution).
- Unit 12 remains **BLOCKED**.
- Evaluation/scoring execution remains **BLOCKED**.
- Promotion authority remains **UNAPPROVED**.
- Broker/API/Alpaca/IBKR/TWS authority remains **UNAPPROVED**.
- Strategy/risk/execution behavior remains **UNCHANGED** (no production behavior
  change).
- Paper trading and live trading remain **UNAPPROVED**.

### D12 Minimum Package-Capture Expansion Targets

- At least **8 to 12** finalized immutable governed baseline packages before any
  sufficiency re-assessment.
- Regular-session coverage over **at least 3 distinct trading days**.
- **Market-closed-only packages do not count** toward the scoring sufficiency
  count (they may be retained as evidence but are excluded from the count).
- **Decision diversity** across available production outcomes where applicable
  (for example `ok` submitted/dry-run and `blocked` runs with distinct reasons
  such as duplicate, risk, or reconciliation).
- A **package inventory** recording, for each package: `run_id`, `sha256`,
  session class, terminal status, terminal reason, decision outcome,
  reproducibility declaration, as-of declaration, and integrity attestation.

### D12 Per-Package Inclusion Requirements

Every package counted toward sufficiency must be:

- A finalized immutable package.
- run_id-aligned (JSONL filename stem equals the canonical run_id; every JSONL
  line `run_id` matches).
- Hash-verified (known sha256; written-byte hash matches).
- Terminal-completion eligible (exactly one `event_type == "system"` /
  `stage == "completion"` event; status `ok` or `blocked` per Gate A Record A2).
- Free of any order_state binding.
- Reproducibility-declaration compatible with Unit 5
  (`tools/replay/reproducibility_governance.py`).
- As-of decision-time compliant with Unit 8
  (`tools/replay/asof_evidence_governance.py`):
  `available_at_timestamp <= decision_timestamp`.
- Metric and attribution vocabulary compatible with Unit 1
  (`tools/replay/metric_vocabulary.py`) and Unit 2
  (`tools/replay/attribution_vocabulary.py`).

### D12 Exclusion Rules

The following packages are excluded from scoring sufficiency:

- Market-closed-only packages (do not count toward scoring sufficiency).
- Draft or incomplete packages.
- Mutable packages.
- Stale packages.
- Mixed-run-id packages.
- Unhashable or hash-mismatch packages.
- Invalidated packages.
- Error-terminal packages.
- Future-dated, leaked, or post-decision evidence.

### D12 Required Pre-Reassessment Artifacts

Before evidence sufficiency may be re-assessed, the following must exist as
source-controlled records:

- A package inventory table (or equivalent source-controlled record).
- A baseline package membership declaration.
- A candidate-evidence mechanism decision (recording how candidate packages
  will be governed and produced, since production capture cannot produce them).
- At least one future baseline-vs-candidate pairing declaration before any
  scoring lane may open (per Unit 7,
  `tools/replay/baseline_candidate_comparison_governance.py`).
- Integrity attestations (no mutation, no hash mismatch, no mixed run_id, no
  future/leaked evidence).
- A fresh evidence-sufficiency re-assessment against the D11 criteria.

### D12 Non-Authorization Statement

D12 does not authorize evaluation or scoring execution, evidence capture
execution, package creation, Unit 12, promotion authority, broker/API/TWS/Alpaca/
IBKR authority, strategy/risk/execution behavior changes, attribution/experiment/
comparison/as-of computation execution, package reading/discovery/selection,
systemd/scheduler/runtime-activation/`.env`/credential changes, cleanup, flatten,
sell, cancel, order submission, order cancellation, broker remediation, paper
trading approval, or live trading approval. The bounded VPS package-capture
execution gate(s) and the separate governed candidate-evidence mechanism are
distinct future gates; none is opened here. Unit 12 remains BLOCKED.

## Gate D Record D13: Market-Session Package-Capture Eligibility Guard

### D13 Status

Recorded on 2026-06-12. This is the implementation record for the deterministic
market-session package-capture eligibility guard identified by the D13 read-only
audit (which classified the prior capture path as PARTIAL_GUARD). It converts the
Gate D Record D12 market-session sufficiency rule into a fail-closed, capture-time
guard. It is **IMPLEMENTED** as a pure in-memory, test-guarded module:
`tools/replay/capture_eligibility_guard.py`, wired into the VPS package-capture
path before any package write.

### D13 Guard Behavior

`evaluate_capture_market_eligibility(...)` inspects already-read JSONL bytes and
already-read last_run_report bytes and fails closed for:

- Market/session-ineligible reasons on the terminal event (`payload.reason` or
  top-level `reason`) or on the last_run_report reason:
  `market_holiday_or_closed_day`, `before_regular_session_open`,
  `after_regular_session_close`, `market_closed` / `market-closed`, and any
  market/session reason token.
- A `blocked` terminal status with a missing reason.
- A `blocked` terminal status with an ambiguous / unknown reason (not on the
  explicit non-market eligible allowlist).
- Malformed JSONL or report bytes, or a non-isolated terminal completion event.

A `blocked` terminal status with an explicit non-market eligible reason (for
example `killswitch_disabled`, `duplicate`, `projected_exposure_exceeds_max_position_size`,
`manual_review_required`) is eligible. A non-`blocked` (e.g. `ok`) terminal
status is eligible. The non-market eligible allowlist is conservative and
extensible: an incomplete allowlist over-rejects (safe) and never over-accepts.

### D13 Wiring

The guard runs inside `package_execution_orchestrator._execute_chain` for the
VPS capture path only (`enforce_market_eligibility=True`), after the
terminal-completion, run_id-alignment, and last_run_report-alignment checks and
**before** `_assemble_governed_evidence` and any package write/finalization. The
local `tmp_path_test` mechanics harness does not enforce the market guard
(`enforce_market_eligibility=False`).

### D13 Preserved Protections

The guard does not weaken existing protections: missing run_id, mixed run_id,
error terminal status, report alignment, order_state binding rejection,
no-overwrite finalization, and the explicit `--authorize-vps-package-write`
requirement all remain in force.

### D13 Status Carry-Forward

- Package capture now fails closed for market-closed / holiday / before-open /
  after-close blocked runs (the current `run_2026-06-13T...` market-closed runs
  are not capture-eligible).
- Evaluation/scoring execution: **BLOCKED**.
- Unit 12: **BLOCKED**.
- Promotion authority: **UNAPPROVED**.
- Broker/API/Alpaca/IBKR/TWS authority: **UNAPPROVED**.
- Strategy/risk/execution behavior: **UNCHANGED**.
- Paper trading and live trading: **UNAPPROVED**.

D13 does not authorize package capture execution, evaluation/scoring execution,
Unit 12, promotion, broker/execution, strategy/risk/execution behavior changes,
paper trading, or live trading.

## Gate D Record D14: Package Inventory / Capture Ledger Schema

### D14 Status

Recorded on 2026-06-13. This is the implementation record for the deterministic
package inventory / capture ledger schema required by Gate D Record D12 before
any future evidence-sufficiency reassessment. It is **IMPLEMENTED** as a pure
in-memory, test-guarded schema/validation module:
`tools/replay/package_capture_ledger.py`.

At implementation time, D14 created no package inventory entries and read no
replay package artifacts. It defined the source-controlled schema for future
governed records only.

### D14 Ledger Fields

Every future package capture ledger record must carry, at minimum:

- `run_id`
- `package_sha256`
- `package_path_or_relative_reference`
- `capture_timestamp_utc`
- `source_commit`
- `session_class`
- `terminal_status`
- `terminal_reason`
- `decision_outcome`
- `evidence_membership` (`baseline`, `candidate`, `excluded`, or `unknown`)
- `strategy_id`
- `parameter_version`
- `reproducibility_declaration_status`
- `asof_declaration_status`
- `integrity_attestation_status`
- `inclusion_status`
- `exclusion_reason` if excluded
- `notes`

The validation schema also requires control metadata proving finalized immutable
package status, run_id alignment, hash verification, complete package authority,
non-draft / non-mutable / non-stale state, no mixed `run_id`, no hash mismatch,
and no future-dated, leaked, or post-decision evidence.

### D14 Validation Rules

`validate_package_capture_ledger_record(...)` validates already-loaded metadata
only and fails closed when:

- The ledger schema version is missing or unsupported.
- Any required ledger field is missing.
- `run_id`, `package_sha256`, package reference, capture timestamp, or source
  commit is malformed.
- `session_class`, `terminal_status`, `decision_outcome`,
  `evidence_membership`, declaration status, integrity status, or inclusion
  status is unknown.
- The package is not finalized and immutable.
- The package is draft, incomplete, mutable, stale, mixed-run-id, hash-mismatch,
  or error-terminal evidence.
- The package has future-dated, leaked, or post-decision evidence.
- Reproducibility, as-of, or integrity declarations are missing.
- A market/session-ineligible package is not marked excluded.
- A non-regular-session package attempts to count toward sufficiency.
- An excluded record lacks an exclusion reason.
- Any authority-bearing field is present.

### D14 D12/D13 Preservation

- Market-closed-only packages do not count toward scoring sufficiency.
- Market/session-ineligible packages are excluded from sufficiency counts.
- Finalized immutable packages only may validate.
- Hash mismatch, mixed `run_id`, stale, mutable, draft, incomplete, and
  error-terminal packages fail closed.
- Future-dated, leaked, or post-decision evidence fails closed.
- D13 remains complete and unchanged; D14 does not reopen or weaken the
  capture-time eligibility guard.

### D14 Non-Authorization Statement

D14 does not authorize package capture execution, package artifact reads,
package discovery, package selection, ledger persistence/writes, evaluation or
scoring execution, Unit 12, promotion authority, broker/API/TWS/Alpaca/IBKR
authority, strategy/risk/execution behavior changes, attribution/experiment/
comparison/as-of computation execution, systemd/scheduler/runtime activation,
`.env`/credential changes, order submission, cancellation, cleanup, paper
trading approval, or live trading approval.

- Package capture remains time-gated until an eligible regular-session
  production run exists and passes D13.
- Evaluation/scoring execution: **BLOCKED**.
- Unit 12: **BLOCKED**.
- Promotion authority: **UNAPPROVED**.
- Broker/API/Alpaca/IBKR/TWS authority: **UNAPPROVED**.
- Strategy/risk/execution behavior: **UNCHANGED**.
- Paper trading and live trading: **UNAPPROVED**.

## Gate D Record D14.1: Governed Package Capture Ledger Entry

Recorded on 2026-06-16 from operator-provided completed capture facts after the
single governed package capture authorized for the 13:30 UTC regular-session
workflow. This record is source-controlled ledger documentation only. It does
not read package artifacts, execute capture, replay, score, generate
candidates, open Unit 12, call broker APIs, mutate systemd, change strategy,
change risk, change config, change credentials, authorize a second capture, or
grant trading authority.

### D14.1 Ledger Entry

- Source-of-truth commit: `32100dab999a45e5e74d8ff3dc1cb1c7a7ac21e1`
- `run_id`: `run_2026-06-16T13:30:14Z_2641ee`
- Symbol: `MSTR`
- Package path:
  `/opt/openclaw-stocks/replay_packages/run_2026-06-16T13:30:14Z_2641ee`
- Manifest sha256:
  `be49b89fd1434e5d8b891b0b3ce878004fec92eac7b576a1e5846870c19998d9`
- Capture classification:
  `ONE_GOVERNED_PACKAGE_CAPTURED_PENDING_D14_LEDGER_FOLLOW_UP`
- Evidence membership: `baseline`
- Session class: `regular_session`
- Inclusion status: `recorded_pending_later_sufficiency_review`
- Trading authority: `false`
- Broker/API authority: `false`
- Gate D authority: `false`
- Replay/scoring/candidate generation: `not_performed`
- Second capture authorization: `not_authorized`

### D14.1 Status Carry-Forward

This entry records one completed governed package capture in the D14 ledger
track, but it does not complete Gate D, does not make D11 sufficient, does not
open Unit 12, and does not authorize evaluation/scoring, candidate generation,
broker/API expansion, paper escalation, live trading, or a second capture.

### D14.1 Read-Only Package Artifact Audit

Recorded on 2026-06-16 from operator-provided read-only package artifact audit
facts. This documentation records the audit result only; it does not perform
package artifact reads, replay, scoring, candidate generation, broker/API work,
systemd mutation, runtime start/restart, package capture, strategy/risk/config
changes, credential changes, Unit 12 opening, trading authorization, or a second
package capture.

- Audit classification: `D14_READ_ONLY_PACKAGE_ARTIFACT_AUDIT_PASS`
- Audit timestamp UTC: `2026-06-16T14:19:04Z`
- VPS service state: `openclaw.service inactive`
- Commit audited: `79a86d6e4a71a4b7855318fe59a69561024ae0bb`
- `run_id`: `run_2026-06-16T13:30:14Z_2641ee`
- Package manifest:
  `/opt/openclaw-stocks/replay_packages/run_2026-06-16T13:30:14Z_2641ee/manifest.json`
- Manifest sha256:
  `be49b89fd1434e5d8b891b0b3ce878004fec92eac7b576a1e5846870c19998d9`
- Manifest JSON validation: `PASS`
- Replay performed: `false`
- Scoring performed: `false`
- Candidate generation performed: `false`
- Broker/API work performed: `false`
- Systemd mutation performed: `false`
- Runtime start/restart performed: `false`
- Strategy/risk/config changes performed: `false`
- Second package capture authorized: `false`
- Gate D remains **NOT COMPLETE**.

## Gate D Record D11.1: Post-D14.1 Evidence-Sufficiency Reconciliation

Recorded on 2026-06-16 after the D14.1 governed package capture ledger entry,
D14.1 read-only artifact audit, settle-classifier fix, and source-controlled
sync at commit `9a8b8616863c01ee2890005bc0ba63cc5e9e723b`. This is a
docs-only / read-only evidence-sufficiency reconciliation. It performs no
package reads, package mutation, capture, replay, scoring, candidate
generation, Unit 12 opening, broker/API work, systemd mutation, runtime
start/restart, strategy/risk/config change, credential change, paper/live
escalation, or second capture.

### D11.1 Current Gate D Status

- Gate D remains **NOT COMPLETE → PARKED**.
- Evaluation/scoring execution remains **BLOCKED**.
- Unit 12 remains **BLOCKED**.
- Promotion authority remains **UNAPPROVED**.
- Broker/API/Alpaca/IBKR/TWS authority remains **UNAPPROVED**.
- Strategy/risk/execution behavior remains **UNCHANGED**.
- Paper trading and live trading remain **UNAPPROVED**.

### D11.1 D14.1 Evidence Inventory Update

D14.1 records one governed regular-session baseline package and a read-only
artifact audit pass. This improves the baseline evidence inventory because the
package is a governed regular-session package rather than a market-closed-only
observation, but it does not by itself create evidence sufficiency.

Current source-controlled evidence inventory after D14.1:

- Baseline package: `run_2026-06-16T13:30:14Z_2641ee`
- Symbol: `MSTR`
- Manifest sha256:
  `be49b89fd1434e5d8b891b0b3ce878004fec92eac7b576a1e5846870c19998d9`
- Evidence membership: `baseline`
- Session class: `regular_session`
- Read-only artifact audit: `D14_READ_ONLY_PACKAGE_ARTIFACT_AUDIT_PASS`
- Candidate package inventory added: `false`
- Replay/scoring/candidate generation performed: `false`

### D11.1 Sufficiency Reconciliation Decision

D11 remains **INSUFFICIENT**. D14.1 improves the evidence inventory, but the
Gate D Record D11 minimum sufficiency criteria are still not met:

- The evidence inventory has one governed regular-session baseline package, not
  multiple finalized immutable governed packages.
- The evidence inventory does not provide regular-session package coverage over
  multiple distinct trading days.
- The evidence inventory does not yet establish meaningful decision diversity
  sufficient for a baseline-vs-candidate evaluation lane.
- No candidate-side package evidence has been added.
- No baseline-vs-candidate pair can be formed.
- No scoring/evaluation authority exists.

Therefore, evidence sufficiency for scoring remains **NOT MET**; D11 remains
**INSUFFICIENT** and controlling; Gate D remains **NOT COMPLETE → PARKED**; and
Unit 12 remains **BLOCKED**.

### D11.1 Next Valid Checkpoint

No exact next numbered checkpoint is opened by this reconciliation. The next
required checkpoint is a future separately authorized **D11 sufficiency evidence
expansion / package inventory planning step**, aligned with Gate D Record D12.
That checkpoint may plan additional governed baseline package inventory and the
separate candidate-evidence mechanism needed before a baseline-vs-candidate pair
can exist. It must not authorize execution.

### D11.1 Prohibited Actions

This reconciliation authorizes none of the following: replay, scoring,
candidate generation, Unit 12 opening, broker/API expansion, paper/live
escalation, second package capture, systemd mutation, runtime start/restart,
strategy/risk/config changes, credential changes, package mutation, order
submission, order cancellation, cleanup, flatten, sell, or broker remediation.

## Gate D Record D11.2: Sufficiency Evidence Expansion / Package Inventory Plan

Recorded on 2026-06-16 after D11.1 identified the next required checkpoint as a
future separately authorized sufficiency evidence expansion / package inventory
planning step. This is a documentation/planning record only. It performs no
package reads, package mutation, package capture, replay, scoring, candidate
generation, Unit 12 opening, broker/API work, systemd mutation, runtime
start/restart, strategy/risk/config change, credential change, paper/live
escalation, or second capture.

### D11.2 Remaining Sufficiency Requirements

D11 remains **INSUFFICIENT**. Before sufficiency can be reconsidered, the
evidence inventory must satisfy the existing D11/D12 terminology and criteria:

- Multiple finalized immutable governed packages, not one package.
- Regular-session package coverage over multiple distinct trading days.
- Decision diversity where applicable, including production outcomes such as
  hold/no-order, buy/submit or dry-run equivalents, and substantive blocked
  reasons such as risk or reconciliation.
- Baseline package membership declarations for counted production packages.
- Candidate-side package evidence governed by a separately approved
  candidate-evidence mechanism.
- Baseline-vs-candidate pairing compatibility before any scoring lane may open.
- Package inventory records carrying run_id, sha256, session class, terminal
  status, terminal reason, decision outcome, reproducibility declaration,
  as-of declaration, and integrity attestation.
- Integrity attestations proving no mutation, no hash mismatch, no mixed
  `run_id`, no future/leaked/post-decision evidence, and no order_state binding.

### D11.2 Existing D14.1 Package Placement

The D14.1 MSTR package fits the inventory as one governed regular-session
baseline package:

- `run_id`: `run_2026-06-16T13:30:14Z_2641ee`
- Symbol: `MSTR`
- Manifest sha256:
  `be49b89fd1434e5d8b891b0b3ce878004fec92eac7b576a1e5846870c19998d9`
- Evidence membership: `baseline`
- Session class: `regular_session`
- Artifact audit: `D14_READ_ONLY_PACKAGE_ARTIFACT_AUDIT_PASS`

This package improves the baseline inventory, but one baseline package is
insufficient because D11 requires multiple finalized immutable packages,
multi-day coverage, decision diversity, candidate-side evidence, and
baseline-vs-candidate pairing compatibility. It does not create scoring,
evaluation, Unit 12, broker/API, paper/live, or second-capture authority.

### D11.2 Future Inventory Shape

Future sufficiency planning should target, before any later reassessment:

- Multi-day baseline packages.
- Multiple symbols where available under the existing scheduled runtime.
- Multiple decision types and substantive blocked reasons.
- Candidate-side packages produced only after a separate governed candidate
  mechanism is approved.
- Baseline-vs-candidate paired packages or pairing declarations compatible with
  existing baseline-vs-candidate comparison governance.

The current latest-symbol `last_run_report.json` alignment rule limits
multi-symbol package capture because the derived report can align to only one
latest symbol-level run_id at a time. A future design checkpoint is therefore
needed before broadening capture beyond the currently report-aligned run: it
should address per-symbol report preservation, report-alignment evidence, or
package eligibility broadening without weakening D13, run_id alignment,
no-overwrite, report-alignment, and no-order_state-binding protections.

### D11.2 Next Valid Checkpoint

The next valid checkpoint is a future separately authorized **package inventory
expansion design step**. It is docs/design work unless a later explicit gate
authorizes code/test implementation. It should define how additional baseline
packages and any future candidate-side packages can be recorded without
opening execution authority. It must not authorize package capture, replay,
scoring, candidate generation, Unit 12, broker/API expansion, paper/live
escalation, systemd mutation, runtime start/restart, strategy/risk/config
changes, credential changes, package mutation, or a second capture.

### D11.2 Prohibited Actions

Until a future explicit gate says otherwise, the following remain prohibited:
replay, scoring, candidate generation, Unit 12 opening, broker/API expansion,
paper/live escalation, second package capture, systemd mutation, runtime
start/restart, strategy/risk/config changes, credential changes, package
mutation, package artifact mutation, order submission, order cancellation,
cleanup, flatten, sell, and broker remediation.

### D11.4 Per-Run Report Preservation Implementation

D11.4 implements the package-inventory expansion design selected in D11.3:
preserve one exact per-run report artifact while keeping
`last_run_report.json` as the latest pointer. Runtime report persistence now
writes:

- `last_run_report.json` as the latest derived operational summary.
- `run_reports/{run_id}.json` as the run-addressable report for that exact
  symbol-level run.

Package discovery and capture continue to require report alignment. They now
prefer `run_reports/{run_id}.json` when present and fall back to
`last_run_report.json` only when the exact per-run report is absent. JSONL-only
evidence remains insufficient for capture readiness. Stale, mismatched,
missing, mixed-run, D13-rejected, pre-existing-package, and unsafe-run_id cases
remain fail-closed.

D11.4 is an evidence-preservation and package-readiness implementation only. It
does not complete D11, does not complete Gate D, does not authorize package
capture, does not authorize replay/scoring/candidate generation, and does not
open Unit 12. D11 remains **INSUFFICIENT** until later evidence expansion proves
the D11 sufficiency criteria with multiple governed packages, multi-day
coverage, candidate-side evidence, and baseline-vs-candidate pairing
compatibility.

The next valid checkpoint remains a separately authorized D11 evidence
inventory expansion step. That checkpoint may use the D11.4 per-run reports to
plan or evaluate additional governed baseline package eligibility, but it must
not perform capture, replay, scoring, candidate generation, Unit 12 opening,
broker/API expansion, systemd mutation, runtime start/restart, strategy/risk
changes, config changes, credential changes, package mutation, or a second
capture unless a later gate explicitly authorizes the specific action.

### D11.5 Per-Run Report Artifact Verification Pass

D11.5 read-only per-run report artifact verification passed after D11.4
implementation and D11.6 runtime artifact Git hygiene. The VPS was aligned to
source-of-truth commit `9b722d808d37c7e578b83260fa79f660e8ad49b9`; GitHub
remote matched the same commit; the VPS worktree was clean; and
`openclaw.service` was inactive.

D11.4 per-run report preservation is operationally observed from natural
systemd timer output. The 2026-06-16 20:15 UTC natural timer cycle produced
valid per-run reports aligned to each symbol-level `run_id`:

- AAPL: `run_2026-06-16T20:15:01Z_23cbad`
- MSFT: `run_2026-06-16T20:15:04Z_35fd8d`
- NVDA: `run_2026-06-16T20:15:06Z_323fd2`
- TSLA: `run_2026-06-16T20:15:08Z_4b3d81`
- MSTR: `run_2026-06-16T20:15:09Z_c74412`

Each `run_reports/{run_id}.json` artifact was present, valid JSON, and aligned
to its `run_id`. `last_run_report.json` remained the latest pointer and aligned
to `run_2026-06-16T20:15:09Z_c74412` / MSTR. D11.6 hygiene was effective:
ignoring `run_reports/` preserved a clean Git worktree during verification.

Final verification classification:
`D11_5_PER_RUN_REPORT_ARTIFACT_VERIFICATION_PASS`.

D11.5 records read-only artifact verification only. It does not complete D11,
does not complete Gate D, does not authorize package capture, replay, scoring,
candidate generation, package mutation, broker/API expansion, trading,
systemd mutation, runtime start/restart, or Unit 12 opening. D11 remains
**INSUFFICIENT** and Unit 12 remains **BLOCKED**. The next valid checkpoint
must remain separately authorized.

### D11.6 Runtime Artifact Git Hygiene Record

D11.4 per-run report artifact production was observed on the VPS after sync to
commit `4548ef0bf6a99b8f311d5861b5e9aeb4f275b2b5`. Natural timer execution
created `run_reports/{run_id}.json` artifacts as intended, but D11.5 read-only
verification was blocked because those generated runtime artifacts appeared as
untracked files and made the worktree dirty.

`run_reports/` artifacts are runtime-generated evidence artifacts. They are not
source files and should not be committed. Source-controlled Git hygiene now
ignores `run_reports/` alongside other runtime state and evidence outputs such
as `last_run_report.json`, `logs/`, and `replay_packages/`.

D11.6 records hygiene only. It does not complete D11, does not complete Gate D,
does not authorize package capture, replay, scoring, candidate generation,
package mutation, broker/API expansion, systemd mutation, runtime
start/restart, or Unit 12 opening. D11 remains **INSUFFICIENT** and Unit 12
remains **BLOCKED**.

### D11.7 Package Inventory Audit Tooling

D11.7 adds a narrow local package inventory audit tool:
`tools/replay/d11_inventory_audit.py`. The tool evaluates already-loaded D14
package capture ledger metadata against the documented D11/D12 sufficiency
criteria. It does not read replay package directories, discover packages,
capture packages, replay, score, generate candidates, call broker/API services,
touch runtime state, mutate artifacts, or open Unit 12.

The audit classifies inventory against:

- finalized immutable governed baseline package count;
- regular-session trading-day coverage;
- symbol coverage where `symbol` metadata is present;
- decision/outcome diversity;
- D14-compliant ledger validation via `package_capture_ledger`;
- integrity, hash, reproducibility, as-of, no-mutation, and no-mixed-run
  attestations carried by D14 records;
- candidate-side package inventory presence;
- baseline-vs-candidate pairing readiness.

JSONL-only evidence remains insufficient. `run_reports/{run_id}.json` remains
per-run report evidence, not governed package inventory by itself. The audit
reports `D11_INSUFFICIENT` unless the documented criteria are met, and even a
criteria-met result is only
`D11_CRITERIA_MET_PENDING_SEPARATE_GOVERNANCE_REASSESSMENT`; it does not open
evaluation/scoring or Unit 12.

Local metadata-only usage:

```bash
python -m tools.replay.d11_inventory_audit < package_inventory_metadata.json
```

The input JSON must be an object with `ledger_records` containing already-loaded
D14 package capture ledger records and optional `pairing_records` containing
`baseline_run_id` / `candidate_run_id` metadata. The command reads metadata from
stdin only and must not be pointed at replay package directories.

D11.7 records tooling only. It does not complete D11, does not complete Gate D,
does not authorize package capture, replay, scoring, candidate generation,
package mutation, broker/API expansion, systemd mutation, runtime
start/restart, strategy/risk/config changes, credential changes, or Unit 12
opening. D11 remains **INSUFFICIENT** and Unit 12 remains **BLOCKED** until a
future separately authorized sufficiency reassessment records otherwise.

### D11.8 Package Market-Data Quality Classification

D11.8 extends `tools/replay/d11_inventory_audit.py` with a metadata-only
market-data quality layer. D14 package ledger validation remains structural:
manifest/hash/finalized/immutable/run-alignment/as-of/integrity checks are not
weakened or replaced. D11 counting now also requires market-data validity, so a
package can be structurally valid while not being clean D11 evidence.

The inventory audit reports each structurally valid record with:

- `run_id`;
- `symbol`;
- `structural_validity`;
- `market_data_validity`;
- `inventory_classification`;
- `d11_countable`;
- `quarantine_reason` or `caveat_reason`;
- `latest_candle_timestamp`;
- `run_timestamp`;
- `data_warnings`.

Inventory classifications are:

- `clean`: market data from the relevant U.S. equity regular session, no
  market-input warnings, and the latest candle timestamp is within the
  source-controlled freshness threshold;
- `recency_caveated`: market data from the relevant U.S. equity regular session
  with no warnings, but latest-candle lag exceeds the freshness threshold or the
  diagnostic ran after regular-session close;
- `quarantined`: stale prior-session candles, future-session candles,
  missing/malformed market timestamps, non-regular-session candles, or any
  `market_input_captured`/market-data warnings.

Only `clean` records count toward D11 sufficiency. `recency_caveated` records
may be listed for review but must not silently count as clean evidence.
`quarantined` records do not count. JSONL-only evidence remains insufficient,
and `run_reports/{run_id}.json` remains report evidence rather than governed
package inventory by itself.

The current D11.8 freshness threshold is 30 minutes from `run_timestamp` to
`latest_candle_timestamp`, allowing same-day completed 15-minute candle evidence
with limited collection delay while preventing older same-day data from silently
counting as clean. Any future threshold change requires a separate
source-controlled governance update.

D11.16 hardens this rule for U.S. equities by comparing the relevant regular
session in `America/New_York` rather than raw UTC calendar dates. The regular
session rule for this gate is 09:30-16:00 America/New_York. A latest candle from
the most recent completed U.S. regular session must not be quarantined merely
because the diagnostic run happened after UTC midnight. Such after-hours
diagnostic evidence is still `recency_caveated` and `d11_countable=false` unless
a later separately authorized gate records otherwise. Genuinely older prior
sessions remain `quarantined`.

D11.8 records data-quality audit behavior only. It does not complete D11, does
not complete Gate D, does not authorize package capture, replay, scoring,
candidate generation, package mutation, broker/API expansion, IBKR/TWS/Gateway
work, systemd mutation, runtime start/restart, strategy/risk/config changes,
credential changes, or Unit 12 opening. D11 remains **INSUFFICIENT** and Unit 12
remains **BLOCKED** until a future separately authorized sufficiency
reassessment records otherwise.

### D11.9 Market Data Provider Boundary and Alpaca/IEX Freshness Block

D11.9 records the market-data provider boundary created after D11 collection was
parked for repeated Alpaca/IEX freshness failures. Alpaca paper/broker plumbing
remains parked and unchanged; Alpaca/IEX market data is retained only as one
market-data provider implementation behind `market_data.MarketDataProvider`.
Strategy evaluation consumes normalized `Candle`/close data from
`HistoricalBarsResult`, not Alpaca client internals.

`market_input_captured` JSONL events include provider diagnostic metadata:

- `provider`;
- `feed`;
- `symbol`;
- `timeframe`;
- `requested_start`;
- `requested_end`;
- `latest_candle_timestamp`;
- `run_timestamp`;
- `lag_minutes`;
- `freshness_classification`;
- `warnings`.

The local read-only diagnostic command is:

```bash
python -m tools.ops.market_data_freshness_diagnostic --timeframe 15Min --limit 5
```

The diagnostic computes an explicit UTC request window for every provider
request. By default `requested_end` is the diagnostic run timestamp and
`requested_start` is derived from the requested timeframe and limit. Operators
may pin the window for audit replayability with `--requested-end` and
`--lookback-minutes`; the diagnostic output must include non-null
`requested_start` and `requested_end` for each provider result.

The command checks provider freshness across configured symbols and reports
read-only diagnostic output only. It does not capture packages, replay, score,
generate candidates, submit/cancel/modify/flatten orders, mutate packages, touch
systemd, start/restart runtime, open IBKR/TWS/Gateway, or open Unit 12.

D11.9 does not make Alpaca/IEX trusted primary D11 evidence. D11.8 data-quality
classification remains controlling: only `clean` package records may count;
`recency_caveated` records require separate review and do not silently count;
`quarantined` records do not count. D11 remains **INSUFFICIENT**, Gate D remains
**NOT COMPLETE / PARKED**, and Unit 12 remains **BLOCKED**.

### D11.10 Market Data Provider Replacement Readiness

D11.10 adds a deterministic metadata-only provider registry in
`market_data_provider_registry.py`. The registry separates provider role and
status from provider implementation. It records the vocabulary:

- provider roles: `primary`, `secondary`;
- provider statuses: `primary`, `secondary`, `suspect`, `unavailable`,
  `not_configured`.

The registry currently records:

- `alpaca_iex`: `provider_role="secondary"`, `provider_status="suspect"`,
  `d11_primary_eligible=false`;
- `future_primary`: `provider_role="primary"`,
  `provider_status="not_configured"`, `d11_primary_eligible=false`.

Alpaca/IEX is not D11-primary eligible because the explicit-window diagnostic
for 2026-06-17T12:17:01Z through 2026-06-17T20:17:01Z returned latest 15-minute
candles 122-167 minutes stale across AAPL, MSFT, NVDA, TSLA, and MSTR. All
records were `recency_caveated` and `d11_countable=false`.

Market-data freshness diagnostics include provider registry fields:
`provider_role`, `provider_status`, `d11_primary_eligible`, and `reason`.
Unavailable or not-configured providers cannot be used for D11 sufficiency.

D11.10 does not add provider credentials, does not implement Polygon, Tiingo,
IBKR, Schwab, or any other replacement provider, and does not modify runtime,
systemd, timer, service, broker, order, execution, strategy, risk, package
capture, replay, scoring, candidate generation, or Unit 12 authority. D11
remains **INSUFFICIENT**, Gate D remains **NOT COMPLETE / PARKED**, and Unit 12
remains **BLOCKED**.

### D11.11 Market Data Provider Selection Criteria Gate

D11.11 adds a metadata-only provider selection criteria module:
`market_data_provider_selection.py`. This gate defines deterministic criteria
for any future D11 primary market-data provider before implementation,
credentials, runtime use, or VPS diagnostics are authorized.

D11 primary eligibility requires:

- explicit request windows;
- provider/feed metadata;
- latest-candle freshness classified `clean` under D11.8;
- support for target symbols;
- timezone-aware UTC timestamps;
- no strategy/risk/execution coupling;
- no broker/order authority through the data path;
- auditable failure reasons;
- read-only diagnostic testability;
- continued D11-primary ineligibility until a separate VPS read-only diagnostic
  proves freshness.

Candidate status vocabulary is:

- `candidate`;
- `eligible_for_read_only_diagnostic`;
- `diagnostic_failed`;
- `diagnostic_passed`;
- `approved_primary`;
- `rejected`.

The metadata contract for future providers is:
`provider_key`, `provider_name`, `asset_classes_supported`,
`data_type_supported`, `feed_name`, `auth_required`, `credentials_configured`,
`network_required_for_diagnostic`, `broker_coupled`, `order_authority`,
`execution_authority`, `d11_primary_candidate_status`,
`d11_primary_eligible`, and `reason`.

D11.11 records candidate placeholders only:

- `ibkr_market_data_candidate`;
- `polygon_candidate`;
- `tiingo_candidate`;
- `schwab_market_data_candidate`;
- `manual_csv_offline_candidate`.

No candidate is D11-primary eligible by default. IBKR remains a candidate
placeholder only: IBKR/TWS/Gateway is not opened, no broker/order/execution
authority is added, and no provider API implementation exists. Credentialed
providers remain not configured until a separate explicit gate records
otherwise. Alpaca/IEX remains secondary/suspect and not D11-primary eligible.

D11.11 does not add provider credentials, does not implement IBKR, Polygon,
Tiingo, Schwab, CSV ingestion, or any other provider, and does not modify VPS
runtime, systemd, timer, service, broker, order, execution, strategy, risk,
package capture, replay, scoring, candidate generation, or Unit 12 authority.
D11 remains **INSUFFICIENT**, Gate D remains **NOT COMPLETE / PARKED**, and Unit
12 remains **BLOCKED**.

### D11.12 IBKR Read-Only Market Data Diagnostic Contract

D11.12 adds a metadata-only IBKR read-only market-data diagnostic contract:
`ibkr_market_data_diagnostic_contract.py`. The contract separates a future
read-only historical market-data diagnostic from broker/order/execution
authority. It does not import `ibapi` or `ib_insync`, does not connect to TWS or
Gateway, does not add credentials, and does not implement real IBKR market-data
fetching.

The allowed IBKR diagnostic boundary is:

- may request historical market data only after separate explicit authorization;
- may not place, modify, cancel, or route orders;
- may not query positions, account balances, margin, buying power, or portfolio
  state;
- may not start TWS/Gateway;
- may not mutate runtime, systemd, timer, or service state;
- may not capture packages;
- may not replay, score, or generate candidates;
- may not open Unit 12;
- may not mark D11 complete.

The required diagnostic output fields are:
`provider_key`, `provider_name`, `connection_mode`, `read_only`,
`requested_start`, `requested_end`, `symbol`, `timeframe`,
`latest_candle_timestamp`, `lag_minutes`, `freshness_classification`,
`d11_countable`, `d11_primary_candidate_status`, `d11_primary_eligible`,
`failure_reason`, and `authority_boundary`.

The contract fails closed for missing timestamps, non-UTC timestamps, stale
latest candles, warning-bearing results, detected account/order/position
capability, unavailable TWS/Gateway, missing explicit request windows,
missing credentials/config, or any network/client import in the metadata-only
contract module.

The `ibkr_market_data_candidate` remains `d11_primary_eligible=false`.
It may move only to `eligible_for_read_only_diagnostic` after a future explicit
authorization records that status. `approved_primary` remains impossible without
a later VPS read-only diagnostic result and separate governance record.

D11.12 does not add IBKR credentials, does not open IBKR/TWS/Gateway, does not
query account, position, margin, buying power, portfolio, or order state, does
not add order functions, and does not modify VPS runtime, systemd, timer,
service, broker, order, execution, strategy, risk, package capture, replay,
scoring, candidate generation, or Unit 12 authority. D11 remains
**INSUFFICIENT**, Gate D remains **NOT COMPLETE / PARKED**, and Unit 12 remains
**BLOCKED**.

### D11.13 IBKR Read-Only Diagnostic Scaffold

D11.13 adds a fail-closed local CLI scaffold:
`tools/ops/ibkr_market_data_freshness_diagnostic.py`. The scaffold prepares the
D11.12 output shape for a future separately authorized IBKR historical
market-data diagnostic, but it does not implement real IBKR market-data fetching
and does not connect to IBKR, TWS, or Gateway.

The scaffold accepts symbols, timeframe, `--requested-end`, and
`--lookback-minutes`, computes explicit UTC `requested_start` / `requested_end`,
and emits one fail-closed diagnostic row per symbol:

- `provider_key="ibkr_market_data_candidate"`;
- `connection_mode="not_opened"`;
- `read_only=true`;
- `latest_candle_timestamp=null`;
- `lag_minutes=null`;
- `freshness_classification="unavailable"`;
- `d11_countable=false`;
- `d11_primary_candidate_status="candidate"`;
- `d11_primary_eligible=false`;
- failure reason stating that the real IBKR diagnostic is not authorized/opened.

The scaffold authority boundary records:
`no_ibkr_connection`, `no_tws_gateway_start`, `no_credentials_read`,
`no_account_query`, `no_position_query`, `no_margin_query`,
`no_portfolio_query`, `no_order_authority`, `no_execution_authority`,
`no_package_capture`, `no_replay`, `no_scoring`, `no_candidate_generation`,
`no_unit_12_opening`, and `no_d11_completion`.

D11.13 does not import `ibapi` or `ib_insync`, does not connect to TWS/Gateway,
does not read credentials, does not query account, position, margin, buying
power, portfolio, or order state, does not add order functions, and does not
modify VPS runtime, systemd, timer, service, broker, order, execution, strategy,
risk, package capture, replay, scoring, candidate generation, or Unit 12
authority. D11 remains **INSUFFICIENT**, Gate D remains **NOT COMPLETE /
PARKED**, and Unit 12 remains **BLOCKED**.

### D11.14 IBKR Read-Only Implementation Design Gate

D11.14 adds a metadata-only implementation design module:
`ibkr_read_only_implementation_design.py`. This gate defines the future contract
for an eventual separately authorized IBKR historical market-data diagnostic,
but it does not import `ibapi` or `ib_insync`, does not add socket/network client
code, does not connect to IBKR/TWS/Gateway, does not start TWS/Gateway, and does
not read credentials.

Future implementation requirements are:

- explicit operator authorization required;
- local-only first implementation;
- TWS/Gateway must already be running manually before any future diagnostic;
- code may not start TWS/Gateway;
- credentials must not be stored in the repository;
- this design module may not read credentials;
- connection must be read-only historical market data only;
- account, position, margin, buying power, portfolio, and order endpoints remain
  prohibited;
- order placement, modification, cancellation, and routing remain prohibited;
- output must conform to the D11.12 diagnostic contract;
- clean D11.8 freshness proof is required before any primary eligibility;
- D11 cannot be marked complete by this design gate;
- Unit 12 remains blocked.

The future inert IBKR connection configuration contract is:
`host`, `port`, `client_id`, `readonly_mode`, `connection_mode`,
`market_data_type`, `timeout_seconds`, `symbols`, `timeframe`,
`requested_start`, `requested_end`, `outside_rth`, `exchange`, `currency`, and
`sec_type`.

Fail-closed design statuses are:
`design_only`, `awaiting_local_authorization`, `awaiting_manual_tws_gateway`,
`awaiting_credentials_configuration`, `ready_for_local_read_only_smoke`, and
`rejected`.

D11.14 schema alias hardening: after VPS smoke verification, the design
dictionary also exposes explicit top-level aliases
`implementation_requirements` and `future_connection_config_contract`, matching
the canonical `requirements` and `config_contract_fields` tuples. It also
exposes fail-closed booleans for `credentials_read`, `connection_opened`,
`tws_gateway_started`, `account_query_authority`, `position_query_authority`,
`margin_query_authority`, `buying_power_query_authority`, and
`portfolio_query_authority`. These aliases make future gates deterministic and
do not change authority.

D11.14 does not implement real IBKR API calls, does not query account,
position, margin, buying power, portfolio, or order state, does not add order
functions, and does not modify VPS runtime, systemd, timer, service, broker,
order, execution, strategy, risk, package capture, replay, scoring, candidate
generation, or Unit 12 authority. D11 remains **INSUFFICIENT**, Gate D remains
**NOT COMPLETE / PARKED**, and Unit 12 remains **BLOCKED**.

### D11.15 IBKR Local Read-Only Smoke Implementation

D11.15 adds a local-only IBKR historical market-data smoke implementation path:
`tools/ops/ibkr_market_data_read_only_smoke.py`. Without
`--authorize-local-ibkr-read-only-smoke`, the command delegates to the D11.13
fail-closed scaffold and makes no connection attempt.

When explicitly authorized by the local CLI flag, the smoke path may attempt
only a local read-only historical bars request against a manually running
TWS/Gateway. The IBKR client import is confined to the authorized execution
function. If the dependency is unavailable, the path emits a fail-closed
D11.12-compatible diagnostic row. Even when bars are returned and freshness is
classified through D11.8 logic, `d11_primary_eligible=false`, D11 remains
**INSUFFICIENT**, and Unit 12 remains **BLOCKED** until a later separate
governance record says otherwise.

The smoke CLI accepts symbols, timeframe, `--requested-end`,
`--lookback-minutes`, host, port, client-id, exchange, currency, sec-type,
outside-RTH, timeout seconds, and the required authorization flag. It does not
read credentials from the repository, environment, dotenv, keychains, or
secrets; does not start TWS/Gateway; and assumes TWS/Gateway is already running
manually before any authorized local smoke.

D11.15 does not query account, position, margin, buying power, portfolio, or
order state; does not place, modify, cancel, or route orders; does not grant
broker/order/execution authority beyond the local read-only historical
market-data smoke path; and does not modify VPS runtime, systemd, timer,
service, strategy, risk, package capture, replay, scoring, candidate generation,
or Unit 12 authority.

### D11.16 Session-Aware U.S. Equity Freshness Classification

D11.16 records the local IBKR read-only smoke observation from the authorized
local-only diagnostic path: AAPL, MSFT, and NVDA returned latest 15-minute
regular-session bars at `2026-06-17T19:45:00+00:00` while the diagnostic
`requested_end` was around `2026-06-18T02:15:00+00:00`. The previous D11.8
freshness classifier treated the UTC date mismatch as
`latest_candle_prior_to_run_date` and `quarantined`.

That UTC-date comparison is incorrect for U.S. equities after UTC midnight. For
D11.16, freshness classification uses the U.S. regular-session date in
`America/New_York` with a deterministic 09:30-16:00 regular-session window. The
`2026-06-17T19:45:00+00:00` candle belongs to the 2026-06-17 U.S. regular
session. A diagnostic run at `2026-06-18T02:15:00+00:00` is after that same
regular session, so the row is classified as `recency_caveated` with reason
`regular_session_closed_latest_candle_valid_for_last_session`; it remains
`d11_countable=false`.

D11.16 preserves UTC timestamps in diagnostic JSON. It does not make
market-closed-only or after-hours evidence sufficient, does not make IBKR an
approved primary provider, does not complete D11, and does not open Unit 12.
Stale prior-session candles, warning-bearing data, missing/malformed timestamps,
and non-regular-session candles remain fail-closed. D11 remains
**INSUFFICIENT**, Gate D remains **NOT COMPLETE / PARKED**, and Unit 12 remains
**BLOCKED**.

### D11.17 IBKR Regular-Session Evidence Review

D11.17 records a local-only read-only evidence review after the authorized IBKR
smoke was run outside Codex from LOCAL_MAC with TWS/Gateway manually open and
VPS runtime still parked. The reviewed terminal evidence was:

- timestamp UTC: `2026-06-18T14:00:33Z`;
- source commit: `77d854ef811fbdc5fe253cc76ac31c9e54a459a1`;
- branch: `main`;
- worktree before and after smoke: clean;
- result type: `ibkr_local_read_only_market_data_smoke`;
- symbols: AAPL, MSFT, NVDA;
- timeframe: `15Min`;
- latest candle timestamp: `2026-06-18T13:45:00+00:00`;
- lag: about 15.57 minutes;
- freshness classification: `clean`;
- `d11_countable=true`;
- `d11_primary_eligible=false`;
- `D11_STATUS=D11_INSUFFICIENT`;
- `UNIT_12_STATUS=UNIT_12_BLOCKED`;
- package capture, replay, scoring, candidate generation, broker API authority,
  order authority, and execution authority: all false.

This is clean regular-session market-data freshness evidence for the local
read-only smoke path. It does not by itself satisfy D11 sufficiency, does not
make IBKR an approved primary market-data provider, and does not authorize Unit
12, package capture, replay, scoring, candidate generation, broker/API work,
account/position/margin/buying-power/portfolio queries, orders, execution,
runtime mutation, VPS mutation, or systemd/timer changes.

The repository dependency manifests were also reviewed for reproducibility.
`requirements.txt` and `requirements-test.txt` do not pin or declare
`ib_insync`. Any broader reproducible use of the IBKR local read-only smoke path
requires a separate dependency-pinning and installation decision before it can
be treated as a repeatable operational diagnostic. D11.17 records no dependency
change.

### D11.18 IBKR Dependency-Pinning And Primary-Provider Readiness Decision

D11.18 records the dependency and provider-readiness decision after D11.17. The
source-controlled dependency manifests remain:

- `requirements.txt`: `alpaca-py`, `python-dotenv`, `pytz`;
- `requirements-test.txt`: `pytest>=8.0,<10.0`.

`ib_insync` is available on LOCAL_MAC for the manually authorized local smoke,
but it is not declared or pinned in either manifest. D11.18 therefore defers
pinning to a separate dependency-management gate. This checkpoint does not
install dependencies, does not alter requirements files, and does not make the
local environment state a reproducible repo contract.

IBKR remains a market-data candidate only. The D11.11/D11.12 provider-selection
contract still requires a separate governance record before any
`approved_primary` status or `d11_primary_eligible=true` result can exist. The
D11.17 clean/countable regular-session observation is accepted as local
read-only candidate evidence, not as primary-provider approval and not as D11
sufficiency.

Before IBKR can be considered for primary market-data status, a future separate
gate must at minimum record:

- a source-controlled dependency-pinning / installation decision for the IBKR
  read-only diagnostic dependency;
- repeatable read-only diagnostic procedure and version evidence;
- explicit request windows and provider/feed metadata;
- clean D11.8/D11.16 freshness evidence for the target symbols and timeframe;
- no broker/order/execution/account/position/margin/buying-power/portfolio
  authority through the data path;
- a separate approval record changing provider candidate status, if justified.

D11.18 does not complete D11, does not make IBKR a primary provider, does not
open Unit 12, and does not authorize package capture, replay, scoring,
candidate generation, broker/API work, account/position/margin/buying-power/
portfolio queries, orders, execution, VPS mutation, runtime mutation, systemd
mutation, timer/service changes, or credential changes. D11 remains
**INSUFFICIENT**, IBKR primary eligibility remains **NOT APPROVED**, Gate D
remains **NOT COMPLETE / PARKED**, and Unit 12 remains **BLOCKED**.

### D11.19 IBKR Dependency-Pinning / Reproducible Diagnostic Environment Gate

D11.19 records the source-controlled dependency decision for the optional local
IBKR read-only market-data diagnostic environment. The observed working LOCAL_MAC
dependency version for the D11.17/D11.18 smoke path was `ib_insync` version
`0.9.86`.

D11.19 adds `requirements-diagnostics.txt` with the exact optional diagnostic
pin:

```text
ib_insync==0.9.86
```

This pin is intentionally isolated from `requirements.txt` and
`requirements-test.txt`. The base runtime/test dependency manifests remain free
of `ib_insync`, so installing normal runtime or test dependencies does not make
IBKR diagnostics available by default and does not alter deployed runtime
authority. The IBKR smoke module still imports `ib_insync` lazily only inside
the explicitly authorized local smoke execution path and still fails closed when
the dependency is unavailable.

The optional diagnostics pin makes a future local read-only diagnostic
environment reproducible, but it does not install dependencies, does not run the
smoke, does not open TWS/Gateway, and does not change provider approval status.
IBKR remains `ibkr_market_data_candidate`; `d11_primary_eligible=false` remains
the source-controlled status until a later separate provider-approval gate
records otherwise.

D11.19 does not complete D11, does not make IBKR a primary provider, does not
open Unit 12, and does not authorize package capture, replay, scoring,
candidate generation, broker/API work, account/position/margin/buying-power/
portfolio queries, orders, execution, dependency installation, VPS mutation,
runtime mutation, systemd mutation, timer/service changes, or credential
changes. D11 remains **INSUFFICIENT**, IBKR primary eligibility remains **NOT
APPROVED**, Gate D remains **NOT COMPLETE / PARKED**, and Unit 12 remains
**BLOCKED**.

### D11.20 IBKR Primary-Provider Approval Criteria / Sufficiency Decision Gate

D11.20 records the primary-provider approval and D11 sufficiency decision after
D11.17-D11.19. The inspected source-controlled rules do not permit a status
change from one clean local read-only smoke. IBKR remains
`ibkr_market_data_candidate`, `d11_primary_eligible=false`, and
`d11_primary_candidate_status="candidate"`.

Before IBKR may become an approved primary market-data provider, a future
separate approval gate must record, at minimum:

- the optional diagnostic dependency environment installed from the pinned
  `requirements-diagnostics.txt` contract;
- explicit request windows, provider/feed metadata, UTC timestamps, and
  auditable failure reasons;
- read-only diagnostic evidence across the target symbols and timeframe with
  D11.8/D11.16 `clean` freshness and no warnings;
- repeatability evidence beyond a single local smoke, including separately
  governed diagnostic procedure/version evidence;
- credentials/configuration status for diagnostic use without storing
  credentials in the repository;
- proof that the data path carries no broker/order/execution/account/position/
  margin/buying-power/portfolio authority;
- an explicit source-controlled provider-approval record changing candidate
  status from `candidate` to an approved primary state.

The D11.17 clean/countable local smoke is candidate evidence only. It is not
enough for IBKR primary approval and is not enough for D11 sufficiency.

Before D11 may become sufficient, the existing D11/D12 evidence rules still
require, at minimum:

- a governed package inventory with finalized immutable package evidence;
- regular-session package coverage over at least three distinct trading days;
- package records that are clean under D11.8/D11.16 market-data quality rules;
- symbol coverage and decision/outcome diversity sufficient for the evidence
  plan;
- candidate-side package inventory or a separately approved candidate-evidence
  mechanism;
- baseline-vs-candidate pairing readiness;
- hash, no-mutation, no-mixed-run, as-of, integrity, and reproducibility
  attestations;
- a fresh source-controlled sufficiency reassessment explicitly recording D11
  sufficiency.

D11.20 does not complete D11, does not make IBKR a primary provider, does not
open Unit 12, and does not authorize package capture, replay, scoring,
candidate generation, broker/API work, account/position/margin/buying-power/
portfolio queries, orders, execution, dependency installation, VPS mutation,
runtime mutation, systemd mutation, timer/service changes, or credential
changes. D11 remains **INSUFFICIENT**, IBKR primary eligibility remains **NOT
APPROVED**, Gate D remains **NOT COMPLETE / PARKED**, and Unit 12 remains
**BLOCKED**.

### D11.21 IBKR Repeatability Evidence Plan / Controlled Multi-Day Diagnostic Procedure

D11.21 records the repeatability evidence protocol required before any later
IBKR primary-provider approval gate can be considered. This is a planning and
control checkpoint only; it does not run diagnostics and does not change
provider status.

The minimum repeatability protocol is:

- at least **3 successful read-only diagnostic runs**;
- coverage over at least **3 distinct regular-session trading days**;
- each run performed from the pinned optional diagnostic environment
  (`requirements-diagnostics.txt`, `ib_insync==0.9.86`);
- each run started only by explicit local operator authorization, with
  TWS/Gateway already manually open;
- no VPS runtime, timer, service, package capture, replay, scoring, or
  candidate-generation activity during the diagnostic window.

Required symbol and timeframe coverage:

- symbols: AAPL, MSFT, NVDA, TSLA, and MSTR;
- timeframe: `15Min`;
- each counted diagnostic run must include all target symbols in the same
  evidence set;
- any future additional timeframe requires a separate source-controlled update.

Each diagnostic evidence record must capture, at minimum:

- source commit, branch, and clean worktree status before and after the run;
- local timestamp UTC and requested window (`requested_start`, `requested_end`);
- provider key/name, connection mode, read-only flag, symbol, and timeframe;
- latest candle timestamp, lag minutes, freshness classification,
  `d11_countable`, `d11_primary_candidate_status`, `d11_primary_eligible`, and
  failure reason;
- full authority flags for package capture, replay, scoring,
  candidate generation, broker API, order, execution, D11 completion, and Unit
  12;
- dependency contract used (`requirements-diagnostics.txt`,
  `ib_insync==0.9.86`);
- confirmation that no account, position, margin, buying power, portfolio,
  order, balance, or execution query was performed.

Freshness and warning requirements:

- every target-symbol row must be `freshness_classification="clean"`;
- every target-symbol row must be `d11_countable=true`;
- every target-symbol row must have a timezone-aware UTC latest candle
  timestamp;
- warnings must be absent; any warning-bearing result invalidates that
  diagnostic run for repeatability evidence;
- stale, caveated, quarantined, missing, malformed, or non-UTC timestamp results
  do not count.

Stop conditions for the repeatability protocol are:

- stale/caveated/quarantined data for any target symbol;
- any market-data warning;
- dirty worktree before or after the run;
- wrong branch or wrong source commit;
- missing optional diagnostic dependency or dependency-version mismatch;
- wrong session or missing explicit request window;
- failed focused test suite before the run;
- any authority breach, including broker/API/account/position/margin/
  buying-power/portfolio/order/execution calls;
- package capture, replay, scoring, candidate generation, Unit 12 opening, VPS
  mutation, runtime mutation, timer/service mutation, or systemd mutation.

Repeatability evidence remains separate from D11 sufficiency and Unit 12. Even
if the D11.21 protocol is completed in a future gate, it can only support a
later provider-approval decision. It does not by itself create governed package
inventory, candidate package evidence, baseline-vs-candidate pairing, scoring
authority, D11 sufficiency, or Unit 12 opening.

D11.21 does not complete D11, does not make IBKR a primary provider, does not
open Unit 12, and does not authorize package capture, replay, scoring,
candidate generation, broker/API work, account/position/margin/buying-power/
portfolio queries, orders, execution, dependency installation, VPS mutation,
runtime mutation, systemd mutation, timer/service changes, or credential
changes. D11 remains **INSUFFICIENT**, IBKR primary eligibility remains **NOT
APPROVED**, Gate D remains **NOT COMPLETE / PARKED**, and Unit 12 remains
**BLOCKED**.

### D11.22 IBKR Repeatability Evidence Ledger / Operator Runbook Template

D11.22 adds the source-controlled repeatability ledger and operator runbook
template:

```text
docs/ibkr_market_data_repeatability_ledger_template.md
```

The template captures the D11.21 required fields for future local-only
read-only IBKR market-data diagnostics. It separates planned protocol,
completed evidence, invalidated evidence, stop conditions, operator runbook
steps, and final provider-approval review. The completed and invalidated future run ledgers start empty.

D11.22 records no completed future diagnostic runs and no provider-approval
review. It preserves `D11_INSUFFICIENT`, `UNIT_12_BLOCKED`,
`ibkr_market_data_candidate`, `d11_primary_eligible=false`,
`PACKAGE_CAPTURE=BLOCKED`, `ORDER_AUTHORITY=NONE`, `EXECUTION_AUTHORITY=NONE`,
and `VPS_RUNTIME=PARKED`.

D11.22 does not run diagnostics, does not complete D11, does not make IBKR a
primary provider, does not open Unit 12, and does not authorize package capture,
replay, scoring, candidate generation, broker/API work, account/position/
margin/buying-power/portfolio queries, orders, execution, dependency
installation, VPS mutation, runtime mutation, systemd mutation, timer/service
changes, or credential changes.

### D11.23 IBKR Repeatability Run 1 Preflight Packet

D11.23 adds the source-controlled preflight/control packet for a future
separately authorized repeatability run 1:

```text
docs/ibkr_market_data_repeatability_run_1_preflight_packet.md
```

The packet is not the live diagnostic run and is not authorization to run
outside a valid regular-session window. It defines the future `LOCAL_MAC`-only
control surface, expected source-control checks, optional diagnostic dependency
contract, focused no-runtime validation command, future command template,
required paste-back fields, invalidation criteria, and post-run review routing.

D11.23 records no completed repeatability evidence, does not mutate the D11.22
ledger counts, and preserves `completed_repeatability_runs=0`,
`invalidated_repeatability_runs=0`, `D11_INSUFFICIENT`, `UNIT_12_BLOCKED`,
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `PACKAGE_CAPTURE=BLOCKED`,
`ORDER_AUTHORITY=NONE`, `EXECUTION_AUTHORITY=NONE`, and `VPS_RUNTIME=PARKED`.

D11.23 does not run diagnostics, does not complete D11, does not make IBKR a
primary provider, does not open Unit 12, and does not authorize package capture,
replay, scoring, candidate generation, broker/API work, account/position/
margin/buying-power/portfolio queries, orders, execution, dependency
installation, VPS mutation, runtime mutation, systemd mutation, timer/service
changes, or credential changes.

### D11.24 IBKR Repeatability Run 1 Adjudication Packet

D11.24 adds the source-controlled post-run adjudication/control packet for a
future ledger recording review after a separately authorized D11.23 run 1:

```text
docs/ibkr_market_data_repeatability_run_1_adjudication_packet.md
```

The packet is not the diagnostic run, is not evidence recording, and is not
authorization to mutate ledger counts. It defines acceptance criteria,
invalidation criteria, blocked-review criteria, and the only allowed review
outcomes:

- `ACCEPT_FOR_D11_24_LEDGER_RECORDING_REVIEW`;
- `INVALIDATED_EVIDENCE_REVIEW_REQUIRED`;
- `BLOCKED_FOR_SOURCE_CONTROL_OR_AUTHORITY_DEFECT`.

D11.24 records no completed repeatability evidence, records no invalidated
repeatability evidence, does not mutate the D11.22 ledger counts, and preserves
`completed_repeatability_runs=0`, `invalidated_repeatability_runs=0`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`,
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `PACKAGE_CAPTURE=BLOCKED`,
`ORDER_AUTHORITY=NONE`, `EXECUTION_AUTHORITY=NONE`, and `VPS_RUNTIME=PARKED`.

D11.24 does not run diagnostics, does not complete D11, does not make IBKR a
primary provider, does not open Unit 12, and does not authorize package capture,
replay, scoring, candidate generation, broker/API work, account/position/
margin/buying-power/portfolio queries, orders, execution, dependency
installation, VPS mutation, runtime mutation, systemd mutation, timer/service
changes, or credential changes.

### D11.26 IBKR Repeatability Run 1 Ledger Recording

D11.26 records accepted D11.23 repeatability run 1 evidence in the
source-controlled repeatability ledger:

```text
docs/ibkr_market_data_repeatability_ledger_template.md
```

The ledger entry is based only on accepted D11.23 paste-back evidence
adjudicated as `ACCEPT_FOR_D11_24_LEDGER_RECORDING_REVIEW`. No diagnostic rerun
was performed for this ledger recording.

Run 1 evidence status:

- `completed_repeatability_runs=1`;
- `invalidated_repeatability_runs=0`;
- symbols: AAPL, MSFT, NVDA, TSLA, MSTR;
- timeframe: `15Min`;
- `freshness_classification=clean`;
- `d11_countable=true`;
- `d11_primary_candidate_status=candidate`;
- `d11_primary_eligible=false`;
- `NO_RERUN_PERFORMED=true`;
- `VPS_RUNTIME=NOT_TOUCHED`;
- `TIMER_SERVICE=NOT_TOUCHED`;
- `PACKAGE_CAPTURE=BLOCKED`;
- `UNIT_12_STATUS=UNIT_12_BLOCKED`;
- `ORDER_AUTHORITY=NONE`;
- `EXECUTION_AUTHORITY=NONE`.

D11.26 records one accepted repeatability run only. It does not record runs 2
or 3, does not satisfy the D11.21 three-run repeatability protocol, does not
complete D11, does not make IBKR a primary provider, does not open Unit 12, and
does not authorize package capture, replay, scoring, candidate generation,
broker/API work, account/position/margin/buying-power/portfolio/order/balance/
execution queries, orders, execution, dependency installation, VPS mutation,
runtime mutation, systemd mutation, timer/service changes, or credential
changes.

### D11.27 IBKR Repeatability Run 2 Preflight Packet

D11.27 adds the source-controlled preflight/control packet for a future
separately authorized repeatability run 2:

```text
docs/ibkr_market_data_repeatability_run_2_preflight_packet.md
```

The packet is not the live diagnostic run and is not authorization to run
today. It defines the future `LOCAL_MAC`-only control surface for Run #2,
requires Run #2 to occur on a distinct regular-session trading day after Run #1,
requires the future authorization to supply the expected source commit, preserves
`02339cba3239b9148ca352e2970cb658bdacc58a` as historical packet-creation
context only, preserves the D11.26 ledger counts, and provides a `LOCAL_MAC`-
only no-heredoc operator wrapper that emits all D11.28 adjudication inputs
before and after exactly one source-controlled diagnostic command.

D11.27 is not authorization to run today.

D11.27 records no completed repeatability evidence, records no invalidated
repeatability evidence, does not mutate the D11.26 ledger counts, and preserves
`completed_repeatability_runs=1`, `invalidated_repeatability_runs=0`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`,
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `PACKAGE_CAPTURE=BLOCKED`,
`ORDER_AUTHORITY=NONE`, `EXECUTION_AUTHORITY=NONE`, and `VPS_RUNTIME=PARKED`.
Run #1 remains the only completed run. Run #2 is planned only, not completed and
not invalidated. Run #3 remains future and pending.

Run #2 is planned only, not completed and not invalidated.

D11.27 does not run diagnostics, does not complete D11, does not make IBKR a
primary provider, does not open Unit 12, and does not authorize package capture,
replay, scoring, candidate generation, broker/API work, account/position/
margin/buying-power/portfolio/order/balance/execution queries, orders,
execution, dependency installation, VPS mutation, runtime mutation, systemd
mutation, timer/service changes, or credential changes.

### D11.28 IBKR Repeatability Run 2 Adjudication Packet

D11.28 adds the source-controlled post-run adjudication/control packet for a
future ledger-recording review after a separately authorized D11.27 Run #2:

```text
docs/ibkr_market_data_repeatability_run_2_adjudication_packet.md
```

The packet is not the diagnostic run, is not evidence recording, and is not
authorization to mutate ledger counts. It requires Run #2 to have been
separately authorized and executed on a distinct regular-session trading day
after Run #1. It requires every paste-back field from
`docs/ibkr_market_data_repeatability_run_2_preflight_packet.md` and forbids
inferring missing evidence from memory, terminal scrollback, screenshots, broker
state, or operator confidence.

D11.28 is not authorization to mutate ledger counts.

Allowed D11.28 outcomes are exactly:

- `ACCEPT_FOR_D11_28_RUN_2_LEDGER_RECORDING_REVIEW`;
- `INVALIDATED_RUN_2_EVIDENCE_REVIEW_REQUIRED`;
- `BLOCKED_FOR_RUN_2_SOURCE_CONTROL_OR_AUTHORITY_DEFECT`.

D11.28 records no completed repeatability evidence, records no invalidated
repeatability evidence, does not mutate the D11.26 ledger counts, and preserves
`completed_repeatability_runs=1`, `invalidated_repeatability_runs=0`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`,
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `PACKAGE_CAPTURE=BLOCKED`,
`ORDER_AUTHORITY=NONE`, `EXECUTION_AUTHORITY=NONE`, and `VPS_RUNTIME=PARKED`.
Run #1 remains the only completed run. Run #2 remains planned only, not
completed and not invalidated. Run #3 remains future and pending.

Run #2 remains planned only, not completed and not invalidated.

D11.28 does not run diagnostics, does not complete D11, does not make IBKR a
primary provider, does not open Unit 12, and does not authorize package capture,
replay, scoring, candidate generation, broker/API work, account/position/
margin/buying-power/portfolio/order/balance/execution queries, orders,
execution, dependency installation, VPS mutation, runtime mutation, systemd
mutation, timer/service changes, or credential changes. Do not rerun by
impulse.

Do not rerun by impulse.

### D11.30 IBKR Repeatability Run 2 Ledger Recording

D11.30 records accepted Run #2 evidence in the source-controlled repeatability
ledger after adjudication as
`ACCEPT_FOR_D11_28_RUN_2_LEDGER_RECORDING_REVIEW`. It records no diagnostic
rerun, broker/API call, dependency installation, VPS or timer/service mutation,
package capture, replay, scoring, candidate generation, Unit 12 activity, or
authority expansion.

Run #2 was a `LOCAL_MAC` read-only diagnostic on 2026-06-23 at source commit
`43057a4b2689da57a1f7a6517159eaf4109f83ca`. Its requested window was
`2026-06-23T12:00:00+00:00` through `2026-06-23T14:00:00+00:00`; all target
symbols AAPL, MSFT, NVDA, TSLA, and MSTR had a latest candle timestamp of
`2026-06-23T13:45:00+00:00`, `freshness_classification=clean`, and
`d11_countable=true`.

The ledger now preserves `completed_repeatability_runs=2` and
`invalidated_repeatability_runs=0`. Run #1 remains recorded for 2026-06-22;
Run #3 remains future and pending. The two accepted runs do not satisfy the
three-run D11.21 repeatability protocol, so `D11_INSUFFICIENT`,
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `UNIT_12_BLOCKED`,
`PACKAGE_CAPTURE=BLOCKED`, `ORDER_AUTHORITY=NONE`,
`EXECUTION_AUTHORITY=NONE`, and `VPS_RUNTIME=PARKED` remain unchanged.

### D11.31 IBKR Repeatability Run 3 Preflight Packet

D11.31 adds the source-controlled control-prep packet for planned Run #3:

```text
docs/ibkr_market_data_repeatability_run_3_preflight_packet.md
```

The packet is prepared in `CODEX_LOCAL`; it reserves the future diagnostic for
separately authorized `LOCAL_MAC` execution and reserves `VPS` only for
post-commit validation if a source-controlled change is committed. It does not
approve the diagnostic, broker/TWS use, IBKR submit smoke, live trading,
runtime activation, or any strategy/risk/execution behavior change.

Run #3 was planned only at this D11.31 control-prep stage and had to occur on a
distinct regular-session trading day after Run #2. Its later acceptance and
ledger recording are recorded by D11.32.

### D11.32 IBKR Repeatability Run 3 Ledger / Adjudication Update

D11.32 records accepted Run #3 `LOCAL_MAC` paste-back evidence in the
source-controlled repeatability ledger. It records no diagnostic rerun,
broker/API call, dependency installation, VPS or timer/service mutation,
package capture, replay, scoring, candidate generation, Unit 12 activity, or
authority expansion.

Run #3 was a read-only diagnostic on 2026-06-24 at source commit
`8d3565208fcfeb62ad5230ada72a38a08852eb8b`. The branch and observed HEAD were
`main` and that same commit, and the worktree was clean before and after the
run. Its requested window was `2026-06-24T12:00:00+00:00` through
`2026-06-24T14:00:00+00:00`; all target symbols AAPL, MSFT, NVDA, TSLA, and
MSTR had a latest candle timestamp of `2026-06-24T13:45:00+00:00`,
`freshness_classification=clean`, and `d11_countable=true`.

The ledger now records Runs #1, #2, and #3 as completed/countable with
`completed_repeatability_runs=3` and `invalidated_repeatability_runs=0`. The
three accepted runs satisfy the D11.21 evidence-count and distinct-day
requirements only. Under D11.21, repeatability evidence remains separate from
provider approval and D11 sufficiency; therefore IBKR remains
`ibkr_market_data_candidate`, `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`,
`ORDER_AUTHORITY=NONE`, `EXECUTION_AUTHORITY=NONE`, and `VPS_RUNTIME=PARKED`
remain unchanged. No replay, scoring, candidate generation, broker/account/
order/execution query, cleanup, flatten, sell, cancel, or live-trading
authority is granted.

### D11.33 Evidence-Count Completion / Sufficiency-Boundary Review

D11.33 records a source-controlled boundary review after the accepted Run #3
ledger update. `completed_repeatability_runs=3` and
`invalidated_repeatability_runs=0`; Runs #1 (2026-06-22), #2 (2026-06-23), and
#3 (2026-06-24) are clean, countable, and completed. This completes the
D11.21 three-run evidence-count and distinct-day requirement only.

Under D11.21, the completed evidence count independently changes none of the
following: IBKR remains `ibkr_market_data_candidate` with
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`; D11 remains `D11_INSUFFICIENT`; Unit
12 remains `UNIT_12_BLOCKED`; `PACKAGE_CAPTURE=BLOCKED`; and
`VPS_RUNTIME=PARKED`. It does not authorize package capture, replay, scoring,
candidate generation, broker/API or account/position/margin/buying-power/
portfolio/order/balance/execution queries, runtime, timer, service, systemd,
strategy, risk, execution, orders, cleanup, flatten, sell, cancel, or live
trading.

The next permissible gate is the ledger's separately authorized final
provider-approval review. That review may decide only whether the completed
repeatability evidence supports provider approval; it remains separate from
D11 sufficiency, Unit 12, package inventory, candidate evidence,
baseline-vs-candidate pairing, replay, scoring, and every operational or
trading authority. Current status labels are: `EVIDENCE_COUNT_COMPLETE`,
`D11_INSUFFICIENT`, `IBKR_CANDIDATE_ONLY`,
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `UNIT_12_BLOCKED`, and
`VPS_RUNTIME=PARKED`.

### D11.34 Final IBKR Market-Data Provider-Approval Review

D11.34 performs the final provider-approval review allowed after D11.33.
Decision: `NOT_APPROVED`. The completed clean/countable Run #1, #2, and #3
evidence satisfies the D11.21 repeatability requirement, but it does not meet
all source-controlled primary-eligibility criteria.

D11.11 requires a separate VPS read-only freshness proof before primary
eligibility. The accepted repeatability evidence is `LOCAL_MAC` only, and no
separate VPS proof is recorded. D11.20 also requires a source-controlled
record of diagnostic credentials/configuration status without storing
credentials; the candidate-placeholder setting `credentials_configured=false`
is not that diagnostic-use record. Therefore the provider status remains
`ibkr_market_data_candidate`,
`d11_primary_candidate_status=candidate`, and
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`.

No provider-approval outcome independently completes D11 or opens Unit 12.
D11 remains `D11_INSUFFICIENT`; Unit 12 remains `UNIT_12_BLOCKED`;
`PACKAGE_CAPTURE=BLOCKED`; and `VPS_RUNTIME=PARKED`. This review grants no
package capture, replay, scoring, candidate generation, broker/API or account/
position/margin/buying-power/portfolio/order/balance/execution query, runtime,
timer, service, systemd, strategy, risk, execution, order, cleanup, flatten,
sell, cancel, or live-trading authority.

The next permissible gate is a separately authorized VPS read-only freshness
proof and its source-controlled diagnostic credential/configuration record.
That future gate remains separate from D11 sufficiency, Unit 12, package
capture, replay, scoring, candidate generation, and all operational or trading
authority.

### D11.35 VPS Read-Only Freshness Proof / Credential-Configuration Control Prep

D11.35 adds the control-prep packet for the missing D11.11 VPS read-only
freshness proof and D11.20 diagnostic credential/configuration record:

```text
docs/ibkr_market_data_vps_freshness_preflight_packet.md
```

It records no VPS proof and no credentials. The existing IBKR smoke command is
local-only and cannot be used as a VPS command. Before any proof, a separate
source-controlled VPS-specific command contract and authorization must capture
the pinned diagnostic environment, non-secret operator-managed
credential/configuration attestation, read-only historical-market-data scope,
clean source state, required diagnostic output, and closed authority boundary.

D11.35 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=PARKED`. It opens no broker/API, account, order, execution,
cleanup, flatten, sell, cancel, live-trading, runtime, timer, service,
systemd, strategy, risk, replay, scoring, or candidate-generation authority.

### D11.36 VPS-Specific Read-Only Diagnostic Command Contract

D11.36 adds the exact future VPS-only diagnostic command contract:

```text
docs/ibkr_market_data_vps_read_only_command_contract.md
```

It names `/opt/openclaw-stocks`, its `venv` Python path, a future
VPS-specific module and authorization flag, the pinned diagnostic dependency,
the existing five-symbol `15Min` / 120-minute request scope, non-secret
credential/configuration fields, required output fields, and all closed
authority flags. It neither implements nor authorizes the command, runs no VPS
proof, and does not permit the local-only IBKR smoke command on VPS.

D11.36 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=PARKED`. Its next permissible gate is separately authorizing the
VPS-specific command contract and one bounded proof; that gate remains separate
from provider approval, D11 sufficiency, Unit 12, and all operational or
trading authority.

### D11.37 VPS Read-Only Freshness Proof Implementation

D11.37 implements the D11.36 contract module and records its implementation
packet:

```text
tools/ops/ibkr_market_data_vps_read_only_freshness_proof.py
docs/ibkr_market_data_vps_read_only_implementation_packet.md
```

The implementation is fail-closed without
`--authorize-vps-ibkr-read-only-freshness-proof`, requires execution context
`VPS`, repo root `/opt/openclaw-stocks`, matching clean `main` source state,
and `requirements-diagnostics.txt` / `ib_insync==0.9.86`. Its only connection
path is an authorized regular-trading-hours historical-bar request; it emits
non-secret credential/configuration attestations and all D11.36 closed-authority
flags.

D11.37 does not run a VPS proof or approve IBKR. It preserves
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=PARKED`. The
next permissible gate is separately authorizing the implemented bounded VPS
proof; provider approval, D11 sufficiency, Unit 12, and all operational or
trading authority remain separate.

### D11.38 Bounded VPS Read-Only Freshness Proof Authorization Packet

D11.38 adds the source-controlled authorization packet for the implemented
D11.37 proof:

```text
docs/ibkr_market_data_vps_proof_authorization_packet.md
```

It pins expected source commit
`c175ac79191d6d82291dea27aaa1976c8bb6ca50`, execution context `VPS`, repo
root `/opt/openclaw-stocks`, and Python path
`/opt/openclaw-stocks/venv/bin/python`, and it bounds the future invocation to
the five-symbol `15Min`, 120-minute, historical-market-data-only contract with
the explicit VPS authorization flag. No proof has run and no credentials are
stored or emitted.

The live regular-session UTC end time, VPS-local endpoint, port, and read-only
client ID have no source-controlled values yet; D11.38 keeps them as required
runtime-parameter-addendum fields rather than inventing them. It preserves
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=PARKED`, and
opens no account/order/execution, cleanup, flatten, sell, cancel, live trading,
runtime, timer, service, systemd, strategy, risk, replay, scoring, or
candidate-generation authority.

### D11.39 Narrow VPS Runtime-Parameter Addendum

D11.39 adds the runtime-parameter addendum required by D11.38:

```text
docs/ibkr_market_data_vps_runtime_parameter_addendum.md
```

It pins expected source commit
`0fb3f459c519b622ed49a6dea580782242b93365`, repo root
`/opt/openclaw-stocks`, Python path `/opt/openclaw-stocks/venv/bin/python`,
the implemented D11.37 module, execution context `VPS`, and the existing
five-symbol `15Min`, 120-minute, SMART/USD/STK, 10-second command boundary.
Its requested end must be a regular-session UTC `Z` time at or after 7:00 AM
Pacific / 10:00 AM Eastern; official market open is not the D11 diagnostic
target.

The addendum is `PREPARED_PENDING_OPERATOR_RUNTIME_VALUES`: the regular-session
UTC end time, VPS-local endpoint, port, and read-only client ID remain pending,
so no proof has run and the command is not executable. It preserves all
non-secret credential/configuration fields and closed authorities, including
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=PARKED`.

The next permissible gate is a source-controlled update supplying all four
operator-confirmed runtime values. It does not authorize any account, order,
execution, cleanup, flatten, sell, cancel, live-trading, runtime, timer,
service, systemd, strategy, risk, replay, scoring, or candidate-generation
activity.

### D11.40 VPS Runtime-Value Confirmation

D11.40 adds the source-controlled runtime-value confirmation required by
D11.39:

```text
docs/ibkr_market_data_vps_runtime_value_confirmation.md
```

It pins expected source commit
`5e2d07110080a90b7d9f9d6f4a37c06f7e56c7b9`, repo root
`/opt/openclaw-stocks`, Python path `/opt/openclaw-stocks/venv/bin/python`,
execution context `VPS`, and the four operator-confirmed runtime values:
`authorized_regular_session_utc_z=2026-06-24T14:00:00Z`,
`authorized_vps_local_endpoint=127.0.0.1`, `authorized_port=7497`, and
`authorized_read_only_client_id=9118`.

The requested end is at 7:00 AM Pacific / 10:00 AM Eastern on 2026-06-24;
official market open is not the D11 diagnostic target. The exact future command
is now source-controlled but has not been executed. D11.40 preserves the
non-secret credential/configuration attestation and all closed-authority flags,
including `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=PARKED`.

The next permissible gate is a separate operator terminal step on the VPS that
runs exactly the source-controlled bounded proof command and captures output
for source-controlled adjudication. D11.40 does not authorize account, order,
execution, cleanup, flatten, sell, cancel, live-trading, runtime, timer,
service, systemd, strategy, risk, replay, scoring, or candidate-generation
activity.

### D11.41 Next-Session VPS Runtime-Value Update

D11.41 adds the source-controlled next-session runtime-value update:

```text
docs/ibkr_market_data_vps_next_session_runtime_value_update.md
```

It records that the prior bounded proof attempt did not run
(`vps_freshness_proof_run=false`) because `ib_insync` was unavailable, and that
the after-hours dependency blocker has since been cleared on the VPS with
`/opt/openclaw-stocks/venv/bin/python`, Python 3.12.3,
`requirements-diagnostics.txt / ib_insync==0.9.86`, and boundary validation
`60 passed`. This after-hours readiness is not proof evidence.

D11.41 supersedes the stale D11.40 proof timestamp
`2026-06-24T14:00:00Z` with the next valid proof-window timestamp
`2026-06-25T14:00:00Z`. It preserves the VPS-local endpoint `127.0.0.1`, port
`7497`, read-only client ID `9118`, expected source commit
`c90168d0c655c88183bdac03c4f5de2898387428`, repo root
`/opt/openclaw-stocks`, Python path `/opt/openclaw-stocks/venv/bin/python`,
and execution context `VPS`.

The requested end is at 7:00 AM Pacific / 10:00 AM Eastern on 2026-06-25;
official market open is not the D11 diagnostic target. The exact future command
is source-controlled but has not been executed. D11.41 preserves the non-secret
credential/configuration attestation and all closed-authority flags, including
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=PARKED`.

The next permissible gate is a separate operator terminal step on the VPS, in
the next valid regular-session proof window, that runs exactly the
source-controlled bounded proof command and captures output for
source-controlled adjudication. D11.41 does not authorize account, order,
execution, cleanup, flatten, sell, cancel, live-trading, runtime, timer,
service, systemd, strategy, risk, replay, scoring, or candidate-generation
activity.

### D11.42 VPS Read-Only Freshness Proof Connection-Refused Adjudication

D11.42 adds the source-controlled adjudication record for the bounded VPS
read-only proof attempt:

```text
docs/ibkr_market_data_vps_proof_connection_refused_adjudication.md
```

The proof command ran during the authorized proof window
(`authorized_pacific=2026-06-25 07:00:00 PDT`,
`authorized_utc=2026-06-25 14:00:00 UTC`) on branch `main` with expected and
observed source commit `04e856c8a8d3387ccf2b0af5e55b493ea853a401`, clean
pre/post worktree status, repo root `/opt/openclaw-stocks`, and satisfied
dependency contract `requirements-diagnostics.txt / ib_insync==0.9.86`.

D11.42 classifies the attempt as `PROOF_RUN_BUT_NON_COUNTABLE`:
`vps_freshness_proof_run=true`, but `d11_countable_evidence_produced=false`.
All five requested symbols (`AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`) are
recorded as `freshness_classification=unavailable`, `d11_countable=false`,
`d11_primary_eligible=false`, `latest_candle_timestamp=null`,
`lag_minutes=null`, with failure reason `historical read-only request failed:
ConnectionRefusedError`.

The proven blocker is `VPS_LOCALHOST_CONTEXT_MISMATCH`:
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`. The proof targeted
`127.0.0.1:7497` from the VPS context, that endpoint refused connection, later
VPS audit showed no listener on `127.0.0.1:7497`, and later VPS audit showed
`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`. Existing docs state
`127.0.0.1` means loopback of the current process context. The adjudication
therefore records `NOT_PROVEN_TWS_ISSUE` and `NOT_PROVEN_IB_GATEWAY_ISSUE`.
This is not provider approval evidence and does not complete D11.

D11.42 preserves read-only historical-market-data boundaries and closed
authority flags, including `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`. The next permissible gate is operator-managed VPS
endpoint/context readiness confirmation only, not bot-started gateway/runtime
and not account, position, margin, buying-power, portfolio, order, balance,
execution, cleanup, flatten, sell, cancel, live-trading, package capture,
replay, scoring, candidate generation, timer, service, systemd, runtime
mutation, strategy, risk, or execution authority.

### D11.43 VPS Endpoint/Context Correction Gate

D11.43 adds the source-controlled endpoint/context correction gate after D11.42
VPS validation:

```text
docs/ibkr_market_data_vps_endpoint_context_correction_gate.md
```

It records current validated source commit
`de2fcb8efbc9843333f004db45c75c603c744312` and D11.42 VPS validation
`62 passed in 1.47s`. It preserves the D11.42 labels
`PROOF_RUN_BUT_NON_COUNTABLE`, `VPS_LOCALHOST_CONTEXT_MISMATCH`,
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`,
`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`, `NOT_PROVEN_TWS_ISSUE`, and
`NOT_PROVEN_IB_GATEWAY_ISSUE`.

D11.43 records that the proof ran from VPS, targeted `127.0.0.1:7497` from the
VPS process context, `127.0.0.1:7497` refused connection, no listener was
observed on `127.0.0.1:7497`, `openclaw-gateway` was present as a Node process,
`openclaw-gateway` listened on `127.0.0.1:18789` and `127.0.0.1:18791`, and
`openclaw-gateway.service` was not found in systemd. Existing doctrine states
`127.0.0.1` is process-context-local loopback and VPS/CODEX_LOCAL IBKR socket
paths are not valid for Mac-local TWS evidence without separate
execution-context proof.

D11.43 does not choose a new endpoint blindly. It forbids proof rerun until
endpoint/context correction is source-controlled and validated, and it forbids
changing to `18789` or `18791` without a separate source-controlled approval
explaining what those ports are and why the selected port is the approved
read-only bridge. The next allowed operator evidence must decide among using an
approved `openclaw-gateway` exposed local port, creating a separately
source-controlled tunnel prerequisite, or abandoning VPS-local proof and
returning to Mac-local IBKR evidence only.

D11.43 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`,
and opens no account, position, margin, buying-power, portfolio, order,
balance, execution, cleanup, flatten, sell, cancel, live-trading, package
capture, replay, scoring, candidate generation, timer, service, systemd,
runtime mutation, gateway mutation, strategy, risk, or execution authority.

### D11.44 VPS Endpoint/Context Operator Evidence Packet

D11.44 adds the source-controlled operator endpoint/context evidence packet:

```text
docs/ibkr_market_data_vps_endpoint_context_operator_evidence_packet.md
```

It records current validated source commit
`3905f9ab4cf993103ff9aaa3c4619851ba00ae2d` and D11.43 VPS validation
`63 passed in 1.10s`. It preserves the D11.42/D11.43 labels
`PROOF_RUN_BUT_NON_COUNTABLE`, `VPS_LOCALHOST_CONTEXT_MISMATCH`,
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`,
`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`, `NOT_PROVEN_TWS_ISSUE`, and
`NOT_PROVEN_IB_GATEWAY_ISSUE`.

D11.44 records no endpoint replacement selected and no proof rerun authorized.
It preserves `127.0.0.1:7497` as the prior failed VPS-local endpoint and
records `127.0.0.1:18789` and `127.0.0.1:18791` as observed
`openclaw-gateway` ports only, not approved proof endpoints. Endpoint liveness
is not provider approval evidence, protocol approval, or market-data proof
evidence; an open TCP port is not proof that it is an approved read-only IBKR
market-data bridge.

D11.44 defines future read-only operator evidence for VPS process/port identity
only: `git status --short`, `git rev-parse HEAD`, `git log -1 --oneline`,
`ss -ltnp` filtered for `18789`, `18791`, and `7497`, `ps` identity for the
`openclaw-gateway` PID, `readlink -f /proc/<pid>/exe`, `pwdx <pid>`,
`/proc/<pid>/cmdline` with nulls converted to spaces, and repo references to
`openclaw-gateway`, `18789`, `18791`, and `7497`.

D11.44 does not choose a new endpoint and forbids switching a proof command to
`18789` or `18791` until a later source-controlled approval identifies
protocol/bridge semantics and explains why the selected port is the approved
read-only bridge. The future evidence must decide among an approved
`openclaw-gateway` bridge path, a separately source-controlled tunnel
prerequisite path, or abandoning VPS-local proof and returning to Mac-local
IBKR evidence only.

D11.44 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`,
and opens no account, position, margin, buying-power, portfolio, order,
balance, execution, cleanup, flatten, sell, cancel, live-trading, package
capture, replay, scoring, candidate generation, timer, service, systemd,
runtime mutation, gateway mutation, strategy, risk, or execution authority.

### D11.45 VPS Endpoint/Context Evidence Adjudication

D11.45 adds the source-controlled adjudication for the D11.44 VPS operator
endpoint/context evidence:

```text
docs/ibkr_market_data_vps_endpoint_context_evidence_adjudication.md
```

It records `OPERATOR_ENDPOINT_CONTEXT_EVIDENCE_ADJUDICATED`, execution context
`VPS`, source commit `7ca0f2904f4d3b7376df0d699d2bc6d6bd128a4b`, commit
message `7ca0f29 Define D11 VPS endpoint context operator evidence`,
`current_utc=2026-06-25 15:29:39 UTC`, and D11.44 VPS validation
`64 passed in 1.27s`. The evidence is identity/liveness only: no proof was
rerun, no endpoint was changed, no gateway/runtime/service/systemd mutation
occurred, and no IBKR/TWS/Gateway connection or account/order/execution access
was opened.

D11.45 classifies `127.0.0.1:18789` and `127.0.0.1:18791` as
`OPEN_LIVENESS_ONLY`, with `openclaw-gateway` PID `846`, command
`openclaw-gateway`, executable `/usr/bin/node`, working directory `/root`, and
cmdline `openclaw-gateway`. It records `[::1]:18789` as
`OPEN_LIVENESS_ONLY` and `127.0.0.1:7497` as `CLOSED_OR_REFUSED`.

D11.45 preserves the corrected labels `VPS_LOCALHOST_CONTEXT_MISMATCH`,
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`,
`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791`, `NOT_PROVEN_TWS_ISSUE`, and
`NOT_PROVEN_IB_GATEWAY_ISSUE`. It records
`endpoint_liveness_confirmed_for_18789=true`,
`endpoint_liveness_confirmed_for_18791=true`,
`endpoint_liveness_confirmed_for_7497=false`,
`openclaw_gateway_identity_confirmed=true`,
`openclaw_gateway_protocol_approved=false`, `proof_endpoint_approved=false`,
`proof_rerun_authorized=false`, `provider_approval_evidence=false`, and
`market_data_proof_evidence=false`.

D11.45 corrects source-document typos by requiring
`OPENCLAW_GATEWAY_PRESENT_ON_18789_AND_18791` and
`rg -n "openclaw-gateway|18789|18791|7497" .`. It records that the former
gateway label typo omitted the final `9` in `18789`, and the former repository
search typo omitted the final `y` in `openclaw-gateway`. It also records the
future runbook formatting fix: avoid `printf '--- pid=%s ---\n' "$pid"` and
use `printf '%s\n' "--- pid=$pid ---"`.

D11.45 forbids treating open TCP liveness as approved protocol/bridge
semantics, provider approval evidence, endpoint approval, or market-data proof
evidence. It forbids switching the proof command to `18789` or `18791` without
a later source-controlled bridge/protocol approval. It preserves
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`,
and opens no account, position, margin, buying-power, portfolio, order,
balance, execution, cleanup, flatten, sell, cancel, live-trading, package
capture, replay, scoring, candidate generation, timer, service, systemd,
runtime mutation, gateway mutation, strategy, risk, or execution authority.

### D11.46 VPS Bridge/Protocol Decision Prerequisite

D11.46 adds the source-controlled bridge/protocol decision prerequisite gate:

```text
docs/ibkr_market_data_vps_bridge_protocol_decision_prerequisite.md
```

It records current validated source commit
`73b3b22297ba82d61eb915351349eb758589724a`, D11.45 VPS validation
`65 passed in 0.23s`, and the D11.45 classification: `18789` and `18791` are
liveness-confirmed only, `7497` is closed/refused, `openclaw-gateway` identity
is confirmed, `openclaw_gateway_protocol_approved=false`,
`proof_endpoint_approved=false`, `proof_rerun_authorized=false`,
`provider_approval_evidence=false`, and `market_data_proof_evidence=false`.

D11.46 preserves the adjudicated facts that `openclaw-gateway` was PID `846`,
executable `/usr/bin/node`, working directory `/root`, cmdline
`openclaw-gateway`, with `127.0.0.1:18789` and `127.0.0.1:18791` classified as
`OPEN_LIVENESS_ONLY`, `[::1]:18789` also open liveness only, and
`127.0.0.1:7497` classified as `CLOSED_OR_REFUSED`.

D11.46 does not approve `18789` or `18791` as proof endpoints and does not
authorize a proof rerun. Before any later approval could classify an
`openclaw-gateway` port as an approved read-only IBKR market-data bridge, future
source-controlled evidence must identify package/source provenance, protocol
on `18789` and `18791`, whether either port exposes IBKR API, HTTP, WebSocket,
RPC, proxy, tunnel, or other bridge semantics, whether historical market-data
read-only requests can occur without account/order/execution authority, exact
command boundaries for any protocol probe, separate approval before execution,
and a non-mutating fail-closed probe design.

D11.46 requires a clear negative path: if protocol semantics cannot be proven
source-controlled, abandon VPS-local proof or create a separate tunnel
prerequisite. It forbids treating liveness as bridge/protocol approval and
forbids switching the proof command to `18789` or `18791`. It preserves
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`,
and opens no account, position, margin, buying-power, portfolio, order,
balance, execution, cleanup, flatten, sell, cancel, live-trading, package
capture, replay, scoring, candidate generation, timer, service, systemd,
runtime mutation, gateway mutation, strategy, risk, or execution authority.

### D11.47 VPS Bridge/Protocol Static Evidence Packet

D11.47 adds the source-controlled bridge/protocol static evidence-collection
packet:

```text
docs/ibkr_market_data_vps_bridge_protocol_static_evidence_packet.md
```

It records current validated source commit
`2d68d0d3d5ca72be0fd39c751148bd4d1c392c9b`, D11.46 VPS validation
`66 passed in 1.89s`, and that D11.46 remains unchanged: `18789` and `18791`
are liveness-confirmed only, `7497` is closed/refused,
`openclaw_gateway_protocol_approved=false`, `proof_endpoint_approved=false`,
`proof_rerun_authorized=false`, `provider_approval_evidence=false`, and
`market_data_proof_evidence=false`.

D11.47 does not approve `18789` or `18791` as proof endpoints, does not
authorize proof rerun, and does not authorize protocol probing. It defines only
read-only static evidence to identify `openclaw-gateway` package/source/protocol
provenance: source state commands, `which openclaw-gateway`, `command -v`,
`readlink`, `file`, `ls -l`, optional `dpkg -S`, optional `npm root -g`,
optional `npm list -g --depth=0`, optional `node --version`, optional
`npm --version`, optional `systemctl status openclaw-gateway --no-pager` as
service-identity only, and repo-only `rg` search for gateway, port, protocol,
proxy, tunnel, IBKR, and market-data references.

D11.47 explicitly forbids `curl`, `nc`, `telnet`, `/dev/tcp`, protocol
handshake, broker API import or connect, and any traffic to `18789`, `18791`,
or `7497`. It forbids treating package/source identity, service identity, or
liveness as protocol approval, and forbids switching the proof command to
`18789` or `18791`.

D11.47 requires package/source provenance evidence before any protocol decision,
protocol semantics evidence before any bridge approval, and separate
source-controlled protocol-probe approval before any traffic is sent to `18789`
or `18791`. It preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11_INSUFFICIENT`, `UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`, and opens no account, position, margin,
buying-power, portfolio, order, balance, execution, cleanup, flatten, sell,
cancel, live-trading, package capture, replay, scoring, candidate generation,
timer, service, systemd, runtime mutation, gateway mutation, strategy, risk, or
execution authority.

### D11.48 VPS Bridge/Protocol Static Evidence Adjudication

D11.48 adds the source-controlled adjudication of D11.47 VPS static provenance
evidence:

```text
docs/ibkr_market_data_vps_bridge_protocol_static_evidence_adjudication.md
```

It records `STATIC_PROVENANCE_EVIDENCE_ADJUDICATED`, D11.47 VPS validation
`67 passed in 1.67s`, static evidence file
`/tmp/d11_47_static_evidence_20260625T202035Z.txt`, line count `30022`, byte
count `3132489`, SHA-256
`26c21cdf1a3af3e4e15e8e7e8e9c9c3f3ce24c806c97110ede6a1a9050b2676c`, source
commit `3592b3068fd6bce0296d28db6ddd579ae90e8574`, and commit message
`3592b30 Define D11 VPS bridge protocol static evidence`.

D11.48 adjudicates that `openclaw_gateway_command_v` was empty,
`openclaw_gateway_binary=NOT_FOUND`, `openclaw_gateway_binary_on_path=false`,
`npm_global_openclaw_package_observed=true` with `openclaw@2026.3.24`,
`node_version=v24.13.0`, `npm_version=11.6.2`, and
`openclaw_gateway_service_found=false`. The repo reference output was too
broad/noisy for protocol approval, so `package_source_provenance_complete=false`
and `protocol_semantics_proven=false`.

D11.48 keeps `bridge_protocol_approved=false`, `proof_endpoint_approved=false`,
`proof_rerun_authorized=false`, `provider_approval_evidence=false`, and
`market_data_proof_evidence=false`. It does not approve `18789` or `18791` as
proof endpoints, does not authorize proof rerun, does not authorize protocol
probing, does not authorize endpoint switch, and does not authorize
account/order/execution access.

D11.48 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`,
and opens no account, position, margin, buying-power, portfolio, order,
balance, execution, cleanup, flatten, sell, cancel, live-trading, package
capture, replay, scoring, candidate generation, timer, service, systemd,
runtime mutation, gateway mutation, strategy, risk, or execution authority.

### D11.49 VPS Bridge/Protocol Negative-Path Decision

D11.49 adds the source-controlled negative-path decision for the current VPS
bridge/protocol path:

```text
docs/ibkr_market_data_vps_bridge_protocol_negative_path_decision.md
```

It records `VPS_BRIDGE_PROTOCOL_NEGATIVE_PATH_DECISION`, current validated
commit `3c49b5cdfcb1e135fcad10c4af7a8af9ce00ab32`, and D11.48 VPS validation
`68 passed in 1.85s`.

D11.49 carries forward the D11.48 negative evidence:
`openclaw_gateway_binary_on_path=false`,
`npm_global_openclaw_package_observed=true`,
`openclaw_gateway_service_found=false`,
`package_source_provenance_complete=false`,
`repo_reference_search_too_broad=true`, and
`protocol_semantics_proven=false`.

D11.49 records that the current VPS bridge/protocol path is not approved for
market-data proof. Ports `18789` and `18791` remain liveness-only/non-approved
endpoints. Port `7497` remains unavailable from the VPS proof context. No
current VPS endpoint can be used for D11 countable market-data proof.

D11.49 is a negative-path decision, not a new test plan. It records that the
immediate current path is closed to proof rerun and keeps
`current_vps_bridge_path_approved=false`,
`current_18789_endpoint_approved=false`,
`current_18791_endpoint_approved=false`,
`current_7497_endpoint_available=false`, `proof_rerun_authorized=false`,
`protocol_probe_authorized=false`, `endpoint_switch_authorized=false`,
`bridge_protocol_approved=false`, `provider_approval_evidence=false`,
`market_data_proof_evidence=false`, and `d11_completion_authority=false`.

Any future bridge revival requires a separate source-controlled plan with exact
binary/source provenance, exact protocol semantics, explicit non-mutating probe
boundary, explicit operator-output compression, and separate authorization
before any traffic.

D11.49 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`,
and opens no account, position, margin, buying-power, portfolio, order,
balance, execution, cleanup, flatten, sell, cancel, live-trading, package
capture, replay, scoring, candidate generation, timer, service, systemd,
runtime mutation, gateway mutation, strategy, risk, execution, proof rerun,
endpoint switch, or protocol-probe authority.

### D11.50 Post-VPS Negative-Path Routing Decision

D11.50 adds the source-controlled post-VPS routing decision:

```text
docs/ibkr_market_data_post_vps_negative_path_routing_decision.md
```

It records `POST_VPS_NEGATIVE_PATH_ROUTING_DECISION`, current validated commit
`ce132ae4334f2e9c315fbfdd9133affc1f070be5`, and D11.49 VPS validation
`69 passed in 1.75s`.

D11.50 carries forward the D11.49 result:
`VPS_BRIDGE_PROTOCOL_NEGATIVE_PATH_DECISION`,
`current_vps_bridge_path_approved=false`,
`current_18789_endpoint_approved=false`,
`current_18791_endpoint_approved=false`,
`current_7497_endpoint_available=false`, `proof_rerun_authorized=false`,
`protocol_probe_authorized=false`, `endpoint_switch_authorized=false`,
`bridge_protocol_approved=false`, `provider_approval_evidence=false`,
`market_data_proof_evidence=false`, and `d11_completion_authority=false`.

D11.50 records `vps_bridge_path_closed=true` and
`current_vps_endpoint_available_for_countable_proof=false`. Ports `18789` and
`18791` are not approved endpoints, `7497` remains unavailable from the VPS
proof context, and no current VPS endpoint can be used for D11 countable
market-data proof.

D11.50 sets `next_route=MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY` while keeping
`mac_local_market_test_authorized=false`, `vps_market_test_authorized=false`,
`proof_rerun_authorized=false`, `protocol_probe_authorized=false`, and
`endpoint_switch_authorized=false`. The immediate current step is
evidence/routing documentation, not proof execution.

Any future Mac-local market test requires a separately source-controlled
preflight gate with explicit date and session window, explicit TWS/manual
operator readiness boundary, explicit historical-market-data-only command,
explicit compact output handling, expected commit, clean worktree requirement,
and no account/order/execution authority.

D11.50 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`,
and opens no account, position, margin, buying-power, portfolio, order,
balance, execution, cleanup, flatten, sell, cancel, live-trading, package
capture, replay, scoring, candidate generation, timer, service, systemd,
runtime mutation, gateway mutation, strategy, risk, execution, proof rerun,
endpoint switch, protocol probe, or market-test authority.

### D11.51 Mac-Local IBKR Evidence-Review Prerequisite

D11.51 adds the source-controlled Mac-local evidence-review prerequisite:

```text
docs/ibkr_market_data_mac_local_evidence_review_prerequisite.md
```

It records `MAC_LOCAL_IBKR_EVIDENCE_REVIEW_PREREQUISITE`, current validated
commit `cf7e9bb0a62c1d6e94524b0f7597090fe80596c6`, and D11.50 VPS validation
`70 passed in 0.21s`.

D11.51 carries forward the D11.50 routing result:
`POST_VPS_NEGATIVE_PATH_ROUTING_DECISION`, `vps_bridge_path_closed=true`,
`current_vps_endpoint_available_for_countable_proof=false`,
`next_route=MAC_LOCAL_IBKR_EVIDENCE_REVIEW_ONLY`,
`mac_local_market_test_authorized=false`,
`vps_market_test_authorized=false`, `proof_rerun_authorized=false`,
`protocol_probe_authorized=false`, and `endpoint_switch_authorized=false`.

D11.51 records that the VPS bridge/protocol path remains closed, no current VPS
endpoint can be used for D11 countable market-data proof, and the only active
next route is Mac-local IBKR evidence review. It sets
`mac_local_evidence_review_authorized=true` while keeping
`mac_local_market_test_authorized=false`.

D11.51 authorizes documentation/evidence review only. It does not authorize
Mac-local market testing yet, TWS/Gateway connection commands, broker API
import/connect, proof rerun, protocol probing, endpoint switching, or
account/order/execution access.

Any future Mac-local market-test preflight must be separately source-controlled
and include exact future date, explicit regular-session window, explicit
diagnostic target at or after 7:00 AM Pacific / 10:00 AM Eastern, 6:55 AM
Pacific readiness-check boundary only, explicit expected source commit, clean
worktree requirement before and after, explicit TWS/manual operator readiness
boundary, historical-market-data-only command, explicit compact output handling,
no account/position/margin/buying-power/portfolio/order/balance/execution/
cleanup/flatten/sell/cancel/live-trading authority, and no package capture,
replay, scoring, candidate generation, strategy, risk, or execution authority.

D11.51 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`,
and opens no market-test authority, VPS proof authority, protocol-probe
authority, endpoint-switch authority, account/order/execution authority,
package capture, replay, scoring, candidate generation, timer/service/systemd
or runtime mutation, gateway mutation, strategy/risk/execution authority, D11
completion authority, or Unit 12 opening authority.

### D11.52 Official IBKR Endpoint Documentation Adjudication

D11.52 adds the source-controlled official IBKR endpoint documentation
adjudication:

```text
docs/ibkr_market_data_official_endpoint_documentation_adjudication.md
```

It records `OFFICIAL_IBKR_ENDPOINT_DOCUMENTATION_ADJUDICATION`, current
validated commit `79e5d354c1bba7b1b3b45d1b3ec8267c5a32e052`, and D11.51 VPS
validation `71 passed in 2.36s`.

D11.52 records the official IBKR documentation sources reviewed:
`https://interactivebrokers.github.io/tws-api/initial_setup.html`,
`https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/`, and
`https://ibkrcampus.com/campus/trading-lessons/accessing-the-tws-python-api-source-code/`.

D11.52 records `official_tws_api_transport=TCP_SOCKET`,
`official_tws_live_default_port=7496`, `official_tws_paper_default_port=7497`,
`official_gateway_live_default_port=4001`,
`official_gateway_paper_default_port=4002`, and
`configured_port_must_match_client_port=true`. The endpoint is not guessed; it
must match the configured TWS/Gateway socket port.

D11.52 keeps `mac_local_endpoint_selection_authorized=false`,
`mac_local_endpoint_inspection_authorized=false`,
`mac_local_market_test_authorized=false`, `vps_market_test_authorized=false`,
`proof_rerun_authorized=false`, `protocol_probe_authorized=false`, and
`endpoint_switch_authorized=false`. It does not authorize TWS/Gateway
connection commands or broker API import/connect.

Any future Mac-local endpoint-inspection gate must be separately
source-controlled and include exact expected source commit, clean worktree
requirement, explicit operator-readiness boundary, exact non-mutating inspection
commands only, no broker API import/connect, no market-data request, and no
account/order/execution authority.

Any future Mac-local market-test preflight must be separately source-controlled
and include exact future date, explicit regular-session window, explicit
diagnostic target at or after 7:00 AM Pacific / 10:00 AM Eastern, 6:55 AM
Pacific readiness-check boundary only, explicit expected source commit, clean
worktree requirement before and after, explicit TWS/manual operator readiness
boundary, historical-market-data-only command, explicit compact output handling,
no account/position/margin/buying-power/portfolio/order/balance/execution/
cleanup/flatten/sell/cancel/live-trading authority, and no package capture,
replay, scoring, candidate generation, strategy, risk, or execution authority.

D11.52 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`.

### D11.53 Mac-Local Endpoint Inspection Authorization

D11.53 adds the source-controlled Mac-local endpoint inspection authorization:

```text
docs/ibkr_market_data_mac_local_endpoint_inspection_authorization.md
```

It records `MAC_LOCAL_ENDPOINT_INSPECTION_AUTHORIZATION`, current validated
commit `6f50a0d1a795eed2ec69559c9b6ba61ed8875b18`, and D11.52 VPS validation
`72 passed in 1.76s`.

D11.53 carries forward D11.52 official endpoint adjudication:
`official_tws_live_default_port=7496`, `official_tws_paper_default_port=7497`,
`official_gateway_live_default_port=4001`,
`official_gateway_paper_default_port=4002`, and
`configured_port_must_match_client_port=true`. The endpoint is not guessed; it
must be observed locally and later matched to configured TWS/Gateway socket
settings.

D11.53 sets `mac_local_endpoint_inspection_authorized=true` with
`allowed_inspection_mode=LOCAL_LISTENER_INSPECTION_ONLY`. The future operator
inspection command must be compact and may inspect only local listening sockets
and process identity for `7496`, `7497`, `4001`, and `4002`.

D11.53 keeps `mac_local_endpoint_selection_authorized=false`,
`mac_local_market_test_authorized=false`, `vps_market_test_authorized=false`,
`proof_rerun_authorized=false`, `protocol_probe_authorized=false`, and
`endpoint_switch_authorized=false`. It keeps `broker_api_import_authorized=false`,
`broker_connect_authorized=false`, `market_data_request_authorized=false`, and
`account_order_execution_authority=false`.

D11.53 does not authorize sending traffic to any endpoint and does not authorize
`nc`, `curl`, `telnet`, `/dev/tcp`, Python socket connect, broker API connect,
or market-data requests. Any later endpoint selection must be separately
source-controlled after local listener evidence is reviewed.

Any later Mac-local market-test preflight must be separately source-controlled
and include exact future date, explicit regular-session window, explicit
diagnostic target at or after 7:00 AM Pacific / 10:00 AM Eastern, 6:55 AM
Pacific readiness-check boundary only, explicit expected source commit, clean
worktree requirement before and after, explicit TWS/manual operator readiness
boundary, historical-market-data-only command, explicit compact output handling,
no account/position/margin/buying-power/portfolio/order/balance/execution/
cleanup/flatten/sell/cancel/live-trading authority, and no package capture,
replay, scoring, candidate generation, strategy, risk, or execution authority.

D11.53 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`.

### D11.54 Mac-Local Endpoint Listener Evidence Adjudication

D11.54 adds the source-controlled Mac-local endpoint listener evidence
adjudication:

```text
docs/ibkr_market_data_mac_local_endpoint_listener_evidence_adjudication.md
```

It records `MAC_LOCAL_ENDPOINT_LISTENER_EVIDENCE_ADJUDICATION`,
`source_commit=62ce269f9105f38f6ac9bde69e4263a8a282491c`,
`source_commit_message=62ce269 Authorize D11 Mac-local endpoint inspection`,
and D11.53 VPS validation `73 passed in 2.28s`.

D11.54 records that the operator listener command was local-listener inspection
only. The compact filtered output showed `COMMAND=JavaAppli`, `PID=13194`,
`USER=openclawcontrol`, and `TCP *:7497 (LISTEN)`. Process identity evidence
showed
`/Users/openclawcontrol/Applications/Trader Workstation/Trader Workstation.app/Contents/MacOS/JavaApplicationStub`.

D11.54 records `observed_mac_local_tws_paper_listener=true`,
`observed_mac_local_tws_paper_port=7497`, and
`observed_mac_local_tws_process=Trader Workstation JavaApplicationStub`.
No listener was shown for official IBKR ports `7496`, `4001`, or `4002` in the
compact filtered output, so
`observed_mac_local_tws_live_listener=false`,
`observed_mac_local_gateway_live_listener=false`, and
`observed_mac_local_gateway_paper_listener=false`.

Port `7497` matches the official IBKR paper TWS default adjudicated in D11.52.
This resolves the prior endpoint ambiguity for Mac-local context only. It does
not retroactively make the VPS `127.0.0.1:7497` endpoint valid because
`127.0.0.1` on VPS and `127.0.0.1` on Mac are different process contexts. The
prior VPS failure remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

D11.54 records `candidate_mac_local_endpoint=127.0.0.1:7497` while preserving
`endpoint_selection_authorized=false`, `mac_local_market_test_authorized=false`,
`broker_api_import_authorized=false`, `broker_connect_authorized=false`,
`market_data_request_authorized=false`, and
`account_order_execution_authority=false`. Any future endpoint selection must
be separately source-controlled.

Any later Mac-local market-test preflight must be separately source-controlled
and include exact future date, explicit regular-session window, explicit
diagnostic target at or after 7:00 AM Pacific / 10:00 AM Eastern, 6:55 AM
Pacific readiness-check boundary only, explicit expected source commit, clean
worktree requirement before and after, explicit TWS/manual operator readiness
boundary, historical-market-data-only command, explicit compact output handling,
no account/position/margin/buying-power/portfolio/order/balance/execution/
cleanup/flatten/sell/cancel/live-trading authority, and no package capture,
replay, scoring, candidate generation, strategy, risk, or execution authority.

D11.54 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`.

### D11.55 Mac-Local Endpoint Selection Adjudication

D11.55 adds the source-controlled Mac-local endpoint selection adjudication:

```text
docs/ibkr_market_data_mac_local_endpoint_selection_adjudication.md
```

It records `MAC_LOCAL_ENDPOINT_SELECTION_ADJUDICATION`,
`source_commit=90545de3c6fcfb8ebacea282a751ae3305b78f26`, and D11.54 VPS
validation `74 passed in 2.24s`.

D11.55 carries forward D11.54 listener evidence:
`observed_mac_local_tws_paper_listener=true`,
`observed_mac_local_tws_paper_port=7497`,
`observed_mac_local_tws_process=Trader Workstation JavaApplicationStub`, and
`candidate_mac_local_endpoint=127.0.0.1:7497`.

D11.54 observed Trader Workstation JavaApplicationStub listening on
`TCP *:7497`, and `7497` matches the official IBKR paper TWS default
adjudicated in D11.52. D11.55 selects
`candidate_mac_local_endpoint=127.0.0.1:7497` as
`selected_mac_local_endpoint=127.0.0.1:7497` with
`selected_endpoint_context=LOCAL_MAC`, `selected_endpoint_type=TWS_PAPER`,
`selected_endpoint_port=7497`, and
`selected_endpoint_basis=D11.54 observed Mac-local TWS paper listener evidence`.

The selected endpoint is valid only for the `LOCAL_MAC` process context. It does
not validate VPS `127.0.0.1:7497`; the prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

D11.55 sets `endpoint_selection_authorized=true` while preserving
`mac_local_market_test_authorized=false`, `vps_market_test_authorized=false`,
`proof_rerun_authorized=false`, `protocol_probe_authorized=false`,
`endpoint_switch_authorized=false`, `broker_api_import_authorized=false`,
`broker_connect_authorized=false`, `market_data_request_authorized=false`, and
`account_order_execution_authority=false`.

Any later Mac-local market-test preflight must be separately source-controlled
and include exact future date, explicit regular-session window, explicit
diagnostic target at or after 7:00 AM Pacific / 10:00 AM Eastern, 6:55 AM
Pacific readiness-check boundary only, explicit expected source commit, clean
worktree requirement before and after, explicit TWS/manual operator readiness
boundary, historical-market-data-only command, explicit compact output handling,
no account/position/margin/buying-power/portfolio/order/balance/execution/
cleanup/flatten/sell/cancel/live-trading authority, and no package capture,
replay, scoring, candidate generation, strategy, risk, or execution authority.

D11.55 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`.

### D11.56 Mac-Local Historical Market-Data Test Preflight

D11.56 adds the source-controlled Mac-local historical market-data diagnostic
preflight:

```text
docs/ibkr_market_data_mac_local_historical_data_test_preflight.md
```

It records `MAC_LOCAL_HISTORICAL_MARKET_DATA_TEST_PREFLIGHT`,
`source_commit=d64ee84942533a4727df66b72c9e4175bb6713c1`, and D11.55 VPS
validation `75 passed in 2.07s`.

D11.56 carries forward `selected_mac_local_endpoint=127.0.0.1:7497`,
`selected_endpoint_context=LOCAL_MAC`, `selected_endpoint_type=TWS_PAPER`, and
`selected_endpoint_port=7497`. The endpoint remains valid only for the
`LOCAL_MAC` process context; it does not validate VPS `127.0.0.1:7497`, and the
prior VPS failure remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

D11.56 records `test_date=2026-06-26`,
`readiness_check_time_pacific=06:55`, `readiness_check_time_eastern=09:55`,
`diagnostic_not_before_pacific=07:00`, and
`diagnostic_not_before_eastern=10:00`. The `06:55` Pacific readiness check is
only a readiness boundary; the diagnostic must not use 6:30 AM Pacific / 9:30
AM Eastern as its diagnostic time.

D11.56 sets `mac_local_market_test_preflight_authorized=true` and
`mac_local_market_test_authorized_for_2026_06_26_after_0700_pacific=true` while
preserving `vps_market_test_authorized=false`, `proof_rerun_authorized=false`,
`protocol_probe_authorized=false`, `endpoint_switch_authorized=false`, and
`account_order_execution_authority=false`.

The future diagnostic is Mac-local only. VPS is only for source sync and tests,
not IBKR/TWS connectivity. TWS must be manually open and logged into paper mode
before the diagnostic. Source worktree must be clean before and after the
diagnostic.

D11.56 derives the future command from the existing accepted LOCAL_MAC
repeatability diagnostic pattern using `.venv-312/bin/python -m
tools.ops.ibkr_market_data_read_only_smoke` with
`--authorize-local-ibkr-read-only-smoke`, host `127.0.0.1`, port `7497`,
symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`, timeframe `15Min`,
`--requested-end 2026-06-26T14:00:00Z`, and `--lookback-minutes 120`.
The command starts with `cd /Users/openclawcontrol/Documents/openclaw-stocks`
and emits compact evidence between `SUMMARY_START` and `SUMMARY_END`.

The compact output requirement includes command used, source commit, clean
pre-worktree, clean post-worktree, dependency versions, endpoint host and port,
instruments, requested UTC window, latest candle timestamp per instrument,
pass/fail classification, and no account/order/execution fields. Expected
regular-session evidence behavior is that the latest returned candle should be
explainable by market-data freshness and 15-minute candle timing.

D11.56 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and `VPS_RUNTIME=NOT_TOUCHED`,
and opens no account, position, margin, buying-power, portfolio, balance, order,
execution, cleanup, flatten, sell, cancel, live-trading, package capture,
replay, scoring, candidate generation, strategy, risk, or execution authority.

### D11.57 Mac-Local Historical Diagnostic Evidence Adjudication

D11.57 adds the source-controlled Mac-local historical diagnostic evidence
adjudication:

```text
docs/ibkr_market_data_mac_local_historical_data_diagnostic_evidence_adjudication.md
```

It records
`MAC_LOCAL_HISTORICAL_MARKET_DATA_DIAGNOSTIC_EVIDENCE_ADJUDICATION`,
`source_commit=5fa8a8e221b79219c86eb3abcd67ad491692de21`, and D11.56 VPS
validation `76 passed in 2.49s`.

D11.57 adjudicates the D11.56 operator evidence for diagnostic date
`2026-06-26`: `authorized_utc=2026-06-26T14:00:00Z`,
`observed_run_utc=2026-06-26T14:00:26Z`, and
`diagnostic_window_guard=PASSED`. The run occurred after the authorized UTC
boundary and recorded `worktree_before=CLEAN` and `worktree_after=CLEAN`.

The evidence is accepted only as `LOCAL_MAC` historical market-data diagnostic
evidence. It records `selected_mac_local_endpoint=127.0.0.1:7497`,
`selected_endpoint_context=LOCAL_MAC`, `selected_endpoint_type=TWS_PAPER`,
`selected_endpoint_port=7497`, `observed_listener=TCP *:7497 (LISTEN)`, and
`observed_dependency_ib_insync=0.9.86`. It does not validate VPS
`127.0.0.1:7497`; the prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

D11.57 records symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`, timeframe
`15Min`, `requested_start_utc=2026-06-26T12:00:00+00:00`, and
`requested_end_utc=2026-06-26T14:00:00+00:00`. All five symbols returned
`d11_countable=true` and `freshness_classification=clean`. Latest candles and
lags were `AAPL=2026-06-26T13:30:00+00:00/30.0`,
`MSFT=2026-06-26T13:30:00+00:00/30.0`,
`NVDA=2026-06-26T13:45:00+00:00/15.0`,
`TSLA=2026-06-26T13:45:00+00:00/15.0`, and
`MSTR=2026-06-26T13:45:00+00:00/15.0`. Each symbol retained
`d11_primary_candidate_status=candidate`, `d11_primary_eligible=false`, and an
empty failure reason.

D11.57 sets `mac_local_historical_diagnostic_evidence=ACCEPTED` while
preserving `vps_market_test_authorized=false`,
`account_order_execution_authority=false`, and historical-market-data-only
scope. It grants no account, order, execution, package capture, replay,
scoring, candidate generation, strategy, risk, live-trading, VPS proof, VPS
market test, broker endpoint traffic, gateway mutation, runtime mutation, timer
mutation, service mutation, systemd mutation, D11 completion, Unit 12 opening,
or IBKR primary approval authority.

D11.57 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.

### D11.58 IBKR Primary Market-Data Eligibility Adjudication

D11.58 adds the source-controlled IBKR primary market-data eligibility
adjudication:

```text
docs/ibkr_market_data_primary_eligibility_adjudication.md
```

It records `IBKR_PRIMARY_MARKET_DATA_ELIGIBILITY_ADJUDICATION`,
`source_commit=4839f8ff3f09f746edcca3ab464a4771ae922f0d`, and D11.57 VPS
validation `77 passed in 3.05s and 77 passed in 0.25s`.

D11.58 accepts D11.57 as Mac-local historical diagnostic evidence:
`mac_local_historical_diagnostic_evidence=ACCEPTED`,
`all_symbols_d11_countable=true`, and
`all_symbols_freshness_classification=clean` for `AAPL`, `MSFT`, `NVDA`,
`TSLA`, and `MSTR`.

D11.58 fails closed on primary eligibility. Existing source-controlled criteria
do not clearly support IBKR primary approval because
`D11_PRIMARY_PROVIDER_SELECTION_CRITERIA` still requires
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`,
and D11.57 records only `LOCAL_MAC` evidence.

D11.58 records `selected_mac_local_endpoint=127.0.0.1:7497`,
`selected_endpoint_context=LOCAL_MAC`, `selected_endpoint_type=TWS_PAPER`,
`selected_endpoint_port=7497`, `endpoint_scope=LOCAL_MAC_ONLY`, and
`vps_127_0_0_1_7497_validated=false`. The prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

The unresolved criteria are the absent separate VPS read-only freshness proof,
the `LOCAL_MAC_ONLY` endpoint scope, the lack of VPS `127.0.0.1:7497`
validation, and the existing source provider candidate remaining broker-coupled
and not approved primary under `candidate_can_count_for_d11`.

D11.58 sets `ibkr_primary_eligibility=NOT_APPROVED`,
`d11_primary_eligibility_adjudication=BLOCKED_CRITERIA_UNRESOLVED`,
`d11_primary_candidate_status=candidate`, and `d11_status=D11_INSUFFICIENT`.
It preserves `unit_12_status=UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`,
`VPS_RUNTIME=NOT_TOUCHED`, and `account_order_execution_authority=false`.

D11.58 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof, VPS market test, broker
endpoint traffic, runtime mutation, timer mutation, service mutation, systemd
mutation, TWS mutation, Gateway mutation, Unit 12 opening, or live-trading
authority.

### D11.59 IBKR VPS Proof Requirement Route Adjudication

D11.59 adds the source-controlled route adjudication for the remaining IBKR
primary-eligibility blocker:

```text
docs/ibkr_market_data_vps_proof_requirement_route_adjudication.md
```

It records `IBKR_VPS_PROOF_REQUIREMENT_ROUTE_ADJUDICATION`,
`source_commit=874544fb1b860bf753d788f20bf3f143b027ff11`, D11.58 VPS
validation `78 passed in 2.39s`, and
`d11_58_result=BLOCKED_CRITERIA_UNRESOLVED`.

D11.59 keeps `ibkr_primary_eligibility=NOT_APPROVED`,
`d11_status=D11_INSUFFICIENT`, `unit_12_status=UNIT_12_BLOCKED`,
`PACKAGE_CAPTURE=BLOCKED`, `VPS_RUNTIME=NOT_TOUCHED`, and
`account_order_execution_authority=false`.

D11.59 records that D11.57 Mac-local evidence remains accepted:
`mac_local_historical_diagnostic_evidence=ACCEPTED`,
`all_symbols_d11_countable=true`, and
`all_symbols_freshness_classification=clean` for all five symbols.

The exact active rule remains
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility` in
`D11_PRIMARY_PROVIDER_SELECTION_CRITERIA`. D11.59 finds no existing
source-controlled rule that retires or narrows the requirement for the selected
`LOCAL_MAC_ONLY` architecture.

D11.59 records `selected_endpoint_context=LOCAL_MAC`,
`selected_endpoint_type=TWS_PAPER`,
`selected_mac_local_endpoint=127.0.0.1:7497`,
`endpoint_scope=LOCAL_MAC_ONLY`, and
`vps_127_0_0_1_7497_validated=false`. VPS `127.0.0.1:7497` must not be reused
as a proof target because `127.0.0.1` is process-context local, the previous
VPS proof failed from the VPS process context, and the prior failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

D11.59 sets
`vps_proof_requirement_route=REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED` and
`next_permissible_gate=D11.60_SOURCE_CONTROLLED_VPS_PROOF_SAFE_PREFLIGHT_OR_FORMAL_LOCAL_MAC_CRITERIA_REVISION`.
That future gate must either identify an explicitly validated VPS-accessible
endpoint that is not guessed and not `127.0.0.1:7497` unless observed listening
in the VPS process context and separately authorized, or formally revise the
source-controlled criteria to retire or narrow VPS proof for a
`LOCAL_MAC_ONLY` architecture.

D11.59 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, Unit 12 opening, or live-trading authority.

### D11.60 VPS Proof Safe Preflight Or LOCAL_MAC Criteria Revision

D11.60 adds the source-controlled decision artifact:

```text
docs/ibkr_market_data_vps_proof_safe_preflight_or_local_mac_criteria_revision.md
```

It records `IBKR_VPS_PROOF_SAFE_PREFLIGHT_OR_LOCAL_MAC_CRITERIA_REVISION`,
`source_commit=002602313f022ea2581cd7d30d3453aca9b4f50f`, D11.59 VPS
validation `79 passed in 2.77s`,
`d11_59_route=REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`, and
`d11_58_result=BLOCKED_CRITERIA_UNRESOLVED`.

D11.60 chooses Option C:
`d11_60_decision=BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION`.
It records `vps_proof_safe_target_status=NO_VALIDATED_TARGET` and
`local_mac_criteria_revision_status=NOT_SUPPORTED`.

D11.60 keeps `ibkr_primary_eligibility=NOT_APPROVED`,
`d11_status=D11_INSUFFICIENT`, `unit_12_status=UNIT_12_BLOCKED`,
`PACKAGE_CAPTURE=BLOCKED`, `VPS_RUNTIME=NOT_TOUCHED`, and
`account_order_execution_authority=false`.

D11.60 records that D11.57 Mac-local evidence remains accepted:
`mac_local_historical_diagnostic_evidence=ACCEPTED`,
`all_symbols_d11_countable=true`, and
`all_symbols_freshness_classification=clean` for all five symbols, with
`selected_endpoint_context=LOCAL_MAC`, `selected_endpoint_type=TWS_PAPER`,
`selected_mac_local_endpoint=127.0.0.1:7497`, and
`endpoint_scope=LOCAL_MAC_ONLY`.

The active rule remains
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility` in
`D11_PRIMARY_PROVIDER_SELECTION_CRITERIA`. D11.60 finds no validated
VPS-accessible proof target and no source-controlled basis to retire or narrow
that rule for `LOCAL_MAC_ONLY` evidence.

D11.60 records `vps_127_0_0_1_7497_validated=false`. VPS `127.0.0.1:7497`
must not be reused as a proof target because `127.0.0.1` is process-context
local, LOCAL_MAC `127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`,
and the prior VPS proof failed because VPS `127.0.0.1:7497` was not listening.
The prior failure remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue.

D11.60 records that `18789` and `18791` are not approved market-data endpoints
unless a separate source-controlled approval exists. Existing evidence
classifies them as liveness/provenance-only paths without approved
bridge/protocol semantics or market-data proof authority.

The next permissible gate is
`D11.61_SOURCE_CONTROLLED_VPS_ENDPOINT_EVIDENCE_OR_CRITERIA_REVISION_PREREQUISITE`.
That future gate may only create source-controlled prerequisite evidence for a
validated VPS-accessible endpoint or a formal criteria revision; it does not
authorize proof execution, endpoint inspection, protocol probing, broker
endpoint traffic, runtime mutation, Unit 12 opening, or IBKR primary approval.

D11.60 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, Unit 12 opening, or live-trading authority.

### D11.61 VPS Endpoint Evidence Or Criteria Revision Prerequisite

D11.61 adds the source-controlled prerequisite gate:

```text
docs/ibkr_market_data_vps_endpoint_evidence_or_criteria_revision_prerequisite.md
```

It records
`IBKR_VPS_ENDPOINT_EVIDENCE_OR_CRITERIA_REVISION_PREREQUISITE`,
`source_commit=fd2258ee6efaff23886914b519b971b2f58c15c9`, D11.60 VPS
validation `80 passed in 2.54s`,
`d11_60_decision=BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION`,
`d11_59_route=REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`, and
`d11_58_result=BLOCKED_CRITERIA_UNRESOLVED`.

D11.61 chooses `d11_61_decision=DUAL_PREREQUISITE_REQUIRED` with
`vps_endpoint_evidence_prerequisite=REQUIRED` and
`local_mac_criteria_revision_prerequisite=REQUIRED`. It keeps
`ibkr_primary_eligibility=NOT_APPROVED`, `d11_status=D11_INSUFFICIENT`,
`unit_12_status=UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`,
`VPS_RUNTIME=NOT_TOUCHED`, and `account_order_execution_authority=false`.

D11.61 records that D11.57 Mac-local evidence remains accepted:
`mac_local_historical_diagnostic_evidence=ACCEPTED`,
`all_symbols_d11_countable=true`, and
`all_symbols_freshness_classification=clean` for all five symbols, with
`selected_endpoint_context=LOCAL_MAC`, `selected_endpoint_type=TWS_PAPER`,
`selected_mac_local_endpoint=127.0.0.1:7497`, and
`endpoint_scope=LOCAL_MAC_ONLY`.

The active rule remains
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility` in
`D11_PRIMARY_PROVIDER_SELECTION_CRITERIA`. The accepted LOCAL_MAC evidence does
not validate VPS `127.0.0.1:7497`.

D11.61 records missing VPS-proof evidence: no validated VPS-accessible IBKR
market-data endpoint, VPS `127.0.0.1:7497` was not listening during the prior
proof, `18789` and `18791` are not approved IBKR market-data endpoints unless
separately approved by source-controlled criteria, and no source-controlled
proof exists that a VPS process can safely reach a broker market-data endpoint.

D11.61 records missing LOCAL_MAC criteria-revision evidence: no explicit
source-controlled rule yet states that `LOCAL_MAC_ONLY` accepted historical
evidence supersedes the separate VPS proof requirement, no committed criteria
revision packet exists, and no focused test yet proves the revision path
preserves fail-closed account/order/execution authority and Unit 12 blocking
unless separately opened.

D11.61 records that `127.0.0.1` is process-context local; LOCAL_MAC
`127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`; prior VPS failure
remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`; and that failure is not a
proven TWS issue or proven IB Gateway issue.

Future bounded VPS endpoint evidence collection requires a separate
source-controlled authorization gate before any endpoint inspection. It must be
non-mutating only, with no service/timer/runtime/systemd/TWS/Gateway/
openclaw-gateway/VPS mutation, no market-data request, no broker connection,
no protocol probe, no account/order/execution authority, compact output only,
and evidence identifying process context, listening endpoints, process names,
and whether each endpoint is approved or only observed.

Future formal LOCAL_MAC criteria revision requires a separate source-controlled
revision packet identifying the superseded rule, stating whether
`LOCAL_MAC_ONLY` architecture is intended for provider eligibility, proving no
account/order/execution expansion, preserving `UNIT_12_BLOCKED` unless later
opened, and adding focused boundary tests before any approval.

The exact next permissible gate is
`D11.62_SOURCE_CONTROLLED_PREREQUISITE_PATH_SELECTION_FOR_VPS_ENDPOINT_EVIDENCE_OR_LOCAL_MAC_CRITERIA_REVISION`.
D11.61 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, Unit 12 opening, or live-trading authority.

### D11.62 IBKR Prerequisite Path Selection

D11.62 adds the source-controlled path-selection packet:

```text
docs/ibkr_market_data_d11_62_prerequisite_path_selection.md
```

It records `IBKR_D11_PREREQUISITE_PATH_SELECTION`,
`source_commit=eb54ef6d8affb13ec8f6909208b0a8c1de729bde`, D11.61 VPS
validation `81 passed in 3.42s`,
`d11_61_decision=DUAL_PREREQUISITE_REQUIRED`,
`d11_60_decision=BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION`,
`d11_59_route=REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED`, and
`d11_58_result=BLOCKED_CRITERIA_UNRESOLVED`.

D11.62 selects
`d11_62_decision=LOCAL_MAC_CRITERIA_REVISION_PATH_SELECTED` with
`vps_endpoint_evidence_path=NOT_SELECTED` and
`local_mac_criteria_revision_path=SELECTED`. The exact next permissible gate is
`D11.63_FORMAL_LOCAL_MAC_ONLY_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REVISION`.

D11.62 keeps `ibkr_primary_eligibility=NOT_APPROVED`,
`d11_status=D11_INSUFFICIENT`, `unit_12_status=UNIT_12_BLOCKED`,
`PACKAGE_CAPTURE=BLOCKED`, `VPS_RUNTIME=NOT_TOUCHED`, and
`account_order_execution_authority=false`.

D11.62 records that D11.57 Mac-local evidence remains accepted:
`mac_local_historical_diagnostic_evidence=ACCEPTED`,
`all_symbols_d11_countable=true`, and
`all_symbols_freshness_classification=clean` for all five symbols, with
`selected_endpoint_context=LOCAL_MAC`, `selected_endpoint_type=TWS_PAPER`,
`selected_mac_local_endpoint=127.0.0.1:7497`, and
`endpoint_scope=LOCAL_MAC_ONLY`.

The active rule remains
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility` in
`D11_PRIMARY_PROVIDER_SELECTION_CRITERIA`. D11.62 selects the LOCAL_MAC
criteria-revision path because the selected architecture is `LOCAL_MAC_ONLY`,
accepted IBKR historical diagnostic evidence already exists from `LOCAL_MAC`,
and a formal criteria revision can evaluate whether that evidence supersedes,
narrows, or replaces the separate VPS proof requirement without broker traffic,
runtime mutation, account/order/execution authority, or inventing a VPS
endpoint.

D11.62 does not select VPS endpoint evidence because there is no validated
VPS-accessible IBKR market-data endpoint, VPS `127.0.0.1:7497` was not
listening during the prior failed proof, and `18789` and `18791` are not
approved IBKR market-data endpoints unless separately approved by
source-controlled criteria.

D11.62 records that `127.0.0.1` is process-context local, LOCAL_MAC
`127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`,
`vps_127_0_0_1_7497_validated=false`, and the prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue or
proven IB Gateway issue. No future VPS proof may target `127.0.0.1:7497`
unless that endpoint is observed listening in the VPS process context and
separately authorized. No future proof may target `18789` or `18791` as
market-data endpoints unless source-controlled evidence explicitly approves
them.

D11.63 must be a formal criteria revision gate that evaluates whether
`LOCAL_MAC_ONLY` accepted historical diagnostic evidence can supersede, narrow,
or replace
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`.
It must preserve no account/order/execution authority, preserve Unit 12 blocked
unless separately opened, add focused boundary tests before any approval, and
must not run broker traffic, endpoint inspection, market testing, VPS proof,
protocol probing, or runtime mutation.

D11.62 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, Unit 12 opening, or live-trading authority.

### D11.63 Formal LOCAL_MAC-Only IBKR Criteria Revision

D11.63 adds the source-controlled criteria-revision adjudication:

```text
docs/ibkr_market_data_d11_63_formal_local_mac_only_criteria_revision.md
```

It records `IBKR_D11_LOCAL_MAC_ONLY_CRITERIA_REVISION_ADJUDICATION`,
`source_commit=94fdbbe93ff4b9d4b46018a3a9cef211dd142049`,
`d11_62_decision=LOCAL_MAC_CRITERIA_REVISION_PATH_SELECTED`, and
`d11_62_next_gate=D11.63_FORMAL_LOCAL_MAC_ONLY_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REVISION`.

D11.63 fails closed:
`d11_63_decision=BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE`,
`criteria_revision_result=NOT_APPROVED`,
`primary_eligibility_revision=NOT_REVISED`, and
`separate_vps_proof_rule_revision=NOT_REVISED`.

D11.63 keeps `ibkr_primary_eligibility=NOT_APPROVED`,
`d11_status=D11_INSUFFICIENT`, `unit_12_status=UNIT_12_BLOCKED`,
`PACKAGE_CAPTURE=BLOCKED`, `VPS_RUNTIME=NOT_TOUCHED`, and
`account_order_execution_authority=false`.

D11.63 records that D11.57 LOCAL_MAC historical evidence remains accepted:
`mac_local_historical_diagnostic_evidence=ACCEPTED`,
`all_symbols_d11_countable=true`, and
`all_symbols_freshness_classification=clean`, with
`selected_endpoint_context=LOCAL_MAC`, `selected_endpoint_type=TWS_PAPER`,
`selected_mac_local_endpoint=127.0.0.1:7497`, and
`endpoint_scope=LOCAL_MAC_ONLY`.

D11.63 distinguishes historical data availability evidence from endpoint
locality evidence, provider primary eligibility, runtime deployment
eligibility, broker submit readiness, and live trading readiness. The accepted
LOCAL_MAC evidence supports only historical data availability through a local
TWS paper endpoint for the diagnostic window.

D11.63 does not revise
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`.
The inspected provider-selection source still requires
`candidate_can_count_for_d11`, and `ibkr_market_data_candidate` remains
`d11_primary_candidate_status=candidate`, `d11_primary_eligible=false`,
`broker_coupled=true`, `order_authority=false`, and
`execution_authority=false`.

D11.63 records that `127.0.0.1` is process-context local, LOCAL_MAC
`127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`,
`vps_127_0_0_1_7497_validated=false`, and the prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, not a proven TWS issue or
proven IB Gateway issue. `18789` and `18791` remain not approved market-data
endpoints unless separately approved by source-controlled criteria.

D11.63 preserves separation between LOCAL_MAC evidence and VPS production or
runtime eligibility. It also preserves separation between market-data
availability, broker submit readiness, and live trading readiness.

The exact next permissible gate is
`D11.64_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_BLOCKER_RESOLUTION_PLAN`.
That future gate may plan source-controlled blocker resolution only; it must not
imply broker/TWS/API/runtime/network/service/scheduler/systemd/credential/VPS
actions, market-session diagnostics, package capture, replay, scoring,
candidate generation, strategy/risk/execution behavior changes,
provider-selection runtime behavior changes, account/order/execution
authority, Unit 12 opening, broker submit readiness, or live trading readiness.

D11.63 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, scheduler mutation, credential access, Unit 12
opening, broker submit readiness, or live-trading authority.

### D11.64 IBKR Primary Eligibility Blocker Resolution Plan

D11.64 adds the source-controlled blocker-resolution plan:

```text
docs/ibkr_market_data_d11_64_primary_eligibility_blocker_resolution_plan.md
```

It records `IBKR_D11_PRIMARY_ELIGIBILITY_BLOCKER_RESOLUTION_PLAN`,
`source_commit=ac78409fa0c81c97f2a357671cbc55fd55988f4b`,
`d11_63_decision=BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE`,
`criteria_revision_result=NOT_APPROVED`,
`primary_eligibility_revision=NOT_REVISED`, and
`separate_vps_proof_rule_revision=NOT_REVISED`.

D11.64 records
`d11_64_decision=BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED`. It keeps
`ibkr_primary_eligibility=NOT_APPROVED`, `d11_status=D11_INSUFFICIENT`,
`unit_12_status=UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`,
`VPS_RUNTIME=NOT_TOUCHED`, and `account_order_execution_authority=false`.

D11.64 records that D11.57 LOCAL_MAC historical evidence remains accepted:
`mac_local_historical_diagnostic_evidence=ACCEPTED`,
`all_symbols_d11_countable=true`, and
`all_symbols_freshness_classification=clean`, with
`selected_endpoint_context=LOCAL_MAC`, `selected_endpoint_type=TWS_PAPER`,
`selected_mac_local_endpoint=127.0.0.1:7497`, and
`endpoint_scope=LOCAL_MAC_ONLY`.

D11.64 identifies the missing evidence classes before any future IBKR primary
eligibility reconsideration: historical data availability governance mapping,
endpoint locality governance mapping, broker-coupling resolution,
provider-primary eligibility evidence satisfying `candidate_can_count_for_d11`,
VPS production/runtime eligibility evidence, broker submit readiness evidence,
and live trading readiness evidence.

D11.64 separates governance/documentation blockers from future runtime, broker,
VPS, or market-session evidence blockers. Governance blockers include the lack
of an adopted criteria rule mapping LOCAL_MAC historical evidence to primary
eligibility reconsideration and the lack of a source-controlled
evidence-requirements packet. Future evidence blockers include absent VPS
production/runtime eligibility, absent broker submit readiness, and absent live
trading readiness; D11.64 does not capture that evidence and does not create
commands for it.

D11.64 preserves the localhost and endpoint boundaries:
`127.0.0.1` is process-context local, LOCAL_MAC `127.0.0.1:7497` is not
equivalent to VPS `127.0.0.1:7497`, `vps_127_0_0_1_7497_validated=false`, the
prior VPS failure remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, and `18789` and `18791`
remain not approved market-data endpoints unless separately approved by
source-controlled criteria.

The exact next permissible gate is
`D11.65_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE`.
That gate must be a narrowly scoped source-controlled evidence-requirements
prerequisite. It is not runtime activation, broker activation, Unit 12 opening,
or IBKR primary eligibility approval.

D11.64 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, scheduler mutation, credential access, Unit 12
opening, broker submit readiness, live-trading readiness, or IBKR primary
eligibility approval.

### D11.65 IBKR Primary Eligibility Evidence Requirements Prerequisite

D11.65 adds the source-controlled evidence-requirements prerequisite:

```text
docs/ibkr_market_data_d11_65_primary_eligibility_evidence_requirements_prerequisite.md
```

It records `IBKR_D11_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE`,
`source_commit=cee9f5237e2ff220d4230fabd1d905be90e79b9a`,
`d11_64_decision=BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED`,
`d11_63_decision=BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE`,
`criteria_revision_result=NOT_APPROVED`,
`primary_eligibility_revision=NOT_REVISED`, and
`separate_vps_proof_rule_revision=NOT_REVISED`.

D11.65 records
`d11_65_decision=EVIDENCE_REQUIREMENTS_PREREQUISITE_RECORDED_FAIL_CLOSED`,
`evidence_collected=false`,
`runtime_broker_vps_scheduler_systemd_credential_action=false`, and
`production_provider_selection_behavior_changed=false`. It keeps
`ibkr_primary_eligibility=NOT_APPROVED`, `d11_status=D11_INSUFFICIENT`,
`unit_12_status=UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`,
`VPS_RUNTIME=NOT_TOUCHED`, and `account_order_execution_authority=false`.

D11.65 converts the D11.64 blockers into explicit auditable evidence
requirements for historical data availability evidence, endpoint locality
evidence, VPS production/runtime reachability evidence, broker-coupling
evidence, provider primary-eligibility evidence, `candidate_can_count_for_d11`
evidence, broker submit readiness evidence, live trading readiness evidence,
and Unit 12 opening prerequisites.

D11.65 records already-satisfied evidence: D11.57 accepted LOCAL_MAC
historical diagnostic evidence, all five symbols were clean/countable, and the
selected endpoint was LOCAL_MAC `127.0.0.1:7497` / `TWS_PAPER` with
`endpoint_scope=LOCAL_MAC_ONLY`. This evidence remains historical data
availability and endpoint locality evidence only.

D11.65 records still-missing evidence: source-controlled governance mapping
from historical data availability to any allowable primary-eligibility evidence
bundle, source-controlled endpoint locality rule for `LOCAL_MAC_ONLY` evidence,
source-controlled broker-coupling adjudication for `broker_coupled=true`,
source-controlled provider primary-eligibility evidence for changing
candidate-only status, proof that `candidate_can_count_for_d11` is satisfied or
has been explicitly revised, VPS production/runtime reachability evidence if a
future path keeps a VPS requirement, and separate future authorization for any
broker/TWS evidence if later required.

D11.65 records fail-closed disqualifiers: approving from lane name, option
order, prior assistant expectation, or user framing; treating historical data
availability as provider primary eligibility; treating LOCAL_MAC
`127.0.0.1:7497` as VPS `127.0.0.1:7497`; treating `18789` or `18791` as
approved market-data endpoints without separate source-controlled approval;
implying broker submit readiness or live trading readiness from market-data
evidence; modifying production provider-selection behavior; or collecting new
runtime, broker, TWS, VPS, scheduler, systemd, credential, package-capture,
replay, scoring, candidate-generation, or live-trading evidence inside this
gate.

The exact next permissible gate is
`D11.66_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN`.
That gate may authorize only a source-controlled read-only evidence
authorization plan. It must not activate runtime, activate broker systems, open
Unit 12, approve IBKR primary eligibility, imply broker submit readiness, imply
live trading readiness, or create operational commands for broker, TWS,
runtime, VPS, scheduler, systemd, credentials, package capture, replay,
scoring, candidate generation, or live trading.

D11.65 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, scheduler mutation, credential access, Unit 12
opening, broker submit readiness, live-trading readiness, or IBKR primary
eligibility approval.

### D11.66 IBKR Primary Eligibility Read-Only Evidence Authorization Plan

D11.66 adds the source-controlled read-only evidence authorization plan:

```text
docs/ibkr_market_data_d11_66_read_only_evidence_authorization_plan.md
```

It records
`IBKR_D11_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN`,
`source_commit=3e66732e4cfbcb454fb72d9036bcb1921c0b24b2`,
`d11_65_classification=IBKR_D11_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE`,
`d11_65_decision=EVIDENCE_REQUIREMENTS_PREREQUISITE_RECORDED_FAIL_CLOSED`,
`d11_64_decision=BLOCKER_RESOLUTION_PLAN_RECORDED_FAIL_CLOSED`, and
`d11_63_decision=BLOCKED_INSUFFICIENT_PRIMARY_ELIGIBILITY_EVIDENCE`.

D11.66 records
`d11_66_decision=READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN_RECORDED_FAIL_CLOSED`,
`evidence_collected=false`,
`actual_read_only_evidence_capture_authorized=false`,
`runtime_broker_vps_scheduler_systemd_credential_action=false`,
`executable_evidence_capture_commands_created=false`, and
`production_provider_selection_behavior_changed=false`. It keeps
`ibkr_primary_eligibility=NOT_APPROVED`, `d11_status=D11_INSUFFICIENT`,
`unit_12_status=UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`,
`VPS_RUNTIME=NOT_TOUCHED`, and `account_order_execution_authority=false`.

D11.66 converts the D11.65 evidence requirements into authorization boundaries
for already satisfied source-controlled records, future documentation/test
adjudication, future LOCAL_MAC read-only evidence authorization, future VPS
read-only evidence authorization, future broker/TWS read-only evidence
authorization, and categories explicitly out of scope for D11 primary
eligibility.

D11.66 records already-satisfied evidence: D11.57 accepted LOCAL_MAC
historical diagnostic evidence, all five symbols were clean/countable, and the
selected endpoint was LOCAL_MAC `127.0.0.1:7497` / `TWS_PAPER` with
`endpoint_scope=LOCAL_MAC_ONLY`. This remains historical data availability and
endpoint locality evidence only.

D11.66 records still-missing evidence: source-controlled governance mapping
from historical data availability to any allowable primary-eligibility evidence
bundle, endpoint locality rule for `LOCAL_MAC_ONLY` evidence,
broker-coupling adjudication for `broker_coupled=true`, provider
primary-eligibility evidence for changing candidate-only status, proof that
`candidate_can_count_for_d11` is satisfied or explicitly revised, and future
LOCAL_MAC, VPS, or broker/TWS read-only evidence authorization design if later
required.

D11.66 records authorization preconditions: a later gate must define the exact
evidence requirement, source context, allowed fields, forbidden fields,
read-only authority boundary, process-context boundary, endpoint approval
status, no-account/order/execution boundary, no-credential-disclosure boundary,
no-runtime/service/scheduler/systemd mutation boundary, adjudication criteria,
and fail-closed result before any future read-only evidence capture could be
authorized.

D11.66 records authorization disqualifiers: executable commands in the
authorization-plan gate, implied evidence collection, unsafe VPS localhost
targets, treating LOCAL_MAC and VPS localhost as equivalent, treating `18789`
or `18791` as approved without separate source-controlled approval,
account/order/execution or submit/live readiness authority, runtime/service/
scheduler/systemd/credential mutation, production provider-selection behavior
changes, or implied IBKR primary approval, D11 sufficiency, or Unit 12 opening.

The exact next permissible gate is
`D11.67_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN`. That gate may
create only a source-controlled read-only evidence preflight design. It must
not execute evidence capture, activate runtime, activate broker systems, open
Unit 12, approve IBKR primary eligibility, imply broker submit readiness,
imply live trading readiness, or create executable commands for broker, TWS,
runtime, VPS, scheduler, systemd, credentials, package capture, replay,
scoring, candidate generation, or live trading.

D11.66 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, scheduler mutation, credential access, Unit 12
opening, broker submit readiness, live-trading readiness, actual read-only
evidence capture, or IBKR primary eligibility approval.

### D11.67 Read-Only Evidence Preflight Design

D11.67 adds the source-controlled read-only evidence preflight design:

```text
docs/ibkr_market_data_d11_67_read_only_evidence_preflight_design.md
```

It records `IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN`,
`source_commit=fbef77a96eac9e7552ac739250113e328225c579`,
`d11_66_classification=IBKR_D11_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN`,
`d11_66_decision=READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN_RECORDED_FAIL_CLOSED`,
`d11_65_classification=IBKR_D11_PRIMARY_ELIGIBILITY_EVIDENCE_REQUIREMENTS_PREREQUISITE`,
and `d11_65_decision=EVIDENCE_REQUIREMENTS_PREREQUISITE_RECORDED_FAIL_CLOSED`.

D11.67 records
`d11_67_decision=READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_RECORDED_FAIL_CLOSED`,
`evidence_collected=false`, `evidence_collection_authorized=false`,
`executable_evidence_capture_commands_created=false`,
`runtime_broker_vps_scheduler_systemd_credential_action=false`, and
`production_provider_selection_behavior_changed=false`. It keeps
`ibkr_primary_eligibility=NOT_APPROVED`, `d11_status=D11_INSUFFICIENT`,
`unit_12_status=UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`,
`VPS_RUNTIME=NOT_TOUCHED`, and `account_order_execution_authority=false`.

D11.67 defines design-only lanes for LOCAL_MAC read-only evidence, VPS
read-only evidence, broker/TWS read-only evidence, source-controlled
documentation/test adjudication, evidence collection, evidence adjudication,
provider primary eligibility, runtime deployment eligibility, broker submit
readiness, live trading readiness, and Unit 12 opening. It records that
evidence collection and evidence adjudication are not performed or authorized
by D11.67.

D11.67 allows only design-form evidence classes: historical data availability,
endpoint locality, documentation/test adjudication, LOCAL_MAC read-only
evidence shape, VPS read-only evidence shape, broker/TWS read-only evidence
shape, broker-coupling adjudication criteria, provider primary-eligibility
criteria, and `candidate_can_count_for_d11` criteria satisfaction or revision
criteria.

D11.67 forbids account/order/execution, submit, cleanup, broker submit
readiness, live trading readiness, credentials, package capture, runtime
reports, diagnostic reports, replay, scoring, candidate generation,
market-session diagnostics, broker/TWS/API/runtime/network/service/scheduler/
systemd/credential/VPS actions, behavior mutation, and executable
evidence-capture commands.

D11.67 records preflight safety checks required for a later gate: exact
evidence requirement, source context, allowed and forbidden fields, allowed and
forbidden process context, endpoint approval status, localhost
process-context treatment, no account/order/execution authority, no credential
disclosure, no submit or live readiness, no runtime/service/scheduler/systemd
mutation, no package capture/replay/scoring/candidate generation, timing
expectations if applicable, non-executable artifact format, adjudication
criteria, and fail-closed result.

D11.67 preserves the locality and broker-coupling blockers. LOCAL_MAC
`127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`,
`vps_127_0_0_1_7497_validated=false`, prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`, `18789` and `18791` remain
not approved market-data endpoints unless separately approved, and
`ibkr_market_data_candidate` remains `broker_coupled=true`,
`d11_primary_eligible=false`, and `d11_primary_candidate_status=candidate`.

The exact next permissible gate is
`D11.68_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_REVIEW`. That
gate may only review this source-controlled preflight design. It must not be
runtime activation, broker activation, submit readiness, live trading, package
capture, replay, scoring, candidate generation, actual evidence execution, or
IBKR primary eligibility approval.

D11.67 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, scheduler mutation, credential access, Unit 12
opening, broker submit readiness, live-trading readiness, evidence collection,
executable evidence-capture commands, or IBKR primary eligibility approval.

### D11.68 Read-Only Evidence Preflight Design Review

D11.68 adds the source-controlled read-only evidence preflight design review:

```text
docs/ibkr_market_data_d11_68_read_only_evidence_preflight_design_review.md
```

It records `IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_REVIEW`,
`source_commit=469fe863578693cf01171198a66a0fcd2204e37f`,
`d11_67_classification=IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN`,
`d11_67_decision=READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_RECORDED_FAIL_CLOSED`,
`d11_66_classification=IBKR_D11_PRIMARY_ELIGIBILITY_READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN`,
and `d11_66_decision=READ_ONLY_EVIDENCE_AUTHORIZATION_PLAN_RECORDED_FAIL_CLOSED`.

D11.68 records
`d11_68_decision=READ_ONLY_EVIDENCE_CAPTURE_BLOCKED_WITH_CONCRETE_BLOCKER`,
`minimum_future_evidence_capture_target_set=NOT_SELECTED_BLOCKED`,
`concrete_blocker_status=PRESENT`, `evidence_collected=false`,
`evidence_collection_authorized=false`,
`executable_evidence_capture_commands_created=false`,
`runtime_broker_vps_scheduler_systemd_credential_action=false`, and
`production_provider_selection_behavior_changed=false`. It keeps
`ibkr_primary_eligibility=NOT_APPROVED`, `d11_status=D11_INSUFFICIENT`,
`unit_12_status=UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`,
`VPS_RUNTIME=NOT_TOUCHED`, and `account_order_execution_authority=false`.

D11.68 forces exactly one of the two permitted review outcomes and selects
`READ_ONLY_EVIDENCE_CAPTURE_BLOCKED_WITH_CONCRETE_BLOCKER`. It does not select
`READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_READY` because D11.67 defines
design lanes and fail-closed checks but does not select an exact minimum future
evidence-capture target set, single source context, allowed fields, forbidden
fields, endpoint/process context, or adjudication artifact contract.

D11.68 reviews the D11.67 dimensions for LOCAL_MAC read-only evidence, VPS
read-only evidence, broker/TWS read-only evidence, documentation/test
adjudication, evidence collection, evidence adjudication, provider primary
eligibility, runtime deployment eligibility, broker submit readiness, live
trading readiness, and Unit 12 opening. It records that the boundaries exist
but are not authorization-ready.

D11.68 records concrete blockers: no exact target set, no selected source
context, no per-target allowed or forbidden fields, no non-executable artifact
contract, no approved endpoint or process context for future capture, VPS
`127.0.0.1:7497` remains unvalidated, `18789` and `18791` remain unapproved
market-data endpoints unless separately approved, `ibkr_market_data_candidate`
remains `broker_coupled=true`, `d11_primary_eligible=false`, and
`d11_primary_candidate_status=candidate`, and `candidate_can_count_for_d11`
remains unsatisfied.

D11.68 preserves the LOCAL_MAC/VPS locality distinction. LOCAL_MAC
`127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`,
`vps_127_0_0_1_7497_validated=false`, and prior VPS failure remains
`VPS_LOCALHOST_CONTEXT_MISMATCH` /
`AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`.

The exact next permissible gate is
`D11.69_SOURCE_CONTROLLED_READ_ONLY_EVIDENCE_CAPTURE_BLOCKER_REMEDIATION`.
That gate may only remediate the concrete source-controlled blockers listed by
D11.68 or remain fail-closed. It must not be runtime activation, broker
activation, submit readiness, live trading, package capture, replay, scoring,
candidate generation, actual evidence execution, or IBKR primary eligibility
approval.

D11.68 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, scheduler mutation, credential access, Unit 12
opening, broker submit readiness, live-trading readiness, evidence collection,
executable evidence-capture commands, or IBKR primary eligibility approval.

### D11.69 Read-Only Evidence Capture Blocker Remediation

D11.69 adds the source-controlled read-only evidence capture blocker
remediation packet:

```text
docs/ibkr_market_data_d11_69_read_only_evidence_capture_blocker_remediation.md
```

It records `IBKR_D11_READ_ONLY_EVIDENCE_CAPTURE_BLOCKER_REMEDIATION`,
`source_commit=9d59af162232bbf0d54dd95d4c55b4dfc475fb57`,
`d11_68_classification=IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN_REVIEW`,
`d11_68_decision=READ_ONLY_EVIDENCE_CAPTURE_BLOCKED_WITH_CONCRETE_BLOCKER`,
and `d11_67_classification=IBKR_D11_READ_ONLY_EVIDENCE_PREFLIGHT_DESIGN`.

D11.69 records
`d11_69_decision=READ_ONLY_EVIDENCE_CAPTURE_CONTRACT_READY`,
`selected_future_source_context=LOCAL_MAC_ONLY_DIRECT_MAC_TERMINAL_127_0_0_1_7497`,
`future_vps_endpoint_reliance=false`,
`future_18789_18791_reliance=false`, `future_bridge_tunnel_reliance=false`,
`evidence_collected=false`, `evidence_collection_authorized=false`,
`executable_evidence_capture_commands_created=false`,
`runtime_broker_vps_scheduler_systemd_credential_action=false`,
`production_provider_selection_behavior_changed=false`,
`remaining_capture_contract_blockers=NONE`, and
`remaining_provider_eligibility_blockers=broker_coupled_candidate_unresolved;
candidate_can_count_for_d11_unsatisfied`. It keeps
`ibkr_primary_eligibility=NOT_APPROVED`, `d11_status=D11_INSUFFICIENT`,
`unit_12_status=UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`,
`VPS_RUNTIME=NOT_TOUCHED`, and `account_order_execution_authority=false`.

D11.69 remediates each D11.68 capture-contract blocker by selecting the first
future evidence context as `LOCAL_MAC_ONLY`, `DIRECT_MAC_TERMINAL`, LOCAL_MAC
process context only, IBKR Paper TWS/Gateway local socket candidate, endpoint
candidate `127.0.0.1:7497`, no VPS endpoint reliance, no `18789`/`18791`
reliance, and no bridge, tunnel, or proxy reliance.

D11.69 defines the exact future evidence target set as market-data/provider-
readiness evidence only: LOCAL_MAC process-context endpoint identity, read-only
socket configuration evidence, API connection mode evidence, historical bars
availability for `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`, `15Min`, `120
minutes`, response metadata needed for adjudication, and negative evidence
that no account/order/execution/submit authority was requested or used.

D11.69 records allowed fields for each target: source context, operator
surface, process context, endpoint host/port/type candidate, localhost
process-context statement, no VPS equivalence, read-only socket scope,
market-data-only scope, mutation flags fixed false, API connection mode,
paper-mode candidate, historical request window, bar count, latest candle
timestamp, freshness classification, provider/feed metadata, redacted warnings
or errors, PASS/FAIL markers, adjudication summary, and negative authority
markers.

D11.69 records forbidden fields: account IDs, balances, buying power, margin,
portfolio contents, positions, open orders, executions, trade history, P&L,
order IDs, credentials, tokens, session secrets, submit/cancel/modify
endpoints, live trading status changes, service/systemd/scheduler mutations,
environment changes, VPS runtime mutation, VPS `127.0.0.1:7497`, `18789`,
`18791`, bridge/tunnel/proxy endpoints, package capture, replay, scoring,
candidate generation, strategy, risk, execution behavior, and Unit 12 opening.

D11.69 defines a non-executable artifact contract with artifact identity,
operator context, source-control references, target results, required
redactions, prohibited-fields attestation, negative-authority attestation,
locality attestation, and adjudication summary sections. It requires
PASS/FAIL markers for LOCAL_MAC context, endpoint candidate scope, read-only
socket scope, historical bars scope, forbidden-fields absence, negative
authority, and adjudication readiness. Any missing marker, prohibited field,
VPS field, `18789`/`18791` market-data endpoint field, bridge/tunnel field,
runtime mutation field, or executable command forces fail-closed adjudication.

D11.69 preserves the provider-eligibility blockers as later adjudication
blockers only: `ibkr_market_data_candidate` remains `broker_coupled=true`,
`d11_primary_eligible=false`, `d11_primary_candidate_status=candidate`, and
`candidate_can_count_for_d11` remains unsatisfied. These blockers do not block
the LOCAL_MAC-only evidence-capture contract because the contract forbids
account/order/execution authority and does not approve eligibility.

D11.69 preserves the LOCAL_MAC/VPS locality distinction. LOCAL_MAC
`127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`; D11.69 rejects VPS
`127.0.0.1:7497` evidence unless separately authorized and validated later;
D11.69 rejects `18789` and `18791` as approved market-data endpoints unless a
later source-controlled endpoint adjudication approves them.

The exact next permissible gate is
`D11.70_SOURCE_CONTROLLED_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`.
D11.70 may authorize a bounded future LOCAL_MAC-only read-only evidence capture
if it preserves the D11.69 contract and remains source controlled. D11.69
itself does not authorize capture.

D11.69 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, scheduler mutation, credential access, Unit 12
opening, broker submit readiness, live-trading readiness, evidence collection,
executable evidence-capture commands, or IBKR primary eligibility approval.

### D11.70 LOCAL_MAC Read-Only Evidence Capture Authorization Packet

D11.70 adds the source-controlled LOCAL_MAC read-only evidence capture
authorization packet:

```text
docs/ibkr_market_data_d11_70_local_mac_read_only_evidence_capture_authorization_packet.md
```

It records `IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`,
`source_commit=36342c53ef9ae0fc026c8588511d4a9c8d05f90f`,
`d11_69_classification=IBKR_D11_READ_ONLY_EVIDENCE_CAPTURE_BLOCKER_REMEDIATION`,
`d11_69_decision=READ_ONLY_EVIDENCE_CAPTURE_CONTRACT_READY`, and
`d11_70_decision=LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_NEXT_GATE`.

D11.70 authorizes only a future
`D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET`. It records
`d11_70_evidence_collected=false`,
`d11_70_executable_evidence_capture_commands_created=false`,
`runtime_broker_vps_scheduler_systemd_credential_action=false`,
`production_provider_selection_behavior_changed=false`,
`ibkr_primary_eligibility=NOT_APPROVED`, `d11_status=D11_INSUFFICIENT`,
`unit_12_status=UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`,
`VPS_RUNTIME=NOT_TOUCHED`, `account_order_execution_authority=false`,
`broker_submit_readiness=NOT_APPROVED`, and
`live_trading_readiness=NOT_APPROVED`.

D11.70 records satisfied preconditions: D11.68 forced a concrete blocker
review, D11.69 remediated capture-contract blockers, the exact source context
exists, the exact target set exists, allowed and forbidden field boundaries
exist, and provider eligibility remains closed. No source-controlled
contradiction was found that blocks a later D11.71 LOCAL_MAC-only read-only
evidence capture execution packet.

D11.70 authorizes the future source context only as `LOCAL_MAC_ONLY`,
`DIRECT_MAC_TERMINAL`, LOCAL_MAC process context, endpoint candidate
`127.0.0.1:7497`, IBKR Paper TWS/Gateway local socket candidate,
market-data/provider-readiness evidence only, no VPS reliance, no `18789` or
`18791` reliance, no bridge/tunnel/proxy reliance, no runtime mutation, and no
account/order/execution authority.

D11.70 authorizes the future target set only as LOCAL_MAC process-context
endpoint identity, read-only local socket configuration, API connection mode,
historical bars availability for `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`,
timeframe `15Min`, lookback/request scope `120 minutes`, response metadata
needed for adjudication, and negative evidence proving no
account/order/execution/submit authority was requested, returned, retained,
logged, or used.

D11.70 records allowed fields: source context, operator surface, process
context, endpoint host/port/class, localhost process-context statement,
rejected VPS equivalence, authorization gate, source commit, read-only socket
scope, market-data-only scope, mutation flags fixed false, API connection
mode, paper-mode candidate, market-data request scope, account/order/execution/
position/submit-cancel-modify requested flags fixed false, symbols, timeframe,
lookback, UTC request window, regular-session window, historical-market-data
flag, bar count, latest candle timestamp, freshness classification,
provider/feed metadata, redacted errors or warnings, PASS/FAIL markers,
adjudication-ready summary, and negative authority markers.

D11.70 records forbidden fields and activities: account IDs, balances, buying
power, margin, portfolio, positions, open orders, executions, trade history,
P&L, order IDs, credentials, tokens, secrets, submit/cancel/modify endpoints,
flatten/sell/cleanup evidence, service/systemd/scheduler/timer/runtime/
environment/TWS/Gateway/openclaw-gateway/VPS mutation, VPS `127.0.0.1:7497`,
`18789`, `18791`, bridge/tunnel/proxy endpoints, broker submit readiness, live
trading readiness, package capture, replay, scoring, candidate generation,
strategy/risk/execution behavior, and Unit 12 opening.

D11.70 requires D11.71 artifacts to include artifact identity, operator
context, source-control references, target results, redactions,
prohibited-fields attestation, negative-authority attestation, locality
attestation, and adjudication summary sections. It requires PASS/FAIL markers
for LOCAL_MAC context, endpoint candidate scope, read-only socket scope, API
connection mode, historical bars scope, forbidden-fields absence, negative
authority, and adjudication readiness.

D11.70 requires future capture to fail closed if the source context, operator
surface, endpoint candidate, target set, allowed fields, artifact sections,
timestamps/timezone fields, source-control references, redactions, or PASS/FAIL
markers deviate from the authorization. It also requires fail-closed handling
if account/order/execution/position/balance/portfolio/P&L/margin/buying-power/
trade/credential data is requested, returned, retained, or logged; if VPS,
`18789`, `18791`, bridge, tunnel, proxy, service, scheduler, systemd, runtime
mutation, credential mutation, package capture, replay, scoring,
candidate generation, strategy/risk/execution mutation, broker submit
readiness, live trading readiness, or Unit 12 opening is introduced.

D11.70 preserves the LOCAL_MAC/VPS locality distinction. LOCAL_MAC
`127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`. D11.70 rejects
treating LOCAL_MAC `127.0.0.1:7497` as VPS `127.0.0.1:7497`, and rejects
`18789` and `18791` as approved market-data endpoints.

D11.70 preserves provider eligibility blockers: `ibkr_market_data_candidate`
remains `broker_coupled=true`, `d11_primary_eligible=false`,
`d11_primary_candidate_status=candidate`, and `candidate_can_count_for_d11`
remains unsatisfied. Future evidence capture may support later market-data
provider-readiness adjudication, but it cannot itself approve IBKR primary
eligibility.

The exact next permissible gate is
`D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET`. D11.71 may be
the first gate allowed to contain exact bounded execution instructions for
LOCAL_MAC-only read-only market-data evidence capture, but only if it remains
inside the D11.70 authorization packet and the D11.69 contract. D11.70 itself
does not collect evidence and does not create executable evidence-capture
commands.

D11.70 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic, runtime mutation, timer
mutation, service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, scheduler mutation, credential access, Unit 12
opening, broker submit readiness, live-trading readiness, evidence collection
in D11.70, executable evidence-capture commands in D11.70, or IBKR primary
eligibility approval.

### D11.71 LOCAL_MAC Read-Only Evidence Capture Execution Packet

D11.71 adds the source-controlled LOCAL_MAC read-only evidence capture
execution packet:

```text
docs/ibkr_market_data_d11_71_local_mac_read_only_evidence_capture_execution_packet.md
```

It records `IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET`,
`source_commit=2f05f254f54f2feb87760820ddc48456e48f0c89`,
`d11_70_classification=IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`,
`d11_70_decision=LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_NEXT_GATE`,
`d11_70_authorized_gate_only=D11.71_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET`,
`d11_69_decision=READ_ONLY_EVIDENCE_CAPTURE_CONTRACT_READY`, and
`d11_71_decision=LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET_READY`.

D11.71 records the future execution source context as `LOCAL_MAC_ONLY`,
operator surface as `DIRECT_MAC_TERMINAL`, endpoint candidate as
`127.0.0.1:7497`, endpoint class as IBKR Paper TWS/Gateway local socket
candidate, symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`, timeframe `15Min`,
and lookback/request scope `120 minutes`. It records
`d11_71_evidence_capture_executed=false`,
`d11_71_broker_tws_api_network_runtime_action=false`,
`d11_71_executable_commands_run_by_codex=false`,
`production_provider_selection_behavior_changed=false`,
`ibkr_primary_eligibility=NOT_APPROVED`, `d11_status=D11_INSUFFICIENT`,
`unit_12_status=UNIT_12_BLOCKED`, `broker_submit_readiness=NOT_APPROVED`, and
`live_trading_readiness=NOT_APPROVED`.

D11.71 defines the exact future D11.72 operator command block and marks it
`FUTURE D11.72 ONLY - DO NOT RUN IN D11.71`. The future command starts from
`/Users/openclawcontrol/Documents/openclaw-stocks`, uses
`.venv-312/bin/python`, targets only `127.0.0.1:7497`, requests only
`AAPL`, `MSFT`, `NVDA`, `TSLA`, `MSTR`, timeframe `15Min`, lookback
`120 minutes`, exchange `SMART`, currency `USD`, security type `STK`, and the
existing local read-only smoke authorization flag.

D11.71 requires future output to be compact and adjudication-ready with run
identity, operator context, request scope, per-symbol result, provider
metadata, negative authority, locality summary, and adjudication summary
fields. It requires negative-authority markers showing no broker API authority,
order authority, execution authority, package capture, replay, scoring,
candidate generation, D11 completion authority, or Unit 12 opening.

D11.71 requires PASS/FAIL markers for LOCAL_MAC context, direct Mac terminal,
endpoint `127.0.0.1:7497` scope, no VPS/`18789`/`18791`/bridge/tunnel/proxy,
symbol scope, `15Min` timeframe, `120 minutes` lookback, historical bars scope,
forbidden-fields absence, negative authority, and adjudication readiness.
Missing, ambiguous, duplicated, or contradictory markers force fail-closed
handling.

D11.71 forbids account IDs, account aliases, account values, balances, buying
power, margin, portfolio contents, positions, position quantities, position
values, P&L, cash, equity, net liquidation, account summary, account ledger,
open orders, order IDs, order status, executions, fills, trade history,
commission reports, submit/cancel/modify endpoints, flatten/sell/cleanup
evidence, credentials, tokens, secrets, VPS, `18789`, `18791`, bridge, tunnel,
proxy, service/systemd/scheduler/timer/runtime/environment/TWS/Gateway/
openclaw-gateway/VPS/credential/strategy/risk/execution/provider-selection
runtime mutation, broker submit readiness, live trading readiness, package
capture, replay, scoring, candidate generation, Unit 12 opening, and IBKR
primary eligibility approval.

D11.71 requires future D11.72 to fail closed on wrong branch, dirty worktree,
HEAD mismatch, endpoint other than `127.0.0.1:7497`, source context other than
`LOCAL_MAC_ONLY`, operator surface other than `DIRECT_MAC_TERMINAL`,
TWS/Gateway not already manually open by the operator before future capture,
account/order/execution/position/balance/portfolio/credential access attempts,
forbidden fields in output, symbols outside `AAPL`, `MSFT`, `NVDA`, `TSLA`,
`MSTR`, timeframe other than `15Min`, lookback/request scope other than
`120 minutes`, VPS/`18789`/`18791`/bridge/tunnel/proxy/service/systemd/
scheduler/timer/runtime/environment/package capture/replay/scoring/
candidate-generation/strategy/risk/execution/live-readiness/broker-submit/
Unit 12/IBKR-primary-approval expansion, or missing artifact fields,
PASS/FAIL markers, redactions, or source-control references.

D11.71 preserves provider eligibility blockers: `ibkr_market_data_candidate`
remains `broker_coupled=true`, `d11_primary_eligible=false`,
`d11_primary_candidate_status=candidate`, and `candidate_can_count_for_d11`
remains unsatisfied. `IBKR_PRIMARY_ELIGIBILITY` remains `NOT_APPROVED`, D11
remains `D11_INSUFFICIENT`, Unit 12 remains `UNIT_12_BLOCKED`, broker submit
readiness remains `NOT_APPROVED`, and live trading readiness remains
`NOT_APPROVED`.

The exact next permissible gate is
`D11.72_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN`. D11.72 may be the
first gate where the operator actually runs the bounded LOCAL_MAC-only
read-only evidence capture, but only if the run remains inside the D11.71
execution packet, the D11.70 authorization packet, and the D11.69 contract.

D11.71 grants no account, order, execution, package capture, replay, scoring,
candidate generation, strategy, risk, VPS proof run, VPS market test, protocol
probe, endpoint inspection, broker endpoint traffic by Codex, runtime mutation,
timer mutation, service mutation, systemd mutation, TWS mutation, Gateway
mutation, openclaw-gateway mutation, scheduler mutation, credential access,
Unit 12 opening, broker submit readiness, live-trading readiness, evidence
capture in D11.71, executable command execution by Codex, or IBKR primary
eligibility approval.

### D11.72 LOCAL_MAC Read-Only Evidence Capture Operator Run Record

D11.72 adds the source-controlled LOCAL_MAC read-only evidence capture
operator-run record:

```text
docs/ibkr_market_data_d11_72_local_mac_read_only_evidence_capture_operator_run_record.md
```

It records
`IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN_RECORD`,
`source_commit=7479f708c53067980491c31bb37b41c2bcbf4eea`,
`d11_71_decision=LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_EXECUTION_PACKET_READY`,
`d11_72_run_status=COMPLETED_BY_OPERATOR`, and
`d11_72_evidence_classification=READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT`.
The command was run by the operator, not by Codex, using the
D11.71-authorized LOCAL_MAC-only read-only smoke path.

D11.72 records the completed run context as `LOCAL_MAC_ONLY`,
`DIRECT_MAC_TERMINAL`, endpoint candidate `127.0.0.1:7497`, endpoint class
IBKR Paper TWS/Gateway local socket candidate, symbols `AAPL`, `MSFT`, `NVDA`,
`TSLA`, `MSTR`, timeframe `15Min`, lookback `120 minutes`, and result type
`ibkr_local_read_only_market_data_smoke`.

D11.72 records that all five symbols returned `read_only=true`,
`provider_key=ibkr_market_data_candidate`, provider name `IBKR read-only
market-data diagnostic candidate`, `connection_mode=local_read_only_smoke`,
`d11_primary_candidate_status=candidate`, `d11_primary_eligible=false`,
`d11_countable=false`,
`failure_reason=regular_session_closed_latest_candle_valid_for_last_session`,
`freshness_classification=recency_caveated`,
`latest_candle_timestamp=2026-06-26T19:45:00+00:00`,
`requested_start=2026-06-27T01:40:31.383039+00:00`,
`requested_end=2026-06-27T03:40:31.383039+00:00`, and
`lag_minutes=475.52305065`.

D11.72 classifies the evidence as
`READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT`. The evidence is not
D11-countable for primary eligibility because all five symbols returned
`d11_countable=false` and
`failure_reason=regular_session_closed_latest_candle_valid_for_last_session`.

D11.72 records negative authority: no account query, position query, margin
query, buying-power query, portfolio query, order placement, order
modification, order cancellation, order routing, execution authority, package
capture, replay, scoring, candidate generation, Unit 12 opening, or VPS
runtime/systemd/timer mutation. It records `broker_api_authority=false`,
`order_authority=false`, `execution_authority=false`,
`package_capture=false`, `replay=false`, `scoring=false`, and
`candidate_generation=false`.

D11.72 preserves the LOCAL_MAC/VPS locality distinction. LOCAL_MAC
`127.0.0.1:7497` evidence is not VPS `127.0.0.1:7497` evidence. The operator
result used no VPS path, no `18789`, no `18791`, no bridge, no tunnel, and no
proxy. D11.72 does not approve `18789` or `18791` as market-data endpoints and
does not authorize rerun or endpoint substitution.

D11.72 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11=D11_INSUFFICIENT`, `UNIT_12=UNIT_12_BLOCKED`,
`broker_submit_readiness=NOT_APPROVED`, and
`live_trading_readiness=NOT_APPROVED`. It does not approve IBKR primary
eligibility, does not mark D11 complete, does not open Unit 12, does not
approve broker submit readiness, and does not approve live trading readiness.

D11.72 does not authorize a rerun. The exact next permissible gate is
`D11.73_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`. D11.73 must be a
source-controlled adjudication gate that decides whether this D11.72 capture
is sufficient, insufficient due to the recency caveat, or requires a fresh
regular-session rerun under a new authorization.

### D11.73 LOCAL_MAC Read-Only Evidence Capture Adjudication

D11.73 adds the source-controlled adjudication packet for the completed D11.72
operator-run record:

```text
docs/ibkr_market_data_d11_73_local_mac_read_only_evidence_capture_adjudication.md
```

It records
`IBKR_D11_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`,
`source_commit=7f62130f08a03167975f9187c5a0314f95074568`,
`d11_72_evidence_classification=READ_ONLY_CAPTURE_SUCCEEDED_WITH_RECENCY_CAVEAT`,
and
`d11_73_decision=D11_72_EVIDENCE_ADJUDICATED_INSUFFICIENT_REQUIRES_FRESH_REGULAR_SESSION_RERUN`.
D11.73 adjudicates only the D11.72 recorded evidence. It does not rerun IBKR,
does not execute evidence capture, does not create executable evidence-capture
commands, and does not perform runtime, broker, TWS, API, VPS, scheduler,
systemd, or credential action.

D11.73 records the D11.72 evidence as operationally useful proof that the
LOCAL_MAC read-only diagnostic path returned historical bar metadata. It is
not countable for D11 primary eligibility because all five symbols returned
`d11_countable=false`, `d11_primary_eligible=false`,
`freshness_classification=recency_caveated`, and
`failure_reason=regular_session_closed_latest_candle_valid_for_last_session`.

D11.73 records per-symbol adjudication for `AAPL`, `MSFT`, `NVDA`, `TSLA`,
and `MSTR`: `read_only=true`, `provider_key=ibkr_market_data_candidate`,
`connection_mode=local_read_only_smoke`,
`latest_candle_timestamp=2026-06-26T19:45:00+00:00`,
`requested_start=2026-06-27T01:40:31.383039+00:00`,
`requested_end=2026-06-27T03:40:31.383039+00:00`,
`lag_minutes=475.52305065`,
`freshness_classification=recency_caveated`,
`failure_reason=regular_session_closed_latest_candle_valid_for_last_session`,
`d11_countable=false`, `d11_primary_eligible=false`, and
`d11_primary_candidate_status=candidate`.

D11.73 adjudicates that the D11.72 run occurred outside the usable freshness
window for countable primary-eligibility evidence. `candidate_can_count_for_d11`
remains unsatisfied, and the IBKR candidate remains candidate-only and
`d11_primary_eligible=false`.

D11.73 accepts the D11.72 negative-authority record for this adjudication: no
account query, position query, margin query, buying-power query, portfolio
query, order placement, order modification, order cancellation, order routing,
execution authority, package capture, replay, scoring, candidate generation,
Unit 12 opening, or VPS runtime/systemd/timer mutation appeared. The D11.72
record used no VPS path, no `18789`, no `18791`, no bridge, no tunnel, and no
proxy.

D11.73 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11=D11_INSUFFICIENT`, `UNIT_12=UNIT_12_BLOCKED`,
`broker_submit_readiness=NOT_APPROVED`, and
`live_trading_readiness=NOT_APPROVED`. It does not approve IBKR primary
eligibility, does not mark D11 complete, does not open Unit 12, and does not
modify production provider-selection behavior.

The exact next permissible gate is
`D11.74_SOURCE_CONTROLLED_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`.
D11.74 must be source-controlled authorization only for a fresh LOCAL_MAC-only
regular-session read-only evidence capture. It must preserve the
D11.69/D11.70/D11.71 boundaries unless explicitly narrowed, must not itself
perform evidence capture, and must not approve IBKR primary eligibility.

### D11.74 Fresh Regular-Session Read-Only Evidence Capture Authorization Packet

D11.74 adds the source-controlled authorization packet for a fresh
regular-session LOCAL_MAC-only read-only operator rerun:

```text
docs/ibkr_market_data_d11_74_fresh_regular_session_read_only_evidence_capture_authorization_packet.md
```

It records
`IBKR_D11_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZATION_PACKET`,
`source_commit=08bc4cbedd4b465eb6308deadb4a781acc991512`,
`d11_73_decision=D11_72_EVIDENCE_ADJUDICATED_INSUFFICIENT_REQUIRES_FRESH_REGULAR_SESSION_RERUN`,
and
`d11_74_decision=FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_AUTHORIZED_FOR_OPERATOR_RUN`.
D11.74 authorizes only the next operator-run gate. D11.74 itself collects no
evidence, runs no executable evidence-capture command, performs no runtime,
broker, TWS, API, VPS, scheduler, systemd, or credential action, and changes
no production provider-selection behavior.

D11.74 uses the D11.73 adjudication basis: D11.72 was operationally useful but
non-countable because all five symbols returned `d11_countable=false`,
`d11_primary_eligible=false`, `freshness_classification=recency_caveated`, and
`failure_reason=regular_session_closed_latest_candle_valid_for_last_session`.
The prior recorded values were
`latest_candle_timestamp=2026-06-26T19:45:00+00:00`,
`requested_start=2026-06-27T01:40:31.383039+00:00`,
`requested_end=2026-06-27T03:40:31.383039+00:00`, and
`lag_minutes=475.52305065`.

D11.74 authorizes the future source context only as `LOCAL_MAC_ONLY`,
`DIRECT_MAC_TERMINAL`, LOCAL_MAC process context, endpoint candidate
`127.0.0.1:7497`, IBKR Paper TWS/Gateway local socket candidate,
market-data/provider-readiness only, symbols `AAPL`, `MSFT`, `NVDA`, `TSLA`,
`MSTR`, timeframe `15Min`, and lookback `120 minutes`.

D11.74 requires fresh regular-session timing: the future operator run must
occur during a regular-session window where a current or sufficiently recent
`15Min` candle is expected to be available. It explicitly rejects after-session
reruns expected to reproduce
`regular_session_closed_latest_candle_valid_for_last_session`. The future run
must record `requested_start`, `requested_end`, `latest_candle_timestamp`,
`lag_minutes`, `freshness_classification`, `failure_reason`, `d11_countable`,
and `d11_primary_eligible` for every symbol, and must fail closed if all
symbols remain `d11_countable=false` due to the regular-session-closed recency
caveat.

D11.74 records allowed fields for LOCAL_MAC process endpoint identity,
read-only socket/API mode, regular-session historical bars availability,
response metadata for adjudication, and negative authority evidence. It
forbids account IDs, account values, balances, buying power, margin, portfolio,
positions, P&L, open orders, order IDs, order status, executions, fills, trade
history, credentials, tokens, secrets, VPS `127.0.0.1:7497`, `18789`, `18791`,
bridge, tunnel, proxy, service/scheduler/systemd/timer/runtime/environment/
TWS/Gateway/openclaw-gateway/VPS/credential mutation, package capture, replay,
scoring, candidate generation, strategy/risk/execution mutation, Unit 12
opening, D11 completion, broker submit readiness, live trading readiness, and
IBKR primary eligibility approval.

D11.74 requires PASS/FAIL markers for LOCAL_MAC context, direct Mac terminal,
endpoint `127.0.0.1:7497`, regular-session timing, no after-session stale
capture, symbol scope, `15Min` timeframe, `120 minutes` lookback, historical
bars scope, forbidden-fields absence, negative authority, and adjudication
readiness, including `REGULAR_SESSION_TIMING_PASS` or
`REGULAR_SESSION_TIMING_FAIL` and `NO_AFTER_SESSION_STALE_CAPTURE_PASS` or
`NO_AFTER_SESSION_STALE_CAPTURE_FAIL`. It requires artifact sections for identity, operator context,
regular-session timing, request scope, target results, negative authority,
locality, and adjudication summary.

D11.74 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11=D11_INSUFFICIENT`, `UNIT_12=UNIT_12_BLOCKED`,
`broker_submit_readiness=NOT_APPROVED`, and
`live_trading_readiness=NOT_APPROVED`. It preserves provider eligibility
blockers: `broker_coupled=true`, `d11_primary_eligible=false`,
`d11_primary_candidate_status=candidate`, and `candidate_can_count_for_d11`
unsatisfied. Future evidence capture may support later adjudication but cannot
itself approve IBKR primary eligibility.

The exact next permissible gate is
`D11.75_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN`.
D11.75 may be the operator-run gate where the bounded fresh regular-session
LOCAL_MAC-only read-only evidence capture is actually run, but only if it
remains inside the D11.69 contract, D11.70 authorization packet, D11.71
execution packet, D11.73 adjudication, and D11.74 authorization packet.

### D11.76 Fresh Regular-Session LOCAL_MAC Read-Only Evidence Capture Operator Run Record

D11.76 adds the source-controlled operator-run record for the completed D11.75
fresh regular-session LOCAL_MAC-only read-only evidence capture:

docs/ibkr_market_data_d11_76_fresh_regular_session_local_mac_read_only_evidence_capture_operator_run_record.md

D11.76 records
`IBKR_D11_FRESH_REGULAR_SESSION_LOCAL_MAC_READ_ONLY_EVIDENCE_CAPTURE_OPERATOR_RUN_RECORD`
at `source_commit=6db5d0b2f1cc47679dd194c846206a0dde36693c` with
`d11_75_run_status=COMPLETED_BY_OPERATOR` and
`d11_76_evidence_classification=FRESH_REGULAR_SESSION_READ_ONLY_CAPTURE_SUCCEEDED_WITH_CLEAN_COUNTABLE_EVIDENCE`.
The capture was run by the operator, not by Codex. D11.76 is an evidence
record only and is not provider approval.

D11.76 records the completed run context as `LOCAL_MAC_ONLY`,
`DIRECT_MAC_TERMINAL`, endpoint candidate `127.0.0.1:7497`, symbols `AAPL`,
`MSFT`, `NVDA`, `TSLA`, `MSTR`, timeframe `15Min`, lookback `120 minutes`,
authority `READ_ONLY_MARKET_DATA_ONLY`, and result type
`ibkr_local_read_only_market_data_smoke`.

D11.76 records that all five symbols returned `read_only=true`,
`provider_key=ibkr_market_data_candidate`, connection mode
`local_read_only_smoke`, `latest_candle_timestamp=2026-06-29T14:00:00+00:00`,
`requested_start=2026-06-29T12:20:17.713714+00:00`,
`requested_end=2026-06-29T14:20:17.713714+00:00`,
`lag_minutes=20.295228566666665`, `freshness_classification=clean`,
empty `failure_reason`, and `d11_countable=true`.

D11.76 also records that all five symbols remain
`d11_primary_eligible=false` with `d11_primary_candidate_status=candidate`.
The record preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11=D11_INSUFFICIENT`, `UNIT_12=UNIT_12_BLOCKED`,
`broker_submit_readiness=NOT_APPROVED`, and
`live_trading_readiness=NOT_APPROVED`.

D11.76 records negative authority: no account query, position query, portfolio
query, balance query, margin query, buying-power query, order placement, order
modification, order cancellation, order routing, execution authority, package
capture, replay, scoring, candidate generation, Unit 12 opening, or VPS
runtime/systemd/timer mutation appeared. D11.76 does not rerun IBKR, does not
execute evidence capture, does not perform broker/TWS/API/network/runtime/
VPS/scheduler/systemd/credential work, and does not modify production
provider-selection behavior.

The exact next permissible gate is
`D11.77_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`.
D11.77 must adjudicate whether the D11.75/D11.76 clean countable evidence is
sufficient to change IBKR primary eligibility or close D11. D11.76 itself does
not approve IBKR primary eligibility, does not complete D11, and does not open
Unit 12.

### D11.77 Fresh Regular-Session Read-Only Evidence Capture Adjudication

D11.77 adds the source-controlled adjudication packet for the D11.75/D11.76
fresh regular-session LOCAL_MAC-only read-only evidence:

docs/ibkr_market_data_d11_77_fresh_regular_session_read_only_evidence_capture_adjudication.md

D11.77 records
`IBKR_D11_FRESH_REGULAR_SESSION_READ_ONLY_EVIDENCE_CAPTURE_ADJUDICATION`
at `source_commit=1afb04c64275e039d598203dcbcc40b3b2ef9bc2` and selects the
single decision
`D11_75_76_CLEAN_COUNTABLE_EVIDENCE_ADJUDICATED_COUNTABLE_BUT_INSUFFICIENT_TO_APPROVE_PRIMARY_ELIGIBILITY`.

D11.77 accepts the D11.75/D11.76 evidence as clean and countable: all five
symbols returned `freshness_classification=clean`, `d11_countable=true`, empty
`failure_reason`, `latest_candle_timestamp=2026-06-29T14:00:00+00:00`,
`requested_start=2026-06-29T12:20:17.713714+00:00`,
`requested_end=2026-06-29T14:20:17.713714+00:00`, and
`lag_minutes=20.295228566666665`.

D11.77 adjudicates that countability is not provider approval. All five
D11.75/D11.76 rows still returned `d11_primary_eligible=false` and
`d11_primary_candidate_status=candidate`. The source-controlled provider
candidate still records `broker_coupled=true`, and `candidate_can_count_for_d11`
still requires `approved_primary`, `d11_primary_eligible=true`, and
`broker_coupled=false`. The active criteria still include
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`.

D11.77 therefore preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`,
`D11=D11_INSUFFICIENT`, `UNIT_12=UNIT_12_BLOCKED`,
`broker_submit_readiness=NOT_APPROVED`, and
`live_trading_readiness=NOT_APPROVED`.

D11.77 accepts the negative-authority evidence: no account query, position
query, portfolio query, balance query, margin query, buying-power query, order
placement, order modification, order cancellation, order routing, execution
authority, package capture, replay, scoring, candidate generation, Unit 12
opening, VPS runtime/systemd/timer mutation, VPS endpoint, `18789`, `18791`,
bridge, tunnel, or proxy appeared.

D11.77 collected no evidence, ran no executable broker/TWS/API/network/runtime
command, performed no broker/runtime/VPS/scheduler/systemd/credential action,
changed no production provider-selection runtime behavior, and performed no
commit or push.

The exact next permissible gate is
`D11.78_SOURCE_CONTROLLED_IBKR_PRIMARY_ELIGIBILITY_CRITERIA_AND_CANDIDATE_STATUS_REMEDIATION`.
D11.78 must remediate the remaining candidate-status, primary-eligible,
broker-coupling, `candidate_can_count_for_d11`, and unrevised separate VPS
read-only freshness proof blockers before any later approval attempt.

### D11.78 Source-Controlled IBKR Primary Eligibility Criteria And Candidate Status Remediation

D11.78 adds the source-controlled criteria and candidate-status remediation
packet for the blockers identified by D11.77:

docs/ibkr_market_data_d11_78_primary_eligibility_criteria_and_candidate_status_remediation.md

D11.78 records
`IBKR_D11_PRIMARY_ELIGIBILITY_CRITERIA_AND_CANDIDATE_STATUS_REMEDIATION`
at `source_commit=b3ecf93cc49e45787c963930a14a4b7256cc9122` and selects the
single decision
`IBKR_PRIMARY_ELIGIBILITY_CRITERIA_REMEDIATED_READY_FOR_FINAL_D11_CLOSURE_ADJUDICATION`.

D11.78 uses the D11.75/D11.76 clean countable evidence only as a
provider-readiness evidence input: all five symbols `AAPL`, `MSFT`, `NVDA`,
`TSLA`, and `MSTR` returned `freshness_classification=clean`,
`d11_countable=true`, empty `failure_reason`,
`latest_candle_timestamp=2026-06-29T14:00:00+00:00`,
`requested_start=2026-06-29T12:20:17.713714+00:00`,
`requested_end=2026-06-29T14:20:17.713714+00:00`, and
`lag_minutes=20.295228566666665`.

D11.78 remediates the D11.77 blockers at the source-controlled governance
layer only. Artifact row status remains `candidate`, but governance status is
`READY_FOR_FINAL_D11_CLOSURE_ADJUDICATION`. The artifact
`d11_primary_eligible=false` value is treated as a non-self-approval safety
marker, not as a final adjudication blocker. `broker_coupled=true` is narrowed
as compatible with read-only market-data qualification only under D11.69-D11.77
negative-authority controls. `candidate_can_count_for_d11` is revised for this
source-controlled evidence bundle only as satisfied for provider-readiness
final adjudication. The separate VPS read-only freshness proof criterion is
narrowed and retired for this LOCAL_MAC-only path; this does not approve any
VPS endpoint and does not treat LOCAL_MAC `127.0.0.1:7497` as VPS
`127.0.0.1:7497`.

D11.78 preserves
`IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED_READY_FOR_FINAL_ADJUDICATION_ONLY`,
`D11=D11_INSUFFICIENT`, `UNIT_12=UNIT_12_BLOCKED`,
`broker_submit_readiness=NOT_APPROVED`, and
`live_trading_readiness=NOT_APPROVED`.

D11.78 collected no evidence, ran no executable broker/TWS/API/network/runtime
command, performed no broker/runtime/VPS/scheduler/systemd/credential action,
changed no production provider-selection runtime behavior, opened no Unit 12,
and performed no commit or push.

The exact next permissible gate is
`D11.79_FINAL_IBKR_PRIMARY_ELIGIBILITY_AND_D11_CLOSURE_ADJUDICATION`.
D11.79 must perform the final source-controlled IBKR primary eligibility and
D11 closure adjudication.

### D11.79 Final IBKR Primary Eligibility And D11 Closure Adjudication

D11.79 adds the final source-controlled IBKR read-only market-data primary
eligibility and D11 closure adjudication packet:

docs/ibkr_market_data_d11_79_final_primary_eligibility_and_d11_closure_adjudication.md

D11.79 records
`IBKR_D11_FINAL_READ_ONLY_MARKET_DATA_PRIMARY_ELIGIBILITY_AND_D11_CLOSURE_ADJUDICATION`
at `source_commit=74c2cad5087214aff9cc7b108900547f250d28cd` and selects the
single decision
`IBKR_READ_ONLY_MARKET_DATA_PRIMARY_ELIGIBILITY_APPROVED_AND_D11_CLOSED`.

D11.79 uses only the D11.75/D11.76 clean countable LOCAL_MAC evidence, D11.77
adjudication, and D11.78 remediation basis. The D11.75/D11.76 evidence covered
`AAPL`, `MSFT`, `NVDA`, `TSLA`, and `MSTR`, `15Min`, `120` minutes,
`latest_candle_timestamp=2026-06-29T14:00:00+00:00`,
`requested_start=2026-06-29T12:20:17.713714+00:00`,
`requested_end=2026-06-29T14:20:17.713714+00:00`,
`lag_minutes=20.295228566666665`, `freshness_classification=clean`, empty
`failure_reason`, `d11_countable=true`, and `read_only=true`.

D11.79 accepts D11.78 remediation of the D11.77 blockers: candidate status is
a diagnostic artifact status, `d11_primary_eligible=false` is a non-self-
approval marker, `broker_coupled=true` is compatible only with read-only
market-data qualification under negative-authority boundaries,
`candidate_can_count_for_d11` is remediated for the D11.75/D11.76 clean
countable LOCAL_MAC bundle, and the separate VPS read-only freshness proof
criterion is narrowed and retired for this LOCAL_MAC-only path with no VPS
endpoint approved.

D11.79 sets
`IBKR_PRIMARY_ELIGIBILITY=APPROVED_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`
and `D11=D11_CLOSED_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`.
This approval and closure are limited to IBKR read-only market-data provider
qualification only.

D11.79 preserves `UNIT_12=UNIT_12_NOT_OPENED_BOUNDARY_REVIEW_REQUIRED`,
`broker_submit_readiness=NOT_APPROVED`, `live_trading_readiness=NOT_APPROVED`,
`account_authority=NONE`, `order_authority=NONE`, `execution_authority=NONE`,
`package_capture=NOT_AUTHORIZED`, `replay=NOT_AUTHORIZED`,
`scoring=NOT_AUTHORIZED`, `candidate_generation=NOT_AUTHORIZED`, and
`strategy_risk_execution_changes=NOT_AUTHORIZED`.

D11.79 also preserves endpoint locality: LOCAL_MAC `127.0.0.1:7497` remains a
LOCAL_MAC process-context endpoint and is not VPS `127.0.0.1:7497`. D11.79
approves no VPS endpoint, no `18789`, no `18791`, no bridge, no tunnel, and no
proxy.

D11.79 collected no evidence, ran no executable broker/TWS/API/network/runtime
command, performed no broker/runtime/VPS/scheduler/systemd/credential action,
changed no production provider-selection runtime behavior, implemented no Unit
12, and performed no commit or push.

The exact next permissible gate is
`POST_D11_SOURCE_CONTROLLED_REPLAY_PACKAGE_PREREQUISITE_AND_UNIT_12_BOUNDARY_REVIEW`.
This next gate is a review/authorization prerequisite only and must not itself
perform package capture, replay, scoring, candidate generation, strategy/risk/
execution changes, broker actions, live trading, or Unit 12 implementation.

### Post-D11 Replay Package Prerequisite And Unit 12 Boundary Review

The post-D11 source-controlled boundary review packet is recorded here:

docs/post_d11_replay_package_prerequisite_and_unit_12_boundary_review.md

The packet records
`POST_D11_SOURCE_CONTROLLED_REPLAY_PACKAGE_PREREQUISITE_AND_UNIT_12_BOUNDARY_REVIEW`
at `source_commit=a09ce5e477d568907f32f43732dd5dd2e6741eda` and selects the
single decision
`POST_D11_REPLAY_PACKAGE_AND_UNIT_12_BOUNDARY_REVIEW_COMPLETED_READY_FOR_SOURCE_CONTROLLED_AUTHORIZATION_PACKET`.

D11 closure unlocks only a governance transition from the read-only
market-data primary-eligibility lane into a post-D11 prerequisite review lane.
It allows a later source-controlled authorization packet to be drafted for
package-capture criteria. It does not unlock package capture execution, replay
execution, scoring execution, candidate generation execution, strategy/risk/
execution changes, scheduler/runtime/service/systemd/timer changes, credential
or environment-file changes, broker submit readiness, live trading readiness,
account authority, order authority, execution authority, VPS endpoint approval,
`18789` or `18791` endpoint approval, bridge/tunnel/proxy approval, or Unit 12
opening or implementation.

The boundary review preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`package_capture_execution=NOT_AUTHORIZED`, `replay_execution=NOT_AUTHORIZED`,
`scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`vps_endpoint_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The packet defines the required prerequisites before any future package capture
can be authorized: expected source commit and clean worktree, exact operator
surface and source context, eligible `run_id` selection from scheduled runtime
evidence only, JSONL and `last_run_report.json` alignment, D13
market-session eligibility, no-overwrite checks, immutable package lifecycle,
hash/manifest/integrity evidence, redaction/provenance requirements,
`order_state.json` exclusion or absent/not-applicable treatment, fail-closed
conditions, and explicit proof that package capture does not imply replay,
scoring, candidate generation, Unit 12, broker authority, strategy/risk/
execution changes, paper approval, or live approval.

The packet defines the required prerequisites before any future Unit 12 work
can be authorized: completed and reviewed package evidence, ledger or inventory
evidence, separately authorized replay/scoring/evaluation prerequisites,
candidate-generation prerequisites if candidate work is in scope, broker
submit/live trading separation, account/order/execution exclusion unless a
later broker-authority gate exists, and a source-controlled Unit 12 scope with
allowed fields, forbidden fields, fail-closed conditions, and non-runtime
behavior boundaries.

The boundary review performed no package capture, no replay, no scoring, no
candidate generation, no broker/TWS/API/network/runtime action, no IBKR
connection, no TWS/Gateway inspection, no VPS action, no service/systemd/
scheduler/timer/runtime command, no credential or environment-file access, no
account/portfolio/balance/position/order/execution/trade/P&L/margin/
buying-power access, no strategy/risk/execution/scheduler behavior change, no
production runtime or provider-selection runtime behavior change, no Unit 12
implementation, no Unit 12 opening, and no commit or push.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET`. That next gate is still
an authorization packet only unless it explicitly authorizes a later bounded
operator run. It must not itself perform package capture, replay, scoring,
candidate generation, broker actions, runtime actions, live trading, or Unit
12 implementation.

### Post-D11 Replay Package Capture Authorization Packet

The post-D11 source-controlled package-capture authorization packet is recorded
here:

docs/post_d11_replay_package_capture_authorization_packet.md

The packet records `POST_D11_REPLAY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET` at
`source_commit=cd9768f1ae39f91ef513bf1ab68fe1c737e6bd2f` and selects the
single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_AUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_OPERATOR_RUN`.

D11.79 read-only IBKR market-data provider qualification plus the post-D11
boundary review are sufficient to authorize the later bounded operator-run
gate `POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN`. The authorization packet
does not execute package capture and does not infer package-capture execution
authority from D11 closure alone.

The future operator run is authorized only as `LOCAL_MAC_ONLY`. The approved
provider scope remains
`IBKR_READ_ONLY_MARKET_DATA_PROVIDER_QUALIFICATION_ONLY`. LOCAL_MAC
`127.0.0.1:7497` remains a LOCAL_MAC process-context endpoint from the D11
read-only market-data qualification lane. The packet approves no endpoint use
for package capture, no broker/TWS/API traffic, no VPS endpoint, no VPS
`127.0.0.1:7497`, no `18789`, no `18791`, no bridge, no tunnel, no proxy, and
no endpoint substitution.

The future operator-run package-capture scope is one bounded replay package for
exactly one `run_id`, with aligned JSONL event stream, terminal completion
event, terminal status and reason, aligned `last_run_report.json`, explicit
`order_state.json` exclusion or absent/not-applicable declaration, package
identity and layout metadata, package creation timestamp, code/version
metadata, configuration metadata, market input evidence, strategy input/output
evidence, risk/reconciliation evidence, provenance and redaction status,
manifest, hash, integrity, persistence, and finalized immutability evidence.

Required future preflight checks include expected source commit, clean
worktree, LOCAL_MAC-only source context, exact selected `run_id`, scheduled
runtime evidence source, aligned `logs/{run_id}.jsonl`, aligned
`last_run_report.json`, terminal completion event, D13 market-session
eligibility, approved LOCAL_MAC package root/path, no existing package
directory, no mixed `run_id`, no stale report, no hash mismatch, no path
traversal, no overwrite, no future/leaked/post-decision evidence, no broker/
order-state binding, no credential or environment-file access, and no runtime,
scheduler, service, systemd, or timer mutation.

Expected future artifacts include `run_id`, source commit, clean worktree
evidence, JSONL path, last-run-report alignment, terminal event/status/reason,
D13 eligibility, package path, manifest path, manifest schema version,
manifest package id, manifest canonical run id, manifest source references,
section provenance, section redaction status, package sha256,
integrity-validation result, finalized immutable marker, no-overwrite
attestation, order-state handling, and operator attestation that no replay,
scoring, candidate generation, broker action, runtime mutation, or Unit 12
occurred.

The packet preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`production_runtime_provider_selection_runtime_changes=BLOCKED`,
`vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The authorization packet performed no package capture, no replay, no scoring,
no candidate generation, no broker/TWS/API/network/runtime action, no IBKR
connection, no TWS/Gateway inspection, no VPS action, no service/systemd/
scheduler/timer/runtime command, no credential or environment-file access, no
account/portfolio/balance/position/order/execution/trade/P&L/margin/
buying-power access, no strategy/risk/execution/scheduler behavior change, no
production runtime or provider-selection runtime behavior change, no Unit 12
implementation, no Unit 12 opening, and no commit or push.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN`.

### Post-D11 Replay Package Capture Operator Run Preflight Blocker Record

The source-controlled preflight blocker record for the authorized operator-run
gate is recorded here:

docs/post_d11_replay_package_capture_operator_run_preflight_blocker_record.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_PREFLIGHT_BLOCKER_RECORD` at
`source_commit=917af7e67e20faf8494afabe425716efd6ae3ae7` and selects the
single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKED_PENDING_LOCAL_ARTIFACTS_AND_AUTHORITY_SURFACE_REMEDIATION`.

The operator-run gate is blocked by missing local artifacts: operator static
discovery records `logs=MISSING`, `run_reports=MISSING`,
`replay_packages=MISSING`, `last_run_report.json=ABSENT`, and
`order_state.json=ABSENT`. No eligible `run_id` can be selected because the
source-controlled capture preflight requires `logs/<run_id>.jsonl` and either
`run_reports/<run_id>.json` or `last_run_report.json`, plus safe `run_id`,
absent `replay_packages/<run_id>`, and capture readiness reproved.

The operator-run gate is also blocked by authority-surface mismatch. The
authorization packet approved `authorized_source_context=LOCAL_MAC_ONLY`, but
`tools/ops/gate_d_market_session_operator.py` capture requires
`capture --run-id <run_id> --expected-commit <commit>
--authorize-vps-package-write` and delegates to
`package_execution_orchestrator --run-id <run_id> --execution-mode vps --authorize-vps-package-write`.
`tools/replay/package_execution_orchestrator.py`
states production `vps` execution and the standalone `--execution-mode vps`
surface defer unless a future bounded VPS execution gate authorizes real `/opt`
reads and writes. The current gate did not
authorize a VPS execution gate.

`order_state.json` remains absent/excluded/not-bound. The source-controlled
runtime artifact reader and package writer block order-state reads and writes
pending a later explicit binding gate, so order-state absence must not be used
to unblock package capture.

The blocker record preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`production_runtime_provider_selection_runtime_changes=BLOCKED`,
`vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The blocker record performed no package capture, no replay, no scoring, no
candidate generation, no broker/TWS/API/network/runtime action, no IBKR
connection, no TWS/Gateway inspection, no VPS action, no service/systemd/
scheduler/timer/runtime command, no credential or environment-file access, no
account/portfolio/balance/position/order/execution/trade/P&L/margin/
buying-power access, no strategy/risk/execution/scheduler behavior change, no
production runtime or provider-selection runtime behavior change, no package-
capture/orchestrator production behavior change, no Unit 12 implementation, no
Unit 12 opening, and no commit or push.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_PLAN`.

### Post-D11 Replay Package Capture Operator Run Blocker Remediation Plan

The source-controlled remediation plan for the operator-run blocker is recorded
here:

docs/post_d11_replay_package_capture_operator_run_blocker_remediation_plan.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_PLAN` at
`source_commit=ae9469c9de44f275b25d61f80d88667648434e00` and selects the
single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_PLAN_COMPLETED_READY_FOR_REMEDIATION_AUTHORIZATION_PACKET`.

The plan separates artifact remediation from authority-surface remediation.
The artifact-remediation side covers the missing local artifact blocker:
`logs=MISSING`, `run_reports=MISSING`, `replay_packages=MISSING`, and
`last_run_report.json=ABSENT`. It records that artifacts must either be
generated by a separate prior market-session/runtime artifact gate or
discovered from already-existing deterministic outputs under a future
authorization packet. It does not authorize artifact creation. It also records
that `replay_packages` directory creation must be deferred to a later governed
package-capture execution or separately authorized by a narrow layout gate.

The authority-surface side covers the `LOCAL_MAC_ONLY` authorization versus
the current capture surface. The existing surface requires
`--authorize-vps-package-write` and delegates to `--execution-mode vps`. The
plan requires a future authorization packet to choose either a LOCAL_MAC
package-capture command surface, a bounded VPS execution authorization path, or
a source-controlled legacy-name adjudication path. Until remediated,
`--authorize-vps-package-write` is authority-bearing and must be treated as VPS
package-write authority.

`order_state.json` remains `ABSENT_EXCLUDED_NOT_BOUND`; source-controlled
reader/writer behavior still blocks order-state reads and writes pending a
later explicit binding gate.

The plan preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`package_capture_execution=NOT_AUTHORIZED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`production_runtime_provider_selection_runtime_changes=BLOCKED`,
`production_package_capture_orchestrator_behavior_changes=NOT_AUTHORIZED_BY_THIS_GATE`,
`vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The plan performed no remediation, no package capture, no replay, no scoring,
no candidate generation, no broker/TWS/API/network/runtime action, no VPS
action, no package-capture/orchestrator production behavior change, no Unit 12
implementation, no commit, and no push.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET`.

### Post-D11 Replay Package Capture Operator Run Blocker Remediation Authorization Packet

The source-controlled authorization packet for future blocker remediation is
recorded here:

docs/post_d11_replay_package_capture_operator_run_blocker_remediation_authorization_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET`
at `source_commit=8faf4258e373a467753377150dfcee764483d1c8` and selects the
single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_AUTHORIZATION_PACKET_APPROVED_FOR_SOURCE_CONTROLLED_REMEDIATION_EDIT_GATE`.

The authorization packet approves only a later source-controlled remediation
edit gate. It authorizes both separable lanes for the next edit packet:
`artifact-path remediation` and `authority-surface remediation`. The
recommended next edit priority is LOCAL_MAC command-surface reconciliation plus
artifact discovery/layout criteria. It does not authorize remediation execution,
artifact creation, package capture, package-capture/orchestrator production
behavior changes, bounded VPS execution, or Unit 12 implementation.

Artifact-path adjudication preserves the missing local artifact blocker:
`logs=MISSING`, `run_reports=MISSING`, `replay_packages=MISSING`, and
`last_run_report.json=ABSENT`. The next edit packet may define fail-closed
criteria for `logs/<run_id>.jsonl`, `run_reports/<run_id>.json`,
`last_run_report.json`, safe `run_id`, absent `replay_packages/<run_id>`, and
capture readiness, but it must not create artifacts or select an eligible
`run_id`.

Authority-surface adjudication preserves the `LOCAL_MAC_ONLY` authorization
boundary while recognizing that the current surface requires
`--authorize-vps-package-write` and delegates to `--execution-mode vps`. The
next edit packet may reconcile that source-controlled mismatch. Until later
source-controlled remediation narrows or renames it,
`--authorize-vps-package-write` remains authority-bearing. Bounded VPS
execution remains unauthorized, and legacy-name adjudication is allowed only by
later source-controlled remediation.

`order_state.json` remains `ABSENT_EXCLUDED_NOT_BOUND`; this authorization
packet does not authorize order-state binding, reads, writes, or broker-visible
state expansion.

The authorization packet preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`package_capture_execution=NOT_AUTHORIZED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`production_runtime_provider_selection_runtime_changes=BLOCKED`,
`production_package_capture_orchestrator_behavior_changes=NOT_AUTHORIZED_BY_THIS_GATE`,
`vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The authorization packet performed no remediation, no package capture, no
replay, no scoring, no candidate generation, no broker/TWS/API/network/runtime
action, no VPS action, no package-capture/orchestrator production behavior
change, no Unit 12 implementation, no commit, and no push.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET`.

### Post-D11 Replay Package Capture Operator Run Blocker Remediation Edit Packet

The bounded source-controlled remediation edit packet is recorded here:

docs/post_d11_replay_package_capture_operator_run_blocker_remediation_edit_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET`
at `source_commit=340f26fce661c0a36179d3a7473dafe8a209d086` and selects the
single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_BLOCKER_REMEDIATION_EDIT_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`.

Artifact-path remediation criteria are source-controlled: any later bounded
operator-run reauthorization must fail closed unless an explicit safe `run_id`
is supplied, `logs/<run_id>.jsonl` exists, `run_reports/<run_id>.json` or
`last_run_report.json` exists and aligns to the selected `run_id`, terminal
completion is present, D13 market-session eligibility is evaluated from
already-existing artifacts, `replay_packages/<run_id>` is absent, capture
readiness is reproved, and no mixed-run-id, stale report, path traversal,
overwrite, future, leaked, or post-decision evidence appears.

The artifact criteria create no `logs/`, no `run_reports/`, no
`replay_packages/`, no `last_run_report.json`, and no `order_state.json`.
`replay_packages` remains a package-output target only, not proof of runtime
artifact availability.

Authority-surface remediation is blocked by the concrete blocker
`NO_SAFE_LOCAL_MAC_PACKAGE_CAPTURE_EXECUTION_SURFACE_WITHOUT_PRODUCTION_PACKAGE_CAPTURE_ORCHESTRATOR_BEHAVIOR_CHANGE`.
The inspected operator `capture` path still requires
`--authorize-vps-package-write` and delegates through `--execution-mode vps`.
The inspected orchestrator exposes no safe LOCAL_MAC package-capture execution
mode that can be selected without production package-capture/orchestrator
behavior changes. `--authorize-vps-package-write` remains authority-bearing,
bounded VPS execution remains unauthorized, and the current `capture` path must
not be treated as LOCAL_MAC-safe.

`order_state.json` remains `ABSENT_EXCLUDED_NOT_BOUND`; the edit packet does
not read, write, create, bind, validate, infer, or use broker-visible order
state.

The edit packet preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`package_capture_execution=NOT_AUTHORIZED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`production_runtime_provider_selection_runtime_changes=BLOCKED`,
`production_package_capture_orchestrator_behavior_changes=BLOCKED`,
`vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The edit packet performed no package capture, no replay, no scoring, no
candidate generation, no broker/TWS/API/network/runtime action, no VPS action,
no package-capture/orchestrator production behavior change, no Unit 12 action,
no commit, and no push.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET`.

### Post-D11 Replay Package Capture LOCAL_MAC Command Surface Design Packet

The source-controlled design packet for the LOCAL_MAC command-surface blocker is
recorded here:

docs/post_d11_replay_package_capture_local_mac_command_surface_design_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET` at
`source_commit=e869845e47f3982b7c74b8151665616964d9af97` and selects the
single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_DESIGN_PACKET_COMPLETED_READY_FOR_IMPLEMENTATION_EDIT_PACKET`.

The design defines a distinct LOCAL_MAC package-capture command surface,
separate from VPS package writing. The future implementation may introduce a
local-only operator surface such as
`capture-local --run-id <run_id> --expected-commit <commit> --authorize-local-package-write`,
or an equivalent source-controlled command surface. The LOCAL_MAC path must not
require `--authorize-vps-package-write`, must not delegate through
`--execution-mode vps`, must not perform real `/opt` VPS reads or writes, and
must not approve VPS endpoint, `18789`, `18791`, bridge, tunnel, or proxy
authority.

The design preserves `--authorize-vps-package-write` as authority-bearing. It
does not treat that flag as legacy-only. Bounded VPS execution remains
`NOT_AUTHORIZED` unless a later bounded VPS execution gate explicitly
authorizes it. Package capture execution remains `NOT_AUTHORIZED` until a later
bounded operator-run reauthorization gate explicitly authorizes it.

The future implementation edit packet may choose to expose an existing
non-synthetic local execution mode if one exists, add a new local execution
mode if needed, bypass the VPS orchestration path through a safe local-only
package writer path, or block if none can be implemented without unacceptable
behavior drift. The design permits only source-controlled LOCAL_MAC command
surface changes, local-only preflight gating, local-only package output path
control, and local-only tests/docs.

Artifact fail-closed design remains active: no artifact creation, no `run_id`
selection from absent artifacts, fail closed if `logs/<run_id>.jsonl` is
absent, fail closed if `run_reports/<run_id>.json` or `last_run_report.json`
alignment is absent, preserve `replay_packages` as an output target only, and
require expected commit, worktree, `run_id`, terminal completion, D13
eligibility, package-directory absence, and alignment checks before any later
operator-run reattempt.

`order_state.json` remains `ABSENT_EXCLUDED_NOT_BOUND`; the design prohibits
order-state reads, writes, creation, binding, validation, inference, and
broker-visible state inference.

The future implementation edit packet must not change strategy behavior, risk
behavior, execution behavior, broker behavior, provider-selection runtime
behavior, scheduler/runtime/service/systemd/timer behavior, credentials or
environment files, Unit 12, replay behavior, scoring behavior,
candidate-generation behavior, broker submit readiness, live trading readiness,
account/order/execution authority, VPS endpoint approval, `18789`/`18791`,
bridge, tunnel, or proxy approval.

The design packet performed no implementation, no package capture, no replay,
no scoring, no candidate generation, no broker/TWS/API/network/runtime action,
no VPS action, no package-capture/orchestrator production behavior change, no
Unit 12 action, no commit, and no push.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET`.

### Post-D11 Replay Package Capture LOCAL_MAC Command Surface Implementation Edit Packet

The source-controlled implementation edit packet for the LOCAL_MAC command
surface is recorded here:

docs/post_d11_replay_package_capture_local_mac_command_surface_implementation_edit_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET`
at `source_commit=69d4a5232bfc4b8a8b3f37ed6210df24d90eaa48` and selects the
single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_COMMAND_SURFACE_IMPLEMENTATION_EDIT_PACKET_COMPLETED_READY_FOR_OPERATOR_RUN_REAUTHORIZATION_PACKET`.

The implementation adds a distinct LOCAL_MAC operator command surface:
`capture-local --run-id <run_id> --expected-commit <commit> --authorize-local-package-write`.
The command requires `--run-id`, requires `--expected-commit`, requires
`--authorize-local-package-write`, does not require or accept
`--authorize-vps-package-write` as LOCAL_MAC authority, does not delegate
through `--execution-mode vps`, does not call
`package_execution_orchestrator.main`, does not write packages, and does not
execute package capture. The existing VPS `capture` path remains isolated and
unchanged.

The LOCAL_MAC path is fail-closed. It requires clean source-control checks,
safe `run_id`, `logs/<run_id>.jsonl`, `run_reports/<run_id>.json` or
`last_run_report.json`, absent `replay_packages/<run_id>`, capture readiness
reproved from already-existing artifacts, local-only authorization, no VPS
package-write authority use, no `--execution-mode vps`, and
`order_state_json=ABSENT_EXCLUDED_NOT_BOUND`. It creates no artifacts, no
`logs/`, no `run_reports/`, no `replay_packages/`, no `last_run_report.json`,
no `order_state.json`, and no package artifact.

If all local preflight checks pass, the command reports
`LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_READY_REAUTHORIZATION_REQUIRED`; this is
not package-capture authorization. If any check fails, it reports
`LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_FAILED_CLOSED`.

The prior concrete blocker
`NO_SAFE_LOCAL_MAC_PACKAGE_CAPTURE_EXECUTION_SURFACE_WITHOUT_PRODUCTION_PACKAGE_CAPTURE_ORCHESTRATOR_BEHAVIOR_CHANGE`
is remediated at the command-surface level. Package capture execution remains
`NOT_AUTHORIZED` until a later bounded operator-run reauthorization gate
explicitly authorizes it. Bounded VPS execution remains `NOT_AUTHORIZED`.

The implementation preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`package_capture_execution=NOT_AUTHORIZED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`production_runtime_provider_selection_runtime_changes=BLOCKED`,
`bounded_vps_execution=NOT_AUTHORIZED`,
`vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The implementation edit packet performed no package capture, no replay, no
scoring, no candidate generation, no broker/TWS/API/network/runtime action, no
VPS action, no Unit 12 action, no commit, and no push.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_REAUTHORIZATION_PACKET`.

### Post-D11 Replay Package Capture Operator Run Reauthorization Packet

The source-controlled reauthorization packet for the bounded LOCAL_MAC
operator-run reattempt is recorded here:

docs/post_d11_replay_package_capture_operator_run_reauthorization_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_REAUTHORIZATION_PACKET` at
`source_commit=53a836ac91e3d9fd11cf9b9368e1eab6128657e4` and selects the
single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_REAUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_LOCAL_MAC_OPERATOR_RUN`.

The only authorized future command surface is
`.venv-312/bin/python tools/ops/gate_d_market_session_operator.py capture-local --run-id <run_id> --expected-commit 53a836ac91e3d9fd11cf9b9368e1eab6128657e4 --authorize-local-package-write`.
This reauthorization packet is source-controlled approval only; it performs no
package capture and does not execute the operator run.

The later bounded operator-run packet must fail closed unless branch is `main`,
LOCAL_MAC HEAD and `origin/main` both equal
`53a836ac91e3d9fd11cf9b9368e1eab6128657e4`, worktree is clean, a concrete safe
`run_id` is supplied from already-existing eligible artifacts,
`logs/<run_id>.jsonl` exists, `run_reports/<run_id>.json` exists or
`last_run_report.json` alignment exists, report evidence is aligned to the
selected `run_id`, terminal completion evidence is present, capture readiness
is reproved from already-existing artifacts, and `replay_packages/<run_id>` is
absent before package capture.

The future operator-run packet must preserve
`order_state_json=ABSENT_EXCLUDED_NOT_BOUND`; no `order_state` read, write,
creation, binding, validation, inference, or use is authorized. It must not use
`--authorize-vps-package-write`, must not use `--execution-mode vps`, must not
delegate to `package_execution_orchestrator.main`, and must not perform VPS,
broker/TWS/API/network/runtime/scheduler/systemd/timer/service, replay,
scoring, candidate-generation, or Unit 12 action.

The packet preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`package_capture_execution_in_this_gate=NOT_AUTHORIZED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`production_runtime_provider_selection_runtime_changes=BLOCKED`,
`production_broker_behavior_changes=BLOCKED`,
`bounded_vps_execution=NOT_AUTHORIZED`,
`vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`.

### Post-D11 Replay Package Capture Operator Run Expected Commit Alignment Packet

The source-controlled expected-commit alignment packet for the bounded
LOCAL_MAC operator-run envelope is recorded here:

docs/post_d11_replay_package_capture_operator_run_expected_commit_alignment_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_EXPECTED_COMMIT_ALIGNMENT_PACKET`
for audit state `local_head=72de932896ca33327efe23f17de055ddf5f9162d`,
`origin_main=72de932896ca33327efe23f17de055ddf5f9162d`, `branch=main`, and
`status_short=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_OPERATOR_RUN_EXPECTED_COMMIT_ALIGNMENT_PACKET_COMPLETED_READY_FOR_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`.

The historical reauthorization packet remains a valid source-controlled
approval artifact, but its static future command binding
`--expected-commit 53a836ac91e3d9fd11cf9b9368e1eab6128657e4` is superseded for
future execution-envelope resolution. The implementation source commit
`53a836ac91e3d9fd11cf9b9368e1eab6128657e4` remains the validated LOCAL_MAC
command-surface implementation basis, not the active operator-run expected
commit.

The active expected commit must be resolved during bounded operator-run
preflight from the current clean, branch-main, origin-aligned HEAD. The bounded
operator-run packet must print and lock `branch=main`,
`local_head=<resolved_current_head>`, `origin_main=<same_resolved_current_head>`,
`status_short=clean`, and `expected_commit=<same_resolved_current_head>`. No
static replacement expected commit is hardcoded in the alignment packet because
the alignment packet commit itself will advance HEAD.

The only authorized future command template is:

```text
EXPECTED_COMMIT="$(git rev-parse HEAD)"
.venv-312/bin/python tools/ops/gate_d_market_session_operator.py capture-local --run-id <run_id> --expected-commit "$EXPECTED_COMMIT" --authorize-local-package-write
```

The later bounded operator-run packet must fail closed unless branch is `main`,
worktree is clean, LOCAL_MAC HEAD equals `origin/main`, `expected_commit`
equals the current LOCAL_MAC HEAD and `origin/main` at bounded-run preflight, a
concrete safe `run_id` is supplied from already-existing eligible artifacts,
`logs/<run_id>.jsonl` exists, `run_reports/<run_id>.json` exists or
`last_run_report.json` alignment exists, report evidence is aligned to the
selected `run_id`, terminal completion evidence is present, capture readiness
is reproved from already-existing artifacts, and `replay_packages/<run_id>` is
absent before package capture.

The future operator-run packet must preserve
`order_state_json=ABSENT_EXCLUDED_NOT_BOUND`; no `order_state` read, write,
creation, binding, validation, inference, or use is authorized. It must not use
`--authorize-vps-package-write`, must not use `--execution-mode vps`, must not
delegate to `package_execution_orchestrator.main`, and must not perform VPS,
broker/TWS/API/network/runtime/scheduler/systemd/timer/service, replay,
scoring, candidate-generation, or Unit 12 action.

The packet preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`package_capture_execution_in_this_gate=NOT_AUTHORIZED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`production_runtime_provider_selection_runtime_changes=BLOCKED`,
`production_command_surface_changes=BLOCKED`,
`production_broker_behavior_changes=BLOCKED`,
`bounded_vps_execution=NOT_AUTHORIZED`,
`vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The exact next permissible gate remains
`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET`.

### Post-D11 Replay Package Capture Bounded LOCAL_MAC Operator Run Packet

The source-controlled bounded LOCAL_MAC operator-run packet is recorded here:

docs/post_d11_replay_package_capture_bounded_local_mac_operator_run_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET` for
`local_head=b06d8a4b96c9237911547cffa6bb31b1d8bf829d`,
`origin_main=b06d8a4b96c9237911547cffa6bb31b1d8bf829d`,
`expected_commit=b06d8a4b96c9237911547cffa6bb31b1d8bf829d`, `branch=main`,
and `status_short=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_OPERATOR_RUN_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`.

The concrete blocker is
`NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS_FOR_PACKAGE_CAPTURE`.

The preflight inventory records `logs=ABSENT`, `run_reports=ABSENT`,
`replay_packages=ABSENT`, `last_run_report.json=ABSENT`,
`order_state.json=ABSENT`, `LOG CANDIDATES=NO_LOGS_DIR`,
`RUN_REPORT CANDIDATES=NO_RUN_REPORTS_DIR`,
`REPLAY_PACKAGE EXISTING TARGETS=NO_REPLAY_PACKAGES_DIR`,
`LAST_RUN_REPORT STATUS=NO_LAST_RUN_REPORT`, and
`ORDER_STATE STATUS=PASS_order_state_absent_excluded_not_bound`.

The `replay_packages` directory absence is not itself the blocking
runtime-artifact criterion because `replay_packages` is a package output target,
not proof of runtime artifact availability. The blocking criteria are absence
of `logs/<run_id>.jsonl`, absence of `run_reports/<run_id>.json` or
`last_run_report.json`, absence of an eligible `run_id`, absence of aligned
report evidence, and absence of terminal completion evidence.

The packet preserves `order_state_json=ABSENT_EXCLUDED_NOT_BOUND`; no
`order_state` read, write, creation, binding, validation, inference, or use is
authorized. It records no `--authorize-vps-package-write`, no `--execution-mode
vps`, no `package_execution_orchestrator.main` delegation, no VPS action, no
broker/TWS/API/network/runtime/scheduler/systemd/timer/service action, no
replay, no scoring, no candidate generation, and no Unit 12 action.

The packet preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`package_capture_execution=NOT_AUTHORIZED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`production_runtime_provider_selection_runtime_changes=BLOCKED`,
`production_command_surface_changes=BLOCKED`,
`production_broker_behavior_changes=BLOCKED`,
`bounded_vps_execution=NOT_AUTHORIZED`,
`vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_AVAILABILITY_PACKET`.

### Post-D11 Replay Package Capture LOCAL_MAC Runtime Artifact Availability Packet

The source-controlled LOCAL_MAC runtime artifact availability packet is
recorded here:

docs/post_d11_replay_package_capture_local_mac_runtime_artifact_availability_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_AVAILABILITY_PACKET`
at `source_commit=b8e9e17ad5fe7377dd721c24e859b66f8024e0e0` with
`local_head=b8e9e17ad5fe7377dd721c24e859b66f8024e0e0`,
`origin_main=b8e9e17ad5fe7377dd721c24e859b66f8024e0e0`,
`expected_commit=b8e9e17ad5fe7377dd721c24e859b66f8024e0e0`, `branch=main`,
and `status_short=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_AVAILABILITY_PACKET_READY_FOR_BOUNDED_LOCAL_MAC_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET`.

The current artifact availability result is
`NO_ELIGIBLE_LOCAL_MAC_RUNTIME_ARTIFACTS_CURRENTLY_AVAILABLE`. The inventory
records `logs=ABSENT`, `run_reports=ABSENT`, `replay_packages=ABSENT`,
`last_run_report.json=ABSENT`, `order_state.json=ABSENT`,
`LOG CANDIDATES=NO_LOGS_DIR`, `RUN_REPORT CANDIDATES=NO_RUN_REPORTS_DIR`,
`REPLAY_PACKAGE EXISTING TARGETS=NO_REPLAY_PACKAGES_DIR`,
`LAST_RUN_REPORT STATUS=NO_LAST_RUN_REPORT`, and
`ORDER_STATE STATUS=PASS_order_state_absent_excluded_not_bound`.

No eligible package-capture `run_id` is currently available because logs,
run_reports, and last_run_report.json are absent; there are no log candidates,
no run-report candidates, no aligned report evidence, and no terminal
completion evidence. The `replay_packages` directory absence is not itself
proof of runtime artifact unavailability because `replay_packages` is a package
output target, not proof of runtime artifact availability.

The packet does not produce runtime artifacts and does not authorize runtime
artifact production by itself. It records
`runtime_artifact_production=NOT_AUTHORIZED_BY_THIS_GATE`,
`runtime_artifact_generation=NOT_AUTHORIZED_BY_THIS_GATE`,
`diagnostic_runtime_report_generation=NOT_AUTHORIZED`, and
`package_capture_execution=NOT_AUTHORIZED`.

The packet preserves `order_state_json=ABSENT_EXCLUDED_NOT_BOUND`; no
`order_state` read, write, creation, binding, validation, inference, or use is
authorized. It preserves no `--authorize-vps-package-write`, no `--execution-mode
vps`, no `package_execution_orchestrator.main` delegation, no VPS action, no
broker/TWS/API/network/runtime/scheduler/systemd/timer/service action, no
replay, no scoring, no candidate generation, and no Unit 12 action.

The packet preserves `broker_submit_readiness=NOT_APPROVED`,
`live_trading_readiness=NOT_APPROVED`, `account_authority=NONE`,
`order_authority=NONE`, `execution_authority=NONE`,
`strategy_risk_execution_changes=BLOCKED`,
`scheduler_runtime_service_systemd_timer_changes=BLOCKED`,
`credential_environment_changes=BLOCKED`,
`production_runtime_provider_selection_runtime_changes=BLOCKED`,
`production_command_surface_changes=BLOCKED`,
`production_broker_behavior_changes=BLOCKED`,
`package_writer_reader_orchestrator_changes=BLOCKED`,
`bounded_vps_execution=NOT_AUTHORIZED`,
`vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`, and
`unit_12_implementation=NOT_OPENED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET`.

### Post-D11 Replay Package Capture LOCAL_MAC Runtime Artifact Production Authorization Packet

The source-controlled LOCAL_MAC runtime artifact production authorization packet
is recorded here:

docs/post_d11_replay_package_capture_local_mac_runtime_artifact_production_authorization_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET`
at `source_commit=d84aa9cdcd21ddfd32f5d39ec1156f76071170ba` with
`local_head=d84aa9cdcd21ddfd32f5d39ec1156f76071170ba`,
`origin_main=d84aa9cdcd21ddfd32f5d39ec1156f76071170ba`, `branch=main`, and
`worktree=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_LOCAL_MAC_RUNTIME_ARTIFACT_PRODUCTION_AUTHORIZATION_PACKET_APPROVED_FOR_BOUNDED_LOCAL_MAC_READ_ONLY_ARTIFACT_PRODUCTION_PACKET`.

The packet authorizes only the later source-controlled gate
`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET`.
It does not produce runtime artifacts and does not authorize package capture.

The packet records the current inventory as `logs=ABSENT`,
`run_reports=ABSENT`, `replay_packages=ABSENT`,
`last_run_report.json=ABSENT`, and `order_state.json=ABSENT_EXCLUDED_NOT_BOUND`.
It preserves `package_capture_execution=NOT_AUTHORIZED`,
`runtime_artifact_production_in_this_gate=NOT_PERFORMED`,
`runtime_artifact_generation_in_this_gate=NOT_PERFORMED`,
`diagnostic_runtime_report_generation_in_this_gate=NOT_PERFORMED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`, `unit_12_implementation=NOT_OPENED`,
`broker_submit_readiness=NOT_APPROVED`, `live_trading_readiness=NOT_APPROVED`,
`account_authority=NONE`, `order_authority=NONE`, `execution_authority=NONE`,
`bounded_vps_execution=NOT_AUTHORIZED`, `vps_endpoint_approval=NOT_APPROVED`,
`endpoint_18789_18791_approval=NOT_APPROVED`,
`bridge_tunnel_proxy_approval=NOT_APPROVED`,
`production_command_surface_changes=BLOCKED`, and
`package_writer_reader_orchestrator_changes=BLOCKED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET`.

### Post-D11 Replay Package Capture Bounded LOCAL_MAC Read-Only Runtime Artifact Production Packet

The source-controlled bounded LOCAL_MAC read-only runtime artifact production
packet is recorded here:

docs/post_d11_replay_package_capture_bounded_local_mac_read_only_runtime_artifact_production_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET`
at `source_commit=a149cdcae1665edd0637897d340393a53133f9dc` with
`local_head=a149cdcae1665edd0637897d340393a53133f9dc`,
`origin_main=a149cdcae1665edd0637897d340393a53133f9dc`, `branch=main`, and
`worktree=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_BOUNDED_LOCAL_MAC_READ_ONLY_RUNTIME_ARTIFACT_PRODUCTION_PACKET_APPROVED_FOR_ONE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`.

The packet authorizes only the next source-controlled gate
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET`.
It does not execute that run and does not create artifacts in this Codex step.

The packet records the current inventory as `logs=ABSENT`,
`run_reports=ABSENT`, `replay_packages=ABSENT`,
`last_run_report.json=ABSENT`, and `order_state.json=ABSENT_EXCLUDED_NOT_BOUND`.
It preserves `package_capture_execution=NOT_AUTHORIZED`,
`runtime_artifact_production_in_this_gate=NOT_PERFORMED`,
`runtime_artifact_generation_in_this_gate=NOT_PERFORMED`,
`diagnostic_runtime_report_generation_in_this_gate=NOT_PERFORMED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`, `unit_12_implementation=NOT_OPENED`,
`broker_submit_readiness=NOT_APPROVED`, `live_trading_readiness=NOT_APPROVED`,
`account_authority=NONE`, `order_authority=NONE`, `execution_authority=NONE`,
`vps_action=NOT_AUTHORIZED`, `bounded_vps_execution=NOT_AUTHORIZED`,
`production_behavior_changes=BLOCKED`,
`production_command_surface_changes=BLOCKED`, and
`package_writer_reader_orchestrator_changes=BLOCKED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET`.

### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Run Packet

The source-controlled DIRECT_MAC_TERMINAL read-only artifact production run
packet is recorded here:

docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_run_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET`
at `source_commit=99c64e16a992c4ce320fea20263ad600468bb6da` with
`local_head=99c64e16a992c4ce320fea20263ad600468bb6da`,
`origin_main=99c64e16a992c4ce320fea20263ad600468bb6da`, `branch=main`, and
`worktree=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN_PACKET_APPROVED_FOR_ONE_DIRECT_MAC_TERMINAL_READ_ONLY_RUN`.

The packet defines the exact next operator step as
`ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`. It does
not execute that operator step and does not create artifacts in this Codex
gate.

The packet records the current inventory as `logs=ABSENT`,
`run_reports=ABSENT`, `replay_packages=ABSENT`,
`last_run_report.json=ABSENT`, and `order_state.json=ABSENT_EXCLUDED_NOT_BOUND`.
It preserves `package_capture_execution=NOT_AUTHORIZED`,
`runtime_artifact_production_in_this_codex_gate=NOT_PERFORMED`,
`runtime_artifact_generation_in_this_codex_gate=NOT_PERFORMED`,
`diagnostic_runtime_report_generation_in_this_codex_gate=NOT_PERFORMED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`, `unit_12_implementation=NOT_OPENED`,
`broker_submit_readiness=NOT_APPROVED`, `live_trading_readiness=NOT_APPROVED`,
`account_authority=NONE`, `order_authority=NONE`, `execution_authority=NONE`,
`vps_action=NOT_AUTHORIZED`, `bounded_vps_execution=NOT_AUTHORIZED`,
`production_behavior_changes=BLOCKED`,
`production_command_surface_changes=BLOCKED`, and
`package_writer_reader_orchestrator_changes=BLOCKED`.

The exact next operator step is
`ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`.

### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Blocker Packet

The source-controlled DIRECT_MAC_TERMINAL read-only artifact production command
surface blocker packet is recorded here:

docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_blocker_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_BLOCKER_PACKET`
at `source_commit=b6ecbe488918e3b1d92d9de73327db2eea161989` with
`local_head=b6ecbe488918e3b1d92d9de73327db2eea161989`,
`origin_main=b6ecbe488918e3b1d92d9de73327db2eea161989`, `branch=main`, and
`worktree=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_BLOCKER_PACKET_BLOCKED_WITH_CONCRETE_BLOCKER`.

The concrete blocker is
`NO_EXACT_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_DEFINED`.
The prior packet approved only the symbolic operator step
`ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_RUN`.
Command-surface inspection found `capture-local` references only;
`capture-local` is package-capture related and requires eligible existing
runtime artifacts.

The packet records the current inventory as `logs=ABSENT`,
`run_reports=ABSENT`, `replay_packages=ABSENT`,
`last_run_report.json=ABSENT`, and `order_state.json=ABSENT_EXCLUDED_NOT_BOUND`.
It preserves `package_capture_execution=NOT_AUTHORIZED`,
`runtime_artifact_production_execution=NOT_AUTHORIZED_BY_THIS_GATE`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`, `unit_12_implementation=NOT_OPENED`,
`broker_submit_readiness=NOT_APPROVED`, `live_trading_readiness=NOT_APPROVED`,
`account_authority=NONE`, `order_authority=NONE`, `execution_authority=NONE`,
`vps_action=NOT_AUTHORIZED`, `bounded_vps_execution=NOT_AUTHORIZED`,
`production_code_changes=BLOCKED`, `command_surface_code_changes=BLOCKED`,
and `package_writer_reader_orchestrator_changes=BLOCKED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET`.

### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Design Packet

The source-controlled DIRECT_MAC_TERMINAL read-only artifact production command
surface design packet is recorded here:

docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_design_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET`
at `source_commit=e9a10ff406d46a77417af50800155cb8f057d4b7` with
`local_head=e9a10ff406d46a77417af50800155cb8f057d4b7`,
`origin_main=e9a10ff406d46a77417af50800155cb8f057d4b7`, `branch=main`, and
`worktree=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_DESIGN_PACKET_READY_FOR_IMPLEMENTATION_GATE`.

The exact proposed command surface is
`.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production`.
The design requires branch `main`, clean worktree, LOCAL_MAC HEAD equal to
`origin/main`, expected commit equal to both, LOCAL_MAC-only execution,
DIRECT_MAC_TERMINAL-only operation, and read-only/no-broker/no-order/no-execution
authority boundaries.

The designed allowed outputs are `logs/<run_id>.jsonl` and
`run_reports/<run_id>.json`. Prohibited outputs include `replay_packages/<run_id>`,
package capture artifacts, replay output, scoring output, candidate-generation
output, Unit 12 output, `order_state.json`, broker/account/order/execution
artifacts, credential or environment files, and scheduler/runtime/service/
systemd/timer mutation artifacts.

The packet preserves `package_capture_execution=NOT_AUTHORIZED`,
`runtime_artifact_production_execution=NOT_AUTHORIZED_BY_THIS_DESIGN_GATE`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`, `unit_12_implementation=NOT_OPENED`,
`broker_submit_readiness=NOT_APPROVED`, `live_trading_readiness=NOT_APPROVED`,
`account_authority=NONE`, `order_authority=NONE`, `execution_authority=NONE`,
`vps_action=NOT_AUTHORIZED`, `bounded_vps_execution=NOT_AUTHORIZED`,
`production_code_changes=BLOCKED_BY_THIS_GATE`,
`command_surface_code_changes=DESIGNED_ONLY_NOT_IMPLEMENTED`, and
`package_writer_reader_orchestrator_changes=BLOCKED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET`.

### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Implementation Packet

The source-controlled DIRECT_MAC_TERMINAL read-only artifact production command
surface implementation packet is recorded here:

docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_implementation_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET`
at `source_commit=71b2717d53ec71afc4a3bead1938a704b8be58b1` with
`local_head=71b2717d53ec71afc4a3bead1938a704b8be58b1`,
`origin_main=71b2717d53ec71afc4a3bead1938a704b8be58b1`, `branch=main`, and
`worktree=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_PACKET_READY_FOR_LOCAL_DIFF_REVIEW`.

The implemented command surface is
`.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production`.
It requires `--run-id`, `--expected-commit`, and
`--authorize-direct-mac-terminal-read-only-artifact-production`.

The implementation enforces current HEAD equals expected commit, local
`origin/main` equals expected commit, LOCAL_MAC HEAD equals local `origin/main`,
clean worktree, safe run ID, LOCAL_MAC-only source context, DIRECT_MAC_TERMINAL
operator surface, and read-only/no-broker/no-order/no-execution authority
boundaries. The later command may write only `logs/<run_id>.jsonl`,
`run_reports/<run_id>.json`, and `last_run_report.json` if separately invoked
by a later authorized operator run.

The packet preserves `package_capture_execution=NOT_AUTHORIZED`,
`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`, `unit_12_implementation=NOT_OPENED`,
`broker_submit_readiness=NOT_APPROVED`, `live_trading_readiness=NOT_APPROVED`,
`account_authority=NONE`, `order_authority=NONE`, `execution_authority=NONE`,
`vps_action=NOT_AUTHORIZED`, and `bounded_vps_execution=NOT_AUTHORIZED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_LOCAL_REVIEW_PACKET`.

### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Command Surface Implementation Local Review Packet

The source-controlled DIRECT_MAC_TERMINAL read-only artifact production command
surface implementation local review packet is recorded here:

docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_command_surface_implementation_local_review_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_LOCAL_REVIEW_PACKET`
at `source_commit=19aff6b597e632427f54e9d8f52972b5eae9f546` with
`local_head=19aff6b597e632427f54e9d8f52972b5eae9f546`,
`origin_main=19aff6b597e632427f54e9d8f52972b5eae9f546`, `branch=main`, and
`worktree=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMMAND_SURFACE_IMPLEMENTATION_LOCAL_REVIEW_PACKET_READY_FOR_OPERATOR_RUN_AUTHORIZATION_PACKET`.

The reviewed command surface is
`.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id <run_id> --expected-commit <commit> --authorize-direct-mac-terminal-read-only-artifact-production`.
The packet records the completed LOCAL_MAC compact review, LOCAL_MAC commit and
push alignment at `19aff6b597e632427f54e9d8f52972b5eae9f546`, and VPS
validation evidence: `PASS_head_matches_expected_19aff6b`,
`PASS_head_origin_main_aligned`, and `120 passed`.

The packet preserves `produce_read_only_artifacts_run_by_this_gate=false`,
`package_capture_execution=NOT_AUTHORIZED`,
`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`, `unit_12_implementation=NOT_OPENED`,
`broker_submit_readiness=NOT_APPROVED`, `live_trading_readiness=NOT_APPROVED`,
`account_authority=NONE`, `order_authority=NONE`, `execution_authority=NONE`,
`vps_action_by_this_gate=false`, and `bounded_vps_execution=NOT_AUTHORIZED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_PACKET`.

### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Authorization Packet

The source-controlled DIRECT_MAC_TERMINAL read-only artifact production operator
run authorization packet is recorded here:

docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_operator_run_authorization_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_PACKET`
at `source_commit=dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2` with
`local_head=dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`,
`origin_main=dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`, `branch=main`, and
`worktree=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_PACKET_APPROVED_FOR_ONE_BOUNDED_DIRECT_MAC_TERMINAL_READ_ONLY_OPERATOR_RUN`.

The packet authorizes exactly one later LOCAL_MAC / DIRECT_MAC_TERMINAL operator
attempt using run ID `post_d11_direct_mac_read_only_artifacts_001`, expected
commit `dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`, and command
`.venv-312/bin/python tools/ops/gate_d_market_session_operator.py produce-read-only-artifacts --run-id post_d11_direct_mac_read_only_artifacts_001 --expected-commit dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2 --authorize-direct-mac-terminal-read-only-artifact-production`.

The packet records VPS validation evidence:
`PASS_head_matches_expected_dcdf6e9`, `PASS_head_origin_main_aligned`, and
`121 tests passed`. It permits only later outputs
`logs/post_d11_direct_mac_read_only_artifacts_001.jsonl`,
`run_reports/post_d11_direct_mac_read_only_artifacts_001.json`, and
`last_run_report.json`.

The packet preserves `produce_read_only_artifacts_run_by_this_gate=false`,
`package_capture_execution=NOT_AUTHORIZED`,
`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`, `unit_12_implementation=NOT_OPENED`,
`broker_submit_readiness=NOT_APPROVED`, `live_trading_readiness=NOT_APPROVED`,
`account_authority=NONE`, `order_authority=NONE`, `execution_authority=NONE`,
`vps_action_by_this_gate=false`, and `bounded_vps_execution=NOT_AUTHORIZED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_PACKET`.

### Post-D11 Replay Package Capture DIRECT_MAC_TERMINAL Read-Only Artifact Production Operator Run Expected-Commit Adjudication Packet

The source-controlled DIRECT_MAC_TERMINAL read-only artifact production operator
run expected-commit adjudication packet is recorded here:

docs/post_d11_replay_package_capture_direct_mac_terminal_read_only_artifact_production_operator_run_expected_commit_adjudication_packet.md

The packet records
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_EXPECTED_COMMIT_ADJUDICATION_PACKET`
at `source_commit=44a39de7728c681aa5f5f8e1ef1a0fec67745bf3` with
`local_head=44a39de7728c681aa5f5f8e1ef1a0fec67745bf3`,
`origin_main=44a39de7728c681aa5f5f8e1ef1a0fec67745bf3`, `branch=main`, and
`worktree=clean`. It selects the single decision
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_EXPECTED_COMMIT_ADJUDICATION_PACKET_BLOCKED_PENDING_CORRECTED_OPERATOR_RUN_AUTHORIZATION`.

The concrete blocker is
`AUTHORIZED_EXPECTED_COMMIT_DOES_NOT_MATCH_CURRENT_SOURCE_OF_TRUTH_HEAD`. The
prior authorization command used expected commit
`dcdf6e91ce8942226ae50e4cbf0e11743ec8cfc2`, while the current source-of-truth
HEAD and `origin/main` are `44a39de7728c681aa5f5f8e1ef1a0fec67745bf3`.

The packet records VPS validation evidence:
`PASS_head_matches_expected_44a39de`, `PASS_head_origin_main_aligned`, and
`122 tests passed`. It preserves
`produce_read_only_artifacts_run_by_this_gate=false`,
`package_capture_execution=NOT_AUTHORIZED`,
`runtime_artifact_production_execution_in_this_gate=NOT_PERFORMED`,
`replay_execution=NOT_AUTHORIZED`, `scoring_execution=NOT_AUTHORIZED`,
`candidate_generation_execution=NOT_AUTHORIZED`, `unit_12_implementation=NOT_OPENED`,
`broker_submit_readiness=NOT_APPROVED`, `live_trading_readiness=NOT_APPROVED`,
`account_authority=NONE`, `order_authority=NONE`, `execution_authority=NONE`,
`vps_action_by_this_gate=false`, and `bounded_vps_execution=NOT_AUTHORIZED`.

The exact next permissible gate is
`POST_D11_REPLAY_PACKAGE_CAPTURE_DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_OPERATOR_RUN_AUTHORIZATION_CORRECTION_PACKET`.

## Gate D Record D15: Candidate-Evidence Mechanism Design Record

### D15 Status

Recorded on 2026-06-13 as a docs-only governance/design record. D15 defines how
future candidate evidence may be produced or represented before any
baseline-vs-candidate comparison can exist. It implements no candidate replay
execution, no candidate package construction, no scoring, no evaluation, no
promotion, no broker/order authority, and no trading behavior.

D15 satisfies the Gate D Record D12 requirement for a candidate-evidence
mechanism decision at the design-record level only. It does not produce candidate
evidence and does not open any candidate execution lane.

### D15 Candidate-Evidence Mechanism Requirements

Any future candidate-evidence mechanism must be governed before any
baseline-vs-candidate pair can exist. At minimum, candidate evidence must:

- Carry an explicit `candidate_strategy_id` compatible with Unit 6 candidate
  strategy identity governance (`tools/replay/candidate_strategy_governance.py`).
- Carry an explicit `parameter_version` compatible with Unit 6 parameter
  versioning.
- Be distinguishable from baseline evidence in D14 ledger membership
  (`evidence_membership == candidate`) and in Unit 7 comparison governance.
- Be reproducible from pinned source inputs and a pinned `source_commit`.
- Use as-of decision-time evidence only, with no future, leaked, or
  post-decision data.
- Never mutate baseline packages.
- Never retroactively relabel production baseline packages as candidates.
- Never depend on broker/API/order-state/live execution.
- Be compatible with D14 package capture ledger membership and Unit 6/Unit 7
  candidate/comparison governance.
- Preserve package-set, reproducibility, as-of, and integrity declarations
  required by D5, D6, D9, and D14.

### D15 Possible Future Mechanisms

D15 separates possible future mechanisms without approving any of them:

- **Offline candidate replay from immutable baseline evidence**: a future
  governed replay mechanism may derive deterministic candidate decisions from
  already-finalized immutable baseline replay inputs, preserving the original
  baseline evidence and recording candidate outputs as separate evidence.
- **Shadow candidate decision generation without broker/order authority**: a
  future governed shadow mechanism may generate candidate decision artifacts
  from approved as-of inputs, but it must not submit orders, bind order state,
  call broker APIs, mutate runtime state, or affect production behavior.
- **Candidate package construction from governed replay inputs**: a future
  governed package mechanism may construct candidate evidence packages from
  approved replay inputs and candidate strategy metadata, but only after a
  separate package-construction gate defines storage, immutability, provenance,
  and ledger rules for candidate artifacts.
- **Explicit exclusion at this stage**: live or paper broker execution is not an
  approved candidate-evidence mechanism. Broker/API/TWS/Alpaca/IBKR execution,
  order submission, order cancellation, order-state binding, paper trading, and
  live trading remain outside D15.

### D15 Minimum Future Candidate-Evidence Acceptance Criteria

Before candidate evidence may be accepted for any future baseline-vs-candidate
pairing declaration, it must provide:

- A deterministic candidate decision artifact.
- `candidate_strategy_id` present.
- `parameter_version` present.
- `source_commit` pinned.
- Input package/run scope declared.
- Baseline package reference declared where applicable.
- Reproducibility declaration present.
- As-of declaration present.
- Integrity attestation present.
- No future, leaked, or post-decision evidence.
- No package mutation.
- No mixed `run_id`.
- No broker/order-state binding.

Candidate evidence that lacks any required identity, version, reproducibility,
as-of, integrity, run-scope, or baseline-reference metadata remains ineligible
for future pairing. Candidate evidence that depends on broker/order/live
execution, mutates baseline packages, relabels baseline packages as candidates,
or uses leaked/post-decision data must fail closed.

### D15 Status Carry-Forward

- Candidate execution remains **UNIMPLEMENTED** and **UNAPPROVED**.
- Candidate package construction remains **UNIMPLEMENTED** and **UNAPPROVED**.
- Package capture remains time-gated until an eligible regular-session
  production run exists and passes D13.
- Evaluation/scoring execution: **BLOCKED**.
- Unit 12: **BLOCKED**.
- Promotion authority: **UNAPPROVED**.
- Broker/API/Alpaca/IBKR/TWS authority: **UNAPPROVED**.
- Strategy/risk/execution behavior: **UNCHANGED**.
- Paper trading and live trading: **UNAPPROVED**.

### D15 Recommended Next Lane

The next candidate-evidence lane should be a **read-only candidate-mechanism
feasibility audit** or a **docs-only candidate-evidence mechanism contract**.
It must not execute candidate replay, create candidate packages, score, evaluate,
open Unit 12, approve promotion, touch broker/API/order-state systems, or change
strategy/risk/execution behavior.

### D15 Non-Authorization Statement

D15 does not authorize candidate replay execution, candidate decision
generation, candidate package construction, package capture execution, package
artifact reads, package mutation, evaluation or scoring execution, Unit 12,
promotion authority, broker/API/TWS/Alpaca/IBKR authority, order-state binding,
strategy/risk/execution behavior changes, systemd/scheduler/runtime activation,
`.env`/credential changes, order submission, cancellation, cleanup, paper
trading approval, or live trading approval.

## Drift Risks

Known drift risks to guard:

- Constants/types mistaken for implementation authority.
- Manifest generation sneaking into schema work.
- Canonical byte generation sneaking into serialization vocabulary work.
- Hash outputs treated as package completeness.
- Storage paths or directories appearing before finalization semantics.
- Runtime capture becoming ungoverned file ingestion.
- Evaluation reports becoming promotion evidence.
- Broker-visible evidence mistaken for broker authority.

## Gate D Record D17: Candidate-Evidence Mechanism Contract

### D17 Status

Recorded on 2026-06-13 as a docs-only governance contract. D17 carries forward
the D16 read-only feasibility audit classification:
`D16_PARTIAL_FEASIBILITY_CONTRACT_REQUIRED`. D16 found that governance
primitives exist, but candidate artifact contract, replay input adapter,
candidate decision schema, candidate-vs-baseline linkage, no-mutation
enforcement, as-of integration, parameter-version bridge, and candidate test
harness are missing.

D17 records the required future contracts before any candidate-evidence
implementation may begin. It implements no candidate replay execution, no
candidate artifact generation, no package capture, no scoring, no evaluation,
no Unit 12 work, no promotion, no broker/API/order execution, and no trading.

### D17 Required Future Candidate-Evidence Contracts

Before candidate evidence may be implemented, the following contracts must be
governed:

- Candidate decision artifact contract.
- Replay input adapter contract.
- Candidate-vs-baseline linkage contract.
- Candidate identity bridge contract.
- Parameter-version bridge contract.
- No-mutation contract.
- As-of enforcement contract.
- Reproducibility declaration contract.
- Integrity attestation contract.
- D14 ledger membership contract.
- Broker/order/live-execution exclusion contract.
- Candidate test harness contract.

### D17 Candidate Decision Artifact Contract

Any future candidate decision artifact must be deterministic, source-controlled
or source-control referenced, and must carry at minimum:

- `candidate_artifact_id`
- `candidate_strategy_id`
- `candidate_parameter_version`
- `source_commit`
- `input_run_id` or `input_package_reference`
- `baseline_package_reference` where applicable
- `decision_timestamp_utc`
- `asof_timestamp_utc`
- `decision_signal`
- `proposed_action`
- `decision_reason`
- `deterministic_inputs_reference`
- `reproducibility_declaration_status`
- `asof_declaration_status`
- `integrity_attestation_status`
- `no_broker_order_state_binding`
- `no_mutation_attestation`

The artifact contract must not create scoring authority, promotion authority,
runtime mutation authority, package capture authority, broker authority,
execution permission, paper trading approval, or live trading authority.

### D17 Replay Input Adapter Contract

Any future replay input adapter for candidate evidence must:

- Consume immutable governed replay inputs only.
- Never mutate baseline packages.
- Preserve original `run_id` and package hash references.
- Expose only as-of decision-time evidence.
- Reject future, leaked, or post-decision evidence.
- Reject broker, order-state, API, and live-execution fields.
- Fail closed on missing identity, version, integrity, reproducibility, as-of,
  run-scope, or package-reference metadata.

The adapter contract may define deterministic read models in a later gate, but
D17 does not authorize package artifact reads, filesystem reads, package
discovery, package mutation, or candidate replay execution.

### D17 Candidate-Vs-Baseline Linkage Contract

Any future candidate artifact must reference the baseline package or run scope
used to generate the candidate evidence. The linkage must:

- Not imply scoring authority.
- Not imply promotion authority.
- Not relabel baseline evidence as candidate evidence.
- Not mutate or rewrite baseline packages.
- Preserve baseline and candidate membership distinctions for D14 ledger
  records.
- Support future Unit 7 baseline-vs-candidate comparison governance without
  executing comparison, scoring, evaluation, or promotion.

### D17 Identity And Parameter-Version Bridge Contract

Production strategy IDs must not be treated as governed candidate IDs. Any
future candidate identity bridge must map production-style strategy metadata to
governed `cand_strategy_*` identities only through explicit source-controlled
records. Candidate parameter versions must use governed `cand_paramset_*` style
records or an equivalent deterministic vocabulary approved by governance.

The bridge contract must keep baseline strategy identity, production runtime
strategy identity, candidate strategy identity, and candidate parameter-set
identity distinct. Missing, ambiguous, production-approved, live, promoted, or
mutable candidate identity/version metadata must fail closed.

### D17 No-Mutation, As-Of, Reproducibility, And Integrity Contracts

Future candidate evidence must be governed by explicit no-mutation,
as-of, reproducibility, and integrity contracts:

- No-mutation contract: candidate evidence must be generated as separate
  evidence, must never alter baseline package bytes, must never rewrite
  baseline ledger membership, and must carry `no_mutation_attestation`.
- As-of enforcement contract: every consumed input must prove
  `available_at_timestamp <= decision_timestamp`; missing, future, leaked,
  post-decision, stale, ambiguous, or unversioned evidence must fail closed.
- Reproducibility declaration contract: source commit, deterministic input
  references, canonical serialization assumptions, stable ordering, and
  environment-independent comparison assumptions must be declared before a
  candidate artifact can be eligible for pairing.
- Integrity attestation contract: package/run references, candidate artifact
  identity, source commit, input hashes where applicable, run-scope alignment,
  no mixed `run_id`, and no hash mismatch must be attested before inclusion.
- D14 ledger membership contract: future candidate evidence must be recorded as
  `evidence_membership == candidate` when eligible, or as excluded when
  ineligible; baseline packages must not be retroactively relabeled as
  candidates.

### D17 Broker/Order/Live-Execution Exclusion Contract

Candidate evidence at this stage must not depend on broker/API/order-state/live
execution. Future candidate contracts must reject broker, Alpaca, IBKR, TWS,
order submission, order cancellation, order-state binding, flatten, cleanup,
paper trading, and live trading fields or authority. Candidate evidence may be
research evidence only; it cannot submit orders, cancel orders, mutate runtime
state, change strategy/risk/execution behavior, or approve promotion.

### D17 Candidate Test Harness Contract

Before any candidate-evidence implementation may begin, a focused candidate test
harness contract must exist. That future test harness must prove deterministic
candidate artifact validation, candidate identity/version validation, replay
input adapter fail-closed behavior, baseline no-mutation enforcement, as-of
enforcement, reproducibility/integrity declaration enforcement, D14 ledger
membership compatibility, and broker/order/live-execution exclusion. The test
harness must remain pure/in-memory until a separate future gate explicitly
authorizes any filesystem/package-read behavior.

### D17 Status Carry-Forward

- Candidate execution remains **UNIMPLEMENTED** and **UNAPPROVED**.
- Candidate artifact generation remains **UNIMPLEMENTED** and **UNAPPROVED**.
- Package capture remains time-gated until an eligible regular-session
  production run exists and passes D13.
- Evaluation/scoring execution: **BLOCKED**.
- Unit 12: **BLOCKED**.
- Promotion authority: **UNAPPROVED**.
- Broker/API/Alpaca/IBKR/TWS/order-state authority: **UNAPPROVED**.
- Strategy/risk/execution behavior: **UNCHANGED**.
- Paper trading and live trading: **UNAPPROVED**.

### D17 Recommended Next Lane

The next lane should be an explicit **implementation-readiness audit** for a
pure in-memory candidate-evidence contract/schema. D17 push/VPS validation alone
does not authorize implementation. Any later implementation lane requires a
separate readiness audit that explicitly authorizes implementation. It must not
execute candidate replay, generate candidate artifacts, create candidate
packages, score, evaluate, open Unit 12, approve promotion, touch broker/API/
order-state systems, or change strategy/risk/execution behavior.

### D17 Non-Authorization Statement

D17 does not authorize candidate replay execution, candidate artifact
generation, candidate package construction, package capture execution, package
artifact reads, package mutation, evaluation or scoring execution, Unit 12,
promotion authority, broker/API/TWS/Alpaca/IBKR authority, order-state binding,
strategy/risk/execution behavior changes, systemd/scheduler/runtime activation,
`.env`/credential changes, order submission, cancellation, cleanup, paper
trading approval, or live trading approval.

## Gate D Status-Semantics Reconciliation Record

### Status-Semantics Correction

Recorded on 2026-06-13 as an append-only correction record. This record
supersedes any current-status reading that treats docs/code/test/VPS validation
as full workflow completion, evidence sufficiency, operational proof, or Gate D
completion.

Gate D overall is **NOT COMPLETE**. Gate D remains incomplete and blocked
pending governed regular-session evidence, eligible-session operational proof,
ledger/evidence inventory population, candidate mechanism implementation
readiness, evidence sufficiency reassessment, and separately approved
evaluation/scoring authority.

Status terms are pinned as follows:

- **Record complete** means a governance/docs record exists and is validated.
- **Implementation complete** means a bounded implementation artifact exists
  and is tested.
- **VPS validated** means the artifact/test suite passed on VPS.
- **Operationally proven** means the workflow has succeeded under the real
  operational condition it governs.
- **Evidence sufficient** means required governed evidence exists and has been
  reassessed.
- **Gate complete** requires all applicable prerequisites, evidence,
  operational proof, and blockers to be cleared.

Hard rule: do not classify any Gate D lane as **complete** without specifying
whether that means record complete, implementation complete, VPS validated,
operationally proven, evidence sufficient, or gate complete.

Hard rule: no implementation lane may follow a docs-only contract unless a
separate readiness audit explicitly authorizes implementation.

### Corrected Gate D Status Table

| Lane | Record/artifact status | Implementation status | VPS validation status | Operational status | Evidence status | Blocker | Next valid action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D12 | Plan/requirements record validated and VPS-synced. | No new evidence workflow implementation completed by D12 itself. | Record synced/validated only. | Actual governed regular-session package capture workflow remains incomplete. | Governed regular-session package evidence and sufficiency remain incomplete. | Eligible regular-session production run and D13 pass required before capture can resume. | Wait for eligible regular-session production run, then execute only separately authorized governed capture. |
| D13 | Market-session guard record exists. | Guard implementation exists and is test-guarded. | Guard implementation is VPS-validated. | Eligible-session capture workflow is not operationally proven. | Does not create evidence sufficiency. | Regular-session capture must succeed under real eligible conditions. | Operational proof of eligible-session governed capture when time-gated condition is met. |
| D14 | Ledger schema record exists. | Ledger schema validator implementation exists and is test-guarded. | Ledger schema implementation is VPS-validated. | Ledger population workflow is not complete. | Evidence inventory is not populated/complete. | Finalized immutable governed package evidence remains insufficient. | Populate only future source-controlled ledger records after governed evidence exists. |
| D15 | Docs/design record complete. | Candidate mechanism is not implemented. | Record validation only. | No candidate mechanism operational proof. | No candidate evidence produced. | Candidate implementation remains unapproved. | Readiness/contract work only; no candidate execution. |
| D16 | Read-only audit complete with `D16_PARTIAL_FEASIBILITY_CONTRACT_REQUIRED`. | No implementation authority. | Not an implementation artifact. | No operational proof. | No evidence produced. | Contract required before implementation readiness can be considered. | Use audit finding to support a contract/readiness audit, not execution. |
| D17 | Docs-only candidate-evidence contract is validated/VPS-validated as a contract record. | Candidate implementation is not authorized by D17. | Contract record validation only. | No candidate mechanism operational proof. | No candidate evidence produced. | Separate implementation-readiness audit required before D18 or any schema implementation. | Run explicit implementation-readiness audit; no implementation yet. |
| D18 | No D18 candidate-evidence schema record is approved here. | **BLOCKED** pending explicit implementation-readiness audit. | Not applicable. | Not operationally proven. | No candidate evidence produced. | D17 contract alone is insufficient implementation authority. | Implementation-readiness audit only. |
| Gate D overall | Governance records and some bounded artifacts exist, but Gate D is not complete. | Overall Gate D implementation/evaluation workflow incomplete. | Some prior artifacts are VPS-validated; this is not gate completion. | Regular-session evidence workflow and candidate mechanism are not operationally proven. | Evidence sufficiency is not met/reassessed. | Candidate execution, evaluation/scoring, Unit 12, promotion, broker/execution/paper/live remain blocked. | Regular-session evidence capture when eligible, readiness audits, and later sufficiency reassessment; no scoring/Unit 12. |

### Corrected Current Institutional Status

- D12 evidence-expansion / governed package capture is **NOT COMPLETE** as an
  evidence workflow. Only the plan/requirements record is complete and
  validated. Actual governed regular-session package evidence remains
  insufficient.
- D13 market-session capture eligibility guard implementation is
  VPS-validated, but the eligible regular-session capture workflow is
  **NOT OPERATIONALLY PROVEN**.
- D14 package capture ledger schema is VPS-validated, but ledger population and
  evidence inventory are **NOT COMPLETE**.
- D15 candidate-evidence mechanism design is docs/design only. Candidate
  mechanism is **NOT IMPLEMENTED**.
- D16 is a read-only audit only. It authorized a contract direction, not
  implementation.
- D17 is a docs-only candidate-evidence mechanism contract. It is
  VPS-validated as a contract record only and does **NOT** authorize
  implementation by itself.
- D18 candidate evidence schema implementation is **BLOCKED** pending an
  explicit implementation-readiness audit.
- Candidate execution remains **BLOCKED**.
- Package capture remains time-gated and incomplete until an eligible
  regular-session production run exists and passes D13.
- Evaluation/scoring remains **BLOCKED**.
- Unit 12 remains **BLOCKED**.
- Promotion/broker/execution/paper/live authority remains **UNAPPROVED**.

### Status-Semantics Non-Authorization Statement

This reconciliation record does not authorize D18 implementation, candidate
schema implementation, candidate replay execution, candidate artifact
generation, candidate package construction, package capture execution, package
artifact reads, package mutation, evaluation or scoring execution, Unit 12,
promotion authority, broker/API/TWS/Alpaca/IBKR authority, order-state binding,
strategy/risk/execution behavior changes, systemd/scheduler/runtime activation,
`.env`/credential changes, order submission, cancellation, cleanup, paper
trading approval, or live trading approval.

## Gate D Record D18: Candidate Decision Artifact Schema (Narrow Implementation)

### D18 Status

Recorded on 2026-06-13. This is the narrow implementation record for the
candidate decision artifact schema authorized by the D18 implementation-readiness
audit (classification `READY_FOR_SEPARATE_IMPLEMENTATION_GATE`, pure-schema scope
only). That audit cleared the prior "BLOCKED pending explicit
implementation-readiness audit" blocker for this narrow pure-schema scope only;
the broader candidate-evidence-generation, replay-adapter, and
package-construction work remains blocked. D18 is **IMPLEMENTED** as a pure
in-memory, test-guarded module: `tools/replay/candidate_decision_artifact.py`.
D18 schema implementation is complete only if its tests pass.

The module implements the Gate D Record D17 Candidate Decision Artifact Contract
as a deterministic, fail-closed validator over already-loaded candidate decision
artifact metadata. It validates the D17 fields (`candidate_artifact_id`,
`candidate_strategy_id`, `candidate_parameter_version`, `source_commit`,
`input_run_id` / `input_package_reference`, `baseline_package_reference`,
`decision_timestamp_utc`, `asof_timestamp_utc`, `decision_signal`,
`proposed_action`, `decision_reason`, `deterministic_inputs_reference`,
`reproducibility_declaration_status`, `asof_declaration_status`,
`integrity_attestation_status`, `no_broker_order_state_binding`,
`no_mutation_attestation`). Candidate identity composes with Unit 6
(`cand_strategy_*`); as-of ordering enforces
`asof_timestamp_utc <= decision_timestamp_utc`. It fails closed for missing or
malformed required fields, malformed candidate artifact / strategy identifiers,
missing input reference, malformed timestamps, as-of violations, missing or
invalid reproducibility / as-of / integrity declarations, missing
no-broker-order-state-binding or no-mutation attestations,
production/approved/live/promoted/mutable markers, future/leaked/post-decision
markers, broker/order/live fields, and authority-bearing fields.

### D18 Non-Authorization Statement

- D18 does not authorize candidate generation.
- D18 does not authorize replay adapter execution.
- D18 does not authorize package reads or package writes.
- D18 does not authorize scoring or evaluation execution.
- D18 does not open Unit 12.
- D18 does not authorize broker/API/TWS/Alpaca/IBKR, order-state binding,
  runtime activation, paper trading, or live trading.
- D18 does not authorize comparison/scoring execution, promotion, or
  strategy/risk/execution behavior changes.

The validator returns non-authoritative research-evidence metadata only and
creates no scoring, promotion, replay, package-read, package-write, runtime,
broker, paper, or live authority.

### D18 Status Carry-Forward

- Gate D overall remains **NOT COMPLETE**.
- Candidate generation, candidate replay execution, and candidate package
  construction remain **UNIMPLEMENTED** and **UNAPPROVED**.
- Package capture remains time-gated until an eligible regular-session
  production run exists and passes D13.
- Evaluation/scoring execution: **BLOCKED**.
- Unit 12: **BLOCKED**.
- Promotion authority: **UNAPPROVED**.
- Broker/API/Alpaca/IBKR/TWS/order-state authority: **UNAPPROVED**.
- Strategy/risk/execution behavior: **UNCHANGED**.
- Paper trading and live trading: **UNAPPROVED**.

The D17 replay-input-adapter, candidate-generation, and package-construction
contracts remain distinct future gates; D18 implements only the candidate
decision artifact schema/validator and opens none of them.

## Gate D Post-D18 Lane Parking / Active-Lane Reset Record

### Parking Status

Recorded as an append-only governance record on 2026-06-13. This record is
governance documentation only: it changes no runtime behavior, strategy, risk,
execution, broker behavior, package capture, replay, scoring, scheduler/systemd,
or Unit 12, and it neither edits nor weakens any production module.

This record **reconciles** the earlier Gate D Status-Semantics Reconciliation
Record — which stated "D18 candidate evidence schema implementation is
**BLOCKED** pending an explicit implementation-readiness audit" and "No D18
candidate-evidence schema record is approved here" — with the later fact that the
D18 implementation-readiness audit ran (classification
`READY_FOR_SEPARATE_IMPLEMENTATION_GATE`) and the **D18 narrow candidate decision
artifact schema implementation is now complete and VPS-validated**
(`VPS_D18_VALIDATION_PASS`) as a pure in-memory schema + fail-closed validator
only. The older reconciliation text is retained verbatim as accurate point-in-time
history and is not rewritten; that blocker was cleared only for the narrow
pure-schema scope, and D18 grants no downstream authority.

### Active Lane

- Active lane: **STOP / NO ACTION**.
- Gate D overall: **NOT COMPLETE → PARKED**.

The default institutional action after D18 validation is to hold at STOP / NO
ACTION. No Gate D lane continues by momentum. Advancement requires an explicitly
operator-opened next governed lane, or the time-gated eligible regular-session
governed capture under separate authorization.

### Per-Lane Parking Classifications

- **D12** — Evidence workflow **NOT COMPLETE**; **RECORD ONLY** and
  **TIME-GATED** on eligible regular-session governed package evidence existing
  and passing D13.
- **D13** — Market-session capture eligibility guard **implementation
  VPS-VALIDATED**; eligible-session governed capture is **NOT OPERATIONALLY
  PROVEN** and **TIME-GATED** on real eligible conditions.
- **D14** — Package inventory / capture ledger schema **VPS-VALIDATED**;
  inventory / evidence population is **INCOMPLETE** and **EVIDENCE-DEPENDENT**.
- **D15** — Candidate-evidence mechanism **DOCS/DESIGN RECORD ONLY**; candidate
  mechanism **NOT IMPLEMENTED**.
- **D16** — **READ-ONLY AUDIT ONLY** (`D16_PARTIAL_FEASIBILITY_CONTRACT_REQUIRED`);
  **NO IMPLEMENTATION AUTHORITY**.
- **D17** — Candidate-evidence mechanism **DOCS CONTRACT ONLY**; does **NOT
  authorize implementation by itself**.
- **D18** — Narrow candidate decision artifact **schema implementation COMPLETE
  and VPS-VALIDATED**, but **NON-AUTHORITATIVE** (pure in-memory schema/validator
  only).

### D18 Non-Authorization (Restated)

D18 grants no candidate generation, replay adapter execution, package reads,
package writes, comparison/scoring/evaluation execution, Unit 12, promotion,
runtime, scheduler/systemd, broker/API/TWS/Alpaca/IBKR, order-state binding,
paper trading, or live trading authority.

### Downstream Blocked Work

The following remain **BLOCKED / UNAPPROVED** and are not opened by this record:
candidate generation, replay adapter execution, candidate package construction,
comparison/scoring/evaluation execution, evidence-set sufficiency reassessment
(no new governed evidence exists), Unit 12, promotion authority,
broker/API/TWS/Alpaca/IBKR/order-state authority, package capture (time-gated),
strategy/risk/execution behavior changes, scheduler/systemd/runtime activation,
`.env`/credential changes, order submission, order cancellation, cleanup,
flatten, sell, broker remediation, paper trading approval, and live trading
approval. Gate D overall remains **NOT COMPLETE**.

## Gate D Record: Replay Input Adapter Schema (Narrow Implementation)

Module: `tools/replay/replay_input_adapter_schema.py`
(`validate_replay_input_adapter_reference`,
`REPLAY_INPUT_ADAPTER_SCHEMA_VERSION = "0.1-replay-input-adapter-schema"`).

Authorized solely by the Gate D Record D17 Replay Input Adapter Contract and the
replay-input-adapter schema readiness audit (READY_FOR_SEPARATE_IMPLEMENTATION_
GATE, narrow pure-schema scope only). This record documents an implementation,
not a Gate D advancement.

### What it is

A deterministic, fail-closed, **pure in-memory** validator over already-loaded
replay input adapter metadata/references. It certifies that one declared
immutable governed replay input is well-formed: governed-namespace adapter
identifier (`replay_input_*`), well-formed run-scope `run_id`, a package hash
**reference string** (never a filesystem path — path-like values fail closed),
a supported `input_adapter_version`, valid UTC ISO-8601 `asof_timestamp_utc` and
`decision_timestamp_utc` with `asof_timestamp_utc <= decision_timestamp_utc`,
`integrity_attestation_status="attested"`, `reproducibility_declaration_status=
"declared"`, and `no_baseline_mutation_attestation=True`. Missing identity,
version, integrity, reproducibility, as-of, run-scope, or package-reference
metadata fails closed; future/leaked/post-decision markers fail closed;
production/approved/live/promoted/mutable markers fail closed; broker/order/API/
live-execution fields fail closed (presence, not merely truthiness); and any
authority-bearing field fails closed. The validator returns non-authoritative
metadata only, with every downstream authority flag `False`.

### What it is NOT (non-authorizations)

This module is research metadata schema validation only. It carries:

- no package reads
- no filesystem reads / no path resolution
- no package discovery / no package mutation
- no replay execution
- no candidate generation
- no comparison / scoring / evaluation
- no Unit 12
- no runtime / systemd / timer / service authority
- no broker / API / TWS / Alpaca / IBKR / order-state authority
- no paper trading authority
- no live trading authority

Validating a reference here authorizes nothing downstream. Composition with
existing governance vocabulary does not change any existing governance module's
behavior. Implementation authority is not inferred from D18 or from any prior
validation.

### Status after this implementation

- Replay-input-adapter schema implementation is **pure in-memory only** and
  **validates already-loaded metadata/references only**.
- Active lane remains **STOP / NO ACTION** after validation.
- Gate D overall remains **NOT COMPLETE → PARKED**. Gate D overall remains
  **NOT COMPLETE**.

## Gate D Record: Candidate-Vs-Baseline Linkage Schema (Narrow Implementation)

Module: `tools/replay/candidate_baseline_linkage_schema.py`
(`validate_candidate_baseline_linkage`,
`CANDIDATE_BASELINE_LINKAGE_SCHEMA_VERSION =
"0.1-candidate-baseline-linkage-schema"`).

Authorized solely by the Gate D Record D17 Candidate-Vs-Baseline Linkage
Contract and the candidate-vs-baseline linkage schema readiness audit
(READY_FOR_SEPARATE_IMPLEMENTATION_GATE, narrow pure-schema scope only). This
record documents an implementation, not a Gate D advancement.

### What it is

A deterministic, fail-closed, **pure in-memory** validator over already-loaded
candidate-vs-baseline linkage metadata. One linkage record binds a candidate
decision artifact (`candidate_artifact_id`, validated via the candidate decision
artifact schema) and its replay input adapter reference
(`replay_input_adapter_id`, validated via the replay input adapter schema) to
the governed baseline package/run scope (`baseline_package_reference`,
`baseline_strategy_id` validated via Unit 8 baseline-vs-candidate comparison
governance) that generated the candidate evidence. It requires a governed
linkage identifier (`candidate_baseline_link_*`), a well-formed `run_id`, a
package hash **reference string** (never a filesystem path — path-like values
fail closed), a non-empty `source_commit`, valid UTC ISO-8601 `asof_timestamp_
utc <= decision_timestamp_utc`, `integrity_attestation_status="attested"`,
`reproducibility_declaration_status="declared"`, and
`no_baseline_mutation_attestation=True`.

It **preserves the D14 baseline/candidate membership distinction**: the
candidate side must carry `candidate` evidence membership, the baseline side must
carry `baseline` evidence membership, the two must remain distinct, and it
**fails closed if baseline evidence is relabeled as candidate evidence** or if a
single reference carries both baseline and candidate markers. Future/leaked/
post-decision markers, production/approved/live/promoted/mutable markers,
broker/order/API/live-execution fields (presence), and any authority-bearing
field (scoring, promotion, comparison/evaluation/replay execution, package
reads/writes/discovery, runtime, broker, paper, live) all fail closed. The
validator returns non-authoritative metadata only, with every downstream
authority flag `False`.

### What it is NOT (non-authorizations)

This module is research metadata linkage validation only. It **supports future
comparison governance without executing comparison** and carries:

- no package reads
- no filesystem reads / no path resolution
- no package discovery / no package mutation
- no replay execution
- no candidate generation
- no comparison / scoring / evaluation
- no promotion
- no Unit 12
- no runtime / systemd / timer / service authority
- no broker / API / TWS / Alpaca / IBKR / order-state authority
- no paper trading authority
- no live trading authority

Validating a linkage here authorizes nothing downstream. Composition with
existing governance modules does not change any composed module's behavior.
Implementation authority is not inferred from D18, replay-input-adapter
validation, or any prior validation.

### Status after this implementation

- Candidate-vs-baseline linkage schema implementation is **pure in-memory only**
  and **validates already-loaded linkage metadata only**.
- It **preserves the D14 baseline/candidate membership distinction** and
  **supports future comparison governance without executing comparison**.
- Active lane remains **STOP / NO ACTION** after validation.
- Gate D overall remains **NOT COMPLETE → PARKED**. Gate D overall remains
  **NOT COMPLETE**.

## Gate D Record: Candidate Test Harness Schema (Narrow Implementation)

Module: `tools/replay/candidate_test_harness_schema.py`
(`validate_candidate_test_harness`,
`CANDIDATE_TEST_HARNESS_SCHEMA_VERSION = "0.1-candidate-test-harness-schema"`).

Authorized solely by the Gate D Record D17 Candidate Test Harness Contract and
the candidate test harness schema readiness audit
(READY_FOR_SEPARATE_IMPLEMENTATION_GATE, narrow pure-schema scope only). This
record documents an implementation, not a Gate D advancement.

### What it is

A deterministic, fail-closed, **pure in-memory** validator over already-loaded
candidate test harness metadata. One harness record *declares* which candidate
governance invariants a future test harness is expected to cover, the candidate
subject references it pertains to, and its pure/in-memory authority boundary. The
validator requires a governed harness identifier (`candidate_test_harness_*`),
valid subject references (`candidate_artifact_id`, `replay_input_adapter_id`,
`candidate_baseline_link_id`, `baseline_strategy_id`, each validated via its
composed governance module), a well-formed `run_id`, a package hash **reference
string** (never a filesystem path — path-like values fail closed), a non-empty
`source_commit`, valid UTC ISO-8601 `asof_timestamp_utc <= decision_timestamp_
utc`, `integrity_attestation_status="attested"`, `reproducibility_declaration_
status="declared"`, and `no_baseline_mutation_attestation=True`.

It **declares expected invariant coverage only**: `expected_invariants` must be
non-empty, drawn exclusively from a fixed `KNOWN_EXPECTED_INVARIANTS` tuple
mirroring the D17 contract verbatim (deterministic candidate artifact
validation, candidate identity/version validation, replay input adapter
fail-closed behavior, baseline no-mutation enforcement, as-of enforcement,
reproducibility/integrity declaration enforcement, D14 ledger membership
compatibility, broker/order/live-execution exclusion), and must cover the full
set. It requires `harness_purity_status="pure_in_memory"` and
`no_filesystem_or_package_read_until_separate_gate=True`. Future/leaked/
post-decision markers, production/approved/live/promoted/mutable markers,
**test-as-promotion-evidence markers**, broker/order/API/live-execution fields
(presence), and any authority-bearing field (test_execution, replay/comparison/
evaluation execution, scoring, promotion, candidate generation, package
reads/writes/discovery, filesystem reads, path resolution, runtime, broker,
paper, live) all fail closed. The validator returns non-authoritative metadata
only, with every downstream authority flag `False`.

### What it is NOT (non-authorizations)

This module is research metadata schema validation only. It **does not execute
tests** and **does not treat tests as promotion evidence**. It carries:

- no package reads
- no filesystem reads / no path resolution
- no package discovery / no package mutation
- no replay execution
- no candidate generation
- no comparison / scoring / evaluation
- no promotion
- no Unit 12
- no runtime / systemd / timer / service authority
- no broker / API / TWS / Alpaca / IBKR / order-state authority
- no paper trading authority
- no live trading authority

Validating a harness record here authorizes nothing downstream and does not
satisfy any precondition for candidate-evidence execution, which remains
UNIMPLEMENTED and UNAPPROVED. Composition with existing governance modules does
not change any composed module's behavior. Implementation authority is not
inferred from D18, replay-input-adapter, candidate-baseline-linkage, or any prior
validation.

### Status after this implementation

- Candidate test harness schema implementation is **pure in-memory only**,
  **validates already-loaded harness metadata only**, and **declares expected
  invariant coverage only**.
- It **does not execute tests** and **does not treat tests as promotion
  evidence**.
- Active lane remains **STOP / NO ACTION** after validation.
- Gate D overall remains **NOT COMPLETE → PARKED**. Gate D overall remains
  **NOT COMPLETE**.

## Gate D Post-Schema Consolidation Record

Docs/test-only consolidation record. It records the joint status of the four
post-D18 candidate-track pure-schema modules after the Gate D post-schema
consolidation/status audit (classified PASS). It implements nothing, changes no
module behavior, and authorizes nothing. It does not advance Gate D.

### Implemented post-D18 pure-schema modules (all NON-AUTHORITATIVE)

- **Candidate decision artifact schema** (`tools/replay/candidate_decision_artifact.py`)
  — **IMPLEMENTED and VPS-VALIDATED**, **non-authoritative**.
- **Replay-input-adapter schema** (`tools/replay/replay_input_adapter_schema.py`)
  — **IMPLEMENTED and VPS-VALIDATED**, **non-authoritative**.
- **Candidate-vs-baseline linkage schema**
  (`tools/replay/candidate_baseline_linkage_schema.py`)
  — **IMPLEMENTED and VPS-VALIDATED**, **non-authoritative**.
- **Candidate test harness schema** (`tools/replay/candidate_test_harness_schema.py`)
  — **IMPLEMENTED and VPS-VALIDATED**, **non-authoritative**.

### What the four schemas authorize

The four schemas authorize **only deterministic pure in-memory validation of
already-loaded metadata records** of their respective kinds. Validating a record
produces non-authoritative metadata, not an action, an approval, or evidence.

### What the four schemas do NOT authorize

- They do **not** authorize package reads / writes / discovery / mutation.
- They do **not** authorize filesystem reads or path resolution.
- They do **not** authorize test execution or tests-as-promotion-evidence.
- They do **not** authorize replay execution.
- They do **not** authorize candidate generation.
- They do **not** authorize comparison / scoring / evaluation.
- They do **not** authorize promotion.
- They do **not** authorize Unit 12.
- They do **not** authorize runtime / systemd / timer / service changes.
- They do **not** authorize broker / API / TWS / Alpaca / IBKR / order-state.
- They do **not** authorize paper / live trading.

Downstream authority is not inferred from any schema validation.

### Remaining Gate D blockers (unchanged)

- **D11** evidence remains **INSUFFICIENT** and **controlling**.
- **D12 / D13** remain **TIME-GATED** on a real eligible regular-session governed
  evidence capture passing D13 under separate authorization.
- **D14** package inventory remains **EVIDENCE-DEPENDENT** and **unpopulated**.
- The candidate-evidence execution mechanism remains **UNIMPLEMENTED /
  UNAPPROVED**.

### Status after this consolidation

- Gate D remains **NOT COMPLETE → PARKED**. Gate D overall remains **NOT
  COMPLETE**.
- Active lane remains **STOP / NO ACTION**.

## Monday Runtime Observation Record — Observational Evidence Only

Recorded as a docs-only operational observation after the Gate D post-schema
consolidation. This record changes no runtime behavior, strategy, risk,
execution, broker behavior, package capture, replay, scoring, scheduler/systemd,
candidate mechanism, or Unit 12 status.

### Observation Summary

The Monday scheduled Alpaca paper runtime observation passed operationally under
the existing VPS systemd timer baseline:

- VPS scheduled paper runtime ran under `openclaw.timer`.
- `openclaw.service` completed cycles successfully and returned inactive/dead
  between runs.
- `openclaw.timer` remained active/enabled.
- Pre-open cycles blocked as `before_regular_session_open`.
- The market-open 13:30 UTC cycle produced mostly hold/no-order decisions.
- MSTR generated a buy signal at 13:30 UTC, but broker reconciliation blocked
  the order because existing MSTR qty=5 plus requested qty=1 would exceed
  `max_position_size=5`.
- Later observed cycles produced hold/no-order behavior.
- The end-of-session corrected check showed final passive state clean.
- No traceback, failed unit, restart loop, unauthorized order submission,
  manual start/restart, VPS repo edit, replay, scoring, package capture, or
  candidate generation was authorized or observed.

### Gate D Relevance

This observation is supporting operational evidence only. It is relevant to
Gate D because it shows the scheduled timer baseline can naturally reach
pre-open and regular-session decision cycles, including a deterministic
reconciliation block for projected exposure above `max_position_size`.

It does **not** create governed package evidence. It does **not** prove package
capture occurred. It does **not** prove D13 operational package-capture behavior,
because no governed package-capture gate is recorded here. It does **not**
populate D14 package inventory. It does **not** create D15 candidate evidence.

### Status Carry-Forward

- Gate D overall remains **NOT COMPLETE → PARKED**.
- D11 evidence sufficiency remains **INSUFFICIENT** and controlling.
- D12/D13 remain **TIME-GATED** on a separately authorized eligible
  regular-session governed evidence capture passing D13.
- D14 package inventory remains **EVIDENCE-DEPENDENT** and unpopulated.
- D15 candidate-evidence mechanism remains docs/design only; candidate
  evidence remains absent.
- Evaluation/scoring execution remains **BLOCKED**.
- Unit 12 remains **BLOCKED**.
- Promotion authority remains **UNAPPROVED**.
- Broker/API/TWS/Alpaca/IBKR expansion, IBKR execution, order-state authority,
  paper-trading escalation, and live trading remain **UNAPPROVED**.

### Non-Authorization Statement

This Monday observation record does not authorize replay, scoring, package
capture, candidate generation, package reads, package writes, package mutation,
candidate replay execution, candidate decision generation, evaluation,
promotion, broker/API expansion, IBKR execution, order submission,
order cancellation, cleanup, flatten, sell, strategy changes, risk-limit
changes, config changes, credential changes, scheduler/systemd changes, paper
trading escalation, live trading, or Unit 12.

## Gate D Governed Package Capture Runbook Reconciliation

Recorded as a docs-only command-surface and operator-runbook reconciliation
after the Monday runtime observation record. This section supersedes older
operator-facing command wording that showed only the unflagged C2 command shape.
The older C2 command text is retained as point-in-time history. The current
source-controlled CLI requires explicit package-write authorization.

This reconciliation does not execute package capture, does not authorize a
capture now, does not mark Gate D complete, does not mark D11 sufficient, does
not open Unit 12, does not claim D13 operational proof, does not populate D14,
and does not create D15 candidate evidence.

### Current Authorized Command Shape

For a future separately authorized eligible regular-session timer run, the
preferred operator command surface is the source-controlled Gate D market-session
operator CLI, not pasted shell/Python heredocs:

```bash
python -m tools.ops.gate_d_market_session_operator precheck --repo-root /opt/openclaw-stocks
python -m tools.ops.gate_d_market_session_operator settle --repo-root /opt/openclaw-stocks
python -m tools.ops.gate_d_market_session_operator discover --repo-root /opt/openclaw-stocks
python -m tools.ops.gate_d_market_session_operator capture --repo-root /opt/openclaw-stocks --run-id <run_id> --authorize-vps-package-write
```

The operator CLI performs the repo, systemd, run_id, artifact, report-alignment,
D13, no-overwrite, and authorization checks before delegating the single package
write to the existing governed package execution orchestrator.

The underlying governed package-write command surface remains:

```bash
python -m tools.replay.package_execution_orchestrator --run-id <run_id> --execution-mode vps --authorize-vps-package-write
```

The unflagged command remains a fail-closed deferral path and is not the
operator command for an authorized package write:

```bash
python -m tools.replay.package_execution_orchestrator --run-id <run_id> --execution-mode vps
```

### Narrow Future-Run Preconditions

All of the following must be true before any future capture command may be run:

- A future eligible regular-session timer run exists.
- The operator explicitly authorizes package capture for exactly one run.
- The `run_id` is known from scheduled runtime evidence, not from manual
  runtime execution.
- The source-controlled repo state is clean and at the expected commit.
- The run was produced by the existing scheduled timer; no manual runtime
  start/restart is part of the evidence lane.
- No broker/API expansion is part of the lane.
- No replay, scoring, package selection for evaluation, candidate generation,
  strategy change, risk change, config change, systemd change, paper escalation,
  or live escalation is part of the lane.

### Run ID Selection

The `run_id` must be selected from scheduled timer evidence only. It must
correspond to `logs/{run_id}.jsonl`, and `last_run_report.json` must align to
the same `run_id`. The selected run must be a regular-session decision run or
an explicit non-market blocked run that passes D13. Market-closed-only evidence
may be retained as observation evidence, but it is not capture-count eligible.

The `discover` subcommand must print exactly one `ELIGIBLE_RUN_ID=<run_id>` only
when a symbol-level run_id is capture-ready. It must print `ELIGIBLE_RUN_ID=`
when no eligible run is found. A 15-minute timer activation is not itself a
run_id and must not be treated as capture-ready.

### Tomorrow Operator Sequence

The next operator attempt is conditional and must stop after at most one
governed capture:

1. Run `precheck --repo-root /opt/openclaw-stocks` around 6:22-6:25 AM PT.
2. Run `settle --repo-root /opt/openclaw-stocks` around 6:36-6:40 AM PT
   after the 13:30 UTC timer settles.
3. Run `discover --repo-root /opt/openclaw-stocks` immediately after a clean
   settle.
4. If `ELIGIBLE_RUN_ID=<run_id>` is found, run `capture` for exactly that one
   run_id with `--repo-root /opt/openclaw-stocks` and
   `--authorize-vps-package-write`.
5. Stop.
6. If no eligible 13:30 run_id is found, repeat only `settle` and `discover`
   after the 13:45 UTC timer settles.
7. Do not perform a second capture.

No pasted heredocs, ad hoc Python snippets, line-wrapped shell commands,
package capture outside the CLI, replay, scoring, candidate generation, Unit 12
opening, systemd mutation, runtime start/restart, strategy/risk/config changes,
credential changes, paper escalation, or live trading is authorized by this
sequence.

### D13 Eligibility Expectations

The D13 market-session guard must run before any package write. Expected
eligible cases are:

- terminal status `ok`; or
- terminal status `blocked` with an explicit non-market eligible reason such as
  `projected_exposure_exceeds_max_position_size`, `duplicate`,
  `killswitch_disabled`, or `manual_review_required`.

Expected ineligible cases fail closed and must not write a package.

### Fail-Closed Stop Conditions

Stop before package writing if any of the following occurs:

- Missing explicit operator authorization.
- Unknown or ambiguous `run_id`.
- Market-closed-only run.
- `before_regular_session_open`.
- `after_regular_session_close`.
- Missing blocked reason.
- Unknown or ambiguous blocked reason.
- Missing runtime artifacts.
- Stale or mismatched `last_run_report.json` and JSONL evidence.
- Existing package directory for the selected `run_id`.
- Hash mismatch.
- Wrong root or path traversal.
- Any attempt to read or bind `order_state.json`.
- Any implied scoring, promotion, Unit 12 opening, broker/API authority,
  strategy/risk/config/systemd change, paper escalation, or live escalation.

### Expected Package Output Evidence

If a later operator-authorized capture is run and succeeds, the evidence to
preserve for review must include:

- selected `run_id`
- exact command used
- source commit
- JSONL path `logs/{run_id}.jsonl`
- `last_run_report.json` alignment result
- terminal status and terminal reason
- D13 eligibility result
- package directory under `/opt/openclaw-stocks/replay_packages/{run_id}`
- written artifact path
- written artifact sha256
- no-overwrite/finalized lifecycle evidence
- immutability marker evidence
- provenance and redaction status
- explicit confirmation that `order_state.json` was not read or bound
- machine-readable package execution evidence report

Package output evidence remains evidence only. Code must not self-declare Gate D
completion, D11 sufficiency, Unit 12 opening, evaluation authority, promotion
authority, broker authority, execution permission, paper approval, or live
approval.

### D14 Ledger Follow-Up Requirement

After any future successful governed package capture, D14 follow-up is required
before the package can be considered in any later sufficiency review. A
source-controlled package inventory / ledger record, or equivalent
source-controlled record, must be prepared with the D14-required fields:
`run_id`, `package_sha256`, package reference, capture timestamp, source
commit, session class, terminal status, terminal reason, decision outcome,
evidence membership, strategy id, parameter version, reproducibility
declaration, as-of declaration, integrity attestation, inclusion status,
exclusion reason if excluded, notes, and control metadata proving finalized
immutable package status, run_id alignment, hash verification, complete package
authority, non-draft/non-mutable/non-stale state, no mixed `run_id`, no hash
mismatch, and no future/leaked/post-decision evidence.

Do not populate D14 from this runbook alone. D14 population requires a real
governed package path/hash from a separately authorized successful capture.
For the 2026-06-16 13:30 UTC capture, the source-controlled ledger follow-up is
recorded above as `Gate D Record D14.1`.

### Explicit Non-Claims

This runbook reconciliation does not authorize live trading, IBKR execution,
replay/scoring, package capture, candidate generation, strategy changes, risk
changes, config changes, systemd changes, broker/API expansion, order
submission, order cancellation, cleanup, flatten, sell, paper escalation, live
escalation, or Unit 12. Gate D remains **NOT COMPLETE -> PARKED**. D11 remains
**INSUFFICIENT**. Unit 12 remains **BLOCKED**.
