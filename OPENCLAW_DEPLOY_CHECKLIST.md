# OpenClaw Deploy Checklist

Use this checklist for small OpenClaw hotfixes and normal deployments.

## Rules

- Mac is the development machine.
- GitHub `main` is the source-control truth.
- VPS is the runtime environment.
- Do not assume Mac, GitHub, and VPS match without checking.
- Do not run `python3 main.py` on the VPS.
- Prefer clean git deploys on the VPS.
- If the local repo is dirty with unrelated work, use a clean clone for hotfixes.

## VPS Safe-Shell Gate Pattern

Direct hard-assertion gates in a live SSH shell can close the session when a
failed assertion runs under `set -e`. Do not paste live-shell gate blocks that
can terminate the operator session before reporting which assertion failed.

VPS gates should use one of these safer patterns:

- A child `bash` heredoc whose failure exits only the child process.
- A soft-gate command sequence that records each check result and prints a
  final pass/fail summary without closing the interactive shell.

Prompts and runbooks that ask an assistant or operator to execute VPS gates
must explicitly state whether the shell should remain open after the gate. If
the shell should remain open, avoid live-shell `set -e` assertions.

Target-already-present commit states are valid verification states when branch,
`HEAD`, `origin/main` alignment, and clean-worktree evidence match the target.
Do not treat an already-correct target state as an unexplained failure.

## VPS Precondition Fail-Closed Pattern

VPS shell gates must fail closed on precondition failures. Do not rely on bare
`test` commands under `set -u` for critical gate assertions, because a failed
`test` does not stop the script unless the shell is also configured to exit on
errors or the result is handled explicitly.

Use explicit precondition checks for critical runtime state:

```bash
if [ "$TIMER_STATE" != "inactive" ]; then
  echo "TIMER_ALREADY_ACTIVE / RESTORE_GATE_NOT_APPLICABLE"
  exit 1
fi
```

Alternatively, use `set -euo pipefail` inside a child `bash <<'EOF'` block when
hard assertions are intentional and the parent shell must remain open.

Restore/capture gates that require `openclaw.timer` to be inactive must stop if
the timer is already active. Re-running a restore/capture gate while the timer
is already active must not start a new polling loop. If the timer is already
active and `openclaw.service` is inactive, classify:

```text
TIMER_ALREADY_ACTIVE / RESTORE_GATE_NOT_APPLICABLE / CAPTURE_ONLY_OR_WAIT_FOR_NEXT_TIMER_RUN
```

If fresh runtime evidence is still needed while the timer is already active,
use a capture-only gate that records the baseline `run_id` and waits for a new
`run_id`, without stopping or starting the timer.

This rule does not change bot runtime behavior, broker behavior, strategy
behavior, or execution authority.

## 1. Confirm You Are On The Right Machine

On Mac:

```bash
hostname && pwd
```

On VPS:

```bash
hostname && pwd
```

## 2. Check Local Repo State On Mac

```bash
cd /Users/openclawcontrol/Documents/openclaw-stocks && git status --short
```

If the repo contains unrelated refactor work, use a clean clone:

```bash
cd /Users/openclawcontrol/Documents && rm -rf openclaw-stocks-hotfix && git clone https://github.com/DickMcGreggor/openclaw-stocks.git openclaw-stocks-hotfix
```

## 3. Make The Smallest Fix Locally

Work in the correct repo, test locally, then commit only the intended fix.

```bash
cd /Users/openclawcontrol/Documents/openclaw-stocks-hotfix && git checkout -b codex/short-hotfix-name
git status --short
git add <file>
git commit -m "Short clear message"
git push -u origin codex/short-hotfix-name
```

## 4. Merge The Hotfix Into GitHub Main

```bash
cd /Users/openclawcontrol/Documents/openclaw-stocks-hotfix && git checkout main
git pull origin main
git merge --ff-only codex/short-hotfix-name
git push origin main
```

## 5. Update The VPS From GitHub

Before any VPS deploy, fetch, pull, merge, restore, or `scp` write, verify the
VPS root filesystem is mounted read-write. If the filesystem is read-only or
the result is ambiguous, stop and report the ambiguity. Do not retry sync,
restore, or copy operations until the filesystem state is resolved.

When `CODEX_VPS` and a direct VPS terminal disagree about filesystem state, the
direct VPS terminal is authoritative for deploy decisions.

Use the VPS git checkout now that SSH deploy access is configured:

```bash
cd /opt/openclaw-stocks && git fetch origin
git merge --ff-only origin/main
```

## 6. Run The Bot Manually On The VPS

Use the wrapper script so the virtual environment is loaded:

```bash
cd /opt/openclaw-stocks && ./run_bot.sh
```

Do not use:

```bash
cd /opt/openclaw-stocks && python3 main.py
```

## 7. Verify The Latest Result

Starting or restarting `openclaw.timer` may immediately trigger a natural
systemd run. After starting the timer, wait for `openclaw.service` to settle
back to inactive before classifying runtime behavior.

Inspect both `last_run_report.json` and the latest `logs/*.jsonl` before
deciding whether the run was expected timer behavior or unexpected runtime
drift.

