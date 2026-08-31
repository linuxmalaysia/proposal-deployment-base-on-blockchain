"""Tests for the RCF & DAC Proposal documentation modularisation PR.

Scope: this PR splits the previously monolithic
``docs/explanation/research-commercialisation-fund-dac-proposal.md`` document
into eight standalone Diátaxis "explanation" documents under
``docs/explanation/``:

- ``rcf-dac-background-problem.md``            (Section 1)
- ``rcf-dac-business-case.md``                 (Section 2)
- ``rcf-dac-solution-architecture.md``         (Section 3)
- ``rcf-dac-technical-data-layer.md``          (Section 4)
- ``rcf-dac-five-phase-process.md``            (Section 5)
- ``rcf-dac-implementation-roadmap.md``        (Section 6)
- ``rcf-dac-governance-budget-risks.md``       (Section 7)
- ``rcf-dac-ecosystem-precedents.md``          (Section 8)

The original hub page is rewritten into a navigation/index page that links
out to each of the eight modular documents, and ``SUMMARY.md`` is
regenerated (via ``tools/generate_summary.py``) to list each new document
alphabetically within the "Explanation" section.

No Python source code was changed by this PR (documentation only), so these
tests validate the *content* of the changed Markdown files rather than
executing any application code, consistent with the text-based content
validation style used elsewhere in this project's test suite (see
``test_generate_summary.py`` and ``test_open_source_mpc_wallet_docs.py``).
"""

import importlib.util
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPLANATION_DIR = REPO_ROOT / "docs" / "explanation"

BACKGROUND_DOC = EXPLANATION_DIR / "rcf-dac-background-problem.md"
BUSINESS_CASE_DOC = EXPLANATION_DIR / "rcf-dac-business-case.md"
ARCHITECTURE_DOC = EXPLANATION_DIR / "rcf-dac-solution-architecture.md"
TECHNICAL_DOC = EXPLANATION_DIR / "rcf-dac-technical-data-layer.md"
FIVE_PHASE_DOC = EXPLANATION_DIR / "rcf-dac-five-phase-process.md"
ROADMAP_DOC = EXPLANATION_DIR / "rcf-dac-implementation-roadmap.md"
GOVERNANCE_DOC = EXPLANATION_DIR / "rcf-dac-governance-budget-risks.md"
ECOSYSTEM_DOC = EXPLANATION_DIR / "rcf-dac-ecosystem-precedents.md"
HUB_DOC = EXPLANATION_DIR / "research-commercialisation-fund-dac-proposal.md"
SUMMARY = REPO_ROOT / "SUMMARY.md"

GENERATE_SUMMARY_PATH = REPO_ROOT / "tools" / "generate_summary.py"

# (path, expected frontmatter title, repo-relative path, expected H1 heading)
DOC_METADATA = [
    (
        BACKGROUND_DOC,
        "RCF & DAC Proposal: 1. Background and Problem Statement",
        "docs/explanation/rcf-dac-background-problem.md",
        "# 1. Background and Problem Statement",
    ),
    (
        BUSINESS_CASE_DOC,
        "RCF & DAC Proposal: 2. Business Case — Research as an Asset Class",
        "docs/explanation/rcf-dac-business-case.md",
        "# 2. Business Case: Research as an Asset Class",
    ),
    (
        ARCHITECTURE_DOC,
        "RCF & DAC Proposal: 3. Proposed Solution Architecture",
        "docs/explanation/rcf-dac-solution-architecture.md",
        "# 3. Proposed Solution Architecture",
    ),
    (
        TECHNICAL_DOC,
        "RCF & DAC Proposal: 4. Technical Architecture & Data Layer",
        "docs/explanation/rcf-dac-technical-data-layer.md",
        "# 4. Technical Architecture & Data Layer",
    ),
    (
        FIVE_PHASE_DOC,
        "RCF & DAC Proposal: 5. Proposed DAC Process — Five Phases",
        "docs/explanation/rcf-dac-five-phase-process.md",
        "# 5. Proposed DAC Process — Five Phases",
    ),
    (
        ROADMAP_DOC,
        "RCF & DAC Proposal: 6. Implementation Methodology & Timeline",
        "docs/explanation/rcf-dac-implementation-roadmap.md",
        "# 6. Implementation Methodology & Timeline",
    ),
    (
        GOVERNANCE_DOC,
        "RCF & DAC Proposal: 7. Governance, Risk Management & Budget",
        "docs/explanation/rcf-dac-governance-budget-risks.md",
        "# 7. Governance, Risk Management & Budget",
    ),
    (
        ECOSYSTEM_DOC,
        "RCF & DAC Proposal: 8. Conclusion & Ecosystem Precedents",
        "docs/explanation/rcf-dac-ecosystem-precedents.md",
        "# 8. Conclusion & Ecosystem Precedents",
    ),
]

