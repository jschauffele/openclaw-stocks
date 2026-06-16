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
