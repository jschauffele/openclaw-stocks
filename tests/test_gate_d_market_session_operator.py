from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.ops import gate_d_market_session_operator as operator


RUN_ID = "run_2026-06-16T13:30:00Z_ab12cd"
EXPECTED = operator.EXPECTED_COMMIT


class FakeRunner:
    def __init__(self, *, dirty: bool = False, remote_ok: bool = True,
                 remote_timeout: bool = False, service_active: bool = False,
                 timer_active: bool = True, timer_enabled: bool = True,
                 mount_options: str = "rw,relatime,errors=remount-ro",
                 journal_text: str | None = None) -> None:
        self.dirty = dirty
        self.remote_ok = remote_ok
        self.remote_timeout = remote_timeout
        self.service_active = service_active
        self.timer_active = timer_active
        self.timer_enabled = timer_enabled
        self.mount_options = mount_options
        self.journal_text = journal_text
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv, timeout=None):
        args = tuple(argv)
        self.calls.append(args)
        joined = " ".join(args)
        if args[:2] == ("git", "-C"):
            git_args = args[3:]
            if git_args == ("rev-parse", "--abbrev-ref", "HEAD"):
                return operator.CommandResult(args, 0, "main\n")
            if git_args == ("rev-parse", "HEAD"):
                return operator.CommandResult(args, 0, f"{EXPECTED}\n")
            if git_args == ("status", "--porcelain"):
                return operator.CommandResult(args, 0, " M main.py\n" if self.dirty else "")
            if git_args == ("status", "--short"):
                return operator.CommandResult(args, 0, "")
        if args[:3] == ("timeout", "15", "git"):
            if self.remote_timeout:
                return operator.CommandResult(args, 124, stderr="timed out", timed_out=True)
            if self.remote_ok:
                return operator.CommandResult(args, 0, f"{EXPECTED}\trefs/heads/main\n")
            return operator.CommandResult(args, 128, stderr="unavailable")
        if args == ("findmnt", "-no", "OPTIONS", "/"):
            return operator.CommandResult(args, 0, f"{self.mount_options}\n")
        if args == ("systemctl", "is-active", "openclaw.timer"):
            return operator.CommandResult(
                args, 0 if self.timer_active else 3, "active\n" if self.timer_active else "inactive\n"
            )
        if args == ("systemctl", "is-enabled", "openclaw.timer"):
            return operator.CommandResult(
                args, 0 if self.timer_enabled else 1, "enabled\n" if self.timer_enabled else "disabled\n"
            )
        if args == ("systemctl", "is-active", "openclaw.service"):
            return operator.CommandResult(
                args, 0 if self.service_active else 3, "active\n" if self.service_active else "inactive\n"
            )
        if args == ("systemctl", "is-failed", "openclaw.service"):
            return operator.CommandResult(args, 1, "inactive\n")
        if joined.startswith("systemctl show openclaw.service"):
            return operator.CommandResult(args, 0, "NRestarts=0\nResult=success\nExecMainStatus=0\n")
        if joined.startswith("systemctl show openclaw.timer"):
            return operator.CommandResult(
                args,
                0,
                "LastTriggerUSec=Tue 2026-06-16 13:30:00 UTC\n"
                "NextElapseUSecRealtime=Tue 2026-06-16 13:45:00 UTC\n",
            )
        if args[:3] == ("journalctl", "-u", "openclaw.service"):
            return operator.CommandResult(
                args,
                0,
                self.journal_text
                if self.journal_text is not None
                else (
                    f"OpenClaw run finished run_id={RUN_ID} symbol=AAPL "
                    "decision=hold action=hold reason=no_signal\n"
                ),
            )
        raise AssertionError(f"unexpected command: {args}")


def _args(**overrides):
    base = {
        "repo_root": ".",
        "expected_commit": EXPECTED,
        "since_utc": operator.DEFAULT_SINCE_UTC,
        "limit": 60,
        "run_id": RUN_ID,
        "authorize_vps_package_write": True,
    }
    base.update(overrides)
    return type("Args", (), base)()