ALL_NEW_DOC_PATHS = [entry[0] for entry in DOC_METADATA]

ALL_CHANGED_FILES = ALL_NEW_DOC_PATHS + [HUB_DOC, SUMMARY]

# Alphabetical order of every docs/explanation/*.md file as produced by
# tools/generate_summary.py's sorted(subdir.glob("**/*.md")) call, taken
# directly from the "### Explanation" section of the regenerated SUMMARY.md.
EXPECTED_EXPLANATION_REL_PATH_ORDER = [
    "docs/explanation/architecture-overview.md",
    "docs/explanation/challenges-and-opportunities.md",
    "docs/explanation/httponly-cookies-and-connection-pooling.md",
    "docs/explanation/open-knowledge-format-v02-guide.md",
    "docs/explanation/open-source-mpc-wallet-architecture.md",
    "docs/explanation/owasp-authorization-framework.md",
    "docs/explanation/percona-timescaledb-blockchain-sync.md",
    "docs/explanation/rcf-dac-background-problem.md",
    "docs/explanation/rcf-dac-business-case.md",
    "docs/explanation/rcf-dac-ecosystem-precedents.md",
    "docs/explanation/rcf-dac-five-phase-process.md",
    "docs/explanation/rcf-dac-governance-budget-risks.md",
    "docs/explanation/rcf-dac-implementation-roadmap.md",
    "docs/explanation/rcf-dac-solution-architecture.md",
    "docs/explanation/rcf-dac-technical-data-layer.md",
    "docs/explanation/research-commercialisation-fund-dac-proposal.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter_block(content: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    assert match, "Expected file to start with a '---' delimited YAML frontmatter block"
    return match.group(1)


def _load_generate_summary_module():
    spec = importlib.util.spec_from_file_location("generate_summary", GENERATE_SUMMARY_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestChangedFilesExist:
    @pytest.mark.parametrize("path", ALL_CHANGED_FILES, ids=lambda p: p.name)
    def test_file_exists_and_is_non_empty(self, path):
        assert path.is_file(), f"{path} should exist"
        assert path.stat().st_size > 0, f"{path} should not be empty"


class TestNewDocFrontmatter:
    @pytest.mark.parametrize("path,title,rel_path,heading", DOC_METADATA)
    def test_frontmatter_okf_version(self, path, title, rel_path, heading):
        frontmatter = _frontmatter_block(_read(path))
        assert 'okf_version: "0.2"' in frontmatter

    @pytest.mark.parametrize("path,title,rel_path,heading", DOC_METADATA)
    def test_frontmatter_type_is_explanation(self, path, title, rel_path, heading):
        frontmatter = _frontmatter_block(_read(path))
        assert 'type: "explanation"' in frontmatter

    @pytest.mark.parametrize("path,title,rel_path,heading", DOC_METADATA)
    def test_frontmatter_title_matches_expected(self, path, title, rel_path, heading):
        frontmatter = _frontmatter_block(_read(path))
        title_match = re.search(r'(?m)^title:\s*(?:"([^"]*)"|\x27([^\']*)\x27|([^"\x27\n]+))\s*$', frontmatter)
        assert title_match, f"title field missing in frontmatter of {path}"
        extracted_title = title_match.group(1) if title_match.group(1) is not None else (title_match.group(2) if title_match.group(2) is not None else title_match.group(3).strip())
        assert extracted_title == title

    @pytest.mark.parametrize("entry", DOC_METADATA)
    def test_frontmatter_status_verified(self, entry):
        path = entry[0]
        frontmatter = _frontmatter_block(_read(path))
        assert 'status: "approved"' in frontmatter or 'status: "verified"' in frontmatter

    @pytest.mark.parametrize("entry", DOC_METADATA)
    def test_frontmatter_language_en_gb(self, entry):
        path = entry[0]
        frontmatter = _frontmatter_block(_read(path))
        assert 'language: "en-GB"' in frontmatter

    @pytest.mark.parametrize("entry", DOC_METADATA)
    def test_frontmatter_created_date(self, entry):
        path = entry[0]
        frontmatter = _frontmatter_block(_read(path))
        assert 'created: "2026-08-25"' in frontmatter or 'timestamp: "2026-08-25T00:00:00Z"' in frontmatter


class TestNewDocStructure:
    @pytest.mark.parametrize("path,title,rel_path,heading", DOC_METADATA)
    def test_h1_heading_present(self, path, title, rel_path, heading):
        content = _read(path)
        assert heading in content

    @pytest.mark.parametrize("path,title,rel_path,heading", DOC_METADATA)
    def test_executive_overview_section_present(self, path, title, rel_path, heading):
        content = _read(path)
        assert "## Executive Overview" in content

    @pytest.mark.parametrize("path,title,rel_path,heading", DOC_METADATA)
    def test_ends_with_related_documentation_section(self, path, title, rel_path, heading):
        content = _read(path).rstrip()
        assert content.endswith(f"Return to [Proposal Overview & Hub Page]({HUB_DOC.name})")


class TestGenerateSummaryToolIntegration:
    """Regression guard tying each new document's frontmatter to the
    documentation index generator (tools/generate_summary.py) so a future
    frontmatter edit that silently breaks title extraction is caught.
    """

    @pytest.mark.parametrize("path,title,rel_path,heading", DOC_METADATA)
    def test_get_markdown_title_matches_expected_and_summary_entry(self, path, title, rel_path, heading):
        module = _load_generate_summary_module()
        extracted_title = module.get_markdown_title(path)
        assert extracted_title == title
        summary_content = _read(SUMMARY)
        assert f"* [{extracted_title}]({rel_path})" in summary_content


class TestSummaryExplanationSection:
    def _explanation_section(self) -> str:
        content = _read(SUMMARY)
        start = content.index("### Explanation")
        end = content.index("### How To")
        return content[start:end]

    def test_explanation_heading_present(self):
        assert "### Explanation" in _read(SUMMARY)

    @pytest.mark.parametrize("rel_path", EXPECTED_EXPLANATION_REL_PATH_ORDER)
    def test_each_explanation_doc_listed(self, rel_path):
        assert rel_path in self._explanation_section()

    def test_explanation_docs_appear_in_alphabetical_order(self):
        section = self._explanation_section()
        positions = [section.index(rel_path) for rel_path in EXPECTED_EXPLANATION_REL_PATH_ORDER]
        assert positions == sorted(positions)

    def test_explanation_section_bullet_count_matches_expected_file_count(self):
        section = self._explanation_section()
        bullet_lines = [line for line in section.splitlines() if line.strip().startswith("* [")]
        assert len(bullet_lines) == len(EXPECTED_EXPLANATION_REL_PATH_ORDER)

    def test_hub_doc_still_listed_in_summary(self):
        content = _read(SUMMARY)
        assert (
            "* [Research Commercialisation Fund (RCF) & Digital Asset Custodian (DAC) "
            "Architecture Proposal](docs/explanation/research-commercialisation-fund-dac-proposal.md)"
        ) in content


class TestCrossDocumentNavigationChain:
    """Verify the "Next Steps" / "Related Proposal Sections" links form a
    coherent forward/backward navigation chain between the eight new
    documents, matching the sequential structure of the original proposal.
    """

    def test_background_doc_links_forward_to_business_case_and_architecture(self):
        content = _read(BACKGROUND_DOC)
        assert "[Business Case: Research as an Asset Class](rcf-dac-business-case.md)" in content
        assert "[Proposed Solution Architecture](rcf-dac-solution-architecture.md)" in content

    def test_business_case_doc_links_forward_and_backward(self):
        content = _read(BUSINESS_CASE_DOC)
        assert "[Proposed Solution Architecture](rcf-dac-solution-architecture.md)" in content
        assert "[Background and Problem Statement](rcf-dac-background-problem.md)" in content

    def test_architecture_doc_links_forward_and_backward(self):
        content = _read(ARCHITECTURE_DOC)
        assert "[Technical Architecture & Data Layer](rcf-dac-technical-data-layer.md)" in content
        assert "[Business Case — Research as an Asset Class](rcf-dac-business-case.md)" in content

    def test_technical_doc_links_forward_and_backward(self):
        content = _read(TECHNICAL_DOC)
        assert "[Proposed DAC Process — Five Phases](rcf-dac-five-phase-process.md)" in content
        assert "[Proposed Solution Architecture](rcf-dac-solution-architecture.md)" in content

    def test_five_phase_doc_links_forward_and_backward(self):
        content = _read(FIVE_PHASE_DOC)
        assert "[Implementation Methodology & Timeline](rcf-dac-implementation-roadmap.md)" in content
        assert "[Technical Architecture & Data Layer](rcf-dac-technical-data-layer.md)" in content

    def test_roadmap_doc_links_forward_and_backward(self):
        content = _read(ROADMAP_DOC)
        assert "[Governance, Risk Management & Budget](rcf-dac-governance-budget-risks.md)" in content
        assert "[Proposed DAC Process — Five Phases](rcf-dac-five-phase-process.md)" in content

    def test_governance_doc_links_forward_and_backward(self):
        content = _read(GOVERNANCE_DOC)
        assert "[Conclusion & Ecosystem Precedents](rcf-dac-ecosystem-precedents.md)" in content
        assert "[Implementation Methodology & Timeline](rcf-dac-implementation-roadmap.md)" in content

    def test_ecosystem_doc_links_back_to_all_seven_prior_sections(self):
        content = _read(ECOSYSTEM_DOC)
        for rel_path in (
            "rcf-dac-background-problem.md",
            "rcf-dac-business-case.md",
            "rcf-dac-solution-architecture.md",
            "rcf-dac-technical-data-layer.md",
            "rcf-dac-five-phase-process.md",
            "rcf-dac-implementation-roadmap.md",
            "rcf-dac-governance-budget-risks.md",
        ):
            assert rel_path in content

    @pytest.mark.parametrize("path,title,rel_path,heading", DOC_METADATA)
    def test_every_new_doc_links_back_to_hub_page(self, path, title, rel_path, heading):
        content = _read(path)
        assert "research-commercialisation-fund-dac-proposal.md" in content


class TestBackgroundDocContent:
    def test_mentions_valley_of_death(self):
        content = _read(BACKGROUND_DOC)
        assert 'technology "Valley of Death"' in content

    def test_mentions_national_grant_bodies(self):
        content = _read(BACKGROUND_DOC)
        assert "FRGS, TRGS, and PRGS" in content

    def test_mentions_mranti_srf_and_ntis(self):
        content = _read(BACKGROUND_DOC)
        assert "Strategic Research Fund (SRF)" in content
        assert "National Technology & Innovation Sandbox (NTIS)" in content

    def test_commercialisation_gap_diagram_present(self):
        content = _read(BACKGROUND_DOC)
        assert "THE COMMERCIALISATION GAP" in content
        assert "THE TECHNOLOGY \"VALLEY OF DEATH\"" in content

    def test_numbered_unverifiable_questions_present(self):
        content = _read(BACKGROUND_DOC)
        assert "1. What research assets currently exist" in content
        assert "4. The fair market value and commercial potential" in content


class TestBusinessCaseDocContent:
    def test_mentions_asset_class_reframing(self):
        content = _read(BUSINESS_CASE_DOC)
        assert "reframing university research as an investable, institutional asset class" in content

    def test_value_creation_table_present(self):
        content = _read(BUSINESS_CASE_DOC)
        assert "| Value Driver | Description & Strategic Impact |" in content
        assert "**Diversified Revenue Streams**" in content
        assert "**Auditable Impact Record**" in content

    def test_mentions_national_alignment_bodies(self):
        content = _read(BUSINESS_CASE_DOC)
        assert "10-10 Malaysian Science, Technology, Innovation and Economy (MySTIE) Framework" in content
        assert "MOSTI-MyIPO IPR Marketplace Portal" in content

    def test_traditional_vs_asset_class_diagram_present(self):
        content = _read(BUSINESS_CASE_DOC)
        assert "TRADITIONAL vs. ASSET CLASS MODEL" in content


class TestArchitectureDocContent:
    def test_defines_rcf_and_dac(self):
        content = _read(ARCHITECTURE_DOC)
        assert "**The Research Commercialisation Fund (RCF):**" in content
        assert "**The Digital Asset Custodian (DAC):**" in content

    def test_dual_pillar_diagram_present(self):
        content = _read(ARCHITECTURE_DOC)
        assert "DUAL-PILLAR SOLUTION ARCHITECTURE" in content

    @pytest.mark.parametrize(
        "function_heading",
        [
            "### 1. Digital Research Asset Registry",
            "### 2. Digital Evidence Repository",
            "### 3. Commercialisation Dashboard",
            "### 4. Investor Dashboard",
            "### 5. Impact Measurement Platform",
        ],
    )
    def test_five_core_functions_present(self, function_heading):
        content = _read(ARCHITECTURE_DOC)
        assert function_heading in content

    def test_five_core_functions_appear_in_ascending_order(self):
        content = _read(ARCHITECTURE_DOC)
        headings = [
            "### 1. Digital Research Asset Registry",
            "### 2. Digital Evidence Repository",
            "### 3. Commercialisation Dashboard",
            "### 4. Investor Dashboard",
            "### 5. Impact Measurement Platform",
        ]
        positions = [content.index(h) for h in headings]
        assert positions == sorted(positions)


class TestTechnicalDocContent:
    def test_mentions_percona_and_timescaledb_dual_write(self):
        content = _read(TECHNICAL_DOC)
        assert "Percona Server for PostgreSQL" in content
        assert "TimescaleDB" in content
        assert "dual-write" in content.lower()

    def test_five_design_principles_diagram_present(self):
        content = _read(TECHNICAL_DOC)
        assert "PLATFORM DESIGN PRINCIPLES" in content

    def test_five_logical_layers_diagram_present(self):
        content = _read(TECHNICAL_DOC)
        assert "LOGICAL ARCHITECTURE — 5 LAYERS" in content
        assert "PERSISTENCE ENGINE: PERCONA POSTGRESQL + TIMESCALEDB DUAL-WRITE" in content

    def test_core_data_objects_table_present(self):
        content = _read(TECHNICAL_DOC)
        assert "| Data Object | Purpose | Primary Storage Engine |" in content
        assert "**Digital Research ID**" in content
        assert "**Market Readiness Score (MRS)**" in content

    def test_pdpa_compliance_mentioned(self):
        content = _read(TECHNICAL_DOC)
        assert "Personal Data Protection Act 2010 (PDPA)" in content


class TestFivePhaseDocContent:
    @pytest.mark.parametrize(
        "phase_heading",
        [
            "## 5.1 Phase 1 — Research Inventory",
            "## 5.2 Phase 2 — Digital Asset Registration",
            "## 5.3 Phase 3 — Commercialisation Assessment",
            "## 5.4 Phase 4 — Funding and Investment",
            "## 5.5 Phase 5 — Revenue Realisation",
        ],
    )
    def test_phase_heading_present(self, phase_heading):
        content = _read(FIVE_PHASE_DOC)
        assert phase_heading in content

    def test_phase_headings_appear_in_ascending_order(self):
        content = _read(FIVE_PHASE_DOC)
        headings = [
            "## 5.1 Phase 1 — Research Inventory",
            "## 5.2 Phase 2 — Digital Asset Registration",
            "## 5.3 Phase 3 — Commercialisation Assessment",
            "## 5.4 Phase 4 — Funding and Investment",
            "## 5.5 Phase 5 — Revenue Realisation",
        ]
        positions = [content.index(h) for h in headings]
        assert positions == sorted(positions)

    def test_five_phase_diagram_present(self):
        content = _read(FIVE_PHASE_DOC)
        assert "PROPOSED DAC PROCESS — 5 PHASES" in content

    def test_mentions_uuid_digital_research_id(self):
        content = _read(FIVE_PHASE_DOC)
        assert "**Digital Research ID**" in content
        assert "`uuid` primary key" in content

    def test_mentions_investment_ready_scorecard_threshold(self):
        content = _read(FIVE_PHASE_DOC)
        assert 'TRL 6, MRS > 75/100' in content
        assert '"Investment Ready"' in content


class TestRoadmapDocContent:
    def test_hybrid_execution_diagram_present(self):
        content = _read(ROADMAP_DOC)
        assert "HYBRID EXECUTION METHODOLOGY" in content
        assert "GOVERNANCE STREAM (Phase-Gated Milestones)" in content
        assert "ENGINEERING STREAM (Agile Platform Releases)" in content

    def test_roadmap_table_present(self):
        content = _read(ROADMAP_DOC)
        assert "| Timeframe | Milestone | Workstream | Key Deliverable |" in content

    def test_roadmap_milestones_appear_in_chronological_order(self):
        content = _read(ROADMAP_DOC)
        milestones = [
            "**Month 1–2**",
            "**Month 1–3**",
            "**Month 2–6**",
            "**Month 4–6**",
            "**Month 6–9**",
            "**Month 7–10**",
            "**Month 9–12**",
            "**Month 10–16**",
            "**Month 16–20**",
            "**Month 16–24+**",
            "**Month 24**",
        ]
        positions = [content.index(m) for m in milestones]
        assert positions == sorted(positions)

    def test_final_milestone_is_full_programme_review(self):
        content = _read(ROADMAP_DOC)
        assert "Full Programme Review & Steady State" in content


class TestGovernanceDocContent:
    def test_budget_table_present(self):
        content = _read(GOVERNANCE_DOC)
        assert "| Budget Item | Estimated Envelope (MYR) | Description & Resource Scope |" in content
        assert "**DAC Platform Development**" in content
        assert "RM 1.5m – 3.0m" in content

    def test_rcf_seed_capital_budget_line(self):
        content = _read(GOVERNANCE_DOC)
        assert "**RCF Seed Capital (Year 1)**" in content
        assert "RM 5.0m – 15.0m" in content

    def test_risk_mitigation_matrix_diagram_present(self):
        content = _read(GOVERNANCE_DOC)
        assert "RISK MITIGATION MATRIX" in content
        assert "RISK VECTOR 1: IP OWNERSHIP DISPUTES" in content
        assert "RISK VECTOR 2: DATA SECURITY & CONFIDENTIAL EXPOSURE" in content
        assert "RISK VECTOR 3: OVERVALUATION & INCONSISTENT SCORING" in content

    @pytest.mark.parametrize(
        "risk_heading",
        [
            "### 1. Disputed IP Ownership & Inventorship Claims",
            "### 2. Data Security & Unauthorised Confidential Exposure",
            "### 3. Overvaluation & Inconsistent Project Scoring",
        ],
    )
    def test_detailed_risk_section_present(self, risk_heading):
        content = _read(GOVERNANCE_DOC)
        assert risk_heading in content

    def test_aes_256_encryption_at_rest_mentioned(self):
        content = _read(GOVERNANCE_DOC)
        assert "encrypted at rest (AES-256)" in content


class TestEcosystemDocContent:
    @pytest.mark.parametrize(
        "institution",
        [
            "Stanford University (Office of Technology Licensing - OTL)",
            "Oxford University (Oxford Science Enterprises - OSE)",
            "University of Pennsylvania (Penn Center for Innovation)",
            "University of Minnesota (Discovery Capital)",
            "Stellenbosch University (Innovus)",
        ],
    )
    def test_international_benchmark_mentioned(self, institution):
        content = _read(ECOSYSTEM_DOC)
        assert institution in content

    def test_international_benchmark_diagram_present(self):
        content = _read(ECOSYSTEM_DOC)
        assert "INTERNATIONAL BENCHMARK MODEL COMPARISON" in content

    def test_malaysian_ecosystem_diagram_present(self):
        content = _read(ECOSYSTEM_DOC)
        assert "MALAYSIAN ECOSYSTEM INTEGRATION" in content
        assert "MRANTI (SRF / NTIS)" in content
        assert "MOSTI-MyIPO IPR" in content

    def test_strategic_conclusion_section_present(self):
        content = _read(ECOSYSTEM_DOC)
        assert "## 8.3 Strategic Conclusion" in content

    def test_document_ends_with_strategic_conclusion_before_navigation(self):
        # Regression guard: ensure the "Related Proposal Sections" nav block
        # comes after (not interleaved with) the strategic conclusion text.
        content = _read(ECOSYSTEM_DOC)
        conclusion_idx = content.index(
            "Approval and implementation of this proposal will position the university"
        )
        nav_idx = content.index("## Related Proposal Sections")
        assert conclusion_idx < nav_idx


class TestHubPageRewrite:
    def test_hub_frontmatter_unchanged(self):
        frontmatter = _frontmatter_block(_read(HUB_DOC))
        assert 'okf_version: "0.2"' in frontmatter
        assert 'type: "explanation"' in frontmatter
        title_match = re.search(r'(?m)^title:\s*(?:"([^"]*)"|\x27([^\']*)\x27|([^"\x27\n]+))\s*$', frontmatter)
        assert title_match, "title field missing in hub frontmatter"
        extracted_title = title_match.group(1) if title_match.group(1) is not None else (title_match.group(2) if title_match.group(2) is not None else title_match.group(3).strip())
        assert extracted_title == (
            "Research Commercialisation Fund (RCF) & Digital Asset Custodian (DAC) "
            "Architecture Proposal"
        )
        assert 'status: "approved"' in frontmatter or 'status: "verified"' in frontmatter

    def test_executive_summary_section_retained(self):
        content = _read(HUB_DOC)
        assert "## Executive Summary & System Backend Mandate" in content

    def test_proposal_modules_navigation_section_present(self):
        content = _read(HUB_DOC)
        assert "## Proposal Modules & Navigation" in content
        assert "divided into eight modular explanation documents" in content

    def test_governance_and_version_controls_section_present(self):
        content = _read(HUB_DOC)
        assert "## Governance & Version Controls" in content
        assert "**Document Version:** `1.0.0`" in content

    @pytest.mark.parametrize(
        "rel_link",
        [
            "[View Section 1](rcf-dac-background-problem.md)",
            "[View Section 2](rcf-dac-business-case.md)",
            "[View Section 3](rcf-dac-solution-architecture.md)",
            "[View Section 4](rcf-dac-technical-data-layer.md)",
            "[View Section 5](rcf-dac-five-phase-process.md)",
            "[View Section 6](rcf-dac-implementation-roadmap.md)",
            "[View Section 7](rcf-dac-governance-budget-risks.md)",
            "[View Section 8](rcf-dac-ecosystem-precedents.md)",
        ],
    )
    def test_modules_table_links_to_each_new_doc(self, rel_link):
        content = _read(HUB_DOC)
        assert rel_link in content

    def test_modules_table_rows_appear_in_ascending_section_order(self):
        content = _read(HUB_DOC)
        links = [f"[View Section {n}](" for n in range(1, 9)]
        positions = [content.index(link) for link in links]
        assert positions == sorted(positions)

    @pytest.mark.parametrize(
        "removed_inline_heading",
        [
            "## 1. Background and Problem Statement",
            "## 2. Business Case: Research as an Asset Class",
            "## 3. Proposed Solution Architecture",
            "## 4. Technical Architecture & Data Layer",
            "## 5. Proposed DAC Process — Five Phases",
            "## 6. Implementation Methodology & Timeline",
            "## 7. Governance, Risk Management & Budget",
            "## 8. Conclusion & Ecosystem Precedents",
        ],
    )
    def test_old_inline_section_headings_removed_from_hub_page(self, removed_inline_heading):
        # Regression guard: the hub page used to contain the full inline
        # content of every section; after modularisation it should only
        # reference the sections via the navigation table, not repeat their
        # original "## N. <Title>" headings verbatim.
        content = _read(HUB_DOC)
        assert removed_inline_heading not in content

    def test_old_inline_budget_bullets_removed_from_hub_page(self):
        # Regression guard: the detailed budget bullet list previously lived
        # inline in the hub page; it now lives solely in the governance doc.
        content = _read(HUB_DOC)
        assert "**DAC Platform Development:** RM 1.5m" not in content


class TestCrossFileConsistency:
    def test_all_eight_new_docs_exist_side_by_side_in_explanation_dir(self):
        for path in ALL_NEW_DOC_PATHS:
            assert path.is_file(), f"{path} should exist"
            assert path.parent == EXPLANATION_DIR

    def test_no_duplicate_summary_bullets_for_explanation_section(self):
        content = _read(SUMMARY)
        start = content.index("### Explanation")
        end = content.index("### How To")
        section = content[start:end]
        bullet_links = re.findall(r"\* \[[^\]]+\]\(([^)]+)\)", section)
        assert len(bullet_links) == len(set(bullet_links)), "Explanation section should not list any path twice"

    @pytest.mark.parametrize("path,title,rel_path,heading", DOC_METADATA)
    def test_new_doc_filename_matches_rel_path_used_in_summary(self, path, title, rel_path, heading):
        assert rel_path == f"docs/explanation/{path.name}"
