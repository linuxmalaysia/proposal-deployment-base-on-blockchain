"""Tests for the repository-wide Open Knowledge Format (OKF) v0.2 frontmatter
migration PR.

Scope: this PR rewrites the YAML frontmatter block of every governance,
gateway, spatial-memory, and Diátaxis documentation Markdown file in the
repository (root ledgers, ``.agents/``, ``.github/copilot-instructions.md``,
and ``docs/**``) from the original 6-field OKF v0.1-style schema
(``okf_version``, ``type``, ``title``, ``created``, ``status``, ``language``)
to the expanded OKF v0.2 13-field schema (``okf_version``, ``type``,
``title``, ``timestamp``, ``topics``, ``description``, ``resource``,
``sources``, ``generated``, ``verified``, ``status``, ``stale_after``,
``language``). It also:

- Adds a brand new Diátaxis "explanation" document,
  ``docs/explanation/open-knowledge-format-v02-guide.md``, documenting the
  OKF v0.2 specification itself (covered by
  ``tests/test_open_knowledge_format_guide_doc.py``).
- Regenerates ``SUMMARY.md``'s body content to list the new document and to
  reflect ``CHANGELOG.md``'s updated title, while leaving ``SUMMARY.md``'s
  own (tool-generated) frontmatter block untouched.
- Retitles several gateway/agent-instructions documents (e.g. ``AGENTS.md``,
  ``.agents/AGENTS.md``, ``.github/copilot-instructions.md``) and changes
  their ``type`` value from ``constitution``/``gateway`` to
  ``agent_instructions``.

No Python source code was changed by this PR (documentation only), so these
tests validate the *content* of the changed Markdown files rather than
executing any application code, consistent with the text-based content
validation style used elsewhere in this project's test suite (see
``test_generate_summary.py``, ``test_jekyll_site_config.py``, and
``test_open_source_mpc_wallet_docs.py``). Where useful, the unchanged
``tools/generate_summary.py`` and ``tools/install_git_guardrails.py`` helper
functions are used as oracles to confirm the new frontmatter style remains
compatible with existing repository tooling.
"""

import importlib.util
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

GENERATE_SUMMARY_PATH = REPO_ROOT / "tools" / "generate_summary.py"
GUARDRAILS_PATH = REPO_ROOT / "tools" / "install_git_guardrails.py"
SUMMARY = REPO_ROOT / "SUMMARY.md"
OKF_GUIDE_DOC = REPO_ROOT / "docs" / "explanation" / "open-knowledge-format-v02-guide.md"