def _write_run(repo: Path, run_id: str = RUN_ID, *, reason: str = "no_signal",
               status: str = "blocked", report_run_id: str | None = None,
               trigger_source: str = "systemd_timer") -> None:
    logs = repo / "logs"
    logs.mkdir(exist_ok=True)
    records = [
        {"run_id": run_id, "event_type": "system", "stage": "startup", "status": "ok", "payload": {"symbol": "AAPL"}},
        {
            "run_id": run_id,
            "event_type": "system",
            "stage": "completion",
            "status": status,
            "payload": {"reason": reason, "symbol": "AAPL", "decision": "hold", "action": "hold"},
        },
    ]
    (logs / f"{run_id}.jsonl").write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    report = {
        "run_id": report_run_id or run_id,
        "status": status,
        "reason": reason,
        "trigger_source": trigger_source,
    }
    (repo / "last_run_report.json").write_text(json.dumps(report), encoding="utf-8")


def _write_per_run_report(
    repo: Path,
    run_id: str = RUN_ID,
    *,
    reason: str = "projected_exposure_exceeds_max_position_size",
    report_run_id: str | None = None,
    trigger_source: str = "systemd_timer",
    status: str = "blocked",
) -> None:
    report = {
        "run_id": report_run_id or run_id,
        "status": status,
        "reason": reason,
        "trigger_source": trigger_source,
    }
    report_dir = repo / "run_reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / f"{run_id}.json").write_text(json.dumps(report), encoding="utf-8")


def test_root_rw_option_parser_does_not_match_remount_ro_substring() -> None:
    assert operator.root_mount_is_rw("ro,relatime,errors=remount-ro") is False
    assert operator.root_mount_is_rw("rw,relatime,errors=remount-ro") is True


def test_expected_commit_validation_blocks_mismatch(tmp_path: Path) -> None:
    checks = operator._repo_checks(tmp_path, "bad", FakeRunner(), require_root_rw=False)
    assert any(check.name == "head_equals_expected" and not check.ok for check in checks)


def test_dirty_git_status_fails_precheck(tmp_path: Path, capsys) -> None:
    code = operator.precheck(_args(repo_root=str(tmp_path)), FakeRunner(dirty=True))
    out = capsys.readouterr().out
    assert code == 1
    assert "git_status_clean" in out
    assert operator.PREOPEN_PASSIVE_CHECK_BLOCKED in out


def test_remote_timeout_blocks_precheck(tmp_path: Path, capsys) -> None:
    code = operator.precheck(_args(repo_root=str(tmp_path)), FakeRunner(remote_timeout=True))
    out = capsys.readouterr().out
    assert code == 1
    assert "remote_main_equals_expected" in out
    assert operator.PREOPEN_PASSIVE_CHECK_BLOCKED in out


def test_service_active_is_unsettled(tmp_path: Path, capsys) -> None:
    code = operator.settle(_args(repo_root=str(tmp_path)), FakeRunner(service_active=True))
    out = capsys.readouterr().out
    assert code == 1
    assert operator.RUNTIME_STATE_UNSETTLED in out


@pytest.mark.parametrize(
    "reason",
    (
        "after_regular_session_close",
        "before_regular_session_open",
        "market_closed",
    ),
)
def test_settle_market_closed_evidence_is_not_regular_session(
    tmp_path: Path, capsys, reason: str
) -> None:
    journal = (
        f"OpenClaw run finished run_id={RUN_ID} symbol=AAPL "
        f"reason={reason}\n"
    )
    code = operator.settle(
        _args(repo_root=str(tmp_path)), FakeRunner(journal_text=journal)
    )
    out = capsys.readouterr().out
    assert code == 1
    assert operator.POST_1330_SETTLED_REGULAR_SESSION_EVIDENCE_FOUND not in out
    assert operator.NO_REGULAR_SESSION_EVIDENCE_FOUND in out


