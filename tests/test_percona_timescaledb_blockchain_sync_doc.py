"""Tests for the Percona/TimescaleDB blockchain-sync explanation doc updates.

Scope: this PR revised ``docs/explanation/percona-timescaledb-blockchain-sync.md``
to soften several previously-absolute claims so that the documentation
accurately reflects the reference/simulated adapter behaviour implemented in
``src/dca_service/adapters/timescaledb_adapter.py``:

- The "Blockchain Storage Partitioning" bullet now clarifies that
  ``BlockchainNodeAdapter.broadcast_transaction`` currently broadcasts the
  *full* transaction payload, and that minimising on-chain data to proof-only
  digests is a future production target rather than current behaviour.
- The Database-Encryption-vs-Blockchain comparison table now describes
  blockchain's role as "Tamper Evidence & Integrity Verification" (detection
  of alterations) instead of an absolute guarantee that records "can never be
  altered", and reflects that threat protection is reconciliation-based
  tamper *evidence* rather than a categorical prevention guarantee.
- The closing paragraph of that section now explains that verification
  requires comparing a locally recomputed hash against the value returned by
  ``BlockchainNodeAdapter.broadcast_transaction`` / ``get_on_chain_transaction``.
- The "Institutional Failover" summary bullet now describes bounded RPO/RTO
  targets contingent on configured backup/WAL-archive policies instead of
  asserting unconditional continuous availability and DR readiness.

These tests validate the *content* of the changed documentation file using
targeted text assertions, consistent with the text-based parsing style used
elsewhere in this project's test suite (see ``test_jekyll_site_config.py``
and ``test_generate_summary.py``), since no Markdown rendering toolchain is
exercised by the Python test suite.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "explanation" / "percona-timescaledb-blockchain-sync.md"


def _read_doc() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


class TestDocFileExists:
    def test_doc_file_exists(self):
        assert DOC_PATH.is_file()


class TestBlockchainStoragePartitioningSection:
    def test_mentions_broadcast_transaction_broadcasts_full_payload(self):
        content = _read_doc()
        assert (
            "`BlockchainNodeAdapter.broadcast_transaction` broadcasts the full "
            "transaction payload" in content
        )

    def test_describes_minimal_proof_data_as_future_target(self):
        content = _read_doc()
        assert "represents a future production target to minimise cost and chain bloat" in content

    def test_no_longer_asserts_minimal_proof_data_is_current_behaviour(self):
        """Regression guard: the old absolute claim must not reappear verbatim."""
        content = _read_doc()
        assert (
            "only minimal cryptographic proof data is maintained on-chain to minimise cost"
            not in content
        )


class TestEncryptionVsBlockchainComparisonTable:
    def test_primary_purpose_uses_tamper_evidence_language(self):
        content = _read_doc()
        assert "**Tamper Evidence & Integrity Verification:**" in content
        assert (
            "Enables detection of payload changes or historical alterations "
            "once confirmed on-chain." in content
        )

    def test_primary_purpose_no_longer_claims_absolute_immutability(self):
        """Regression guard: old absolute 'can never be altered' claim removed."""
        content = _read_doc()
        assert "Ensures historical records can never be altered, modified, or deleted" not in content

    def test_threat_protection_describes_reconciliation_based_evidence(self):
        content = _read_doc()
        assert "Provides tamper evidence against internal fraud" in content
        assert "allowing reconciliation to detect payload modifications" in content

    def test_closing_paragraph_describes_hash_verification_flow(self):
        content = _read_doc()
        assert "comprehensive security covering confidentiality alongside tamper evidence" in content
        assert (
            "comparing the locally recomputed hash with the value retrieved by "
            "`BlockchainNodeAdapter.broadcast_transaction` and `get_on_chain_transaction`" in content
        )


class TestInstitutionalFailoverSummaryBullet:
    def test_describes_bounded_rpo_and_rto_targets(self):
        content = _read_doc()
        assert "targets bounded availability and recovery-time objectives" in content
        assert "RPO near zero" in content
        assert "RTO bounded by failover orchestration timeouts" in content

    def test_ties_dr_readiness_to_configured_backup_policies(self):
        content = _read_doc()
        assert (
            "disaster-recovery readiness depends on configured backup policies "
            "and continuous WAL-archive procedures" in content
        )

    def test_no_longer_asserts_unconditional_continuous_availability(self):
        """Regression guard: old unconditional guarantee text removed."""
        content = _read_doc()
        assert "ensures continuous availability and disaster recovery readiness" not in content
