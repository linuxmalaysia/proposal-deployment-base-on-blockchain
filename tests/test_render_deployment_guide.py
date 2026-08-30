"""Tests for the Render free-tier deployment guide changes."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
DEPLOYMENT_GUIDE = REPO_ROOT / "docs" / "how-to" / "deploy-rcf-dac-web-app-on-render.md"


def _read_guide() -> str:
    return DEPLOYMENT_GUIDE.read_text(encoding="utf-8")


def _section(content: str, heading: str, next_heading_level: int) -> str:
    """Return a Markdown section up to the next heading at the requested level."""
    pattern = rf"(?ms)^{re.escape(heading)}\n(.*?)(?=^{'#' * next_heading_level} |\Z)"
    match = re.search(pattern, content)
    assert match is not None, f"Expected section {heading!r}"
    return match.group(1)


@pytest.fixture(scope="module")
def guide() -> str:
    assert DEPLOYMENT_GUIDE.is_file()
    return _read_guide()


@pytest.fixture(scope="module")
def manual_setup(guide: str) -> str:
    return _section(
        guide,
        "### Method 2: Manual Web Service Setup on Render (Free Tier Compatible)",
        3,
    )


@pytest.fixture(scope="module")
def missing_secret_troubleshooting(guide: str) -> str:
    return _section(
        guide,
        "### 5. Missing Required Environment Variables (`INVESTOR_JWT_SECRET`)",
        3,
    )


def test_manual_setup_documents_all_free_tier_service_settings(manual_setup: str):
    expected_settings = (
        "**Name:** `rcf-dac-web-app`",
        "**Runtime:** `Python 3`",
        "**Branch:** `main` (or active production branch)",
        "**Root Directory:** *(leave empty for repository root)*",
        "**Build Command:** `uv sync`",
        "**Start Command:** "
        "`uvicorn src.dca_service.web_app:app --host 0.0.0.0 --port $PORT`",
        "**Instance Type:** **Free** ($0/month)",
    )

    for setting in expected_settings:
        assert setting in manual_setup


@pytest.mark.parametrize(
    "limitation",
    (
        "testing, prototyping, and hobby projects",
        "after 15 minutes of inactivity",
        "approximately 50-60 seconds",
        "750 free instance hours per month",
        "shared across free web services",
        "may incur charges if a credit card or payment method is attached",
    ),
)
def test_free_tier_warning_sets_operational_expectations(
    manual_setup: str, limitation: str
):
    assert "> [!WARNING]" in manual_setup
    assert limitation in manual_setup


def test_manual_setup_requires_a_random_uncommitted_jwt_secret(manual_setup: str):
    assert "`INVESTOR_JWT_SECRET`" in manual_setup
    assert "cryptographically random 256-bit secret string" in manual_setup
    assert "`openssl rand -hex 32`" in manual_setup
    assert "**NEVER** commit secrets to version control" in manual_setup


def test_missing_secret_troubleshooting_identifies_startup_failure(
    missing_secret_troubleshooting: str,
):
    assert "Missing required environment variable 'INVESTOR_JWT_SECRET'" in (
        missing_secret_troubleshooting
    )
    assert "Exited with status 1" in missing_secret_troubleshooting


def test_missing_secret_troubleshooting_steps_are_complete_and_ordered(
    missing_secret_troubleshooting: str,
):
    expected_steps = (
        "Open your web service",
        "Select **Environment**",
        "click **Add Environment Variable**",
        "Set **Key** to `INVESTOR_JWT_SECRET`",
        "Set **Value** to a cryptographically random 256-bit string",
        "Click **Save Changes**",
    )

    positions = [
        missing_secret_troubleshooting.index(step) for step in expected_steps
    ]
    assert positions == sorted(positions)
    assert "automatically trigger a new deployment" in missing_secret_troubleshooting


def test_manual_secret_generation_is_not_confused_with_blueprint_generation(
    guide: str, missing_secret_troubleshooting: str
):
    blueprint_setup = _section(
        guide, "### Method 1: Render Blueprint Deployment (Recommended)", 3
    )

    assert "automatically detect `render.yaml`" in blueprint_setup
    assert "manual Web Service" in missing_secret_troubleshooting
    assert "does not auto-generate environment variables" in (
        missing_secret_troubleshooting
    )
    assert "Render Blueprints via `generateValue: true`" in (
        missing_secret_troubleshooting
    )


def test_manual_start_command_uses_render_assigned_port(manual_setup: str):
    """Regression guard: a hard-coded port prevents Render from routing traffic."""
    start_command = re.search(r"\*\*Start Command:\*\* `([^`]+)`", manual_setup)
    assert start_command is not None
    assert start_command.group(1).endswith("--port $PORT")