def test_settle_regular_decision_evidence_can_classify_pass(
    tmp_path: Path, capsys
) -> None:
    journal = (
        f"OpenClaw run finished run_id={RUN_ID} symbol=AAPL "
        "decision=hold action=hold reason=no_signal\n"
    )
    code = operator.settle(
        _args(repo_root=str(tmp_path)), FakeRunner(journal_text=journal)
    )
    out = capsys.readouterr().out
    assert code == 0
    assert operator.POST_1330_SETTLED_REGULAR_SESSION_EVIDENCE_FOUND in out


@pytest.mark.parametrize(
    "reason",
    (
        "three_close_confirmation_failed",
        "percent_change_below_buy_threshold",
    ),
)
def test_settle_regular_strategy_hold_reasons_classify_pass(
    tmp_path: Path, capsys, reason: str
) -> None:
    journal = (
        f"OpenClaw run finished run_id={RUN_ID} symbol=MSTR\n"
        f"Strategy pipeline completed: signal=hold, decision=hold, "
        f"action=hold, reason={reason}\n"
        f"Strategy proposed no order submission: action=hold, reason={reason}\n"
    )
    code = operator.settle(
        _args(repo_root=str(tmp_path)), FakeRunner(journal_text=journal)
    )
    out = capsys.readouterr().out
    assert code == 0
    assert operator.POST_1330_SETTLED_REGULAR_SESSION_EVIDENCE_FOUND in out


@pytest.mark.parametrize(
    "error_text",
    (
        "Traceback (most recent call last):",
        "ERROR unhandled runtime failure",
        "Exception: unhandled runtime failure",
    ),
)
def test_settle_runtime_error_markers_block_regular_session_success(
    tmp_path: Path, capsys, error_text: str
) -> None:
    journal = (
        f"OpenClaw run finished run_id={RUN_ID} symbol=MSTR\n"
        "Strategy pipeline completed: signal=hold, decision=hold, "
        "action=hold, reason=percent_change_below_buy_threshold\n"
        f"{error_text}\n"
    )
    code = operator.settle(
        _args(repo_root=str(tmp_path)), FakeRunner(journal_text=journal)
    )
    out = capsys.readouterr().out
    assert code == 1
    assert operator.POST_1330_SETTLED_REGULAR_SESSION_EVIDENCE_FOUND not in out
    assert operator.NO_REGULAR_SESSION_EVIDENCE_FOUND in out


def test_timer_inactive_or_disabled_blocks_precheck(tmp_path: Path, capsys) -> None:
    code = operator.precheck(_args(repo_root=str(tmp_path)), FakeRunner(timer_active=False))
    assert code == 1
    assert operator.PREOPEN_PASSIVE_CHECK_BLOCKED in capsys.readouterr().out
    code = operator.precheck(_args(repo_root=str(tmp_path)), FakeRunner(timer_enabled=False))
    assert code == 1


@pytest.mark.parametrize("run_id", ("../x", "a/b", "a\\b", "", ".."))
def test_run_id_path_safety(run_id: str) -> None:
    assert operator.is_safe_run_id(run_id) is False
    assert operator.is_safe_run_id(RUN_ID) is True


