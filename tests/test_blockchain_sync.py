"""Unit tests for Blockchain Synchroniser & TimescaleDB dual-write pattern."""

from datetime import date, datetime, timedelta, timezone
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


def test_timescaledb_transaction_history_compression_policy_and_stats():
    """Verify TimescaleDB native columnar compression configuration and stats on transaction history."""
    db_adapter = TimescaleDBAdapter(hypertable_name="blockchain_transactions")
    now = datetime.now(timezone.utc)

    # Configure hypertable compression
    config = db_adapter.enable_hypertable_compression(
        segment_by=["account_id", "asset_symbol"],
        order_by="timestamp DESC",
    )
    assert config["compression_enabled"] is True
    assert config["compress_segmentby"] == "account_id, asset_symbol"
    assert config["compress_orderby"] == "timestamp DESC"

    # Add chunks: 1 active (<7 days), 2 historical (>7 days)
    chunk_active = HypertableChunkInfo(
        chunk_name="_hyper_tx_1_chunk",
        range_start=now - timedelta(days=5),
        range_end=now - timedelta(days=2),
        record_count=1000,
    )
    chunk_hist_1 = HypertableChunkInfo(
        chunk_name="_hyper_tx_2_chunk",
        range_start=now - timedelta(days=30),
        range_end=now - timedelta(days=15),
        record_count=10000,
    )
    chunk_hist_2 = HypertableChunkInfo(
        chunk_name="_hyper_tx_3_chunk",
        range_start=now - timedelta(days=60),
        range_end=now - timedelta(days=45),
        record_count=20000,
    )

    db_adapter.add_chunk_info(chunk_active)
    db_adapter.add_chunk_info(chunk_hist_1)
    db_adapter.add_chunk_info(chunk_hist_2)

    # Compress transaction history older than 7 days
    res = db_adapter.compress_transaction_history(compress_older_than_days=7, now=now)
    assert res["compressed_chunks_count"] == 2
    assert res["total_uncompressed_bytes"] == 30000 * 200

    # Get compression stats
    stats = db_adapter.get_compression_stats()
    assert stats["hypertable_name"] == "blockchain_transactions"
    assert stats["compression_enabled"] is True
    assert stats["total_chunks"] == 3
    assert stats["compressed_chunks"] == 2
    assert stats["uncompressed_chunks"] == 1
    assert stats["compression_ratio"] > 1.0


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


def test_insert_transaction_idempotency_and_conflict():
    """Verify idempotent insert behavior and conflict detection on duplicate transaction IDs."""
    db_adapter = TimescaleDBAdapter(hypertable_name="blockchain_transactions")
    now = datetime.now(timezone.utc)

    entry1 = TimeSeriesTransactionEntry(
        transaction_id="tx_dup_1",
        account_id="acc_1",
        asset_symbol="BTC",
        amount=1.0,
        timestamp=now,
    )
    inserted1 = db_adapter.insert_transaction(entry1)
    assert inserted1.transaction_id == "tx_dup_1"

    # Idempotent re-insert with identical payload
    inserted2 = db_adapter.insert_transaction(entry1)
    assert inserted2 == inserted1

    # Conflicting insert with different payload
    entry_conflict = TimeSeriesTransactionEntry(
        transaction_id="tx_dup_1",
        account_id="acc_1",
        asset_symbol="BTC",
        amount=2.5,  # Conflicting amount
        timestamp=now,
    )
    with pytest.raises(ValueError, match="already exists with different payload"):
        db_adapter.insert_transaction(entry_conflict)


def test_hypertable_naive_range_end_datetime_normalisation():
    """Verify TimescaleDBAdapter handles naive range_end and now datetimes safely without tzinfo mismatch errors."""
    db_adapter = TimescaleDBAdapter(hypertable_name="blockchain_transactions")
    now_naive = datetime.now()  # Naive datetime for 'now'

    # Add chunk with non-UTC-aware naive range_end and range_start (no tzinfo)
    naive_end = datetime.now() - timedelta(days=20)
    naive_start = datetime.now() - timedelta(days=30)

    chunk_naive = HypertableChunkInfo(
        chunk_name="_hyper_naive_chunk",
        range_start=naive_start,
        range_end=naive_end,
        record_count=5000,
    )

    db_adapter.add_chunk_info(chunk_naive)

    # Verify add_chunk_info normalized tzinfo to timezone.utc
    stored_chunks = db_adapter.get_chunks()
    assert stored_chunks[0].range_end.tzinfo == timezone.utc
    assert stored_chunks[0].range_start.tzinfo == timezone.utc

    # Compress transaction history older than 7 days safely with naive now
    res = db_adapter.compress_transaction_history(compress_older_than_days=7, now=now_naive)
    assert res["compressed_chunks_count"] == 1

    # Apply archiving policy with naive now
    policy = HypertableArchivingPolicy(
        hypertable_name="blockchain_transactions",
        compress_after_days=7,
        archive_after_days=15,
    )
    arch_res = db_adapter.apply_archiving_policy(policy, now=now_naive)
    assert arch_res["archived"] == 1
    assert stored_chunks[0].state == HypertableChunkState.ARCHIVED_COLD_STORAGE


