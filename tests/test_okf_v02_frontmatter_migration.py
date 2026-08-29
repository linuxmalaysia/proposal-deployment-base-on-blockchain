"""Regression tests for the PR's compact OKF v0.2 frontmatter migration.

The changed Markdown files deliberately use the repository's six required OKF
fields.  These content tests keep that schema, its quoting, and the individual
document metadata stable without requiring a YAML dependency.
"""

import importlib.util
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
GUARDRAILS_PATH = REPO_ROOT / "tools" / "install_git_guardrails.py"

REQUIRED_KEYS = (
    "okf_version",
    "type",
    "title",
    "created",
    "status",
    "language",
)
REMOVED_EXPANDED_KEYS = {
    "timestamp",
    "topics",
    "description",
    "resource",
    "sources",
    "generated",
    "verified",
    "stale_after",
}


def _document(path, document_type, title, status="verified", **extra):
    metadata = {
        "okf_version": "0.2",
        "type": document_type,
        "title": title,
        "created": "2026-08-25",
        "status": status,
        "language": "en-GB",
    }
    metadata.update(extra)
    return pytest.param(path, metadata, id=path.replace("/", "-"))


CHANGED_DOCUMENTS = (
    _document(
        ".agents/AGENTS.md",
        "constitution",
        "DSOM Sovereign AI Master Constitution",
    ),
    _document(
        ".agents/brain/palace_registry.md",
        "spatial_memory",
        "Palace Registry & Asset Mapping",
        status="active",
    ),
    _document(
        ".agents/brain/task.md",
        "spatial_memory",
        "Present Active Task State",
        status="active",
    ),
    _document(
        ".agents/brain/walkthrough.md",
        "spatial_memory",
        "Execution Walkthrough Ledger",
        status="active",
    ),
    _document(
        ".github/copilot-instructions.md",
        "gateway",
        "GitHub Copilot Custom Instructions",
    ),
    _document(
        "AGENTS.md",
        "gateway",
        "Root AI Gateway: Deep State of Mind (DSOM) Protocol",
    ),
    _document("CHANGELOG.md", "changelog", "DCA Service Changelog"),
    _document("CLAUDE.md", "gateway", "Claude AI Integration Rules"),
    _document("HISTORY.md", "history", "DCA Service Project History Ledger"),
    _document(
        "README.md",
        "overview",
        "Digital Custody Asset (DCA) as a Service Platform",
    ),
    _document(
        "index.md",
        "overview",
        "Digital Custody Asset (DCA) as a Service Platform",
        layout="default",
    ),
    _document(
        "docs/explanation/architecture-overview.md",
        "explanation",
        "Institutional Digital Asset Custody Architecture",
    ),
    _document(
        "docs/explanation/challenges-and-opportunities.md",
        "explanation",
        "Challenges, Caveats, and Market Opportunities in DCA",
    ),
    _document(
        "docs/explanation/open-source-mpc-wallet-architecture.md",
        "explanation",
        "Open-Source MPC Wallet System Architecture via cb-mpc",
    ),
    _document(
        "docs/explanation/percona-timescaledb-blockchain-sync.md",
        "explanation",
        "Percona Server for PostgreSQL & TimescaleDB Dual-Write Blockchain Architecture",
    ),
    _document(
        "docs/github-pages-setup.md",
        "howto",
        "GitHub Pages Automated Deployment & 404 Troubleshooting Guide",
    ),
    _document(
        "docs/how-to/install-and-configure-guardrails.md",
        "howto",
        "How-To: Install and Configure Repository Guardrails and Documentation Tools",
    ),
    _document(
        "docs/multi-platform-hosting.md",
        "howto",
        "Multi-Platform Documentation Deployment Guide",
    ),
    _document(
        "docs/reference/dca-dac-api-and-cli-reference.md",
        "reference",
        "DCA & DAC Core API, CLI, and Data Objects Reference",
    ),
    _document(
        "docs/reference/implementation-patterns.md",
        "reference",
        "Industry Implementation Patterns for Custody Platforms",
    ),
    _document(
        "docs/tutorials/getting-started-dca-dac.md",
        "tutorial",
        "Getting Started with the DCA & DAC Platform on Percona PostgreSQL",
    ),
)


def _read(relative_path):
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _split_frontmatter(content):
    match = re.fullmatch(r"---\n(?P<frontmatter>.*?)\n---\n(?P<body>.*)", content, re.DOTALL)
    assert match, "document must have a complete frontmatter block at byte zero"
    return match.group("frontmatter"), match.group("body")


def _parse_quoted_scalars(frontmatter):
    entries = []
    for line in frontmatter.splitlines():
        match = re.fullmatch(r'([a-z_]+): "([^"]*)"', line)
        assert match, f"frontmatter scalar must be double quoted: {line!r}"
        entries.append(match.groups())

    keys = [key for key, _value in entries]
    assert len(keys) == len(set(keys)), "frontmatter keys must not be duplicated"
    return entries


def _load_guardrails_module():
    spec = importlib.util.spec_from_file_location("install_git_guardrails", GUARDRAILS_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("relative_path,expected", CHANGED_DOCUMENTS)
def test_changed_document_exists_and_retains_content(relative_path, expected):
    path = REPO_ROOT / relative_path
    assert path.is_file()
    _frontmatter, body = _split_frontmatter(_read(relative_path))
    assert body.lstrip().startswith("# "), "frontmatter migration must retain the document body"


@pytest.mark.parametrize("relative_path,expected", CHANGED_DOCUMENTS)
def test_frontmatter_matches_exact_document_contract(relative_path, expected):
    frontmatter, _body = _split_frontmatter(_read(relative_path))
    entries = _parse_quoted_scalars(frontmatter)
    assert dict(entries) == expected


@pytest.mark.parametrize("relative_path,expected", CHANGED_DOCUMENTS)
def test_required_keys_are_in_canonical_order(relative_path, expected):
    frontmatter, _body = _split_frontmatter(_read(relative_path))
    keys = tuple(key for key, _value in _parse_quoted_scalars(frontmatter))
    expected_keys = REQUIRED_KEYS + (("layout",) if relative_path == "index.md" else ())
    assert keys == expected_keys


@pytest.mark.parametrize("relative_path,expected", CHANGED_DOCUMENTS)
def test_expanded_metadata_keys_are_removed(relative_path, expected):
    frontmatter, _body = _split_frontmatter(_read(relative_path))
    keys = {key for key, _value in _parse_quoted_scalars(frontmatter)}
    assert keys.isdisjoint(REMOVED_EXPANDED_KEYS)


@pytest.mark.parametrize("relative_path,expected", CHANGED_DOCUMENTS)
def test_repository_guardrail_accepts_compact_frontmatter(relative_path, expected):
    guardrails = _load_guardrails_module()
    assert guardrails.check_okf_frontmatter(REPO_ROOT / relative_path)


def test_compact_schema_covers_each_supported_document_type():
    types = {expected["type"] for _path, expected in [entry.values for entry in CHANGED_DOCUMENTS]}
    assert types == {
        "changelog",
        "constitution",
        "explanation",
        "gateway",
        "history",
        "howto",
        "overview",
        "reference",
        "spatial_memory",
        "tutorial",
    }


def test_only_spatial_memory_documents_use_active_status():
    for relative_path, expected in [entry.values for entry in CHANGED_DOCUMENTS]:
        expected_status = "active" if relative_path.startswith(".agents/brain/") else "verified"
        assert expected["status"] == expected_status
