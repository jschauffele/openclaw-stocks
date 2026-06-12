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

C2 does not imply that the current `package_execution_orchestrator` CLI already
performs VPS package execution. The source-controlled command shape is
nameable, but `vps` mode currently **defers and refuses** real execution: both
`execute_package_orchestration(...)` and `main(...)` fail closed in `vps` mode
(`execute_package_orchestration` raises `VPS_EXECUTION_DEFERRED_MESSAGE`; the
CLI prints the deferral and returns exit code 2). Real execution remains
blocked until a later implementation gate enables the bounded VPS read/write
path.

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

The future bounded VPS package-execution command shape is:

```
python -m tools.replay.package_execution_orchestrator --run-id <run_id> --execution-mode vps
```

This command shape is source-controlled authority metadata
(`PACKAGE_EXECUTION_VPS_COMMAND_CANDIDATE` in
`tools/replay/package_execution_orchestrator.py`) and is recorded as the
expected future execution interface. It does not execute today.

Actual execution remains blocked until all of the following occur in order:

- A later local implementation gate wires `vps` mode to governed runtime
  artifact reads and governed package writes.
- That implementation is committed, pushed, and VPS-synced.
- A separate explicit VPS execution gate is opened by the operator.

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
