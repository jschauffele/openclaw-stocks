"""Gate D market-session operator CLI.

Source-controlled replacement for fragile pasted Gate D operator runbooks.
The precheck, settle, and discover commands are read-only. The capture command
delegates exactly one explicitly authorized package write to the existing
governed package execution orchestrator.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Callable, Iterable, Sequence

from tools.replay import capture_eligibility_guard
from tools.replay import package_execution_orchestrator
from tools.replay.last_run_report_alignment import (
    LastRunReportAlignmentRequest,
    validate_last_run_report_alignment,
)
from tools.replay.terminal_completion_evaluator import (
    TerminalCompletionEvaluationRequest,
    evaluate_terminal_completion_jsonl,
)


EXPECTED_COMMIT = "fde358855d118dd9be1e1a108efafc683b307b16"
DEFAULT_SINCE_UTC = "2026-06-16 13:25:00 UTC"
DEFAULT_LIMIT = 60
TARGET_SYMBOLS = ("AAPL", "MSFT", "NVDA", "TSLA", "MSTR")
EVIDENCE_TOKENS = (
    "run_id",
    "symbol",
    *TARGET_SYMBOLS,
    "decision",
    "action",
    "reason",
    "before_regular_session_open",
    "after_regular_session_close",
    "market_closed",
    "projected_exposure_exceeds_max_position_size",
    "Run report written",
    "OpenClaw run finished",
    "Traceback",
    "ERROR",
    "Exception",
)

PREOPEN_PASSIVE_CHECK_PASS = "PREOPEN_PASSIVE_CHECK_PASS"
PREOPEN_PASSIVE_CHECK_BLOCKED = "PREOPEN_PASSIVE_CHECK_BLOCKED"
POST_1330_SETTLED_REGULAR_SESSION_EVIDENCE_FOUND = (
    "POST_1330_SETTLED_REGULAR_SESSION_EVIDENCE_FOUND"
)
RUNTIME_STATE_UNSETTLED = "RUNTIME_STATE_UNSETTLED"
NO_REGULAR_SESSION_EVIDENCE_FOUND = "NO_REGULAR_SESSION_EVIDENCE_FOUND"
FAIL_CLOSED_SETTLE_CHECK_BLOCKED = "FAIL_CLOSED_SETTLE_CHECK_BLOCKED"
ELIGIBLE_RUN_ID_FOUND_FOR_CAPTURE = "ELIGIBLE_RUN_ID_FOUND_FOR_CAPTURE"
NO_ELIGIBLE_RUN_ID_FOUND = "NO_ELIGIBLE_RUN_ID_FOUND"
FAIL_CLOSED_DISCOVERY_BLOCKED = "FAIL_CLOSED_DISCOVERY_BLOCKED"
ONE_GOVERNED_PACKAGE_CAPTURED_PENDING_D14_LEDGER_FOLLOW_UP = (
    "ONE_GOVERNED_PACKAGE_CAPTURED_PENDING_D14_LEDGER_FOLLOW_UP"
)
CAPTURE_ATTEMPT_FAILED_CLOSED_NO_RETRY_WITHOUT_NEW_AUTHORIZATION = (
    "CAPTURE_ATTEMPT_FAILED_CLOSED_NO_RETRY_WITHOUT_NEW_AUTHORIZATION"
)
LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_READY_REAUTHORIZATION_REQUIRED = (
    "LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_READY_REAUTHORIZATION_REQUIRED"
)
LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_FAILED_CLOSED = (
    "LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_FAILED_CLOSED"
)
DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED = (
    "DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED"
)
DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FAILED_CLOSED = (
    "DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FAILED_CLOSED"
)
DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMPLETED = (
    "DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMPLETED"
)
DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_FAILED_CLOSED = (
    "DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_FAILED_CLOSED"
)

_SAFE_RUN_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")


@dataclass(frozen=True, slots=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


CommandRunner = Callable[[Sequence[str], int | None], CommandResult]


def _run_command(argv: Sequence[str], timeout: int | None = None) -> CommandResult:
    try:
        completed = subprocess.run(
            list(argv),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            argv=tuple(argv),
            returncode=124,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "command timed out",
            timed_out=True,
        )
    except OSError as exc:
        return CommandResult(
            argv=tuple(argv),
            returncode=127,
            stderr=str(exc),
        )
    return CommandResult(
        argv=tuple(argv),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True, slots=True)
class ServiceState:
    timer_active: bool
    timer_enabled: bool
    service_inactive: bool
    service_failed: bool
    n_restarts_parseable: bool
    n_restarts: int | None
    result: str | None
    exec_main_status: str | None
    last_trigger: str | None
    next_elapse: str | None
    checks: tuple[Check, ...]


@dataclass(frozen=True, slots=True)
class DiscoveryCandidate:
    capture_ready: bool
    run_id: str
    symbol: str
    decision: str
    action: str
    status: str
    reason: str
    report_aligned: bool
    mixed_run_id: bool
    package_exists: bool
    d13_result: str
    jsonl_path: str


def root_mount_is_rw(options: str) -> bool:
    """Parse comma-delimited mount options; do not substring-match."""

    return "rw" in {option.strip() for option in options.split(",")}


def is_safe_run_id(run_id: str) -> bool:
    if not run_id or "/" in run_id or "\\" in run_id:
        return False
    if run_id in {".", ".."} or ".." in run_id:
        return False
    return bool(_SAFE_RUN_ID_RE.fullmatch(run_id))


def _repo_root(path: str | Path | None) -> Path:
    return Path(path or ".").resolve()


def _cmd_text(result: CommandResult) -> str:
    return (result.stdout or result.stderr).strip()


def _git(
    repo: Path, runner: CommandRunner, args: Sequence[str], timeout: int | None = None
) -> CommandResult:
    return runner(("git", "-C", str(repo), *args), timeout)


def _repo_checks(
    repo: Path,
    expected_commit: str,
    runner: CommandRunner,
    *,
    require_root_rw: bool,
) -> tuple[Check, ...]:
    checks: list[Check] = []
    checks.append(Check("repo_path_exists", repo.exists(), str(repo)))

    branch = _git(repo, runner, ("rev-parse", "--abbrev-ref", "HEAD"))
    checks.append(
        Check(
            "branch_is_main",
            branch.returncode == 0 and branch.stdout.strip() == "main",
            _cmd_text(branch),
        )
    )

    head = _git(repo, runner, ("rev-parse", "HEAD"))
    checks.append(
        Check(
            "head_equals_expected",
            head.returncode == 0 and head.stdout.strip() == expected_commit,
            _cmd_text(head),
        )
    )

    status = _git(repo, runner, ("status", "--porcelain"))
    checks.append(
        Check(
            "git_status_clean",
            status.returncode == 0 and status.stdout == "",
            _cmd_text(status) or "clean",
        )
    )

    remote = runner(
        ("timeout", "15", "git", "-C", str(repo), "ls-remote", "origin", "refs/heads/main"),
        20,
    )
    remote_head = remote.stdout.split()[0] if remote.stdout.split() else ""
    checks.append(
        Check(
            "remote_main_equals_expected",
            remote.returncode == 0
            and not remote.timed_out
            and remote_head == expected_commit,
            "timeout" if remote.timed_out else (_cmd_text(remote) or remote_head),
        )
    )

    if require_root_rw:
        mount = runner(("findmnt", "-no", "OPTIONS", "/"), 5)
        checks.append(
            Check(
                "root_filesystem_rw",
                mount.returncode == 0 and root_mount_is_rw(mount.stdout.strip()),
                _cmd_text(mount),
            )
        )

    return tuple(checks)


def _parse_show_properties(text: str) -> dict[str, str]:
    props: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            props[key] = value
    return props


def _service_state(runner: CommandRunner, *, include_timer_times: bool) -> ServiceState:
    checks: list[Check] = []
    timer_active = runner(("systemctl", "is-active", "openclaw.timer"), 5)
    timer_enabled = runner(("systemctl", "is-enabled", "openclaw.timer"), 5)
    service_active = runner(("systemctl", "is-active", "openclaw.service"), 5)
    service_failed = runner(("systemctl", "is-failed", "openclaw.service"), 5)
    show = runner(
        (
            "systemctl",
            "show",
            "openclaw.service",
            "-p",
            "NRestarts",
            "-p",
            "Result",
            "-p",
            "ExecMainStatus",
        ),
        5,
    )
    props = _parse_show_properties(show.stdout)
    n_restarts_raw = props.get("NRestarts", "")
    try:
        n_restarts: int | None = int(n_restarts_raw)
        n_restarts_parseable = True
    except ValueError:
        n_restarts = None
        n_restarts_parseable = False

    last_trigger = None
    next_elapse = None
    if include_timer_times:
        timer_show = runner(
            (
                "systemctl",
                "show",
                "openclaw.timer",
                "-p",
                "LastTriggerUSec",
                "-p",
                "NextElapseUSecRealtime",
            ),
            5,
        )
        timer_props = _parse_show_properties(timer_show.stdout)
        last_trigger = timer_props.get("LastTriggerUSec")
        next_elapse = timer_props.get("NextElapseUSecRealtime")
        checks.append(
            Check(
                "timer_times_read",
                timer_show.returncode == 0,
                _cmd_text(timer_show) or f"{last_trigger} {next_elapse}",
            )
        )

    checks.extend(
        (
            Check(
                "openclaw.timer_active",
                timer_active.returncode == 0 and timer_active.stdout.strip() == "active",
                _cmd_text(timer_active),
            ),
            Check(
                "openclaw.timer_enabled",
                timer_enabled.returncode == 0
                and timer_enabled.stdout.strip() == "enabled",
                _cmd_text(timer_enabled),
            ),
            Check(
                "openclaw.service_inactive",
                service_active.returncode == 3
                and service_active.stdout.strip() == "inactive",
                _cmd_text(service_active),
            ),
            Check(
                "openclaw.service_not_failed",
                service_failed.stdout.strip() in {"inactive", "unknown"}
                or service_failed.returncode in {1, 3, 4},
                _cmd_text(service_failed),
            ),
            Check(
                "NRestarts_parseable",
                show.returncode == 0 and n_restarts_parseable,
                n_restarts_raw,
            ),
        )
    )
    return ServiceState(
        timer_active=timer_active.returncode == 0 and timer_active.stdout.strip() == "active",
        timer_enabled=timer_enabled.returncode == 0
        and timer_enabled.stdout.strip() == "enabled",
        service_inactive=service_active.returncode == 3
        and service_active.stdout.strip() == "inactive",
        service_failed=service_failed.stdout.strip() == "failed",
        n_restarts_parseable=n_restarts_parseable,
        n_restarts=n_restarts,
        result=props.get("Result"),
        exec_main_status=props.get("ExecMainStatus"),
        last_trigger=last_trigger,
        next_elapse=next_elapse,
        checks=tuple(checks),
    )


def _print_checks(checks: Iterable[Check]) -> None:
    for check in checks:
        status = "PASS" if check.ok else "BLOCK"
        print(f"{status} {check.name}: {check.detail}")


def precheck(args: argparse.Namespace, runner: CommandRunner = _run_command) -> int:
    repo = _repo_root(args.repo_root)
    checks = list(
        _repo_checks(repo, args.expected_commit, runner, require_root_rw=True)
    )
    service = _service_state(runner, include_timer_times=False)
    checks.extend(service.checks)
    _print_checks(checks)
    classification = (
        PREOPEN_PASSIVE_CHECK_PASS
        if all(check.ok for check in checks) and not service.service_failed
        else PREOPEN_PASSIVE_CHECK_BLOCKED
    )
    print(f"FINAL_CLASSIFICATION={classification}")
    return 0 if classification == PREOPEN_PASSIVE_CHECK_PASS else 1


def _journal_lines(runner: CommandRunner, since_utc: str) -> list[str]:
    result = runner(
        (
            "journalctl",
            "-u",
            "openclaw.service",
            "--since",
            since_utc,
            "--no-pager",
        ),
        15,
    )
    if result.returncode != 0:
        raise RuntimeError(_cmd_text(result) or "journalctl failed")
    return result.stdout.splitlines()


def _evidence_lines(lines: Iterable[str]) -> list[str]:
    evidence: list[str] = []
    for line in lines:
        if any(token in line for token in EVIDENCE_TOKENS):
            evidence.append(line)
    return evidence


def _has_regular_session_evidence(evidence: Sequence[str]) -> bool:
    if not any("run_id" in line for line in evidence):
        return False
    if not any(symbol in line for symbol in TARGET_SYMBOLS for line in evidence):
        return False
    market_closed_only_tokens = (
        "before_regular_session_open",
        "after_regular_session_close",
        "market_closed",
    )
    decision_tokens = (
        "decision=",
        "decision",
        "action=",
        "action",
        "projected_exposure_exceeds_max_position_size",
        "Strategy pipeline completed",
        "Strategy proposed no order submission",
    )
    return any(
        any(token in line for token in decision_tokens)
        and not any(token in line for token in market_closed_only_tokens)
        for line in evidence
    )


def _has_runtime_error_evidence(evidence: Sequence[str]) -> bool:
    runtime_error_tokens = ("Traceback", "ERROR", "Exception")
    return any(token in line for token in runtime_error_tokens for line in evidence)


def settle(args: argparse.Namespace, runner: CommandRunner = _run_command) -> int:
    repo = _repo_root(args.repo_root)
    checks = list(
        _repo_checks(repo, args.expected_commit, runner, require_root_rw=False)
    )
    service = _service_state(runner, include_timer_times=True)
    checks.extend(service.checks)
    _print_checks(checks)
    print(f"Result={service.result}")
    print(f"NRestarts={service.n_restarts}")
    print(f"ExecMainStatus={service.exec_main_status}")
    print(f"LastTriggerUSec={service.last_trigger}")
    print(f"NextElapseUSecRealtime={service.next_elapse}")

    classification = FAIL_CLOSED_SETTLE_CHECK_BLOCKED
    try:
        lines = _journal_lines(runner, args.since_utc)
        evidence = _evidence_lines(lines)
        for line in evidence:
            print(f"EVIDENCE {line}")
        has_regular_evidence = _has_regular_session_evidence(evidence)
        has_error_evidence = _has_runtime_error_evidence(evidence)
        if service.service_inactive is False:
            classification = RUNTIME_STATE_UNSETTLED
        elif all(check.ok for check in checks) and has_regular_evidence and not has_error_evidence:
            classification = POST_1330_SETTLED_REGULAR_SESSION_EVIDENCE_FOUND
        elif all(check.ok for check in checks):
            classification = NO_REGULAR_SESSION_EVIDENCE_FOUND
    except RuntimeError as exc:
        print(f"BLOCK journal_read: {exc}")

    print(f"FINAL_CLASSIFICATION={classification}")
    return 0 if classification == POST_1330_SETTLED_REGULAR_SESSION_EVIDENCE_FOUND else 1


def _load_jsonl(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    data = path.read_bytes()
    records: list[dict[str, Any]] = []
    for line in data.decode("utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError("non-object JSONL record")
        records.append(record)
    return records, data


def _first_string(records: Iterable[dict[str, Any]], keys: Sequence[str]) -> str:
    for record in records:
        payload = record.get("payload")
        for source in (record, payload if isinstance(payload, dict) else {}):
            for key in keys:
                value = source.get(key)
                if isinstance(value, str) and value:
                    return value
    return ""


def _candidate_from_jsonl(
    path: Path,
    report_bytes: bytes | None,
    package_root: Path,
) -> DiscoveryCandidate:
    try:
        records, jsonl_bytes = _load_jsonl(path)
        filename_run_id = path.stem
        run_ids = {
            str(record.get("run_id", record.get("canonical_run_id")))
            for record in records
            if record.get("run_id", record.get("canonical_run_id"))
        }
        mixed_run_id = run_ids != {filename_run_id}
        run_id = filename_run_id
        symbol = _first_string(records, ("symbol",))
        decision = _first_string(records, ("decision", "signal", "final_decision"))
        action = _first_string(records, ("action", "order_action"))
        reason = _first_string(records, ("reason",))
        status = ""
        report_aligned = False
        d13_result = "not_evaluated"
        capture_ready = False
        package_exists = (package_root / run_id).exists()

        terminal = evaluate_terminal_completion_jsonl(
            TerminalCompletionEvaluationRequest(
                canonical_run_id=run_id,
                jsonl_bytes=jsonl_bytes,
                jsonl_filename=f"logs/{run_id}.jsonl",
                expected_filename_stem=run_id,
            )
        )
        status = terminal.terminal_completion_status
        if report_bytes is not None:
            report = json.loads(report_bytes.decode("utf-8"))
            if not isinstance(report, dict):
                raise ValueError("non-object last_run_report")
            validate_last_run_report_alignment(
                LastRunReportAlignmentRequest(
                    canonical_run_id=run_id,
                    report_bytes=report_bytes,
                    terminal_completion_status=status,
                    terminal_completion_eligible=terminal.terminal_completion_eligible,
                )
            )
            report_aligned = True
            if report.get("trigger_source") != "systemd_timer":
                raise ValueError("last_run_report trigger_source is not systemd_timer")
            capture_eligibility_guard.evaluate_capture_market_eligibility(
                canonical_run_id=run_id,
                terminal_completion_status=status,
                jsonl_bytes=jsonl_bytes,
                last_run_report_bytes=report_bytes,
            )
            d13_result = "accepted"
        capture_ready = report_aligned and not mixed_run_id and not package_exists
    except Exception as exc:  # noqa: BLE001 - discovery must list fail-closed reasons.
        if "status" not in locals():
            status = ""
        if "mixed_run_id" not in locals():
            mixed_run_id = False
        if "run_id" not in locals():
            run_id = path.stem
        if "symbol" not in locals():
            symbol = ""
        if "decision" not in locals():
            decision = ""
        if "action" not in locals():
            action = ""
        if "reason" not in locals():
            reason = ""
        if "report_aligned" not in locals():
            report_aligned = False
        if "package_exists" not in locals():
            package_exists = (package_root / run_id).exists()
        d13_result = f"blocked:{exc}"
        capture_ready = False

    return DiscoveryCandidate(
        capture_ready=capture_ready,
        run_id=run_id,
        symbol=symbol,
        decision=decision,
        action=action,
        status=status,
        reason=reason,
        report_aligned=report_aligned,
        mixed_run_id=mixed_run_id,
        package_exists=package_exists,
        d13_result=d13_result,
        jsonl_path=str(path),
    )


def _per_run_report_path(repo: Path, run_id: str) -> Path:
    return repo / "run_reports" / f"{run_id}.json"


def _report_bytes_for_run(repo: Path, run_id: str) -> bytes | None:
    per_run = _per_run_report_path(repo, run_id)
    if per_run.exists():
        return per_run.read_bytes()
    latest = repo / "last_run_report.json"
    if latest.exists():
        return latest.read_bytes()
    return None


def _print_candidate(candidate: DiscoveryCandidate) -> None:
    print(
        "CANDIDATE "
        f"capture_ready={candidate.capture_ready} "
        f"run_id={candidate.run_id} "
        f"symbol={candidate.symbol} "
        f"decision={candidate.decision} "
        f"action={candidate.action} "
        f"status={candidate.status} "
        f"reason={candidate.reason} "
        f"report_aligned={candidate.report_aligned} "
        f"mixed_run_id={candidate.mixed_run_id} "
        f"package_exists={candidate.package_exists} "
        f"d13_result={candidate.d13_result} "
        f"jsonl_path={candidate.jsonl_path}"
    )


def discover(args: argparse.Namespace, runner: CommandRunner = _run_command) -> int:
    repo = _repo_root(args.repo_root)
    checks = list(
        _repo_checks(repo, args.expected_commit, runner, require_root_rw=False)
    )
    service = _service_state(runner, include_timer_times=False)
    checks.extend(service.checks)
    _print_checks(checks)
    print("Hold can count if D13 accepts it.")
    print("Buy can count.")
    print("D13-approved risk block can count.")
    print("Market-closed blocks do not count.")
    if not all(check.ok for check in checks):
        print("ELIGIBLE_RUN_ID=")
        print(f"FINAL_CLASSIFICATION={FAIL_CLOSED_DISCOVERY_BLOCKED}")
        return 1

    logs_dir = repo / "logs"
    package_root = repo / "replay_packages"
    if not logs_dir.exists():
        print("BLOCK logs_dir_missing")
        print("ELIGIBLE_RUN_ID=")
        print(f"FINAL_CLASSIFICATION={NO_ELIGIBLE_RUN_ID_FOUND}")
        return 1
    jsonl_paths = sorted(
        logs_dir.glob("*.jsonl"),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )[: args.limit]
    candidates = [
        _candidate_from_jsonl(
            path,
            _report_bytes_for_run(repo, path.stem),
            package_root,
        )
        for path in jsonl_paths
    ]
    for candidate in candidates:
        _print_candidate(candidate)
    selected = next((candidate for candidate in candidates if candidate.capture_ready), None)
    if selected is None:
        print("ELIGIBLE_RUN_ID=")
        print(f"FINAL_CLASSIFICATION={NO_ELIGIBLE_RUN_ID_FOUND}")
        return 1
    print(f"ELIGIBLE_RUN_ID={selected.run_id}")
    print(f"FINAL_CLASSIFICATION={ELIGIBLE_RUN_ID_FOUND_FOR_CAPTURE}")
    return 0


def _pre_capture_checks(
    repo: Path, expected_commit: str, run_id: str, runner: CommandRunner
) -> tuple[Check, ...]:
    checks = list(_repo_checks(repo, expected_commit, runner, require_root_rw=True))
    service = _service_state(runner, include_timer_times=False)
    checks.extend(service.checks)
    checks.extend(
        (
            Check("run_id_supplied", bool(run_id), run_id),
            Check("run_id_safe_path_segment", is_safe_run_id(run_id), run_id),
            Check("jsonl_exists", (repo / "logs" / f"{run_id}.jsonl").exists(), run_id),
            Check(
                "run_report_exists",
                _per_run_report_path(repo, run_id).exists()
                or (repo / "last_run_report.json").exists(),
                run_id,
            ),
            Check(
                "package_directory_absent",
                not (repo / "replay_packages" / run_id).exists(),
                str(repo / "replay_packages" / run_id),
            ),
        )
    )
    return tuple(checks)


def _print_package_inventory(package_dir: Path) -> None:
    if not package_dir.exists():
        print(f"PACKAGE_DIR_MISSING {package_dir}")
        return
    for path in sorted(p for p in package_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(package_dir)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"PACKAGE_FILE {rel} sha256={digest}")


def _capture_readiness_check(repo: Path, run_id: str) -> Check:
    jsonl_path = repo / "logs" / f"{run_id}.jsonl"
    package_root = repo / "replay_packages"
    try:
        candidate = _candidate_from_jsonl(
            jsonl_path,
            _report_bytes_for_run(repo, run_id),
            package_root,
        )
    except OSError as exc:
        return Check("capture_readiness_reproved", False, str(exc))
    _print_candidate(candidate)
    return Check(
        "capture_readiness_reproved",
        candidate.capture_ready and candidate.run_id == run_id,
        candidate.d13_result,
    )


def _git_stdout(
    repo: Path, runner: CommandRunner, args: Sequence[str], timeout: int | None = None
) -> str:
    result = _git(repo, runner, args, timeout)
    return result.stdout.strip() if result.returncode == 0 else ""


def _direct_mac_terminal_read_only_artifact_checks(
    repo: Path,
    expected_commit: str,
    run_id: str,
    authorized: bool,
    runner: CommandRunner,
) -> tuple[Check, ...]:
    branch = _git_stdout(repo, runner, ("rev-parse", "--abbrev-ref", "HEAD"))
    head = _git_stdout(repo, runner, ("rev-parse", "HEAD"))
    origin_main = _git_stdout(repo, runner, ("rev-parse", "origin/main"))
    status = _git(repo, runner, ("status", "--short"))
    status_short = status.stdout.strip()
    log_path = repo / "logs" / f"{run_id}.jsonl"
    run_report_path = repo / "run_reports" / f"{run_id}.json"
    last_run_report_path = repo / "last_run_report.json"
    replay_package_path = repo / "replay_packages" / run_id
    order_state_path = repo / "order_state.json"

    return (
        Check("repo_path_exists", repo.exists(), str(repo)),
        Check("branch_is_main", branch == "main", branch),
        Check("head_equals_expected", head == expected_commit, head),
        Check("origin_main_equals_expected", origin_main == expected_commit, origin_main),
        Check("local_head_equals_origin_main", head == origin_main and bool(head), origin_main),
        Check(
            "git_status_short_clean",
            status.returncode == 0 and status_short == "",
            status_short or "clean",
        ),
        Check("run_id_supplied", bool(run_id), run_id),
        Check("run_id_safe_path_segment", is_safe_run_id(run_id), run_id),
        Check(
            "direct_mac_terminal_read_only_artifact_authorized",
            authorized,
            "authorization flag supplied"
            if authorized
            else "missing --authorize-direct-mac-terminal-read-only-artifact-production",
        ),
        Check("local_mac_only_source_context", True, "LOCAL_MAC_ONLY"),
        Check("direct_mac_terminal_operator_surface", True, "DIRECT_MAC_TERMINAL"),
        Check("read_only_authority_boundary", True, "read_only_no_broker_no_order_no_execution"),
        Check("broker_submit_readiness_not_approved", True, "NOT_APPROVED"),
        Check("live_trading_readiness_not_approved", True, "NOT_APPROVED"),
        Check("account_authority_none", True, "NONE"),
        Check("order_authority_none", True, "NONE"),
        Check("execution_authority_none", True, "NONE"),
        Check("tws_api_network_runtime_action_not_used", True, "false"),
        Check("vps_action_not_used", True, "false"),
        Check("scheduler_service_systemd_timer_mutation_not_used", True, "false"),
        Check("credential_env_mutation_not_used", True, "false"),
        Check("package_capture_not_executed", True, "false"),
        Check("replay_not_executed", True, "false"),
        Check("scoring_not_executed", True, "false"),
        Check("candidate_generation_not_executed", True, "false"),
        Check("unit_12_not_opened", True, "false"),
        Check("log_output_absent_before_write", not log_path.exists(), str(log_path)),
        Check(
            "run_report_output_absent_before_write",
            not run_report_path.exists(),
            str(run_report_path),
        ),
        Check(
            "last_run_report_output_absent_before_write",
            not last_run_report_path.exists(),
            str(last_run_report_path),
        ),
        Check(
            "replay_package_output_prohibited_and_absent",
            not replay_package_path.exists(),
            str(replay_package_path),
        ),
        Check(
            "order_state_absent_excluded_not_bound",
            not order_state_path.exists(),
            "order_state_json=ABSENT_EXCLUDED_NOT_BOUND",
        ),
    )


def _artifact_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return value


def _first_jsonl_object(path: Path) -> dict[str, Any]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} contained a non-object JSONL record")
        return value
    raise ValueError(f"{path} contained no JSONL records")


def _artifact_json_field(path: Path, field: str) -> str:
    try:
        return str(_read_json_object(path).get(field, ""))
    except (OSError, ValueError, json.JSONDecodeError):
        return ""


def _artifact_jsonl_field(path: Path, field: str) -> str:
    try:
        return str(_first_jsonl_object(path).get(field, ""))
    except (OSError, ValueError, json.JSONDecodeError):
        return ""


def _direct_mac_terminal_read_only_package_checks(
    repo: Path,
    expected_commit: str,
    run_id: str,
    artifact_runtime_commit: str,
    expected_log_sha256: str,
    expected_run_report_sha256: str,
    expected_last_run_report_sha256: str,
    authorized: bool,
    runner: CommandRunner,
) -> tuple[Check, ...]:
    branch = _git_stdout(repo, runner, ("rev-parse", "--abbrev-ref", "HEAD"))
    head = _git_stdout(repo, runner, ("rev-parse", "HEAD"))
    origin_main = _git_stdout(repo, runner, ("rev-parse", "origin/main"))
    status = _git(repo, runner, ("status", "--short"))
    status_short = status.stdout.strip()
    log_path = repo / "logs" / f"{run_id}.jsonl"
    run_report_path = repo / "run_reports" / f"{run_id}.json"
    last_run_report_path = repo / "last_run_report.json"
    replay_package_path = repo / "replay_packages" / run_id
    order_state_path = repo / "order_state.json"

    log_exists = log_path.exists()
    run_report_exists = run_report_path.exists()
    last_run_report_exists = last_run_report_path.exists()
    log_sha256 = _artifact_digest(log_path) if log_exists else ""
    run_report_sha256 = _artifact_digest(run_report_path) if run_report_exists else ""
    last_run_report_sha256 = (
        _artifact_digest(last_run_report_path) if last_run_report_exists else ""
    )
    last_run_report_identical = (
        run_report_exists
        and last_run_report_exists
        and run_report_path.read_bytes() == last_run_report_path.read_bytes()
    )

    return (
        Check("repo_path_exists", repo.exists(), str(repo)),
        Check("branch_is_main", branch == "main", branch),
        Check("head_equals_expected", head == expected_commit, head),
        Check("origin_main_equals_expected", origin_main == expected_commit, origin_main),
        Check("local_head_equals_origin_main", head == origin_main and bool(head), origin_main),
        Check(
            "git_status_short_clean",
            status.returncode == 0 and status_short == "",
            status_short or "clean",
        ),
        Check("run_id_supplied", bool(run_id), run_id),
        Check("run_id_safe_path_segment", is_safe_run_id(run_id), run_id),
        Check(
            "direct_mac_terminal_read_only_package_capture_authorized",
            authorized,
            "authorization flag supplied"
            if authorized
            else "missing --authorize-direct-mac-terminal-read-only-package-capture",
        ),
        Check("local_mac_only_source_context", True, "LOCAL_MAC_ONLY"),
        Check("direct_mac_terminal_operator_surface", True, "DIRECT_MAC_TERMINAL"),
        Check("read_only_package_capture_boundary", True, "read_only_file_package_only"),
        Check("broker_submit_readiness_not_approved", True, "NOT_APPROVED"),
        Check("live_trading_readiness_not_approved", True, "NOT_APPROVED"),
        Check("account_authority_none", True, "NONE"),
        Check("order_authority_none", True, "NONE"),
        Check("execution_authority_none", True, "NONE"),
        Check("tws_api_network_runtime_action_not_used", True, "false"),
        Check("vps_action_not_used", True, "false"),
        Check("scheduler_service_systemd_timer_mutation_not_used", True, "false"),
        Check("credential_env_mutation_not_used", True, "false"),
        Check("replay_not_executed", True, "false"),
        Check("scoring_not_executed", True, "false"),
        Check("candidate_generation_not_executed", True, "false"),
        Check("unit_12_not_opened", True, "false"),
        Check("log_artifact_exists", log_exists, str(log_path)),
        Check("run_report_artifact_exists", run_report_exists, str(run_report_path)),
        Check(
            "last_run_report_artifact_exists",
            last_run_report_exists,
            str(last_run_report_path),
        ),
        Check("log_sha256_matches", log_sha256 == expected_log_sha256, log_sha256),
        Check(
            "run_report_sha256_matches",
            run_report_sha256 == expected_run_report_sha256,
            run_report_sha256,
        ),
        Check(
            "last_run_report_sha256_matches",
            last_run_report_sha256 == expected_last_run_report_sha256,
            last_run_report_sha256,
        ),
        Check(
            "last_run_report_byte_identical_to_run_report",
            last_run_report_identical,
            "BYTE_IDENTICAL" if last_run_report_identical else "NOT_IDENTICAL",
        ),
        Check(
            "log_expected_commit_matches_artifact_runtime_commit",
            _artifact_jsonl_field(log_path, "expected_commit") == artifact_runtime_commit,
            _artifact_jsonl_field(log_path, "expected_commit"),
        ),
        Check(
            "log_actual_head_matches_artifact_runtime_commit",
            _artifact_jsonl_field(log_path, "actual_head") == artifact_runtime_commit,
            _artifact_jsonl_field(log_path, "actual_head"),
        ),
        Check(
            "run_report_expected_commit_matches_artifact_runtime_commit",
            _artifact_json_field(run_report_path, "expected_commit")
            == artifact_runtime_commit,
            _artifact_json_field(run_report_path, "expected_commit"),
        ),
        Check(
            "run_report_origin_main_matches_artifact_runtime_commit",
            _artifact_json_field(run_report_path, "origin_main") == artifact_runtime_commit,
            _artifact_json_field(run_report_path, "origin_main"),
        ),
        Check(
            "package_directory_absent",
            not replay_package_path.exists(),
            str(replay_package_path),
        ),
        Check(
            "order_state_absent_excluded_not_bound",
            not order_state_path.exists(),
            "order_state_json=ABSENT_EXCLUDED_NOT_BOUND",
        ),
    )


def capture_local_read_only_package(
    args: argparse.Namespace, runner: CommandRunner = _run_command
) -> int:
    """LOCAL_MAC-only replay package write from adjudicated read-only artifacts."""

    repo = _repo_root(args.repo_root)
    checks = list(
        _direct_mac_terminal_read_only_package_checks(
            repo,
            args.expected_commit,
            args.run_id,
            args.artifact_runtime_commit,
            args.expected_log_sha256,
            args.expected_run_report_sha256,
            args.expected_last_run_report_sha256,
            args.authorize_direct_mac_terminal_read_only_package_capture,
            runner,
        )
    )
    _print_checks(checks)

    print(f"RUN_ID={args.run_id}")
    print(f"EXPECTED_COMMIT={args.expected_commit}")
    print(f"ARTIFACT_RUNTIME_COMMIT={args.artifact_runtime_commit}")
    print("SOURCE_CONTEXT=LOCAL_MAC_ONLY")
    print("OPERATOR_SURFACE=DIRECT_MAC_TERMINAL")
    print("READ_ONLY_PACKAGE_CAPTURE_AUTHORITY=true")
    print("BROKER_SUBMIT_READINESS=NOT_APPROVED")
    print("LIVE_TRADING_READINESS=NOT_APPROVED")
    print("ACCOUNT_AUTHORITY=NONE")
    print("ORDER_AUTHORITY=NONE")
    print("EXECUTION_AUTHORITY=NONE")
    print("TWS_API_NETWORK_RUNTIME_ACTION=false")
    print("VPS_ACTION=false")
    print("REPLAY_EXECUTED=false")
    print("SCORING_EXECUTED=false")
    print("CANDIDATE_GENERATION_EXECUTED=false")
    print("UNIT_12_ACTION=false")
    print("ORDER_STATE_BOUND=false")
    print("VPS_PACKAGE_WRITE_AUTHORITY_USED=false")
    print("EXECUTION_MODE_VPS_USED=false")

    if not all(check.ok for check in checks):
        print("PACKAGE_CAPTURE_EXECUTED=false")
        print("REPLAY_PACKAGE_PATH=")
        print(
            "FINAL_CLASSIFICATION="
            f"{DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_FAILED_CLOSED}"
        )
        return 1

    log_path = repo / "logs" / f"{args.run_id}.jsonl"
    run_report_path = repo / "run_reports" / f"{args.run_id}.json"
    last_run_report_path = repo / "last_run_report.json"
    package_dir = repo / "replay_packages" / args.run_id
    manifest_path = package_dir / "manifest.json"

    package_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "artifact_runtime_commit": args.artifact_runtime_commit,
        "authority": {
            "account_authority": "NONE",
            "broker_submit_readiness": "NOT_APPROVED",
            "execution_authority": "NONE",
            "live_trading_readiness": "NOT_APPROVED",
            "order_authority": "NONE",
            "order_state_bound": False,
            "vps_action": False,
        },
        "input_artifacts": [
            {
                "path": str(log_path.relative_to(repo)),
                "sha256": _artifact_digest(log_path),
            },
            {
                "path": str(run_report_path.relative_to(repo)),
                "sha256": _artifact_digest(run_report_path),
            },
            {
                "path": str(last_run_report_path.relative_to(repo)),
                "sha256": _artifact_digest(last_run_report_path),
            },
        ],
        "package_capture": {
            "execution_mode_vps_used": False,
            "local_mac_only": True,
            "package_path": str(package_dir.relative_to(repo)),
            "source_artifacts_mutated": False,
            "vps_package_write_authority_used": False,
        },
        "run_id": args.run_id,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print("PACKAGE_CAPTURE_EXECUTED=true")
    print(f"REPLAY_PACKAGE_PATH={package_dir.relative_to(repo)}")
    print(f"PACKAGE_FILE manifest.json sha256={_artifact_digest(manifest_path)}")
    print(
        "FINAL_CLASSIFICATION="
        f"{DIRECT_MAC_TERMINAL_READ_ONLY_PACKAGE_CAPTURE_COMPLETED}"
    )
    return 0


def produce_read_only_artifacts(
    args: argparse.Namespace, runner: CommandRunner = _run_command
) -> int:
    """Produce local read-only runtime artifacts with fail-closed boundaries."""

    repo = _repo_root(args.repo_root)
    checks = list(
        _direct_mac_terminal_read_only_artifact_checks(
            repo,
            args.expected_commit,
            args.run_id,
            args.authorize_direct_mac_terminal_read_only_artifact_production,
            runner,
        )
    )
    _print_checks(checks)

    branch = _git_stdout(repo, runner, ("rev-parse", "--abbrev-ref", "HEAD"))
    actual_head = _git_stdout(repo, runner, ("rev-parse", "HEAD"))
    origin_main = _git_stdout(repo, runner, ("rev-parse", "origin/main"))
    status = _git(repo, runner, ("status", "--short"))
    status_short = status.stdout.strip()

    print(f"RUN_ID={args.run_id}")
    print(f"EXPECTED_COMMIT={args.expected_commit}")
    print(f"ACTUAL_HEAD={actual_head}")
    print(f"ORIGIN_MAIN={origin_main}")
    print(f"ORIGIN_MAIN_ALIGNED={str(actual_head == origin_main and bool(actual_head)).lower()}")
    print(f"BRANCH={branch}")
    print(f"WORKTREE_CLEAN={str(status.returncode == 0 and status_short == '').lower()}")
    print(f"STATUS_SHORT={status_short or 'clean'}")
    print("SOURCE_CONTEXT=LOCAL_MAC_ONLY")
    print("OPERATOR_SURFACE=DIRECT_MAC_TERMINAL")
    print("READ_ONLY_AUTHORITY=true")
    print("BROKER_SUBMIT_READINESS=NOT_APPROVED")
    print("LIVE_TRADING_READINESS=NOT_APPROVED")
    print("ACCOUNT_AUTHORITY=NONE")
    print("ORDER_AUTHORITY=NONE")
    print("EXECUTION_AUTHORITY=NONE")
    print("TWS_API_NETWORK_RUNTIME_ACTION=false")
    print("VPS_ACTION=false")
    print("PACKAGE_CAPTURE_EXECUTED=false")
    print("REPLAY_EXECUTED=false")
    print("SCORING_EXECUTED=false")
    print("CANDIDATE_GENERATION_EXECUTED=false")
    print("UNIT_12_ACTION=false")
    print("ORDER_STATE_BOUND=false")

    if not all(check.ok for check in checks):
        print("PRODUCED_ARTIFACT_PATHS=")
        print(
            "FINAL_CLASSIFICATION="
            f"{DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_FAILED_CLOSED}"
        )
        return 1

    log_path = repo / "logs" / f"{args.run_id}.jsonl"
    run_report_path = repo / "run_reports" / f"{args.run_id}.json"
    last_run_report_path = repo / "last_run_report.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    run_report_path.parent.mkdir(parents=True, exist_ok=True)

    evidence = {
        "account_authority": "NONE",
        "actual_head": actual_head,
        "broker_submit_readiness": "NOT_APPROVED",
        "candidate_generation_executed": False,
        "execution_authority": "NONE",
        "expected_commit": args.expected_commit,
        "live_trading_readiness": "NOT_APPROVED",
        "operator_surface": "DIRECT_MAC_TERMINAL",
        "order_authority": "NONE",
        "package_capture_executed": False,
        "read_only_authority": True,
        "replay_executed": False,
        "run_id": args.run_id,
        "scoring_executed": False,
        "source_context": "LOCAL_MAC_ONLY",
        "terminal_completion_status": (
            "DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETE"
        ),
        "unit_12_action": False,
        "vps_action": False,
    }
    log_path.write_text(json.dumps(evidence, sort_keys=True) + "\n", encoding="utf-8")

    report = {
        "allowed_outputs": [
            f"logs/{args.run_id}.jsonl",
            f"run_reports/{args.run_id}.json",
            "last_run_report.json",
        ],
        "expected_commit": args.expected_commit,
        "origin_main": origin_main,
        "produced_artifacts": [
            str(log_path.relative_to(repo)),
            str(run_report_path.relative_to(repo)),
            str(last_run_report_path.relative_to(repo)),
        ],
        "prohibited_outputs_not_written": [
            "replay_packages/",
            "order_state.json",
            "broker/account/order/execution files",
            "scheduler/service/timer/systemd files",
            "credential/env files",
        ],
        "read_only_authority": True,
        "run_id": args.run_id,
        "source_context": "LOCAL_MAC_ONLY",
        "trigger_source": "direct_mac_terminal_read_only_artifact_production",
        "worktree_clean": status.returncode == 0 and status_short == "",
    }
    report_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    run_report_path.write_text(report_text, encoding="utf-8")
    last_run_report_path.write_text(report_text, encoding="utf-8")

    produced = (log_path, run_report_path, last_run_report_path)
    print(
        "PRODUCED_ARTIFACT_PATHS="
        + ",".join(str(path.relative_to(repo)) for path in produced)
    )
    for path in produced:
        print(f"PRODUCED_ARTIFACT {path.relative_to(repo)} sha256={_artifact_digest(path)}")
    print(
        "FINAL_CLASSIFICATION="
        f"{DIRECT_MAC_TERMINAL_READ_ONLY_ARTIFACT_PRODUCTION_COMPLETED}"
    )
    return 0


def capture(args: argparse.Namespace, runner: CommandRunner = _run_command) -> int:
    repo = _repo_root(args.repo_root)
    checks = list(_pre_capture_checks(repo, args.expected_commit, args.run_id, runner))
    if args.run_id and is_safe_run_id(args.run_id):
        checks.append(_capture_readiness_check(repo, args.run_id))
    _print_checks(checks)
    if not args.authorize_vps_package_write or not all(check.ok for check in checks):
        print(f"FINAL_CLASSIFICATION={CAPTURE_ATTEMPT_FAILED_CLOSED_NO_RETRY_WITHOUT_NEW_AUTHORIZATION}")
        return 1

    old_cwd = Path.cwd()
    try:
        os.chdir(repo)
        code = package_execution_orchestrator.main(
            [
                "--run-id",
                args.run_id,
                "--execution-mode",
                "vps",
                "--authorize-vps-package-write",
            ]
        )
    finally:
        os.chdir(old_cwd)
    package_dir = repo / "replay_packages" / args.run_id
    _print_package_inventory(package_dir)
    status = _git(repo, runner, ("status", "--short"))
    print("GIT_STATUS_BEGIN")
    print(status.stdout.strip())
    print("GIT_STATUS_END")
    classification = (
        ONE_GOVERNED_PACKAGE_CAPTURED_PENDING_D14_LEDGER_FOLLOW_UP
        if code == 0
        else CAPTURE_ATTEMPT_FAILED_CLOSED_NO_RETRY_WITHOUT_NEW_AUTHORIZATION
    )
    print(f"FINAL_CLASSIFICATION={classification}")
    return 0 if code == 0 else 1


def capture_local(
    args: argparse.Namespace, runner: CommandRunner = _run_command
) -> int:
    """LOCAL_MAC-only package-capture preflight surface.

    This command reconciles the LOCAL_MAC authority surface without delegating
    to the VPS package execution path. It does not write a replay package;
    package capture still requires a later bounded operator-run reauthorization
    gate.
    """

    repo = _repo_root(args.repo_root)
    checks = list(_pre_capture_checks(repo, args.expected_commit, args.run_id, runner))
    if args.run_id and is_safe_run_id(args.run_id):
        checks.append(_capture_readiness_check(repo, args.run_id))
    checks.append(
        Check(
            "local_package_write_authorized",
            bool(args.authorize_local_package_write),
            "local-only authorization flag supplied"
            if args.authorize_local_package_write
            else "missing --authorize-local-package-write",
        )
    )
    checks.append(
        Check(
            "vps_package_write_authority_not_used",
            True,
            "--authorize-vps-package-write is not accepted by capture-local",
        )
    )
    checks.append(
        Check(
            "vps_execution_mode_not_used",
            True,
            "capture-local does not delegate to --execution-mode vps",
        )
    )
    checks.append(
        Check(
            "order_state_excluded_not_bound",
            True,
            "order_state_json=ABSENT_EXCLUDED_NOT_BOUND",
        )
    )
    _print_checks(checks)
    classification = (
        LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_READY_REAUTHORIZATION_REQUIRED
        if all(check.ok for check in checks)
        else LOCAL_MAC_PACKAGE_CAPTURE_PREFLIGHT_FAILED_CLOSED
    )
    print("PACKAGE_CAPTURE_EXECUTED=false")
    print("REPLAY_EXECUTED=false")
    print("SCORING_EXECUTED=false")
    print("CANDIDATE_GENERATION_EXECUTED=false")
    print("VPS_ACTION=false")
    print("ORDER_STATE_BOUND=false")
    print(f"FINAL_CLASSIFICATION={classification}")
    return 0 if all(check.ok for check in checks) else 1


def build_parser() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--repo-root", default=".")
    parser = argparse.ArgumentParser(
        prog="gate_d_market_session_operator",
        description="Gate D market-session operator CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    pre = subparsers.add_parser("precheck", parents=[parent])
    pre.add_argument("--expected-commit", default=EXPECTED_COMMIT)
    pre.set_defaults(func=precheck)

    settle_parser = subparsers.add_parser("settle", parents=[parent])
    settle_parser.add_argument("--since-utc", default=DEFAULT_SINCE_UTC)
    settle_parser.add_argument("--expected-commit", default=EXPECTED_COMMIT)
    settle_parser.set_defaults(func=settle)

    disc = subparsers.add_parser("discover", parents=[parent])
    disc.add_argument("--expected-commit", default=EXPECTED_COMMIT)
    disc.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    disc.set_defaults(func=discover)

    cap = subparsers.add_parser("capture", parents=[parent])
    cap.add_argument("--run-id", required=True)
    cap.add_argument("--expected-commit", default=EXPECTED_COMMIT)
    cap.add_argument("--authorize-vps-package-write", action="store_true", required=True)
    cap.set_defaults(func=capture)

    cap_local = subparsers.add_parser("capture-local", parents=[parent])
    cap_local.add_argument("--run-id", required=True)
    cap_local.add_argument("--expected-commit", required=True)
    cap_local.add_argument(
        "--authorize-local-package-write", action="store_true", required=True
    )
    cap_local.set_defaults(func=capture_local)

    cap_local_read_only_package = subparsers.add_parser(
        "capture-local-read-only-package", parents=[parent]
    )
    cap_local_read_only_package.add_argument("--run-id", required=True)
    cap_local_read_only_package.add_argument("--expected-commit", required=True)
    cap_local_read_only_package.add_argument("--artifact-runtime-commit", required=True)
    cap_local_read_only_package.add_argument("--expected-log-sha256", required=True)
    cap_local_read_only_package.add_argument(
        "--expected-run-report-sha256", required=True
    )
    cap_local_read_only_package.add_argument(
        "--expected-last-run-report-sha256", required=True
    )
    cap_local_read_only_package.add_argument(
        "--authorize-direct-mac-terminal-read-only-package-capture",
        action="store_true",
        required=True,
    )
    cap_local_read_only_package.set_defaults(func=capture_local_read_only_package)

    read_only_artifacts = subparsers.add_parser(
        "produce-read-only-artifacts", parents=[parent]
    )
    read_only_artifacts.add_argument("--run-id", required=True)
    read_only_artifacts.add_argument("--expected-commit", required=True)
    read_only_artifacts.add_argument(
        "--authorize-direct-mac-terminal-read-only-artifact-production",
        action="store_true",
        required=True,
    )
    read_only_artifacts.set_defaults(func=produce_read_only_artifacts)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
