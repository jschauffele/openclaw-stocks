# Presenter Mapper Boundary Decision

## Decision

Presenter and mapper pressure in `main.py` is **medium**.

No presenter or mapper extraction is approved yet. The current production
orchestration remains unchanged until a narrower implementation boundary is
reviewed.

## Boundary

`main.py` retains ownership of:

- orchestration sequencing
- side-effect timing
- early returns
- event/report/observation persistence timing
- state-write timing
- completion control flow

Future presenter or mapper helpers may only build already-decided payload
dictionaries or notes. They may format report notes, event payloads, or
observation field dictionaries after another layer has already made the
decision being reported.

Presenter and mapper helpers must not own:

- strategy, risk, duplicate, reconciliation, or runtime visibility policy
- broker calls
- order construction or submission
- state writes
- event, report, or observation persistence
- retries
- remediation
- cancel, flatten, or resubmit behavior
- completion control flow

## Future Candidates

The safest first future candidates are narrow pure helpers, such as:

- reconciliation event payload mapping
- strategy/action event payload mapping

A full terminal report builder is deferred. Terminal branches combine
sequencing, side effects, and completion semantics, so they should not be moved
wholesale.

## Frozen Boundaries

`execution_use_case.py` remains frozen and detached from runtime orchestration.

Runtime integration remains deferred. Runtime visibility remains observed-only
and must not become an execution or completion-control dependency through
presenter or mapper extraction.
