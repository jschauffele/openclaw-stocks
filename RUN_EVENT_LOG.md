# RUN_EVENT_LOG

## 1. Purpose

The append-only run event log is the source of truth for one simple reason:
it preserves the exact ordered facts of what the bot did during each run.

This trading system is deterministic.
That means the most important record is not a summary of the outcome.
The most important record is the ordered sequence of observed inputs, gate results, decisions, and completion facts.

An append-only log is used because it gives the system:

- a factual run history
- a stable basis for replay
- a clean way to derive state and reports later
- a record that does not depend on mutable summary files

## 2. Core Properties

### append-only

New run facts are recorded by appending new events.
Older events are not rewritten.

### immutable

Once an event is recorded, it is treated as fixed historical fact.
If a later correction is needed, it should appear as a later event or a later derived view, not as an edit to the original event.

### ordered

Events must preserve the exact order in which the run moved through its stages.
The sequence itself is part of the meaning of the log.

### durable

Once an event is successfully written, it should remain part of the run record.
The log exists to preserve history, not just to support immediate runtime visibility.

### replayable

The log must preserve enough ordered fact detail that one run can later be reconstructed step by step.

## 3. Log Structure Options

### one file per run

Strengths:

- simple run isolation
- easy to inspect one run from start to finish
- natural fit for deterministic replay
- avoids mixing unrelated runs in the same file

Weaknesses:

- cross-run reading requires opening multiple files
- later aggregate analysis would require directory-level iteration

### single global log file

Strengths:

- one place to append events
- easy to maintain a single timeline

Weaknesses:

- mixes multiple runs together
- harder to inspect one run cleanly
- replay of one run requires filtering
- log size and readability degrade over time

### segmented logs

Strengths:

- can balance file size and grouping
- can support future partitioning rules

Weaknesses:

- adds structure decisions this system does not need yet
- creates avoidable complexity before indexing or query needs exist

### chosen option: one file per run

For this trading system, one file per run is the best choice.

It fits the current goals because:

- each run is deterministic and naturally bounded
- replay is run-scoped
- debugging is usually run-scoped
- state and report derivation can be tied to one completed run
- it keeps the storage model simple without introducing filtering or segmentation rules

## 4. Event Record Structure

A single event record in the log should contain:

- `schema_version`
- `run_id`
- `event_id`
- `event_type`
- `stage`
- `timestamp_utc`
- `timestamp`
- `status`
- `payload`

Required field meaning:

- `schema_version`
  Identifies the event envelope version.

- `run_id`
  Identifies the run this event belongs to.

- `event_id`
  Uniquely identifies this event within the run log.

- `event_type`
  Names the kind of event being recorded.

- `stage`
  Names the runtime stage associated with the event.

- `timestamp_utc`
  Records when the event was captured in UTC. This is the canonical timestamp
  field for current JSONL event records.

- `timestamp`
  Records when the event was captured and is retained as a compatibility mirror
  of `timestamp_utc` in current event records.

- `status`
  Records the stage outcome at that point, such as pass, block, fail, skip, or complete.

- `payload`
  Holds the decision-relevant facts for this event.

Ordering guarantees:

- events are written in the same order the run reaches them
- event order within one run file is authoritative
- later events must never appear before earlier stage facts in the same run

Uniqueness:

- each run must have one `run_id`
- each event in that run must have a unique `event_id`
- the combination of `run_id` and `event_id` must identify exactly one event record

## 5. Write Model

Events should be written strictly sequentially.

Write rules:

- one run writes one ordered stream of events
- events are appended one at a time
- a later event is not written before the earlier stage fact exists

Single writer assumption:

- assume one writer for one run log
- do not assume concurrent writers to the same run file
- keep the write path simple and deterministic

Failure behavior:

- an event is either recorded as a complete event or treated as not recorded
- partial event records should not be treated as valid history
- if a crash happens mid-write, the log should be treated as ending at the last complete event
- recovery logic should prefer preserving confirmed facts over guessing missing ones

Crash safety conceptually means:

- never depend on an unfinished trailing record
- treat the last known complete event as the last valid fact
- allow derived artifacts to be rebuilt from only confirmed events

## 6. Read Model (simple)

### debugging

For debugging, read one run file from beginning to end.

The reader should be able to see:

- the exact ordered stages reached
- the point where the run blocked, failed, held, or completed
- the decision-relevant facts captured at each stage

### replay

For replay, read one run file in recorded order and reconstruct the run step by step.

The reader should be able to answer:

- what the bot knew at each stage
- what gate result occurred at each stage
- what final decision was made
- whether an order was submitted or intentionally not submitted

No indexing is assumed.
Simple sequential reading is enough for the current design.

## 7. Derived State Relationship

State files and report files are derived artifacts built from the event log.

That means:

- the log is the primary historical record
- state files summarize the latest relevant facts from prior runs
- report files summarize one run outcome in a compact form

This relationship matters because derived files can change shape over time.
The event log should remain the stable source that allows those files to be rebuilt.

The log preserves:

- ordered facts
- stage transitions
- decision reasons
- completion outcome

Derived state preserves:

- convenient current summaries
- compact operator-facing views
- reduced representations of the underlying run facts

## 8. Non-Goals

This design does not try to solve:

- indexing
- query systems
- database design
- multi-writer coordination
- distributed logging
- scaling strategy
- long-term storage optimization
- cross-run analytics infrastructure