def test_package_directory_preexistence_blocks_capture(tmp_path: Path, capsys) -> None:
    _write_run(tmp_path)
    (tmp_path / "replay_packages" / RUN_ID).mkdir(parents=True)
    code = operator.capture(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 1
    assert "package_directory_absent" in out
    assert operator.CAPTURE_ATTEMPT_FAILED_CLOSED_NO_RETRY_WITHOUT_NEW_AUTHORIZATION in out


def test_missing_jsonl_blocks_capture(tmp_path: Path, capsys) -> None:
    (tmp_path / "last_run_report.json").write_text("{}", encoding="utf-8")
    code = operator.capture(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 1
    assert "jsonl_exists" in out


def test_discovery_does_not_mark_non_report_aligned_run_capture_ready(tmp_path: Path, capsys) -> None:
    _write_run(tmp_path, report_run_id="run_other")
    code = operator.discover(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 1
    assert "capture_ready=False" in out
    assert "ELIGIBLE_RUN_ID=\n" in out
    assert operator.NO_ELIGIBLE_RUN_ID_FOUND in out


def test_discovery_marks_report_aligned_d13_passing_run_capture_ready(tmp_path: Path, capsys) -> None:
    _write_run(tmp_path, reason="projected_exposure_exceeds_max_position_size")
    code = operator.discover(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 0
    assert "capture_ready=True" in out
    assert f"ELIGIBLE_RUN_ID={RUN_ID}" in out
    assert operator.ELIGIBLE_RUN_ID_FOUND_FOR_CAPTURE in out


def test_discovery_prefers_exact_per_run_report_for_earlier_symbol_run(
    tmp_path: Path, capsys
) -> None:
    later_run_id = "run_2026-06-16T13:30:10Z_later"
    _write_run(
        tmp_path,
        run_id=RUN_ID,
        reason="projected_exposure_exceeds_max_position_size",
    )
    _write_per_run_report(tmp_path, RUN_ID)
    _write_run(
        tmp_path,
        run_id=later_run_id,
        reason="market_closed",
    )
    code = operator.discover(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 0
    assert f"run_id={RUN_ID}" in out
    assert f"ELIGIBLE_RUN_ID={RUN_ID}" in out
    assert operator.ELIGIBLE_RUN_ID_FOUND_FOR_CAPTURE in out


def test_discovery_stale_per_run_report_fails_even_when_latest_report_matches(
    tmp_path: Path, capsys
) -> None:
    _write_run(tmp_path, reason="projected_exposure_exceeds_max_position_size")
    _write_per_run_report(tmp_path, RUN_ID, report_run_id="run_other")
    code = operator.discover(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 1
    assert "stale or mismatched" in out
    assert "capture_ready=False" in out
    assert "ELIGIBLE_RUN_ID=\n" in out


def test_discovery_requires_systemd_timer_trigger_source(tmp_path: Path, capsys) -> None:
    _write_run(
        tmp_path,
        reason="projected_exposure_exceeds_max_position_size",
        trigger_source="manual_or_systemd",
    )
    code = operator.discover(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 1
    assert "trigger_source is not systemd_timer" in out
    assert "capture_ready=False" in out
    assert "ELIGIBLE_RUN_ID=\n" in out


def test_capture_does_not_call_orchestrator_when_report_not_aligned(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_run(tmp_path, report_run_id="run_other")
    called = False

    def fake_orchestrator_main(argv):
        nonlocal called
        called = True
        return 0

    monkeypatch.setattr(
        operator.package_execution_orchestrator, "main", fake_orchestrator_main
    )
    code = operator.capture(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 1
    assert called is False
    assert "capture_readiness_reproved" in out
    assert operator.CAPTURE_ATTEMPT_FAILED_CLOSED_NO_RETRY_WITHOUT_NEW_AUTHORIZATION in out


def test_capture_reproves_eligibility_with_exact_per_run_report(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    later_run_id = "run_2026-06-16T13:30:10Z_later"
    _write_run(
        tmp_path,
        reason="projected_exposure_exceeds_max_position_size",
    )
    _write_per_run_report(tmp_path, RUN_ID)
    _write_run(
        tmp_path,
        run_id=later_run_id,
        reason="market_closed",
    )
    captured: dict[str, list[str]] = {}

    def fake_orchestrator_main(argv):
        captured["argv"] = list(argv)
        return 0

    monkeypatch.setattr(
        operator.package_execution_orchestrator, "main", fake_orchestrator_main
    )
    code = operator.capture(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 0
    assert captured["argv"][1] == RUN_ID
    assert "capture_readiness_reproved" in out
    assert operator.ONE_GOVERNED_PACKAGE_CAPTURED_PENDING_D14_LEDGER_FOLLOW_UP in out


def test_capture_does_not_call_orchestrator_when_exact_per_run_report_is_stale(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_run(tmp_path, reason="projected_exposure_exceeds_max_position_size")
    _write_per_run_report(tmp_path, RUN_ID, report_run_id="run_other")
    called = False

    def fake_orchestrator_main(argv):
        nonlocal called
        called = True
        return 0

    monkeypatch.setattr(
        operator.package_execution_orchestrator, "main", fake_orchestrator_main
    )
    code = operator.capture(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 1
    assert called is False
    assert "stale or mismatched" in out
    assert operator.CAPTURE_ATTEMPT_FAILED_CLOSED_NO_RETRY_WITHOUT_NEW_AUTHORIZATION in out


def test_capture_does_not_call_orchestrator_when_trigger_source_not_timer(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_run(tmp_path, trigger_source="manual_or_systemd")
    called = False

    def fake_orchestrator_main(argv):
        nonlocal called
        called = True
        return 0

    monkeypatch.setattr(
        operator.package_execution_orchestrator, "main", fake_orchestrator_main
    )
    code = operator.capture(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 1
    assert called is False
    assert "trigger_source is not systemd_timer" in out
    assert operator.CAPTURE_ATTEMPT_FAILED_CLOSED_NO_RETRY_WITHOUT_NEW_AUTHORIZATION in out


def test_capture_does_not_call_orchestrator_when_d13_rejects(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_run(tmp_path, reason="market_closed")
    called = False

    def fake_orchestrator_main(argv):
        nonlocal called
        called = True
        return 0

    monkeypatch.setattr(
        operator.package_execution_orchestrator, "main", fake_orchestrator_main
    )
    code = operator.capture(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 1
    assert called is False
    assert "market/session-ineligible" in out
    assert operator.CAPTURE_ATTEMPT_FAILED_CLOSED_NO_RETRY_WITHOUT_NEW_AUTHORIZATION in out


def test_capture_requires_authorize_vps_package_write() -> None:
    with pytest.raises(SystemExit) as exc:
        operator.main(["capture", "--run-id", RUN_ID])
    assert exc.value.code == 2


def test_capture_uses_package_execution_orchestrator_command_surface(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_run(tmp_path)
    captured: dict[str, list[str]] = {}

    def fake_orchestrator_main(argv):
        captured["argv"] = list(argv)
        return 0

    monkeypatch.setattr(
        operator.package_execution_orchestrator, "main", fake_orchestrator_main
    )
    code = operator.capture(_args(repo_root=str(tmp_path)), FakeRunner())
    out = capsys.readouterr().out
    assert code == 0
    assert captured["argv"] == [
        "--run-id",
        RUN_ID,
        "--execution-mode",
        "vps",
        "--authorize-vps-package-write",
    ]
    assert "PACKAGE_DIR_MISSING" in out
    assert operator.ONE_GOVERNED_PACKAGE_CAPTURED_PENDING_D14_LEDGER_FOLLOW_UP in out


def test_capture_chdirs_to_selected_repo_root_before_delegating(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_run(tmp_path)
    caller_cwd = Path.cwd()
    delegated_cwd: dict[str, Path] = {}

    def fake_orchestrator_main(argv):
        delegated_cwd["cwd"] = Path.cwd()
        return 0

    monkeypatch.setattr(
        operator.package_execution_orchestrator, "main", fake_orchestrator_main
    )
    code = operator.capture(_args(repo_root=str(tmp_path)), FakeRunner())
    capsys.readouterr()
    assert code == 0
    assert delegated_cwd["cwd"] == tmp_path
    assert Path.cwd() == caller_cwd
