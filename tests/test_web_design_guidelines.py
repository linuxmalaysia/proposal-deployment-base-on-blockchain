"""Unit tests for the web-design-guidelines PR accessibility changes."""

from __future__ import annotations

import importlib.util
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

os.environ.setdefault("INVESTOR_JWT_SECRET", "test_web_design_guidelines_secret_2026")

from dca_service.web_app import (
    serve_db_status_page,
    serve_login_page,
    serve_user_management_page,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_MD = REPO_ROOT / "index.md"
CSS_STYLE = REPO_ROOT / "assets" / "css" / "style.css"
SKILL_FILE = REPO_ROOT / ".agents" / "skills" / "web-design-guidelines" / "SKILL.md"
SKILL_GENERATOR = REPO_ROOT / "tools" / "create_antigravity_skills.py"


class _ElementCollector(HTMLParser):
    """Collect start tags so tests can make attribute-level assertions."""

    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.elements.append((tag, dict(attrs)))

    def by_id(self, element_id: str) -> tuple[str, dict[str, str | None]]:
        matches = [element for element in self.elements if element[1].get("id") == element_id]
        assert len(matches) == 1, f"Expected one element with id={element_id!r}, found {len(matches)}"
        return matches[0]


def _parse(markup: str) -> _ElementCollector:
    parser = _ElementCollector()
    parser.feed(markup)
    return parser


def _response_text(response: Any) -> str:
    return response.body.decode("utf-8")


def _assert_element(
    parser: _ElementCollector,
    element_id: str,
    tag: str,
    expected_attrs: dict[str, str],
) -> None:
    actual_tag, attrs = parser.by_id(element_id)
    assert actual_tag == tag
    for name, expected in expected_attrs.items():
        assert attrs.get(name) == expected, (
            f"Expected {element_id!r} to have {name}={expected!r}, got {attrs.get(name)!r}"
        )


LOGIN_CONTROLS = [
    ("username", "input", {"name": "username", "autocomplete": "username", "spellcheck": "false", "aria-label": "System Username"}),
    ("password", "input", {"name": "password", "autocomplete": "current-password", "aria-label": "System Password"}),
]


@pytest.mark.parametrize(("element_id", "tag", "expected_attrs"), LOGIN_CONTROLS)
def test_login_controls_expose_accessible_authentication_metadata(
    element_id: str, tag: str, expected_attrs: dict[str, str]
) -> None:
    parser = _parse(_response_text(serve_login_page()))
    _assert_element(parser, element_id, tag, expected_attrs)


def test_login_page_announces_initial_success_and_failure_states() -> None:
    markup = _response_text(serve_login_page())
    parser = _parse(markup)

    _assert_element(parser, "alertBox", "div", {"role": "alert", "aria-live": "polite"})
    assert "alertBox.setAttribute('role', 'status');" in markup
    assert "alertBox.setAttribute('aria-live', 'polite');" in markup
    assert markup.count("alertBox.setAttribute('role', 'alert');") == 2
    assert markup.count("alertBox.setAttribute('aria-live', 'assertive');") == 2
    assert "Redirecting…" in markup
    assert "Redirecting..." not in markup


USER_MANAGEMENT_CONTROLS = [
    ("reg-fullname", "input", {"name": "fullname", "autocomplete": "name", "aria-label": "Full Name & Title"}),
    ("reg-role", "select", {"name": "role", "aria-label": "Institutional Role"}),
    ("reg-dept", "input", {"name": "dept", "autocomplete": "organization", "aria-label": "Faculty / CoE"}),
    ("reg-email", "input", {"name": "email", "autocomplete": "email", "spellcheck": "false", "aria-label": "Institutional Email"}),
    ("newUsername", "input", {"name": "username", "autocomplete": "username", "spellcheck": "false", "aria-label": "Username"}),
    ("newPassword", "input", {"name": "password", "autocomplete": "new-password", "aria-label": "Password"}),
    ("newName", "input", {"name": "name", "autocomplete": "name", "aria-label": "Full Name"}),
    ("newRole", "select", {"name": "role", "aria-label": "Role"}),
    ("newDept", "input", {"name": "dept", "autocomplete": "organization", "aria-label": "Department"}),
    ("newEmail", "input", {"name": "email", "autocomplete": "email", "spellcheck": "false", "aria-label": "Email"}),
]


@pytest.mark.parametrize(("element_id", "tag", "expected_attrs"), USER_MANAGEMENT_CONTROLS)
def test_user_management_controls_expose_names_and_accessibility_metadata(
    element_id: str, tag: str, expected_attrs: dict[str, str]
) -> None:
    parser = _parse(_response_text(serve_user_management_page()))
    _assert_element(parser, element_id, tag, expected_attrs)


@pytest.mark.parametrize(
    ("element_id", "role"),
    [
        ("unauthAlert", "alert"),
        ("user-reg-output", "status"),
        ("createUserAlert", "alert"),
    ],
)
def test_user_management_dynamic_regions_are_announced(
    element_id: str, role: str
) -> None:
    parser = _parse(_response_text(serve_user_management_page()))
    _assert_element(parser, element_id, "div", {"role": role, "aria-live": "polite"})


def test_user_creation_feedback_switches_urgency_for_success_and_failures() -> None:
    markup = _response_text(serve_user_management_page())

    assert "alertBox.setAttribute('role', 'status');" in markup
    assert "alertBox.setAttribute('aria-live', 'polite');" in markup
    assert markup.count("alertBox.setAttribute('role', 'alert');") == 2
    assert markup.count("alertBox.setAttribute('aria-live', 'assertive');") == 2


INDEX_CONTROLS = [
    ("asset-title", "input", {"name": "asset_title", "autocomplete": "off", "aria-label": "Research Project / Prototype Title"}),
    ("asset-trl", "select", {"name": "asset_trl", "aria-label": "Initial Technology Readiness Level"}),
    ("asset-file", "input", {"name": "asset_file", "aria-label": "Evidentiary File Upload"}),
    ("asset-abstract", "textarea", {"name": "asset_abstract", "aria-label": "Abstract & Scientific Innovation Summary"}),
    ("score-tech", "input", {"name": "score_tech", "aria-label": "Technology Strengths Score"}),
    ("score-market", "input", {"name": "score_market", "aria-label": "Market Attractiveness Score"}),
    ("score-comm", "input", {"name": "score_comm", "aria-label": "Commercialisation Avenues Score"}),
    ("score-mgmt", "input", {"name": "score_mgmt", "aria-label": "Management & Execution Support Score"}),
    ("rev-amount", "input", {"name": "rev_amount", "autocomplete": "off", "inputmode": "decimal", "aria-label": "Total Ingested Revenue (MYR)"}),
    ("rev-type", "select", {"name": "rev_type", "aria-label": "Revenue Stream Type"}),
]


@pytest.mark.parametrize(("element_id", "tag", "expected_attrs"), INDEX_CONTROLS)
def test_portal_controls_expose_names_and_accessibility_metadata(
    element_id: str, tag: str, expected_attrs: dict[str, str]
) -> None:
    parser = _parse(INDEX_MD.read_text(encoding="utf-8"))
    _assert_element(parser, element_id, tag, expected_attrs)


@pytest.mark.parametrize(
    "element_id",
    ["portalSessionBanner", "guestNoticeCard", "asset-reg-output", "cloverleaf-status"],
)
def test_portal_dynamic_regions_are_polite_status_announcements(element_id: str) -> None:
    parser = _parse(INDEX_MD.read_text(encoding="utf-8"))
    _assert_element(parser, element_id, "div", {"role": "status", "aria-live": "polite"})


def test_portal_action_controls_have_non_empty_accessible_names() -> None:
    parser = _parse(INDEX_MD.read_text(encoding="utf-8"))
    actions = [
        (tag, attrs)
        for tag, attrs in parser.elements
        if tag == "button"
        or (
            tag == "a"
            and {"btn", "role-select-btn"}.intersection((attrs.get("class") or "").split())
        )
    ]

    expected_labels = {
        "Show My Role Modules",
        "Show All Modules Read Filter",
        "System Login",
        "User Management Dashboard",
        "Database Connection Status",
        "Click Here to Login",
        "Register Asset & Generate SHA-256 Evidence Hash",
        "Access Data Room",
        "Request Term Sheet",
    }
    assert {attrs.get("aria-label") for _, attrs in actions} == expected_labels
    for tag, attrs in actions:
        assert attrs.get("aria-label"), f"{tag} action lacks an accessible name: {attrs}"


def test_portal_uses_unicode_ellipsis_for_async_action_copy() -> None:
    content = INDEX_MD.read_text(encoding="utf-8")
    assert "payload…" in content
    assert "payload..." not in content


def _database_status_markup(*, connected: bool, latency_ms: int) -> str:
    status = "CONNECTED" if connected else "DISCONNECTED"
    db_info = {
        "is_connected": connected,
        "status": status,
        "status_detail": "unit-test diagnostic",
        "latency_ms": latency_ms,
        "timestamp": "2026-09-01T00:00:00Z",
        "schema_file": "docs/schema.sql",
        "schema_tables": [],
        "cached": False,
    }
    with patch("dca_service.web_app.check_database_connection", return_value=db_info):
        return _response_text(serve_db_status_page())


@pytest.mark.parametrize(("connected", "latency_ms"), [(True, 0), (False, 12345)])
def test_database_status_numbers_and_actions_include_accessibility_styling(
    connected: bool, latency_ms: int
) -> None:
    markup = _database_status_markup(connected=connected, latency_ms=latency_ms)
    parser = _parse(markup)
    tabular_elements = [attrs for _, attrs in parser.elements if attrs.get("class") == "tabular-nums"]
    action_labels = {
        attrs.get("aria-label")
        for tag, attrs in parser.elements
        if tag == "a" and "btn" in (attrs.get("class") or "").split()
    }

    assert len(tabular_elements) == 2
    assert f">{latency_ms} ms<" in markup
    assert action_labels == {"Re-test Database Connection", "View JSON API Endpoint"}


def test_accessibility_css_defines_focus_numeric_touch_and_heading_rules() -> None:
    css = CSS_STYLE.read_text(encoding="utf-8")
    accessibility_css = css.split("Web Interface Guidelines & Accessibility", maxsplit=1)[1]

    for selector in ("button", "a", "input", "select", "textarea"):
        assert f"{selector}:focus-visible" in accessibility_css
    assert "outline: 2px solid #0066cc !important;" in accessibility_css
    assert "outline-offset: 2px !important;" in accessibility_css
    assert "font-variant-numeric: tabular-nums;" in accessibility_css
    assert "font-feature-settings: \"tnum\";" in accessibility_css
    assert "scroll-margin-top: 2rem;" in accessibility_css
    assert "text-wrap: balance;" in accessibility_css
    assert "touch-action: manipulation;" in accessibility_css


def test_reduced_motion_css_preserves_boundary_values() -> None:
    css = CSS_STYLE.read_text(encoding="utf-8")
    reduced_motion = css.split("@media (prefers-reduced-motion: reduce)", maxsplit=1)[1]

    assert "animation-duration: 0.01ms !important;" in reduced_motion
    assert "animation-iteration-count: 1 !important;" in reduced_motion
    assert "transition-duration: 0.01ms !important;" in reduced_motion
    assert "scroll-behavior: auto !important;" in reduced_motion


def test_generated_web_design_skill_matches_its_catalogue_entry() -> None:
    spec = importlib.util.spec_from_file_location("create_antigravity_skills", SKILL_GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    entries = [entry for entry in module.SKILLS if entry["dir"] == "web-design-guidelines"]
    assert len(entries) == 1
    entry = entries[0]
    skill_content = SKILL_FILE.read_text(encoding="utf-8")
    body_match = re.search(
        r"^---\n.*?\n---\n\n(?P<body>.*?)\n\n---\n\n### Deep State of Mind",
        skill_content,
        flags=re.DOTALL,
    )

    assert body_match is not None
    assert body_match.group("body").strip() == entry["content"].strip()
    assert entry["topics"] == [
        "web-design-guidelines",
        "ui-ux",
        "accessibility",
        "a11y",
        "antigravity",
        "playwright",
    ]


@pytest.mark.parametrize(
    "required_rule",
    [
        "Icon-only buttons need `aria-label`.",
        "Async updates (toasts, alert boxes, validation messages) need `aria-live=\"polite\"`.",
        "Inputs need `autocomplete` and meaningful `name` attribute.",
        "Honor `prefers-reduced-motion`",
        "`font-variant-numeric: tabular-nums`",
        "`touch-action: manipulation`",
    ],
)
def test_web_design_skill_preserves_each_implemented_rule(required_rule: str) -> None:
    assert required_rule in SKILL_FILE.read_text(encoding="utf-8")