def test_archiving_policy_hypertable_mismatch_validation():
    """Verify policy application rejects mismatched hypertable names."""
    db_adapter = TimescaleDBAdapter(hypertable_name="btc_transactions")
    now = datetime.now(timezone.utc)

    policy_mismatch = HypertableArchivingPolicy(
        hypertable_name="eth_transactions",
        compress_after_days=7,
        archive_after_days=90,
    )

    with pytest.raises(ValueError, match="does not match adapter hypertable"):
        db_adapter.apply_archiving_policy(policy_mismatch, now=now)


def test_deterministic_tx_hash_payload_encoding():
    """Verify canonical JSON payload encoding and hashing behavior."""
    node = BlockchainNodeAdapter()
    now = datetime.now(timezone.utc)

    # 1. Equivalent metadata with different insertion order produces identical hash
    entry_order1 = TimeSeriesTransactionEntry(
        transaction_id="tx_hash_1",
        account_id="acc_vault",
        asset_symbol="SOL",
        amount=50.0,
        timestamp=now,
        metadata={"tier": "vip", "region": "eu"},
    )

    entry_order2 = TimeSeriesTransactionEntry(
        transaction_id="tx_hash_1",
        account_id="acc_vault",
        asset_symbol="SOL",
        amount=50.0,
        timestamp=now,
        metadata={"region": "eu", "tier": "vip"},
    )

    hash1 = node.broadcast_transaction(entry_order1)["tx_hash"]
    hash2 = node.broadcast_transaction(entry_order2)["tx_hash"]
    assert hash1 == hash2

    # 2. Boundary-distinct field values produce different hashes
    entry_boundary1 = TimeSeriesTransactionEntry(
        transaction_id="tx_1:account_a",
        account_id="vault",
        asset_symbol="BTC",
        amount=10.0,
        timestamp=now,
    )
    entry_boundary2 = TimeSeriesTransactionEntry(
        transaction_id="tx_1",
        account_id="account_a:vault",
        asset_symbol="BTC",
        amount=10.0,
        timestamp=now,
    )

    hash_b1 = node.broadcast_transaction(entry_boundary1)["tx_hash"]
    hash_b2 = node.broadcast_transaction(entry_boundary2)["tx_hash"]
    assert hash_b1 != hash_b2


def test_metadata_normalisation_and_datetime_support():
    """Verify metadata normalisation converts datetime and date objects and nested structures."""
    db_adapter = TimescaleDBAdapter()
    node_adapter = BlockchainNodeAdapter()
    service = DualWriteBlockchainSyncService(db_adapter=db_adapter, node_adapter=node_adapter)

    now = datetime.now(timezone.utc)
    dt_val = datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc)
    date_val = date(2026, 8, 25)

    entry = service.process_new_transaction(
        transaction_id="tx_meta_01",
        account_id="acc_vault_01",
        asset_symbol="BTC",
        amount=2.0,
        timestamp=now,
        metadata={
            "created_at": dt_val,
            "expiry_date": date_val,
            "tags": ["custody", "institutional"],
            "nested": {"key": "value"},
        },
    )

    assert entry.metadata["created_at"] == dt_val.isoformat()
    assert entry.metadata["expiry_date"] == date_val.isoformat()
    assert entry.metadata["tags"] == ["custody", "institutional"]
    assert entry.metadata["nested"] == {"key": "value"}