MANDATORY_OKF_V02_FIELDS = [
    "okf_version",
    "type",
    "title",
    "timestamp",
    "topics",
    "description",
    "resource",
    "sources",
    "generated",
    "verified",
    "status",
    "stale_after",
    "language",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter_block(content: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    assert match, "Expected file to start with a '---' delimited YAML frontmatter block"
    return match.group(1)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _assert_scalar(frontmatter: str, key: str, value: str) -> None:
    candidates = [f'{key}: "{value}"', f"{key}: '{value}'", f"{key}: {value}"]
    assert any(candidate in frontmatter for candidate in candidates), (
        f"Expected one of {candidates!r} in frontmatter, got:\n{frontmatter}"
    )


def _list_block(frontmatter: str, key: str) -> str:
    lines = frontmatter.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip().startswith(f"{key}:"):
            start = idx
            break
    assert start is not None, f"'{key}:' not found in frontmatter"
    block_lines = [lines[start]]
    for line in lines[start + 1:]:
        if re.match(r"^[A-Za-z_]+:", line):
            break
        block_lines.append(line)
    return "\n".join(block_lines)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# Common values shared by every migrated document in this PR.
_COMMON = {
    "timestamp": "2026-08-25T00:00:00Z",
    "generated": "jules",
    "status": "approved",
    "stale_after": "2027-08-25T00:00:00Z",
    "language": "en-GB",
}


def _spec(path: Path, **overrides) -> dict:
    entry = dict(_COMMON)
    entry["path"] = path
    entry.update(overrides)
    return entry


DOC_SPECS = [
    _spec(
        REPO_ROOT / ".agents" / "AGENTS.md",
        type="agent_instructions",
        title="DSOM Digital Twin Agent System Directives & Spatial Protocols",
        topics=["dsom", "agents", "spatial-memory", "okf", "protocol"],
        description_contains="Operational system directives and spatial protocols for AI agents working",
        resource="file:///.agents/AGENTS.md",
        sources=["AGENTS.md"],
    ),
    _spec(
        REPO_ROOT / ".agents" / "brain" / "palace_registry.md",
        type="spatial_memory",
        title="Spatial Memory Palace Registry & Knowledge Map",
        topics=["dsom", "memory-palace", "spatial-memory", "registry"],
        description_contains="Directory registry and structural map of the Spatial Memory Palace",
        resource="file:///.agents/brain/palace_registry.md",
        sources=[".agents/AGENTS.md", "README.md"],
    ),
    _spec(
        REPO_ROOT / ".agents" / "brain" / "task.md",
        type="spatial_memory",
        title="Active Task Tracking & Objective Backlog",
        topics=["dsom", "task-tracking", "memory-palace", "okf"],
        description_contains="Chronological task ledger tracking current objectives",
        resource="file:///.agents/brain/task.md",
        sources=[".agents/AGENTS.md", "README.md"],
    ),
    _spec(
        REPO_ROOT / ".agents" / "brain" / "walkthrough.md",
        type="spatial_memory",
        title="Session Log & Execution Walkthrough History",
        topics=["dsom", "walkthrough", "session-log", "memory-palace"],
        description_contains="Historical record of execution walkthroughs",
        resource="file:///.agents/brain/walkthrough.md",
        sources=[".agents/AGENTS.md", ".agents/brain/task.md"],
    ),
    _spec(
        REPO_ROOT / ".github" / "copilot-instructions.md",
        type="agent_instructions",
        title="GitHub Copilot Workspace Directives & Clean Architecture Guardrails",
        topics=["copilot", "directives", "clean-architecture", "okf", "dsom"],
        description_contains="Custom system prompt and engineering instructions for GitHub Copilot",
        resource="file:///.github/copilot-instructions.md",
        sources=["AGENTS.md"],
    ),
    _spec(
        REPO_ROOT / "AGENTS.md",
        type="agent_instructions",
        title="DCA Platform Core Engineering & Agent Directives",
        topics=["agents", "engineering", "clean-architecture", "okf", "dsom"],
        description_contains="Root-level directives specifying Clean Architecture rules",
        resource="file:///AGENTS.md",
        sources=["README.md"],
    ),
    _spec(
        REPO_ROOT / "CHANGELOG.md",
        type="changelog",
        title="DCA Service Platform Changelog & Release History",
        topics=["changelog", "releases", "dca-service", "versioning"],
        description_contains="Chronological ledger of user-facing changes",
        resource="file:///CHANGELOG.md",
        sources=["HISTORY.md", "README.md"],
    ),
    _spec(
        REPO_ROOT / "CLAUDE.md",
        type="gateway",
        title="Claude AI Integration Rules & Workspace Directives",
        topics=["claude", "directives", "clean-architecture", "okf", "dsom"],
        description_contains="Workspace configuration and guidelines for Anthropic Claude AI",
        resource="file:///CLAUDE.md",
        sources=["AGENTS.md"],
    ),
    _spec(
        REPO_ROOT / "HISTORY.md",
        type="history",
        title="DCA Service Project History Ledger",
        topics=["history", "ledger", "dca-service", "milestones"],
        description_contains="Historical repository milestone ledger",
        resource="file:///HISTORY.md",
        sources=["CHANGELOG.md", "README.md"],
    ),
    _spec(
        REPO_ROOT / "README.md",
        type="overview",
        title="Digital Custody Asset (DCA) as a Service Platform",
        topics=["dca", "custody", "mpc", "postgresql", "timescaledb", "clean-architecture"],
        description_contains="Institutional-grade white-label & API-based Digital Asset Custody Platform",
        resource="file:///README.md",
        sources=["SUMMARY.md", "AGENTS.md"],
    ),
    _spec(
        REPO_ROOT / "index.md",
        type="overview",
        title="Digital Custody Asset (DCA) as a Service Platform",
        topics=["dca", "custody", "mpc", "postgresql", "timescaledb", "overview"],
        description_contains="Web documentation homepage for the Digital Custody Asset (DCA) as a Service",
        resource="file:///index.md",
        sources=["README.md", "SUMMARY.md"],
    ),
    _spec(
        REPO_ROOT / "docs" / "explanation" / "architecture-overview.md",
        type="explanation",
        title="Institutional Digital Asset Custody Architecture",
        topics=["architecture", "custody", "clean-architecture", "mpc", "percona"],
        description_contains="High-level explanation of the DCA platform Concentric Clean Architecture",
        resource="file:///docs/explanation/architecture-overview.md",
        sources=["README.md", "docs/reference/implementation-patterns.md"],
    ),
    _spec(
        REPO_ROOT / "docs" / "explanation" / "challenges-and-opportunities.md",
        type="explanation",
        title="Challenges, Caveats, and Market Opportunities in DCA",
        topics=["market-analysis", "custody", "challenges", "opportunities", "institutional"],
        description_contains="Strategic exploration of industry challenges",
        resource="file:///docs/explanation/challenges-and-opportunities.md",
        sources=["docs/explanation/architecture-overview.md"],
    ),
    _spec(
        REPO_ROOT / "docs" / "explanation" / "open-source-mpc-wallet-architecture.md",
        type="explanation",
        title="Open-Source MPC Wallet System Architecture via cb-mpc",
        topics=["mpc", "cb-mpc", "threshold-signatures", "dkg", "key-management", "cryptography"],
        description_contains="Technical explanation of Coinbase cb-mpc integration",
        resource="file:///docs/explanation/open-source-mpc-wallet-architecture.md",
        sources=["README.md", "src/dca_service/core/key_management.py"],
    ),
    _spec(
        REPO_ROOT / "docs" / "explanation" / "percona-timescaledb-blockchain-sync.md",
        type="explanation",
        title="Percona Server for PostgreSQL & TimescaleDB Dual-Write Blockchain Architecture",
        topics=["percona", "postgresql", "timescaledb", "dual-write", "hypertables", "blockchain-sync"],
        description_contains="Architectural specification of the database-first dual-write pattern",
        resource="file:///docs/explanation/percona-timescaledb-blockchain-sync.md",
        sources=["README.md", "src/dca_service/adapters/timescaledb_adapter.py"],
    ),
    _spec(
        REPO_ROOT / "docs" / "github-pages-setup.md",
        type="howto",
        title="GitHub Pages Automated Deployment & 404 Troubleshooting Guide",
        topics=["github-pages", "jekyll", "deployment", "troubleshooting", "ci-cd"],
        description_contains="Step-by-step guide for configuring Jekyll GitHub Pages deployment",
        resource="file:///docs/github-pages-setup.md",
        sources=["_config.yml", ".github/workflows/jekyll-gh-pages.yml"],
    ),
    _spec(
        REPO_ROOT / "docs" / "how-to" / "install-and-configure-guardrails.md",
        type="howto",
        title="How-To: Install and Configure Repository Guardrails and Documentation Tools",
        topics=["guardrails", "git-hooks", "generate-summary", "pyyaml", "automation"],
        description_contains="Instructions for setting up pre-commit Git guardrail hooks",
        resource="file:///docs/how-to/install-and-configure-guardrails.md",
        sources=["tools/install_git_guardrails.py", "tools/generate_summary.py"],
    ),
    _spec(
        REPO_ROOT / "docs" / "multi-platform-hosting.md",
        type="howto",
        title="Multi-Platform Documentation Deployment Guide",
        topics=["hosting", "gitlab-pages", "gitbook", "readthedocs", "deployment"],
        description_contains="Deployment instructions for hosting documentation across GitLab Pages",
        resource="file:///docs/multi-platform-hosting.md",
        sources=[".gitlab-ci.yml", ".gitbook.yaml", ".readthedocs.yaml"],
    ),
    _spec(
        REPO_ROOT / "docs" / "reference" / "dca-dac-api-and-cli-reference.md",
        type="reference",
        title="DCA & DAC Core API, CLI, and Data Objects Reference",
        topics=["api", "cli", "reference", "data-objects", "dca-service"],
        description_contains="Technical reference for DCA & DAC domain entities",
        resource="file:///docs/reference/dca-dac-api-and-cli-reference.md",
        sources=["src/dca_service/core/account_ledger.py", "src/dca_service/core/policy_engine.py"],
    ),
    _spec(
        REPO_ROOT / "docs" / "reference" / "implementation-patterns.md",
        type="reference",
        title="Industry Implementation Patterns for Custody Platforms",
        topics=["patterns", "custody", "implementation", "security", "architecture"],
        description_contains="Reference guide detailing industry implementation patterns",
        resource="file:///docs/reference/implementation-patterns.md",
        sources=["docs/explanation/architecture-overview.md"],
    ),
    _spec(
        REPO_ROOT / "docs" / "tutorials" / "getting-started-dca-dac.md",
        type="tutorial",
        title="Getting Started with the DCA & DAC Platform on Percona PostgreSQL",
        topics=["tutorial", "getting-started", "percona", "postgresql", "quickstart"],
        description_contains="Hands-on tutorial for initializing, configuring, and executing transactions",
        resource="file:///docs/tutorials/getting-started-dca-dac.md",
        sources=["README.md", "docs/explanation/percona-timescaledb-blockchain-sync.md"],
    ),
]

_IDS = [str(spec["path"].relative_to(REPO_ROOT)) for spec in DOC_SPECS]

_TOPIC_CASES = [(spec, topic) for spec in DOC_SPECS for topic in spec["topics"]]
_TOPIC_IDS = [f"{spec['path'].relative_to(REPO_ROOT)}::{topic}" for spec, topic in _TOPIC_CASES]

_SOURCE_CASES = [(spec, source) for spec in DOC_SPECS for source in spec["sources"]]
_SOURCE_IDS = [f"{spec['path'].relative_to(REPO_ROOT)}::{source}" for spec, source in _SOURCE_CASES]


class TestMigratedFilesExist:
    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_file_exists_and_is_non_empty(self, spec):
        path = spec["path"]
        assert path.is_file(), f"{path} should exist"
        assert path.stat().st_size > 0, f"{path} should not be empty"


class TestFrontmatterDelimiterInvariant:
    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_file_starts_with_frontmatter_delimiter_at_byte_zero(self, spec):
        # OKF v0.2 requires the opening '---' fence at line 1, column 1: no
        # BOM, no leading blank line, no leading whitespace.
        content = _read(spec["path"])
        assert content.startswith("---\n"), (
            f"{spec['path']} must start with '---' at line 1, column 1"
        )


class TestMandatoryFieldsPresent:
    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_all_thirteen_okf_v02_fields_present(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        for field in MANDATORY_OKF_V02_FIELDS:
            assert re.search(rf"(?m)^{field}:", frontmatter), (
                f"Missing mandatory OKF v0.2 field '{field}:' in {spec['path']}"
            )


class TestLegacyOkfV01FieldsRemoved:
    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_legacy_created_field_no_longer_present(self, spec):
        # Regression guard: OKF v0.1's `created` field was renamed to
        # `timestamp` in v0.2; migrated documents must not retain both.
        frontmatter = _frontmatter_block(_read(spec["path"]))
        assert not re.search(r"(?m)^created:", frontmatter), (
            f"{spec['path']} should not retain the legacy 'created:' field after OKF v0.2 migration"
        )


class TestOkfVersionField:
    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_okf_version_is_exactly_0_2(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        _assert_scalar(frontmatter, "okf_version", "0.2")


class TestScalarFieldValues:
    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_type_matches_expected(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        _assert_scalar(frontmatter, "type", spec["type"])

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_title_matches_expected(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        assert spec["title"] in frontmatter

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_status_is_approved(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        _assert_scalar(frontmatter, "status", spec["status"])

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_language_is_en_gb(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        _assert_scalar(frontmatter, "language", spec["language"])

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_generated_is_jules(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        _assert_scalar(frontmatter, "generated", spec["generated"])

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_verified_is_true(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        assert "verified: true" in frontmatter

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_timestamp_matches_expected(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        _assert_scalar(frontmatter, "timestamp", spec["timestamp"])

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_stale_after_matches_expected(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        _assert_scalar(frontmatter, "stale_after", spec["stale_after"])

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_resource_matches_expected(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        _assert_scalar(frontmatter, "resource", spec["resource"])

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_stale_after_is_one_year_after_timestamp(self, spec):
        # Regression guard: every migrated document should carry a
        # `stale_after` exactly one calendar year past its `timestamp`,
        # matching the 2026 -> 2027 pattern used across this PR.
        assert spec["timestamp"].startswith("2026-")
        assert spec["stale_after"].startswith("2027-")
        assert spec["timestamp"][4:] == spec["stale_after"][4:]


class TestDescriptionField:
    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_description_contains_expected_substring(self, spec):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        assert spec["description_contains"] in _normalize(frontmatter)


class TestTopicsListField:
    @pytest.mark.parametrize("spec,topic", _TOPIC_CASES, ids=_TOPIC_IDS)
    def test_topic_listed_under_topics_field(self, spec, topic):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        block = _list_block(frontmatter, "topics")
        assert topic in block

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_topics_are_all_lower_case(self, spec):
        # OKF v0.2 mandates lower-case semantic tags for zero-cost discovery.
        for topic in spec["topics"]:
            assert topic == topic.lower(), f"Topic '{topic}' in {spec['path']} must be lower-case"


class TestSourcesListField:
    @pytest.mark.parametrize("spec,source", _SOURCE_CASES, ids=_SOURCE_IDS)
    def test_source_listed_under_sources_field(self, spec, source):
        frontmatter = _frontmatter_block(_read(spec["path"]))
        block = _list_block(frontmatter, "sources")
        assert source in block


class TestGuardrailScriptAcceptsMigratedFrontmatter:
    """Regression guard tying the frontmatter re-format to the pre-existing,
    unchanged pre-commit guardrail validator
    (``tools/install_git_guardrails.py::check_okf_frontmatter``) so a future
    frontmatter edit that silently breaks compatibility with repository
    tooling is caught.
    """

    @pytest.mark.parametrize("spec", DOC_SPECS, ids=_IDS)
    def test_check_okf_frontmatter_accepts_migrated_file(self, spec):
        module = _load_module(GUARDRAILS_PATH, "install_git_guardrails")
        assert module.check_okf_frontmatter(spec["path"]) is True

    def test_check_okf_frontmatter_rejects_file_missing_okf_version(self, tmp_path):
        # Negative/boundary case: a Markdown file whose frontmatter omits
        # okf_version entirely (e.g. a partially-migrated document) must
        # still be rejected by the guardrail, regardless of the new v0.2
        # field additions being present.
        module = _load_module(GUARDRAILS_PATH, "install_git_guardrails")
        bad_file = tmp_path / "incomplete.md"
        _write(
            bad_file,
            "---\n"
            "type: explanation\n"
            "title: Missing Version Field\n"
            "timestamp: '2026-08-25T00:00:00Z'\n"
            "---\n\n# Missing Version Field\n",
        )
        assert module.check_okf_frontmatter(bad_file) is False

    def test_check_okf_frontmatter_rejects_wrong_okf_version(self, tmp_path):
        module = _load_module(GUARDRAILS_PATH, "install_git_guardrails")
        bad_file = tmp_path / "wrong-version.md"
        _write(bad_file, "---\nokf_version: '0.1'\ntitle: Old Version\n---\n\n# Old Version\n")
        assert module.check_okf_frontmatter(bad_file) is False


class TestSummaryIndexReflectsOkfGuideAddition:
    def test_summary_frontmatter_reflects_okf_v02_mandatory_fields(self):
        # SUMMARY.md is regenerated by tools/generate_summary.py with full
        # OKF v0.2 13-field mandatory YAML frontmatter.
        frontmatter = _frontmatter_block(_read(SUMMARY))
        for field in MANDATORY_OKF_V02_FIELDS:
            assert re.search(rf"(?m)^{field}:", frontmatter), (
                f"Missing mandatory OKF v0.2 field '{field}:' in SUMMARY.md frontmatter"
            )

    def test_summary_generation_date_contract(self, tmp_path, monkeypatch):
        module = _load_module(GENERATE_SUMMARY_PATH, "generate_summary")
        monkeypatch.setattr(module, "__file__", str(tmp_path / "tools" / "generate_summary.py"))
        explicit_dt = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)
        module.generate_summary(gen_datetime=explicit_dt)
        summary_content = (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
        frontmatter = _frontmatter_block(summary_content)
        assert 'timestamp: "2026-08-25T12:00:00Z"' in frontmatter
        assert 'stale_after: "2027-08-25T12:00:00Z"' in frontmatter

    def test_summary_lists_new_okf_guide_document(self):
        content = _read(SUMMARY)
        assert (
            "* [Open Knowledge Format (OKF v0.2) Architectural Specification & "
            "Adoption Guide](docs/explanation/open-knowledge-format-v02-guide.md)"
        ) in content

    def test_summary_changelog_entry_uses_updated_title(self):
        content = _read(SUMMARY)
        assert "* [DCA Service Platform Changelog & Release History](CHANGELOG.md)" in content

    def test_summary_no_longer_uses_old_changelog_title(self):
        # Regression guard: the old, shorter changelog title must not linger
        # alongside the new one.
        content = _read(SUMMARY)
        assert "* [DCA Service Changelog](CHANGELOG.md)" not in content

    def test_okf_guide_ordered_alphabetically_within_explanation_section(self):
        content = _read(SUMMARY)
        challenges_idx = content.index("docs/explanation/challenges-and-opportunities.md")
        okf_guide_idx = content.index("docs/explanation/open-knowledge-format-v02-guide.md")
        mpc_idx = content.index("docs/explanation/open-source-mpc-wallet-architecture.md")
        percona_idx = content.index("docs/explanation/percona-timescaledb-blockchain-sync.md")
        assert challenges_idx < okf_guide_idx < mpc_idx < percona_idx

    def test_get_markdown_title_for_okf_guide_matches_summary_entry(self):
        module = _load_module(GENERATE_SUMMARY_PATH, "generate_summary")
        extracted_title = module.get_markdown_title(OKF_GUIDE_DOC)
        assert extracted_title == (
            "Open Knowledge Format (OKF v0.2) Architectural Specification & Adoption Guide"
        )
        summary_content = _read(SUMMARY)
        assert (
            f"* [{extracted_title}](docs/explanation/open-knowledge-format-v02-guide.md)"
        ) in summary_content


class TestIndexMdRetainsJekyllLayoutField:
    def test_layout_field_present_alongside_new_okf_fields(self):
        # Regression guard: adding the new OKF v0.2 fields to index.md must
        # not have clobbered the Jekyll-specific `layout` key it also needs.
        frontmatter = _frontmatter_block(_read(REPO_ROOT / "index.md"))
        assert re.search(r"(?m)^layout:\s*default$", frontmatter)
