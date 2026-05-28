# IBKR TWS Connection Context Matrix

## Purpose

This document prevents confusion between OpenClaw execution contexts when using
localhost IBKR/TWS paper sockets. It is a documentation guard only.

`127.0.0.1` means the loopback interface of the current execution context. It
does not automatically mean the user's Mac, the Mac GUI session, the VPS, or a
Codex execution container.

## Connection Context Matrix

| Context | What `127.0.0.1` means | Mac GUI TWS Paper on `127.0.0.1:7497` reachable? | IB Gateway Paper on `127.0.0.1:4002` reachable? | Lifecycle smoke valid? | Read-only state smoke valid? | Submit/reconciliation smoke valid? |
| --- | --- | --- | --- | --- | --- | --- |
| `DIRECT_MAC_TERMINAL` | The user's Mac process namespace and Mac loopback | Yes, known-good when Mac GUI TWS Paper is running | Yes only if IB Gateway Paper is running locally on the Mac | Yes, with explicit approval | Only after a separate read-only state gate | Only after a separate submit/reconciliation gate |
| `CODEX_LOCAL` | The Codex local execution context loopback | Not proven; known failing for the same nominal endpoint in current evidence | Unknown and unsupported without separate context proof | Not valid until Codex-local socket equivalence is proven | Not valid | Not valid |
| `VPS` | The VPS loopback | No. It points to the VPS, not the user's Mac | No, unless IB Gateway runs on the VPS under a separately approved design | Unsupported for Mac-local TWS | Unsupported | Unsupported |
| `CODEX_VPS` | The Codex/VPS execution context loopback | No. It points to the Codex/VPS context, not the user's Mac | No, unless explicitly designed and approved | Unsupported for Mac-local TWS | Unsupported | Unsupported |
| Future explicit bridge/tunnel | The bridge endpoint defined by a future approved design | Not approved | Not approved | Not approved until a bridge gate exists | Not approved | Not approved |

## Known-Good Path

The known-good local paper lifecycle path is:

```bash
./.venv-ibkr312/bin/python manual_ibkr_localhost_connect_smoke.py
```

Known-good context and endpoint:

- context: `DIRECT_MAC_TERMINAL`
- host: `127.0.0.1`
- port: `7497`
- client ID: `9107`
- result: `connect_ready`
- readiness evidence: `next_valid_id`
- shutdown evidence: clean disconnect and stopped runtime thread

This proves that the Mac terminal process can reach Mac GUI TWS Paper. It does
not prove that `CODEX_LOCAL`, `VPS`, or `CODEX_VPS` can reach the same socket.

## Known-Failing Path

The known-failing path is:

- context: `CODEX_LOCAL`
- nominal endpoint: `127.0.0.1:7497`
- client ID: `9107`
- result: `connect_error`

This failure must not be treated as proof that TWS Paper settings are wrong when
the direct Mac terminal lifecycle smoke has passed. The likely issue is execution
context: Codex-local loopback/socket behavior is not equivalent to the Mac GUI
TWS loopback context.

## Unsupported Paths

The following remain unsupported:

- `VPS` to Mac-local TWS over `127.0.0.1`
- `CODEX_VPS` to Mac-local TWS over `127.0.0.1`
- any non-localhost endpoint
- any live port, including TWS `7496` or IB Gateway `4001`
- any bridge or tunnel that has not been separately designed and approved
- any scheduled IBKR runtime activation

## Required Evidence Before A Context Is Valid

Each execution context must produce its own evidence before it can be considered
valid for IBKR/TWS work. Evidence from one context does not transfer to another.

Required lifecycle evidence:

- exact execution context label
- exact command
- host, port, and client ID
- paper-only confirmation
- `connect_result.passed`
- `connect_result.reason`
- `connection_completion_source`
- `next_valid_id`
- disconnect result
- runtime thread state
- confirmation that no account, position, open-order, execution, market-data,
  submit, cancel, flatten, retry, or reconciliation behavior occurred

Required read-only state evidence, under a separate gate:

- all lifecycle evidence
- open-order snapshot
- position snapshot
- broker-state classification
- disconnect and stopped-thread evidence
- confirmation that no submit, cancel, flatten, retry, remediation, or
  reconciliation behavior occurred

Required submit/reconciliation evidence, under a separate gate:

- lifecycle and read-only state evidence
- explicit single paper-only order authorization
- pre-submit broker-state evidence
- order ID and submit result evidence
- final broker-state evidence
- reconciliation evidence only if separately approved and required by the
  submit result

## Permanent Rule

Do not re-debug TWS settings from `CODEX_LOCAL` connection failures when the
direct Mac terminal lifecycle smoke has passed. Treat the failure as a
connection-context problem unless a future context proof shows otherwise.

## Boundary

This document does not approve:

- IBKR runtime activation
- read-only state smoke
- submit
- reconciliation
- tunnels or bridges
- VPS work
- `main.py` execution
- `broker_factory.py` routing changes
- scheduled IBKR activation
- live trading