def test_invalid_metadata_type_raises_before_persisting():
    """Verify non-JSON-compatible metadata fails before database insertion or PENDING_BLOCKCHAIN state."""
    db_adapter = TimescaleDBAdapter()
    node_adapter = BlockchainNodeAdapter()
    service = DualWriteBlockchainSyncService(db_adapter=db_adapter, node_adapter=node_adapter)

    class CustomObject:
        pass

    now = datetime.now(timezone.utc)
    invalid_metadata = {"unsupported": CustomObject()}

    with pytest.raises(TypeError, match="Metadata value of type 'CustomObject' is not JSON-compatible."):
        service.process_new_transaction(
            transaction_id="tx_invalid_meta",
            account_id="acc_vault_01",
            asset_symbol="BTC",
            amount=1.0,
            timestamp=now,
            metadata=invalid_metadata,
        )

    # Ensure transaction was NOT saved to the database or marked pending
    assert db_adapter.get_transaction("tx_invalid_meta") is None
    assert len(db_adapter.query_pending_sync()) == 0


def test_metadata_set_canonicalisation_and_validation():
    """Verify set canonicalisation, non-finite float rejection, and non-string key rejection."""
    db_adapter = TimescaleDBAdapter()
    node_adapter = BlockchainNodeAdapter()
    service = DualWriteBlockchainSyncService(db_adapter=db_adapter, node_adapter=node_adapter)
    now = datetime.now(timezone.utc)

    # Set elements in different order produce identical normalised output
    entry1 = TimeSeriesTransactionEntry(
        transaction_id="tx_set_1",
        account_id="acc_1",
        asset_symbol="BTC",
        amount=1.0,
        timestamp=now,
        metadata={"tags": {"b", "a", "c"}},
    )
    entry2 = TimeSeriesTransactionEntry(
        transaction_id="tx_set_1",
        account_id="acc_1",
        asset_symbol="BTC",
        amount=1.0,
        timestamp=now,
        metadata={"tags": {"c", "a", "b"}},
    )

    hash1 = node_adapter.broadcast_transaction(entry1)["tx_hash"]
    hash2 = node_adapter.broadcast_transaction(entry2)["tx_hash"]
    assert hash1 == hash2

    # Non-string dictionary keys rejected
    with pytest.raises(TypeError, match="Metadata dictionary key '123' of type 'int' is not a string."):
        service.process_new_transaction(
            transaction_id="tx_key_err",
            account_id="acc_1",
            asset_symbol="BTC",
            amount=1.0,
            timestamp=now,
            metadata={123: "val"},  # type: ignore
        )

    # Non-finite float values rejected
    with pytest.raises(ValueError, match="Non-finite float value"):
        service.process_new_transaction(
            transaction_id="tx_float_err",
            account_id="acc_1",
            asset_symbol="BTC",
            amount=1.0,
            timestamp=now,
            metadata={"inf": float("inf")},
        )


def test_reconcile_and_sync_on_chain_and_terminal_revert():
    """Verify reconciliation queries on-chain state before re-broadcasting and handles terminal reverts."""
    db_adapter = TimescaleDBAdapter()
    node_adapter = BlockchainNodeAdapter()
    service = DualWriteBlockchainSyncService(db_adapter=db_adapter, node_adapter=node_adapter)
    now = datetime.now(timezone.utc)

    # 1. First broadcast attempt fails network check
    node_adapter.should_fail = True
    failed_entry = service.process_new_transaction(
        transaction_id="tx_recon_01",
        account_id="acc_1",
        asset_symbol="ETH",
        amount=5.0,
        timestamp=now,
    )
    assert failed_entry.sync_state == SyncState.SYNC_FAILED

    # Manually insert on-chain record as if transaction actually reached node before network dropped
    node_adapter.should_fail = False
    stable_hash = node_adapter.compute_tx_hash(failed_entry)
    node_adapter._on_chain_ledger[stable_hash] = {
        "tx_hash": stable_hash,
        "block_id": 100500,
        "timestamp": now.isoformat(),
        "payload": "mock_payload",
        "reverted": False,
    }

    # Reconcile should detect on-chain presence and confirm without re-broadcasting
    reconciled_entry = service.reconcile_and_sync("tx_recon_01")
    assert reconciled_entry.sync_state == SyncState.CHAIN_CONFIRMED
    assert reconciled_entry.block_id == 100500

    # 2. Terminal revert handling
    failed_entry_revert = service.process_new_transaction(
        transaction_id="tx_revert_01",
        account_id="acc_1",
        asset_symbol="ETH",
        amount=5.0,
        timestamp=now,
    )
    revert_hash = node_adapter.compute_tx_hash(failed_entry_revert)
    node_adapter._on_chain_ledger[revert_hash]["reverted"] = True

    reconciled_revert = service.reconcile_and_sync("tx_revert_01")
    assert reconciled_revert.sync_state == SyncState.SYNC_FAILED
    assert "TERMINAL_REVERT" in reconciled_revert.failure_reason
