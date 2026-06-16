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
    report_path = repo / "last_run_report.json"
    package_root = repo / "replay_packages"
    if not logs_dir.exists():
        print("BLOCK logs_dir_missing")
        print("ELIGIBLE_RUN_ID=")
        print(f"FINAL_CLASSIFICATION={NO_ELIGIBLE_RUN_ID_FOUND}")
        return 1
    report_bytes = report_path.read_bytes() if report_path.exists() else None
    jsonl_paths = sorted(
        logs_dir.glob("*.jsonl"),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )[: args.limit]
    candidates = [
        _candidate_from_jsonl(path, report_bytes, package_root) for path in jsonl_paths
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
            Check("last_run_report_exists", (repo / "last_run_report.json").exists(), ""),
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
    report_path = repo / "last_run_report.json"
    package_root = repo / "replay_packages"
    try:
        candidate = _candidate_from_jsonl(
            jsonl_path,
            report_path.read_bytes(),
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