For deploy, sync, or timer-restore gates, record the baseline `run_id` from
`last_run_report.json` before restore or fresh settle recapture. After
restore/capture, runtime evidence is valid for the target commit only when
`last_run_report.json` and the latest JSONL show a fresh `run_id` created after
the target commit became active.

Do not classify VPS runtime from `last_run_report.json` unless all of these
settle checks pass:

- `openclaw.service` is inactive
- `openclaw.timer` is active
- the VPS root filesystem is mounted read-write
- repo `HEAD` is aligned with `origin/main`
- the latest JSONL `run_id` matches `last_run_report.json` `run_id`
- `last_run_report.json` `run_id` differs from the pre-restore/pre-capture
  baseline `run_id`
- `openclaw.service` remains inactive after report and JSONL capture

If the `run_id` remains unchanged from the pre-restore/pre-capture baseline,
classify the gate as:

```text
TIMER_BASELINE_RESTORED / REPO_ALIGNED / STALE_RUNTIME_EVIDENCE_FOR_TARGET
```

Do not classify `DETERMINISTIC_SETTLE_CAPTURED` unless fresh `run_id` evidence
exists for the target commit. Target-already-present repo states remain valid
sync states when branch, `HEAD`, origin alignment, and clean-worktree evidence
match, but they do not by themselves prove fresh runtime evidence.

Replace fixed sleep-only classification with service-settle polling. If
`openclaw.service` is active or activating during capture, or becomes active
or activating after capture, classify the evidence as
`RUNTIME_STATE_UNSETTLED`, wait for the service to settle inactive, and
recapture report and JSONL evidence. Do not use stale reports for final
runtime classification.

```bash
cd /opt/openclaw-stocks && tail -n 50 last_run_report.json
```

### Alpaca Timer Baseline Settle-Capture Runbook

The Alpaca scheduled timer is the current operational baseline. Baseline
verification is observational only: it classifies timer, service, report, and
JSONL evidence, and it must not change runtime behavior.

Use timer/service/report/JSONL evidence for baseline classification. Do not use
raw `python3 main.py` as a baseline verification path.

Required settle-capture checks:

- Expected `HEAD` must be confirmed before classifying the run.
- The worktree must be clean.
- The VPS root filesystem must be mounted read-write.
- `openclaw.service` must be inactive before final classification.
- `openclaw.timer` must be active for restored-baseline classification.
- Do not classify from `last_run_report.json` alone.
- Before timer restore or fresh settle recapture, record the baseline `run_id`
  from `last_run_report.json`.
- After restore/capture, `last_run_report.json` `run_id` must differ from the
  baseline `run_id`.
- The latest JSONL `run_id` must match `last_run_report.json` `run_id`.
- The latest JSONL completion event must be checked for `stage`, `status`, and
  `reason`.
- Stale report or stale JSONL evidence must be explicitly classified and must
  not close a deploy gate.
- If the `run_id` did not change, classify
  `TIMER_BASELINE_RESTORED / REPO_ALIGNED / STALE_RUNTIME_EVIDENCE_FOR_TARGET`
  and do not classify `DETERMINISTIC_SETTLE_CAPTURED`.
- If `openclaw.service` is active or activating during capture, or becomes
  active or activating after capture, classify the evidence as
  `RUNTIME_STATE_UNSETTLED`, wait for the service to settle inactive, and
  recapture report and JSONL evidence.

Expected safe blocked classifications depend on market-session context.
Closed-day and pre-market blocks are both expected when the JSONL completion
reason is consistent with the session state.

Examples:

```text
ALPACA_TIMER_BASELINE_RESTORED / DETERMINISTIC_SETTLE_CAPTURED / EXPECTED_CLOSED_DAY_BLOCK
ALPACA_TIMER_BASELINE_RESTORED / DETERMINISTIC_SETTLE_CAPTURED / EXPECTED_PRE_MARKET_BLOCK
```

Expected safe terminal reasons may include `market_holiday_or_closed_day`,
`before_regular_session_open`, `after_regular_session_close`, or another
explicitly approved market-session guard reason.

Forbidden during baseline monitoring:

- manual `main.py` execution
- broker/API/TWS calls
- `.env` changes
- systemd changes, except explicit approved timer stop/start in sync or restore
  gates
- submit, cancel, flatten, sell, cleanup, or remediation
- live trading

## 8. Verify VPS Repo Is Clean

```bash
cd /opt/openclaw-stocks && git status -sb
```

Expected result after a normal deploy:

```bash
## main...origin/main
```

## 9. If You Must Copy A Single File

Prefer `scp` from Mac to VPS over manual paste into `nano`:

```bash
scp /Users/openclawcontrol/Documents/openclaw-stocks-hotfix/<file> root@146.190.54.10:/opt/openclaw-stocks/
```

Then verify on the VPS:

```bash
cd /opt/openclaw-stocks && git diff -- <file>
```

If the file should match GitHub `main`, finish with:

```bash
cd /opt/openclaw-stocks && git restore --source=origin/main --worktree --staged <file>
```

## 10. Nano

If `nano` opens:

- Save: `Ctrl+O`, then `Enter`
- Exit: `Ctrl+X`
