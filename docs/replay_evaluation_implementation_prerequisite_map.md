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
reference. No artifact in these families may be read until Gate A is open.
Source-reference and source-path authority is now source-controlled
(source_references.py, source_paths.py, verify_vocabulary_boundaries.py); the
remaining Gate A prerequisites (filesystem/source-artifact authority grant and
operator-approved VPS/runtime gate) are not yet recorded:

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
   Gate A cannot open until two governance records are separately completed:
   (a) filesystem/source-artifact authority grant recorded in source-controlled
   docs; (b) operator-approved VPS/runtime gate recorded in source-controlled
   docs. Neither is recorded yet.
3. Package writer and package persistence authority (package_writer.py,
   package_persistence.py) is implemented and validated under Gate B.
4. Complete replay package authority exists with actual on-disk packages
   (Gate C).
5. Finalized immutable evidence exists.
6. Evaluation prerequisite governance is complete (Gate D).

No gate in this chain may be skipped. This operator approval record does not
advance the chain; it records the pre-conditions that must be met.

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
