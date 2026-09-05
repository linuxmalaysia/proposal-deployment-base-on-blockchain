"""Tests for tools/install_git_guardrails.py.

Scope: this PR added an "Auto-generate SUMMARY.md index" step to
``run_pre_commit_checks()`` (a subprocess call to ``tools/generate_summary.py``
that short-circuits the guardrail run on failure). These tests cover that new
behavior in isolation, without invoking real ``uv``/``pytest`` subprocesses and
without mutating the real repository's files.
"""

import importlib.util
import subprocess
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parent.parent / "tools" / "install_git_guardrails.py"


def _load_module():
    """Load tools/install_git_guardrails.py as a fresh, isolated module instance."""
    spec = importlib.util.spec_from_file_location("install_git_guardrails", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def igg_module():
    return _load_module()


class _FakeCompletedProcess:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


class _RecordingSubprocessRun:
    """Stand-in for subprocess.run that records calls and returns canned results."""

    def __init__(self, returncodes):
        # returncodes: iterable of return codes, one per call (last value repeats if exhausted)
        self._returncodes = list(returncodes)
        self.calls = []

    def __call__(self, args, cwd=None, **kwargs):
        self.calls.append({"args": args, "cwd": cwd})
        if self._returncodes:
            code = self._returncodes.pop(0)
        else:
            code = 0
        return _FakeCompletedProcess(code)


def _isolate_repo_root(monkeypatch, igg_module, tmp_path):
    """Point the module's hardcoded `Path(__file__).parent.parent` at tmp_path."""
    monkeypatch.setattr(igg_module, "__file__", str(tmp_path / "tools" / "install_git_guardrails.py"))


class TestSummaryAutoGenerationStep:
    def test_invokes_generate_summary_script_when_present_and_succeeds(
        self, igg_module, tmp_path, monkeypatch, capsys
    ):
        _isolate_repo_root(monkeypatch, igg_module, tmp_path)
        summary_script = tmp_path / "tools" / "generate_summary.py"
        summary_script.parent.mkdir(parents=True, exist_ok=True)
        summary_script.write_text("# dummy script\n", encoding="utf-8")

        fake_run = _RecordingSubprocessRun(returncodes=[0, 0, 0, 0])
        monkeypatch.setattr(subprocess, "run", fake_run)

        result = igg_module.run_pre_commit_checks()

        assert result == 0
        assert len(fake_run.calls) == 4
        assert fake_run.calls[0]["args"] == ["uv", "run", "python", str(summary_script)]
        assert fake_run.calls[0]["cwd"] == tmp_path
        assert fake_run.calls[1]["args"] == ["uv", "run", "ruff", "check", "src/"]
        assert fake_run.calls[2]["args"] == ["uv", "run", "mypy", "--strict", "src/"]
        assert fake_run.calls[3]["args"] == ["uv", "run", "pytest"]
        assert fake_run.calls[3]["cwd"] == tmp_path

        captured = capsys.readouterr()
        assert "Auto-generating SUMMARY.md index" in captured.out

    def test_returns_early_and_skips_further_checks_when_generation_fails(
        self, igg_module, tmp_path, monkeypatch
    ):
        _isolate_repo_root(monkeypatch, igg_module, tmp_path)
        summary_script = tmp_path / "tools" / "generate_summary.py"
        summary_script.parent.mkdir(parents=True, exist_ok=True)
        summary_script.write_text("# dummy script\n", encoding="utf-8")

        # An .md file with invalid/missing OKF frontmatter would normally fail the
        # subsequent guardrail check; it must never be reached because the
        # summary-generation failure short-circuits the function first.
        (tmp_path / "bad.md").write_text("No frontmatter here.\n", encoding="utf-8")

        fake_run = _RecordingSubprocessRun(returncodes=[7])
        monkeypatch.setattr(subprocess, "run", fake_run)

        result = igg_module.run_pre_commit_checks()

        assert result == 7
        # Only the summary-generation call should have happened; the pytest run
        # (and any md frontmatter validation) must not have been reached.
        assert len(fake_run.calls) == 1
        assert fake_run.calls[0]["args"][:3] == ["uv", "run", "python"]

    def test_skips_generation_step_when_script_missing(self, igg_module, tmp_path, monkeypatch, capsys):
        _isolate_repo_root(monkeypatch, igg_module, tmp_path)
        # Note: tools/generate_summary.py is deliberately not created.
        (tmp_path / "tools").mkdir(parents=True, exist_ok=True)

        fake_run = _RecordingSubprocessRun(returncodes=[0, 0, 0])
        monkeypatch.setattr(subprocess, "run", fake_run)

        result = igg_module.run_pre_commit_checks()

        assert result == 0
        assert len(fake_run.calls) == 3
        assert fake_run.calls[0]["args"] == ["uv", "run", "ruff", "check", "src/"]
        assert fake_run.calls[1]["args"] == ["uv", "run", "mypy", "--strict", "src/"]
        assert fake_run.calls[2]["args"] == ["uv", "run", "pytest"]

        captured = capsys.readouterr()
        assert "Auto-generating SUMMARY.md index" not in captured.out

    def test_generation_failure_return_code_is_propagated_unmodified(
        self, igg_module, tmp_path, monkeypatch
    ):
        _isolate_repo_root(monkeypatch, igg_module, tmp_path)
        summary_script = tmp_path / "tools" / "generate_summary.py"
        summary_script.parent.mkdir(parents=True, exist_ok=True)
        summary_script.write_text("# dummy script\n", encoding="utf-8")

        fake_run = _RecordingSubprocessRun(returncodes=[123])
        monkeypatch.setattr(subprocess, "run", fake_run)

        result = igg_module.run_pre_commit_checks()

        assert result == 123