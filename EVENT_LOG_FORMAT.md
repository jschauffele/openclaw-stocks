# EVENT_LOG_FORMAT

## 1. Encoding Choice

JSON is the right encoding choice for this system in its current phase.

It fits because:

- it is simple to read and write
- it is easy to inspect during debugging
- it works well for append-only event records
- it allows payloads to evolve without redesigning the whole format
- it matches the current need for clarity over optimization

This system is still in the phase where durability, readability, and operational simplicity matter more than compactness.
JSON supports that well.

## 2. Core Principles

### append-only

New event records are added to the end of the log.
Older records are not rewritten.

### immutable events

Once an event is written, it is treated as fixed historical fact.
Later understanding should be represented by later events or later derived views, not by editing old records.

### version-tolerant

The format must allow older and newer records to exist together in the same overall system history.
Readers must expect shape differences over time.

### forward/backward compatible

Older readers should be able to safely read newer records at a basic level.
Newer readers should be able to safely read older records without assuming every newer field exists.

## 3. Event Envelope

Every event record should use the same top-level JSON structure.

Required fields:

- `event_type`
  Names the kind of event being recorded.

- `timestamp`
  Records when the event was captured.

- `run_id`
  Identifies the run this event belongs to.

- `event_id`
  Uniquely identifies this event within the run log.

- `payload`
  Holds the event-specific facts for that event type.

The top-level envelope should stay stable.
Most evolution should happen inside `payload` or through additive top-level fields that do not break older readers.

## 4. Compatibility Rules

The format should follow these rules:

- fields are additive only
  New fields may be added over time, but existing fields should not be removed in a way that breaks older readers.

- no breaking changes
  Existing field meaning should remain stable once introduced.

- unknown fields must be ignored
  Readers should skip fields they do not understand rather than failing.

- missing fields must be tolerated
  Readers should not assume every optional or later-added field exists in older records.

Additional compatibility discipline:

- keep field names stable once published
- do not repurpose an existing field to mean something different
- add new meaning through new fields, not by silently changing old ones

## 5. Versioning Strategy

The format should include `schema_version` as an optional top-level field.

Why include it:

- it gives readers an explicit signal about the event shape they are looking at
- it helps later migrations or parsers reason about older versus newer records
- it supports evolution without forcing one rigid global format forever

How it should be used:

- the event envelope remains stable
- schema version changes should be rare and deliberate
- additive changes should not require a version bump unless interpretation would otherwise become unclear
- readers should rely first on tolerant field handling, not only on version matching

Evolution should be handled by:

- keeping the core envelope stable
- adding fields without breaking existing meaning
- allowing old and new payload shapes to coexist
- treating version as a reader aid, not as permission for brittle parsing

## 6. File Structure

The log should use one JSON object per line.

This is preferable to a single JSON array.

Why JSONL fits append-only logging:

- one event can be appended as one new line
- the full file does not need to be reopened and rewritten as a growing array
- an incomplete trailing write affects only the last line, not the validity of the whole file
- line-by-line reading is simple for debugging and replay

Why a JSON array is a worse fit:

- appending requires maintaining shared opening and closing structure
- a partial write can make the whole file invalid
- crash handling is more fragile

## 7. Failure Safety

The format should tolerate partial writes at the line level.

Failure safety rules:

- each complete line is one complete event record
- an incomplete final line must be treated as invalid
- corruption should be bounded to the affected line, not assumed to invalidate earlier complete lines

This creates a clear corruption boundary:

- one line is one event
- a broken line affects that event only
- earlier valid lines remain readable history

## 8. Read Behavior

Logs should be parsed safely and conservatively over time.

Reader behavior should be:

- read line by line
- treat each complete line as one candidate event
- parse only complete JSON objects
- ignore unknown fields
- tolerate missing optional fields
- stop treating a line as valid if it is incomplete or malformed

Over time, safe reading means:

- older records remain usable even if they lack newer fields
- newer records remain readable at a basic level even if they contain extra fields
- readers prioritize preserving known facts over making unsafe assumptions about unknown structure

## 9. Non-Goals

This format does not try to solve:

- databases
- binary encodings
- schema registries
- indexing systems
- query engines
- cross-system transport
- scale optimization
- storage compression strategy
