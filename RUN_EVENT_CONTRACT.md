# RUN_EVENT_CONTRACT

## 1. Purpose

This contract defines the ordered run event record for the trading bot.

Its purpose is to make one bot run reconstructable from a single event stream.
The event stream is the source of truth for what the bot observed, what it evaluated, what it decided, and whether it stopped or completed.

This matters because the bot is deterministic.
If the system records the full decision-relevant inputs at each stage, a run can later be reviewed, replayed, compared, and audited without depending on partial summary files.

## 2. Design Principles

- deterministic execution remains authoritative
  The bot's runtime flow and decision order remain the authority. Event capture records that flow. It does not redefine it.

- data capture is observational only
  Event recording observes what the bot did and saw during a run. It does not introduce new decision logic.

- events are append-only
  Each event is written as a new fact in sequence. New information is added by adding events, not by rewriting older ones.

- events are immutable once recorded
  Once an event is recorded, it should not be edited in place. Corrections belong in later events or later derived views.

- state and reports are derived
  State files and run reports should be treated as summaries built from event facts, not as the primary historical record.

- stable event envelope, flexible payloads
  Every event should share the same top-level structure. The payload can vary by event type so each stage can capture its own decision-relevant facts.

## 3. Canonical Event Envelope

Every event in a run should contain these top-level fields.

### run_id

Purpose:
- identifies the single bot run this event belongs to
- ties all events from one execution together
- allows one run to be reconstructed in order

### event_id

Purpose:
- uniquely identifies this event within the event stream
- allows exact referencing of a single recorded fact
- prevents ambiguity when multiple events share the same type

### event_type

Purpose:
- states what kind of event this is
- defines what stage fact is being recorded
- determines which payload facts are expected

### timestamp

Purpose:
- records when the event was captured
- preserves ordered timing across the run
- supports later audit and replay review

### stage

Purpose:
- names the runtime stage the event belongs to
- keeps the execution sequence explicit
- allows grouped analysis across runs by stage

### status

Purpose:
- states the outcome of that stage at the moment of recording
- distinguishes pass, block, fail, skip, and complete states
- allows run flow to be interpreted without reading payload details first

### payload

Purpose:
- holds the decision-relevant facts for this specific event
- captures what the bot observed, calculated, or concluded at that stage
- stays flexible so different event types can record different fact sets without changing the top-level contract

## 4. Ordered Event Types For One Run

The canonical ordered event sequence for one run is below.
Some runs will stop early, so later events may not occur.
`order_submitted` is optional because some runs block, hold, or stay in dry-run mode.

### run_started

When it occurs:
- at the start of a new bot run before stage evaluation begins

Why it exists:
- marks the existence of the run
- anchors the ordered event stream
- records the starting context for everything that follows

Decision-relevant payload facts:
- run start timestamp
- trigger source for the run
- execution mode in effect for the run
- symbol or symbol set in scope
- environment classification relevant to the run

### config_loaded

When it occurs:
- after runtime configuration is loaded and validated for the run

Why it exists:
- records the configuration facts that shaped the run
- preserves which controls were active during decision-making
- separates configuration facts from later market or strategy facts

Decision-relevant payload facts:
- dry-run status
- killswitch status
- allowed symbol scope
- duplicate cooldown value
- position or exposure limits used by the run
- any validated configuration values that directly affect decision flow

### market_checked

When it occurs:
- after the bot checks market session status for the run

Why it exists:
- records whether the run was allowed to proceed past the market gate
- preserves the market-state fact that explains later continuation or early stop

Decision-relevant payload facts:
- market session classification
- whether trading was allowed at that moment
- any blocking reason from the market check
- effective market timestamp used by the check

### data_fetched

When it occurs:
- after market data needed for strategy evaluation is fetched and validated

Why it exists:
- records the exact market-data facts that shaped strategy evaluation
- preserves whether data was sufficient, missing, retried, or blocked

Decision-relevant payload facts:
- symbol evaluated
- requested data window or data context used by the run
- number of bars or records returned
- key price facts used by the strategy
- any fallback or retry behavior that affected the result
- whether the data was sufficient for strategy evaluation
- any blocking reason caused by insufficient data

### market_input_captured

Canonical event:
- `data / market_input_captured / ok`

When it occurs:
- after successful market data fetch
- before `strategy_evaluated`

Why it exists:
- records replay-grade market input evidence
- preserves the full market input used for strategy evaluation
- makes later strategy reconstruction possible without depending only on
  derived price metrics

Decision-relevant payload facts:
- `symbol`
- `timeframe`
- `source`
- `adjustment`
- `adjusted`
- `warnings`
- `candles[]`
- `candles[].timestamp`
- `candles[].open`
- `candles[].high`
- `candles[].low`
- `candles[].close`
- `candles[].volume`

Authority boundary:
- observational only
- non-authoritative
- does not change strategy inputs
- does not grant strategy authority
- does not grant risk authority
- does not grant reconciliation authority
- does not grant execution authority

