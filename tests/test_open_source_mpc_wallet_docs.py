"""Tests for the Open-Source MPC Wallet System Architecture documentation PR.

Scope: this PR adds a new Diátaxis "explanation" document,
``docs/explanation/open-source-mpc-wallet-architecture.md``, describing how
Coinbase's open-source ``cb-mpc`` threshold cryptography library integrates
with the DCA Platform's P2P node transport, policy engine, and Percona
PostgreSQL/TimescaleDB dual-write pipeline. It also:

- Updates the triple-ledger (``README.md``, ``CHANGELOG.md``, ``HISTORY.md``)
  to reference the new architecture document.
- Regenerates ``SUMMARY.md`` to include the new document in the
  "Explanation" section, in alphabetical order alongside the other
  ``docs/explanation/`` documents.
- Updates the DSOM spatial memory anchors under ``.agents/brain/``
  (``palace_registry.md``, ``task.md``, ``walkthrough.md``) to record the
  new documentation and its provenance.

No Python source code was changed by this PR (documentation only), so these
tests validate the *content* of the changed Markdown files rather than
executing any application code, consistent with the text-based content
validation style used elsewhere in this project's test suite (see
``test_generate_summary.py`` and ``test_jekyll_site_config.py``).
"""

import importlib.util
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

MPC_DOC = REPO_ROOT / "docs" / "explanation" / "open-source-mpc-wallet-architecture.md"
PERCONA_DOC = REPO_ROOT / "docs" / "explanation" / "percona-timescaledb-blockchain-sync.md"
README = REPO_ROOT / "README.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
HISTORY = REPO_ROOT / "HISTORY.md"
SUMMARY = REPO_ROOT / "SUMMARY.md"
PALACE_REGISTRY = REPO_ROOT / ".agents" / "brain" / "palace_registry.md"
TASK_MD = REPO_ROOT / ".agents" / "brain" / "task.md"
WALKTHROUGH_MD = REPO_ROOT / ".agents" / "brain" / "walkthrough.md"

MPC_DOC_REL_PATH = "docs/explanation/open-source-mpc-wallet-architecture.md"

GENERATE_SUMMARY_PATH = REPO_ROOT / "tools" / "generate_summary.py"


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


ALL_CHANGED_DOC_FILES = [
    PALACE_REGISTRY,
    TASK_MD,
    WALKTHROUGH_MD,
    CHANGELOG,
    HISTORY,
    README,
    SUMMARY,
    MPC_DOC,
]


class TestChangedFilesExist:
    @pytest.mark.parametrize("path", ALL_CHANGED_DOC_FILES, ids=lambda p: p.name)
    def test_file_exists_and_is_non_empty(self, path):
        assert path.is_file(), f"{path} should exist"
        assert path.stat().st_size > 0, f"{path} should not be empty"


