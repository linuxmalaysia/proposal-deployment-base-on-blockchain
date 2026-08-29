"""Regression tests for removal of the obsolete standalone OKF guide."""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SUMMARY = REPO_ROOT / "SUMMARY.md"
REMOVED_GUIDE = REPO_ROOT / "docs" / "explanation" / "open-knowledge-format-v02-guide.md"
REMOVED_RELATIVE_PATH = "docs/explanation/open-knowledge-format-v02-guide.md"
REMOVED_TITLE = "Open Knowledge Format (OKF v0.2) Architectural Specification & Adoption Guide"


def _read(path):
    return path.read_text(encoding="utf-8")


def _summary_section(content, heading):
    match = re.search(
        rf"^{re.escape(heading)}\n(?P<body>.*?)(?=^###? |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing SUMMARY section: {heading}"
    return match.group("body")


def test_obsolete_okf_guide_is_deleted():
    assert not REMOVED_GUIDE.exists()


def test_summary_has_no_stale_guide_path_or_title():
    content = _read(SUMMARY)
    assert REMOVED_RELATIVE_PATH not in content
    assert REMOVED_TITLE not in content


def test_no_remaining_markdown_document_links_to_removed_guide():
    for path in REPO_ROOT.rglob("*.md"):
        if ".git" not in path.parts:
            assert REMOVED_GUIDE.name not in _read(path), path.relative_to(REPO_ROOT)


def test_summary_explanation_links_exactly_match_existing_documents():
    section = _summary_section(_read(SUMMARY), "### Explanation")
    listed_paths = re.findall(r"^\* \[[^]]+\]\((docs/explanation/[^)]+\.md)\)$", section, re.MULTILINE)
    actual_paths = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "docs" / "explanation").glob("*.md")
    )
    assert listed_paths == actual_paths


def test_summary_uses_revised_changelog_title():
    content = _read(SUMMARY)
    assert "* [DCA Service Changelog](CHANGELOG.md)" in content
    assert "DCA Service Platform Changelog & Release History" not in content