Deferred items:
- not a replay engine
- not a replay package
- not evaluation infrastructure
- not adaptive behavior

### strategy_evaluated

When it occurs:
- after the strategy logic evaluates the fetched data

Why it exists:
- records the strategy output before later gates change the final outcome
- preserves the distinction between strategy intent and later execution eligibility

Decision-relevant payload facts:
- strategy outcome
- signal side or hold result
- score, threshold, or rule result if used by the strategy
- key facts from the strategy evaluation that explain the signal
- reason for hold or no-action outcome if applicable

### account_checked

When it occurs:
- after account-level facts needed for order eligibility are loaded

Why it exists:
- records whether the account state supported the next step
- preserves the account facts used in later sizing or eligibility checks

Decision-relevant payload facts:
- buying power or equivalent capacity fact
- account status relevant to order eligibility
- any account-level block reason
- any account facts used in sizing or affordability checks

### duplicate_checked

When it occurs:
- after the bot checks whether the proposed action is blocked by duplicate protection

Why it exists:
- records why an otherwise valid signal may be stopped
- preserves cooldown and prior-action facts that explain duplicate prevention

Decision-relevant payload facts:
- proposed action under review
- duplicate check result
- prior matching action facts
- cooldown window used
- elapsed time since prior relevant action if available
- duplicate block reason if blocked

### risk_checked

When it occurs:
- after risk rules are evaluated for the proposed action

Why it exists:
- records whether the action passed the risk gate
- preserves the risk facts used in the pass or fail decision

Decision-relevant payload facts:
- projected exposure or position after the action
- max allowed exposure or position used by the check
- estimated order cost or sizing fact
- risk pass or fail result
- explicit risk rejection reason if blocked

### reconciliation_checked

When it occurs:
- after broker-side position and open-order reconciliation is evaluated

Why it exists:
- records whether live broker state was compatible with the proposed action
- preserves the reconciliation facts that explain pass, hold, or block outcomes

Decision-relevant payload facts:
- current broker position facts
- relevant open-order facts
- projected post-decision broker state if applicable
- reconciliation pass or fail result
- explicit reconciliation block reason if blocked

### decision_made

When it occurs:
- after the bot reaches its final action decision for the run

Why it exists:
- records the final run decision after all gates have been applied
- separates final intent from later submission or completion details

Decision-relevant payload facts:
- final action classification
- final side or hold result
- whether submission is allowed, blocked, skipped, or dry-run only
- final decision reason
- order intent facts if an order would be built or submitted

### order_submitted

When it occurs:
- only when the run reaches an actual submission step

Why it exists:
- records the handoff from decision to broker submission
- preserves the final submitted order facts as part of the run record

Decision-relevant payload facts:
- submitted side
- submitted quantity
- symbol submitted
- submission timestamp
- broker acknowledgement facts available at submission time
- dry-run marker if a submission-like path is recorded without real submission

### run_completed

When it occurs:
- at the end of the run after the final outcome is known

Why it exists:
- closes the event sequence for the run
- records the overall run result in one final event
- gives downstream derived artifacts a stable completion marker

Decision-relevant payload facts:
- final run outcome
- final reason classification
- whether the run ended in block, hold, dry-run completion, submit completion, or error
- final artifact summary facts if needed for derived outputs
- completion timestamp

## 5. Derived Artifacts

`order_state.json` and `last_run_report.json` are derived artifacts because they are summaries of run facts, not the full historical fact record.

They are useful because they provide a compact current view.
They are not the source of truth because:

- they do not preserve the full ordered sequence of one run
- they compress multiple stage facts into a smaller summary
- they are shaped for convenience, not for full replay
- they may change format over time without changing the underlying historical facts

The event stream should hold the primary record.
Derived files should be rebuildable from that record.

## 6. Replay Requirements

The event stream must make it possible to reconstruct:

- the exact ordered stages reached by the run
- where the run stopped or completed
- which configuration facts governed the run
- the market-state fact that allowed or blocked continuation
- the data facts used for strategy evaluation
- the strategy outcome before later gates
- the account facts used for eligibility
- the duplicate check facts and any cooldown block
- the risk check facts and any rejection reason
- the reconciliation facts and any broker-state block
- the final decision and why it was made
- whether an order was submitted or intentionally not submitted
- the final run outcome classification

Replay should allow a reviewer to answer:

- what did the bot know at each stage
- what did the bot decide at each stage
- why did the bot continue, block, hold, or submit
- what facts materially changed the final outcome

## 7. Non-Goals

This contract does not try to solve:

- storage engine selection
- database schema design
- event transport design
- cross-process architecture
- deployment planning
- strategy redesign
- runtime refactor planning
- multi-broker standardization beyond the run facts that must be captured
- research-event contracts outside the live run record
- full historical market-data warehousing
