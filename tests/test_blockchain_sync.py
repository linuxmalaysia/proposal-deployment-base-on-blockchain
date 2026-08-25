"""Unit tests for Blockchain Synchroniser & TimescaleDB dual-write pattern."""

from datetime import datetime, timedelta, timezone
import pytest

from dca_service.adapters.timescaledb_adapter import (
    BlockchainNodeAdapter,
    DualWriteBlockchainSyncService,
    TimescaleDBAdapter,
)
from dca_service.core.blockchain_sync import (
    HypertableArchivingPolicy,
    HypertableChunkInfo,
    HypertableChunkState,
    SyncState,
    TimeSeriesTransactionEntry,
)


def test_dual_write_successful_flow():
    """Verify write-to-database-first then blockchain confirmation workflow."""
    db_adapter = TimescaleDBAdapter(hypertable_name="btc_transactions")
    node_adapter = BlockchainNodeAdapter(current_block=750000)
    service = DualWriteBlockchainSyncService(db_adapter=db_adapter, node_adapter=node_adapter)

    now = datetime.now(timezone.utc)
    entry = service.process_new_transaction(
        transaction_id="tx_1001",
        account_id="acc_vault_01",
        asset_symbol="BTC",
        amount=1.5,
        timestamp=now,
        metadata={"client_ref": "custody_deposit"},
    )

    assert entry.sync_state == SyncState.CHAIN_CONFIRMED
    assert entry.block_id == 750001
    assert entry.tx_hash is not None
    assert entry.tx_hash.startswith("0x")

    # Check hypertable state
    db_record = db_adapter.get_transaction("tx_1001")
    assert db_record is not None
    assert db_record.sync_state == SyncState.CHAIN_CONFIRMED
    assert db_record.amount == 1.5

    # Check on-chain ledger state
    chain_record = node_adapter.get_on_chain_transaction(entry.tx_hash)
    assert chain_record is not None
    assert chain_record["block_id"] == 750001


def test_dual_write_failure_recovery():
    """Verify failure state handling when blockchain broadcast fails."""
    db_adapter = TimescaleDBAdapter()
    node_adapter = BlockchainNodeAdapter()
    node_adapter.should_fail = True
    service = DualWriteBlockchainSyncService(db_adapter=db_adapter, node_adapter=node_adapter)

    now = datetime.now(timezone.utc)
    entry = service.process_new_transaction(
        transaction_id="tx_1002",
        account_id="acc_vault_02",
        asset_symbol="ETH",
        amount=10.0,
        timestamp=now,
    )

    assert entry.sync_state == SyncState.SYNC_FAILED
    assert entry.retry_count == 1
    assert "broadcast network error" in (entry.failure_reason or "")

    # Ensure transaction record remains safely stored in PostgreSQL / TimescaleDB
    db_record = db_adapter.get_transaction("tx_1002")
    assert db_record is not None
    assert db_record.sync_state == SyncState.SYNC_FAILED

    # Pending sync query should return failed transaction for background retry worker
    pending = db_adapter.query_pending_sync()
    assert len(pending) == 1
    assert pending[0].transaction_id == "tx_1002"


def test_hypertable_chunk_compression_and_archiving():
    """Verify TimescaleDB chunk age-based compression and archiving policy execution."""
    db_adapter = TimescaleDBAdapter()
    now = datetime.now(timezone.utc)

    # Active chunk (< 7 days old)
    chunk_active = HypertableChunkInfo(
        chunk_name="_hyper_1_1_chunk",
        range_start=now - timedelta(days=3),
        range_end=now - timedelta(days=1),
        record_count=5000,
    )

    # Compressible chunk (Between 7 and 90 days old)
    chunk_compress = HypertableChunkInfo(
        chunk_name="_hyper_1_2_chunk",
        range_start=now - timedelta(days=20),
        range_end=now - timedelta(days=15),
        record_count=20000,
    )

    # Archivable chunk (> 90 days old)
    chunk_archive = HypertableChunkInfo(
        chunk_name="_hyper_1_3_chunk",
        range_start=now - timedelta(days=120),
        range_end=now - timedelta(days=100),
        record_count=50000,
    )

    db_adapter.add_chunk_info(chunk_active)
    db_adapter.add_chunk_info(chunk_compress)
    db_adapter.add_chunk_info(chunk_archive)

    policy = HypertableArchivingPolicy(
        hypertable_name="blockchain_transactions",
        compress_after_days=7,
        archive_after_days=90,
    )

    results = db_adapter.apply_archiving_policy(policy, now=now)

    assert results["compressed"] == 1
    assert results["archived"] == 1

    chunks = db_adapter.get_chunks()
    assert chunks[0].state == HypertableChunkState.ACTIVE_UNCOMPRESSED
    assert chunks[1].state == HypertableChunkState.COMPRESSED
    assert chunks[1].compressed_size_bytes is not None
    assert chunks[2].state == HypertableChunkState.ARCHIVED_COLD_STORAGE
