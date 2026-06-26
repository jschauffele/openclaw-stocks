# D11.61 IBKR VPS Endpoint Evidence Or Criteria Revision Prerequisite

## Scope and Decision

D11.61 is a source-controlled prerequisite gate for the remaining IBKR primary
market-data eligibility blocker:
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility`.
It defines what evidence is required before any future route can proceed. It
does not approve IBKR primary eligibility, run or authorize immediate VPS proof
execution, run endpoint inspection, run market testing, connect to
IBKR/TWS/Gateway, import broker API code, run protocol probes, send broker
endpoint traffic, mutate runtime/timer/service/systemd/TWS/Gateway/
openclaw-gateway/VPS state, open Unit 12, or authorize account/order/execution
activity.

Decision: both prerequisite paths remain possible, but neither is justified
yet. D11.61 therefore preserves fail-closed status and requires a later
source-controlled gate to choose either bounded VPS endpoint evidence
preflight or formal LOCAL_MAC criteria revision.

| Field | Value |
| --- | --- |
| `classification` | `IBKR_VPS_ENDPOINT_EVIDENCE_OR_CRITERIA_REVISION_PREREQUISITE` |
| `source_commit` | `fd2258ee6efaff23886914b519b971b2f58c15c9` |
| `d11_60_vps_validation` | `80 passed in 2.54s` |
| `d11_60_decision` | `BLOCKED_NO_VALID_VPS_PROOF_TARGET_OR_CRITERIA_REVISION` |
| `d11_59_route` | `REMAINS_ACTIVE_SAFE_PREFLIGHT_REQUIRED` |
| `d11_58_result` | `BLOCKED_CRITERIA_UNRESOLVED` |
| `ibkr_primary_eligibility` | `NOT_APPROVED` |
| `d11_status` | `D11_INSUFFICIENT` |
| `unit_12_status` | `UNIT_12_BLOCKED` |
| `package_capture` | `BLOCKED` |
| `vps_runtime` | `NOT_TOUCHED` |
| `account_order_execution_authority` | `false` |
| `mac_local_historical_diagnostic_evidence` | `ACCEPTED` |
| `all_symbols_d11_countable` | `true` |
| `all_symbols_freshness_classification` | `clean` |
| `selected_endpoint_context` | `LOCAL_MAC` |
| `selected_endpoint_type` | `TWS_PAPER` |
| `selected_mac_local_endpoint` | `127.0.0.1:7497` |
| `endpoint_scope` | `LOCAL_MAC_ONLY` |
| `vps_127_0_0_1_7497_validated` | `false` |
| `prior_vps_failure` | `VPS_LOCALHOST_CONTEXT_MISMATCH / AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS` |
| `vps_endpoint_evidence_prerequisite` | `REQUIRED` |
| `local_mac_criteria_revision_prerequisite` | `REQUIRED` |
| `d11_61_decision` | `DUAL_PREREQUISITE_REQUIRED` |
| `next_permissible_gate` | `D11.62_SOURCE_CONTROLLED_PREREQUISITE_PATH_SELECTION_FOR_VPS_ENDPOINT_EVIDENCE_OR_LOCAL_MAC_CRITERIA_REVISION` |

## Active Rule and Accepted Evidence

The exact active source-controlled rule is
`separate_vps_read_only_freshness_proof_required_before_primary_eligibility` in
`D11_PRIMARY_PROVIDER_SELECTION_CRITERIA`.

Accepted source-controlled evidence:

- D11.57 accepted Mac-local historical diagnostic evidence.
- All five symbols were clean and countable in accepted Mac-local diagnostic
  evidence: `AAPL`, `MSFT`, `NVDA`, `TSLA`, and `MSTR`.
- The selected endpoint is `selected_endpoint_context=LOCAL_MAC`,
  `selected_endpoint_type=TWS_PAPER`, and
  `selected_mac_local_endpoint=127.0.0.1:7497`.
- The selected endpoint scope is `LOCAL_MAC_ONLY`.
- The accepted evidence does not validate VPS `127.0.0.1:7497`.

## Missing Evidence For VPS Proof

The following evidence is missing before any future VPS proof route can
proceed:

- no validated VPS-accessible IBKR market-data endpoint;
- VPS `127.0.0.1:7497` was not listening during the prior proof;
- `18789` and `18791` are not approved IBKR market-data endpoints unless a
  separate source-controlled approval exists;
- no source-controlled proof that a VPS process can safely reach a broker
  market-data endpoint.

Required localhost facts:

- `127.0.0.1` is process-context local.
- LOCAL_MAC `127.0.0.1:7497` is not equivalent to VPS `127.0.0.1:7497`.
- Prior VPS failure remains `VPS_LOCALHOST_CONTEXT_MISMATCH` /
  `AUTHORIZED_ENDPOINT_7497_NOT_LISTENING_ON_VPS`.
- Prior VPS failure is not a proven TWS issue and not a proven IB Gateway
  issue.
- No future VPS proof may target `127.0.0.1:7497` unless that endpoint is
  observed listening in the VPS process context and separately authorized.
- No future proof may target `18789` or `18791` as market-data endpoints unless
  source-controlled evidence explicitly approves them.

## VPS Endpoint Evidence Prerequisites

Any future bounded VPS endpoint evidence collection requires a separate
source-controlled authorization gate before any endpoint inspection. That
future gate must define non-mutating evidence collection only and must satisfy
all of these prerequisites:

- no service, timer, runtime, systemd, TWS, Gateway, openclaw-gateway, or VPS
  mutation;
- no market-data request;
- no broker connection;
- no protocol probe;
- no account, order, or execution authority;
- compact output only;
- evidence must identify process context;
- evidence must identify listening endpoints;
- evidence must identify process names;
- evidence must state whether each endpoint is approved or only observed;
- evidence must fail closed if no valid endpoint is observed.

D11.61 does not authorize that future evidence collection; it defines the
prerequisites only.

## LOCAL_MAC Criteria Revision Prerequisites

Any formal LOCAL_MAC-only criteria revision requires a separate
source-controlled revision packet. That future packet must satisfy all of these
prerequisites:

- identify the superseded rule exactly:
  `separate_vps_read_only_freshness_proof_required_before_primary_eligibility`;
- state whether a `LOCAL_MAC_ONLY` market-data architecture is intended to
  support provider eligibility;
- state exactly why accepted LOCAL_MAC evidence does or does not supersede the
  old VPS-proof rule;
- prove no account/order/execution authority expansion;
- preserve `UNIT_12_BLOCKED` unless a later separate gate opens it;
- add focused boundary tests before any approval;
- avoid production provider-selection code changes unless a separate
  source-controlled rule explicitly requires them.

D11.61 does not approve a criteria revision; it defines the prerequisites only.

## Fail-Closed Boundary

D11.61 fails closed until a future source-controlled gate explicitly satisfies
one prerequisite path.

```text
d11_61_decision=DUAL_PREREQUISITE_REQUIRED
vps_endpoint_evidence_prerequisite=REQUIRED
local_mac_criteria_revision_prerequisite=REQUIRED
ibkr_primary_eligibility=NOT_APPROVED
d11_status=D11_INSUFFICIENT
unit_12_status=UNIT_12_BLOCKED
```

The exact next permissible gate is:

```text
D11.62_SOURCE_CONTROLLED_PREREQUISITE_PATH_SELECTION_FOR_VPS_ENDPOINT_EVIDENCE_OR_LOCAL_MAC_CRITERIA_REVISION
```

## Authority Boundaries Preserved

D11.61 records no account/order/execution authority:

```text
account_order_execution_authority=false
order_authority=false
execution_authority=false
```

D11.61 records no package capture, replay, scoring, candidate generation,
strategy, risk, execution, VPS proof run, VPS market test, protocol probe,
endpoint inspection, broker endpoint traffic, runtime mutation, timer mutation,
service mutation, systemd mutation, TWS mutation, Gateway mutation,
openclaw-gateway mutation, Unit 12 opening, or live-trading authority.

D11.61 preserves `IBKR_PRIMARY_ELIGIBILITY=NOT_APPROVED`, `D11_INSUFFICIENT`,
`UNIT_12_BLOCKED`, `PACKAGE_CAPTURE=BLOCKED`, and
`VPS_RUNTIME=NOT_TOUCHED`.
