"""Tests for the new Open Knowledge Format (OKF v0.2) explanation document
introduced by this PR: ``docs/explanation/open-knowledge-format-v02-guide.md``.

Scope: this PR adds a brand new Diátaxis "explanation" document that
documents the OKF v0.2 specification itself -- its rationale within the Deep
State of Mind (DSOM) protocol, its complete 13-field frontmatter schema, a
concrete worked frontmatter example, the frontmatter invariants/rules, and
verification instructions. Unlike the other documents migrated by this PR
(which now use unquoted/single-quoted, block-list YAML style), this new
document retains the original double-quoted, flow-list YAML style used by
the rest of the pre-migration codebase.

No Python source code was changed by this PR (documentation only), so these
tests validate the *content* of the new Markdown file rather than executing
any application code, consistent with the text-based content validation
style used elsewhere in this project's test suite (see
``test_open_source_mpc_wallet_docs.py`` and ``test_rcf_dac_proposal_docs.py``).
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
OKF_GUIDE_DOC = REPO_ROOT / "docs" / "explanation" / "open-knowledge-format-v02-guide.md"

EXPECTED_TITLE = "Open Knowledge Format (OKF v0.2) Architectural Specification & Adoption Guide"

MANDATORY_OKF_V02_FIELD_NAMES = [
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


class TestFileExists:
    def test_file_exists_and_is_non_empty(self):
        assert OKF_GUIDE_DOC.is_file()
        assert OKF_GUIDE_DOC.stat().st_size > 0

    def test_file_located_in_explanation_directory(self):
        assert OKF_GUIDE_DOC.parent == REPO_ROOT / "docs" / "explanation"


class TestOkfGuideFrontmatter:
    def test_starts_with_frontmatter_delimiter_at_byte_zero(self):
        content = _read(OKF_GUIDE_DOC)
        assert content.startswith("---\n")

    @pytest.mark.parametrize("field", MANDATORY_OKF_V02_FIELD_NAMES)
    def test_mandatory_field_present(self, field):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert re.search(rf"(?m)^{field}:", frontmatter), f"Missing '{field}:' in frontmatter"

    def test_okf_version_is_0_2(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert 'okf_version: "0.2"' in frontmatter

    def test_type_is_explanation(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert 'type: "explanation"' in frontmatter

    def test_title_matches_expected(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert f'title: "{EXPECTED_TITLE}"' in frontmatter

    def test_timestamp_matches_expected(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert 'timestamp: "2026-08-25T00:00:00Z"' in frontmatter

    @pytest.mark.parametrize(
        "topic",
        ["okf", "dsom", "context-engineering", "provenance", "yaml-frontmatter", "diataxis", "specification"],
    )
    def test_topics_list_contains_expected_topic(self, topic):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert f'"{topic}"' in frontmatter

    def test_description_mentions_okf_and_dsom(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert "Open Knowledge Format (OKF v0.2)" in frontmatter
        assert "Deep State of Mind (DSOM) framework" in frontmatter

    def test_resource_matches_expected_path(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert 'resource: "file:///docs/explanation/open-knowledge-format-v02-guide.md"' in frontmatter

    @pytest.mark.parametrize(
        "source",
        [
            "https://linuxmalaysia.github.io/deep-state-of-mind-for-my-ai/OKF-ADOPTION-GUIDE/",
            "README.md",
            "AGENTS.md",
            ".agents/AGENTS.md",
        ],
    )
    def test_sources_list_contains_expected_source(self, source):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert source in frontmatter

    def test_generated_is_jules(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert 'generated: "jules"' in frontmatter

    def test_verified_is_true(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert "verified: true" in frontmatter

    def test_status_is_approved(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert 'status: "approved"' in frontmatter

    def test_stale_after_is_one_year_after_timestamp(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert 'stale_after: "2027-08-25T00:00:00Z"' in frontmatter

    def test_language_is_en_gb(self):
        frontmatter = _frontmatter_block(_read(OKF_GUIDE_DOC))
        assert 'language: "en-GB"' in frontmatter


class TestOkfGuideStructure:
    def test_h1_heading_present(self):
        content = _read(OKF_GUIDE_DOC)
        assert f"# {EXPECTED_TITLE}" in content

    @pytest.mark.parametrize(
        "heading",
        [
            "## Executive Summary & Core Concept",
            "## Why OKF is the Core Engine of Deep State of Mind (DSOM)",
            "### 1. 98%+ Token & Cost Compression Ratio",
            "### 2. Progressive Disclosure via Directory Index Routers",
            "### 3. Zero-Loss Persistent Memory & Instant Reanimation",
            "### 4. The Artifact Pyramid & Zero-Cost Context Prediction",
            "## OKF Technical Specification & Conformance Rules",
            "### OKF v0.2 Complete Frontmatter Schema",
            "## Concrete OKF v0.2 Code Example",
            "## Frontmatter Invariants & Rules",
            "## Verification & Link Validation",
        ],
    )
    def test_expected_heading_present(self, heading):
        content = _read(OKF_GUIDE_DOC)
        assert heading in content

    def test_top_level_headings_appear_in_ascending_order(self):
        content = _read(OKF_GUIDE_DOC)
        top_level_headings = [
            "## Executive Summary & Core Concept",
            "## Why OKF is the Core Engine of Deep State of Mind (DSOM)",
            "## OKF Technical Specification & Conformance Rules",
            "## Concrete OKF v0.2 Code Example",
            "## Frontmatter Invariants & Rules",
            "## Verification & Link Validation",
        ]
        positions = [content.index(heading) for heading in top_level_headings]
        assert positions == sorted(positions)

    def test_advantage_subsection_headings_appear_in_ascending_order(self):
        content = _read(OKF_GUIDE_DOC)
        subsection_headings = [
            "### 1. 98%+ Token & Cost Compression Ratio",
            "### 2. Progressive Disclosure via Directory Index Routers",
            "### 3. Zero-Loss Persistent Memory & Instant Reanimation",
            "### 4. The Artifact Pyramid & Zero-Cost Context Prediction",
        ]
        positions = [content.index(heading) for heading in subsection_headings]
        assert positions == sorted(positions)


class TestOkfGuideExecutiveSummaryContent:
    def test_mentions_google_cloud_data_cloud_team_and_introduction_date(self):
        content = _read(OKF_GUIDE_DOC)
        assert "Google Cloud's Data Cloud team in June 2026" in content

    def test_mentions_rag_limitations(self):
        content = _read(OKF_GUIDE_DOC)
        assert "Retrieval-Augmented Generation (RAG)" in content
        assert "lost-in-the-middle" in content

    def test_mentions_git_native_markdown_representation(self):
        content = _read(OKF_GUIDE_DOC)
        assert "Git-native representation" in content
        assert "UTF-8 Markdown files" in content


class TestOkfGuideArchitectureDiagram:
    def test_workspace_diagram_present(self):
        content = _read(OKF_GUIDE_DOC)
        assert "```text" in content
        assert "Sovereign AI Workspace (DSOM)" in content
        assert "Spatial Memory" in content
        assert "Agent Skill Library" in content
        assert "OKF Frontmatter Index" in content

    def test_diagram_lists_three_performance_advantages(self):
        content = _read(OKF_GUIDE_DOC)
        assert "Progressive" in content
        assert "Zero-Loss" in content
        assert "Multi-Agent" in content


class TestOkfGuideFrontmatterSchemaTable:
    def test_schema_table_header_present(self):
        content = _read(OKF_GUIDE_DOC)
        assert "| Field | Type | Description | Example Value |" in content

    def test_thirteen_mandatory_fields_mentioned(self):
        content = _read(OKF_GUIDE_DOC)
        assert "13 mandatory metadata fields" in content

    @pytest.mark.parametrize("field", MANDATORY_OKF_V02_FIELD_NAMES)
    def test_each_field_documented_in_schema_table(self, field):
        content = _read(OKF_GUIDE_DOC)
        assert f"`{field}`" in content

    def test_schema_table_rows_appear_in_expected_order(self):
        # Regression guard: ensure the table wasn't accidentally reordered
        # or duplicated when authored.
        content = _read(OKF_GUIDE_DOC)
        positions = [content.index(f"`{field}` |") for field in MANDATORY_OKF_V02_FIELD_NAMES]
        assert positions == sorted(positions)


class TestOkfGuideCodeExample:
    def test_yaml_code_block_present(self):
        content = _read(OKF_GUIDE_DOC)
        assert "```yaml" in content

    def test_code_example_shows_full_frontmatter_shape(self):
        content = _read(OKF_GUIDE_DOC)
        assert 'okf_version: "0.2"' in content
        assert 'generated: "google-antigravity"' in content
        assert "stale_after" in content

    def test_code_example_uses_double_quoted_flow_list_topics(self):
        content = _read(OKF_GUIDE_DOC)
        assert 'topics: ["guardrails", "validation", "ast", "mcp", "dsom", "twilight-state", "security", "okf"]' in content


class TestOkfGuideInvariantsAndRules:
    @pytest.mark.parametrize(
        "rule_label",
        [
            "**Line 1 Column 1 Invariant:**",
            "**Mandatory Field Invariant:**",
            "**Quoting Rules:**",
            "**Preservation of Raw Timestamps:**",
            "**Language Standard:**",
        ],
    )
    def test_invariant_rule_present(self, rule_label):
        content = _read(OKF_GUIDE_DOC)
        assert rule_label in content

    def test_exactly_five_numbered_invariant_rules(self):
        content = _read(OKF_GUIDE_DOC)
        start = content.index("## Frontmatter Invariants & Rules")
        end = content.index("## Verification & Link Validation")
        section = content[start:end]
        numbered_items = re.findall(r"^\d+\.\s+\*\*", section, re.MULTILINE)
        assert len(numbered_items) == 5

    def test_okf_version_must_be_0_2_string_rule(self):
        content = _read(OKF_GUIDE_DOC)
        assert 'okf_version` MUST be specified as `"0.2"`' in content

    def test_uk_english_language_standard_examples(self):
        content = _read(OKF_GUIDE_DOC)
        assert "initialise" in content
        assert "prioritise" in content
        assert "segregated" in content


class TestOkfGuideVerificationSection:
    def test_bash_code_block_present(self):
        content = _read(OKF_GUIDE_DOC)
        assert "```bash" in content

    def test_mentions_running_pytest_suite(self):
        content = _read(OKF_GUIDE_DOC)
        assert "uv run pytest" in content

    def test_mentions_regenerating_summary(self):
        content = _read(OKF_GUIDE_DOC)
        assert "uv run python tools/generate_summary.py" in content

    def test_document_ends_with_verification_code_block(self):
        content = _read(OKF_GUIDE_DOC).rstrip()
        assert content.endswith("```")
        assert content.endswith("uv run python tools/generate_summary.py\n```")