class TestMpcWalletDocFrontmatter:
    def test_frontmatter_okf_version(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert 'okf_version: "0.2"' in frontmatter or "okf_version: '0.2'" in frontmatter

    def test_frontmatter_type_is_explanation(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert 'type: "explanation"' in frontmatter or "type: explanation" in frontmatter

    def test_frontmatter_title(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert "Open-Source MPC Wallet System Architecture via cb-mpc" in frontmatter

    def test_frontmatter_status_verified(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert 'status: "approved"' in frontmatter or 'status: "verified"' in frontmatter or 'status: approved' in frontmatter or 'status: verified' in frontmatter

    def test_frontmatter_language_en_gb(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert 'language: "en-GB"' in frontmatter or "language: en-GB" in frontmatter

    def test_frontmatter_created_date(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert 'timestamp: "2026-08-25T00:00:00Z"' in frontmatter or "timestamp: '2026-08-25T00:00:00Z'" in frontmatter or 'created: "2026-08-25"' in frontmatter


class TestMpcWalletDocStructure:
    def test_h1_heading_present(self):
        content = _read(MPC_DOC)
        assert "# Open-Source MPC Wallet System Architecture via Coinbase `cb-mpc`" in content

    @pytest.mark.parametrize(
        "heading",
        [
            "## 1. Executive Summary & Strategic Rationale",
            "## 2. Technical Foundations of Coinbase `cb-mpc`",
            "### 2.1 Supported Cryptographic Schemes & Curves",
            "### 2.2 Key Mathematical Properties",
            "## 3. End-to-End Wallet System Topology & Component Linkage",
            "### 3.1 Participant Node Roles in a 2-of-3 Quorum Model",
            "## 4. Operational Protocol Flows",
            "### 4.1 Distributed Key Generation (DKG)",
            "### 4.2 Threshold Signing & Policy Validation Flow",
            "## 5. Security Architecture, Key Share Protection & Auditing",
            "### 5.1 Envelope Encryption for Key Shares",
            "### 5.2 Proactive Secret Sharing & Key Refresh",
            "### 5.3 Audit Trails & Compliance",
            "## 6. Summary of System Integration Benefits",
        ],
    )
    def test_expected_heading_present(self, heading):
        content = _read(MPC_DOC)
        assert heading in content

    def test_headings_appear_in_ascending_order(self):
        # Regression guard: ensure the numbered top-level sections were not
        # reordered/duplicated when the document was authored.
        content = _read(MPC_DOC)
        top_level_headings = [
            "## 1. Executive Summary & Strategic Rationale",
            "## 2. Technical Foundations of Coinbase `cb-mpc`",
            "## 3. End-to-End Wallet System Topology & Component Linkage",
            "## 4. Operational Protocol Flows",
            "## 5. Security Architecture, Key Share Protection & Auditing",
            "## 6. Summary of System Integration Benefits",
        ]
        positions = [content.index(heading) for heading in top_level_headings]
        assert positions == sorted(positions)

    def test_document_ends_with_final_summary_bullet(self):
        content = _read(MPC_DOC).rstrip()
        assert content.endswith(
            "- **Enterprise Performance:** High-speed off-chain interactive signing linked directly "
            "to Percona Server for PostgreSQL and TimescaleDB dual-write pipelines."
        )


class TestMpcWalletDocContent:
    def test_references_upstream_cb_mpc_repository(self):
        content = _read(MPC_DOC)
        assert "[`cb-mpc`](https://github.com/coinbase/cb-mpc)" in content

    @pytest.mark.parametrize("curve", ["secp256k1", "secp256r1", "Ed25519"])
    def test_mentions_supported_curve(self, curve):
        content = _read(MPC_DOC)
        assert curve in content

    def test_mentions_threshold_schemes(self):
        content = _read(MPC_DOC)
        assert "Threshold ECDSA" in content
        assert "Threshold EdDSA" in content

    @pytest.mark.parametrize(
        "node_description",
        [
            "**Node A (Custodian Engine Node):**",
            "**Node B (Client Co-Signer / Mobile / WebAuthn):**",
            "**Node C (Institutional Recovery Guard Node):**",
        ],
    )
    def test_mentions_quorum_node_role(self, node_description):
        content = _read(MPC_DOC)
        assert node_description in content

    def test_topology_diagram_present(self):
        content = _read(MPC_DOC)
        assert "```text" in content
        assert "MPC Orchestrator & Relay Bus" in content
        assert "Policy Engine & Rules Validation" in content
        assert "Percona PostgreSQL & TimescaleDB" in content

    def test_mentions_dkg_protocol_steps(self):
        content = _read(MPC_DOC)
        assert "Distributed Key Generation (DKG)" in content
        assert "Zero-Knowledge Verification" in content
        assert "Public Key Derivation" in content

    def test_mentions_envelope_encryption_terms(self):
        content = _read(MPC_DOC)
        assert "AES-256-GCM" in content
        assert "Data Encryption Key (DEK)" in content
        assert "Key Encryption Key (KEK)" in content

    def test_mentions_proactive_secret_reshuffling(self):
        content = _read(MPC_DOC)
        assert "proactive secret reshuffling" in content
        assert "Renders stolen historic key shares mathematically useless." in content

    def test_mentions_compliance_standards(self):
        content = _read(MPC_DOC)
        assert "SOC 1 Type II" in content
        assert "SOC 2 Type II" in content

    def test_references_key_management_core_module(self):
        content = _read(MPC_DOC)
        assert "src/dca_service/core/key_management.py" in content

    def test_mentions_dual_write_settlement_states(self):
        content = _read(MPC_DOC)
        assert "DB_RECORDED" in content
        assert "PENDING_BLOCKCHAIN" in content
        assert "CHAIN_CONFIRMED" in content


class TestMpcWalletDocSummaryToolIntegration:
    """Regression guard tying the new document's frontmatter to the
    documentation index generator (tools/generate_summary.py) so that a
    future frontmatter edit that silently breaks title extraction is caught.
    """

    def test_get_markdown_title_matches_summary_entry(self):
        module = _load_generate_summary_module()
        extracted_title = module.get_markdown_title(MPC_DOC)
        assert extracted_title == "Open-Source MPC Wallet System Architecture via cb-mpc"
        summary_content = _read(SUMMARY)
        assert f"* [{extracted_title}]({MPC_DOC_REL_PATH})" in summary_content


class TestReadmeIntegration:
    def test_key_management_bullet_mentions_open_source_cb_mpc(self):
        content = _read(README)
        assert (
            "**Key Management:** Open-source MPC (Multi-Party Computation) threshold quorums "
            "via Coinbase `cb-mpc` integration and HSM-backed Hot/Warm/Cold vault tiering"
        ) in content

    def test_key_management_bullet_links_to_mpc_doc(self):
        content = _read(README)
        assert f"[Open-Source MPC Wallet Architecture]({MPC_DOC_REL_PATH})" in content

    def test_previous_non_open_source_wording_removed(self):
        # Regression guard: the prior bullet described plain "MPC" without
        # attributing it to the open-source cb-mpc library or linking to the
        # new architecture document.
        content = _read(README)
        assert (
            "**Key Management:** MPC (Multi-Party Computation) threshold quorums and "
            "HSM-backed Hot/Warm/Cold vault tiering.\n"
        ) not in content

    def test_other_key_features_bullets_preserved(self):
        # Ensure unrelated bullets in the same list were not clobbered.
        content = _read(README)
        assert "**Client Segregation:**" in content
        assert "**Policy Engine:**" in content
        assert "**Percona PostgreSQL & TimescaleDB Synchronisation:**" in content


class TestChangelogEntry:
    def test_added_section_documents_mpc_wallet_doc(self):
        content = _read(CHANGELOG)
        assert (
            "Open-Source MPC Wallet System Architecture documentation based on Coinbase "
            "`cb-mpc` cryptography library"
        ) in content

    def test_changelog_links_to_new_doc_path(self):
        content = _read(CHANGELOG)
        assert f"([`{MPC_DOC_REL_PATH}`]({MPC_DOC_REL_PATH}))" in content

    def test_new_entry_appended_after_existing_entries(self):
        content = _read(CHANGELOG)
        percona_idx = content.index("Percona Server for PostgreSQL & TimescaleDB Dual-Write")
        mpc_idx = content.index("Open-Source MPC Wallet System Architecture documentation")
        assert percona_idx < mpc_idx


class TestHistoryEntry:
    def test_history_documents_mpc_wallet_design(self):
        content = _read(HISTORY)
        assert (
            "Designed Open-Source MPC Wallet System linking Coinbase `cb-mpc` cryptographic "
            "library with P2P node transport, policy engine quorums, and database dual-write "
            "settlement."
        ) in content

    def test_new_entry_appended_after_timescaledb_entry(self):
        content = _read(HISTORY)
        timescale_idx = content.index("Integrated Percona Server for PostgreSQL and TimescaleDB")
        mpc_idx = content.index("Designed Open-Source MPC Wallet System")
        assert timescale_idx < mpc_idx


class TestSummaryIndexEntry:
    def test_summary_contains_mpc_doc_entry(self):
        content = _read(SUMMARY)
        assert (
            f"* [Open-Source MPC Wallet System Architecture via cb-mpc]({MPC_DOC_REL_PATH})"
        ) in content

    def test_mpc_doc_ordered_alphabetically_within_explanation_section(self):
        # generate_summary.py sorts docs/explanation/*.md files alphabetically
        # by path, so the new document must sit between
        # challenges-and-opportunities.md and percona-timescaledb-blockchain-sync.md.
        content = _read(SUMMARY)
        challenges_idx = content.index("docs/explanation/challenges-and-opportunities.md")
        mpc_idx = content.index(MPC_DOC_REL_PATH)
        percona_idx = content.index("docs/explanation/percona-timescaledb-blockchain-sync.md")
        assert challenges_idx < mpc_idx < percona_idx

    def test_summary_explanation_section_still_present(self):
        content = _read(SUMMARY)
        assert "### Explanation" in content


class TestBrainMemoryLedgers:
    def test_palace_registry_has_documentation_section(self):
        content = _read(PALACE_REGISTRY)
        assert "### Documentation (`docs/`)" in content

    def test_palace_registry_documents_mpc_wallet_doc(self):
        content = _read(PALACE_REGISTRY)
        assert (
            "`docs/explanation/open-source-mpc-wallet-architecture.md` -> Coinbase `cb-mpc` "
            "open-source wallet architecture."
        ) in content

    def test_palace_registry_documents_percona_doc(self):
        content = _read(PALACE_REGISTRY)
        assert (
            "`docs/explanation/percona-timescaledb-blockchain-sync.md` -> Dual-write "
            "PostgreSQL / TimescaleDB architecture."
        ) in content

    def test_palace_registry_documentation_section_before_tools_section(self):
        content = _read(PALACE_REGISTRY)
        docs_idx = content.index("### Documentation (`docs/`)")
        tools_idx = content.index("### Tools & Guardrails (`tools/`)")
        assert docs_idx < tools_idx

    def test_task_md_marks_mpc_design_task_complete(self):
        content = _read(TASK_MD)
        assert (
            "- [x] Design Open-Source MPC Wallet System Architecture using Coinbase `cb-mpc` "
            f"(`{MPC_DOC_REL_PATH}`)."
        ) in content

    def test_task_md_marks_ledger_update_task_complete(self):
        content = _read(TASK_MD)
        assert (
            "- [x] Update triple-ledger (`README.md`, `CHANGELOG.md`, `HISTORY.md`) and "
            "regenerate `SUMMARY.md`."
        ) in content

    def test_task_md_pending_pre_commit_task_still_open(self):
        # Regression guard: completing the MPC doc task should not have
        # accidentally marked the still-outstanding pre-commit task as done.
        content = _read(TASK_MD)
        assert "- [ ] Complete pre-commit checks and submit PR." in content

    def test_walkthrough_md_has_new_session_log_heading(self):
        content = _read(WALKTHROUGH_MD)
        assert (
            "## Session Log: 2026-08-25 (Open-Source MPC Wallet Architecture via cb-mpc)"
        ) in content

    def test_walkthrough_md_session_log_mentions_key_integration_points(self):
        content = _read(WALKTHROUGH_MD)
        for expected in (
            "P2P node transport",
            "policy engine quorums",
            "KMS/HSM share envelope encryption",
            "TimescaleDB dual-write pipelines",
        ):
            assert expected in content

    def test_walkthrough_md_mentions_summary_regeneration(self):
        content = _read(WALKTHROUGH_MD)
        assert "regenerated `SUMMARY.md` via `tools/generate_summary.py`." in content

    def test_walkthrough_md_new_session_appended_after_prior_sessions(self):
        content = _read(WALKTHROUGH_MD)
        percona_session_idx = content.index(
            "## Session Log: 2026-08-25 (Percona PostgreSQL & TimescaleDB Dual-Write Engine)"
        )
        mpc_session_idx = content.index(
            "## Session Log: 2026-08-25 (Open-Source MPC Wallet Architecture via cb-mpc)"
        )
        assert percona_session_idx < mpc_session_idx


class TestCrossFileConsistency:
    @pytest.mark.parametrize(
        "path",
        [README, CHANGELOG, SUMMARY, PALACE_REGISTRY, TASK_MD],
        ids=lambda p: p.name,
    )
    def test_doc_path_referenced_consistently(self, path):
        content = _read(path)
        assert MPC_DOC_REL_PATH in content

    def test_mpc_doc_and_percona_doc_both_exist_side_by_side(self):
        # The palace registry documents both explanation docs together;
        # verify they both actually exist on disk in docs/explanation/.
        assert MPC_DOC.is_file()
        assert PERCONA_DOC.is_file()


class TestMpcWalletDocOkfV02FrontmatterFields:
    """Regression coverage for a later PR that migrated this document's
    frontmatter from the original OKF v0.1-style 6-field schema
    (``okf_version``, ``type``, ``title``, ``created``, ``status``,
    ``language``) to the expanded OKF v0.2 13-field schema (adding
    ``timestamp``, ``topics``, ``description``, ``resource``, ``sources``,
    ``generated``, ``verified``, and ``stale_after``). See
    ``tests/test_okf_v02_frontmatter_migration.py`` for the repository-wide
    version of these checks.
    """

    def test_timestamp_matches_expected(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert "timestamp: '2026-08-25T00:00:00Z'" in frontmatter or 'timestamp: "2026-08-25T00:00:00Z"' in frontmatter

    @pytest.mark.parametrize(
        "topic",
        ["mpc", "cb-mpc", "threshold-signatures", "dkg", "key-management", "cryptography"],
    )
    def test_topics_list_contains_expected_topic(self, topic):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert topic in frontmatter

    def test_description_mentions_cb_mpc_integration(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        normalized = re.sub(r"\s+", " ", frontmatter)
        assert "Technical explanation of Coinbase cb-mpc integration" in normalized

    def test_resource_matches_file_path(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert "resource: file:///docs/explanation/open-source-mpc-wallet-architecture.md" in frontmatter

    @pytest.mark.parametrize("source", ["README.md", "src/dca_service/core/key_management.py"])
    def test_sources_list_contains_expected_source(self, source):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert source in frontmatter

    def test_generated_is_jules(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert "generated: jules" in frontmatter

    def test_verified_is_true(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert "verified: true" in frontmatter

    def test_stale_after_matches_expected(self):
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert "stale_after: '2027-08-25T00:00:00Z'" in frontmatter or 'stale_after: "2027-08-25T00:00:00Z"' in frontmatter

    def test_legacy_created_field_removed(self):
        # Regression guard: OKF v0.1's `created` field was renamed to
        # `timestamp` in v0.2; the migrated document must not retain both.
        frontmatter = _frontmatter_block(_read(MPC_DOC))
        assert not re.search(r"(?m)^created:", frontmatter)


class TestSummaryExplanationSectionIncludesLaterOkfGuideDoc:
    """Regression guard: a later PR inserted a new document,
    ``docs/explanation/open-knowledge-format-v02-guide.md``, alphabetically
    between ``challenges-and-opportunities.md`` and this document. This must
    not break the ordering relationship already asserted by
    ``TestSummaryIndexEntry.test_mpc_doc_ordered_alphabetically_within_explanation_section``
    above.
    """

    def test_okf_guide_doc_sits_between_challenges_and_mpc_doc(self):
        content = _read(SUMMARY)
        okf_guide_rel_path = "docs/explanation/open-knowledge-format-v02-guide.md"
        if okf_guide_rel_path not in content:
            pytest.skip("open-knowledge-format-v02-guide.md not present in this SUMMARY.md revision")
        challenges_idx = content.index("docs/explanation/challenges-and-opportunities.md")
        okf_guide_idx = content.index(okf_guide_rel_path)
        mpc_idx = content.index(MPC_DOC_REL_PATH)
        assert challenges_idx < okf_guide_idx < mpc_idx
