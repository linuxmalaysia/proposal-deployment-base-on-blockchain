"""Unit tests for Blockchain Synchroniser & TimescaleDB dual-write pattern."""

from datetime import date, datetime, timedelta, timezone
import pytest

from dca_service.adapters.timescaledb_adapter import (
    BlockchainNodeAdapter,
    DualWriteBlockchainSyncService,
    TimescaleDBAdapter,
    normalize_metadata,
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


def test_metadata_normalization_and_datetime_support():
    """Verify metadata normalization converts datetime and date objects and nested structures."""
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


# ---------------------------------------------------------------------------
# normalize_metadata() unit tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [None, True, False, 0, 42, -3.14, "", "custody_deposit"],
)
def test_normalize_metadata_primitives_pass_through_unchanged(value):
    """Verify None, bool, int, float, and str values are returned unmodified."""
    assert normalize_metadata(value) == value


def test_normalize_metadata_converts_datetime_to_isoformat_string():
    """Verify a top-level datetime value is converted to its ISO-8601 string."""
    dt_val = datetime(2026, 1, 15, 9, 30, 0, tzinfo=timezone.utc)
    assert normalize_metadata(dt_val) == dt_val.isoformat()
    assert isinstance(normalize_metadata(dt_val), str)


def test_normalize_metadata_converts_date_to_isoformat_string():
    """Verify a top-level date value is converted to its ISO-8601 string."""
    date_val = date(2026, 1, 15)
    assert normalize_metadata(date_val) == date_val.isoformat()
    assert isinstance(normalize_metadata(date_val), str)


def test_normalize_metadata_dict_keys_are_stringified():
    """Verify non-string dict keys are converted to strings."""
    result = normalize_metadata({1: "one", 2.5: "two_point_five", "three": 3})
    assert result == {"1": "one", "2.5": "two_point_five", "three": 3}
    assert all(isinstance(k, str) for k in result)


def test_normalize_metadata_recurses_into_nested_dicts():
    """Verify nested dict values (including dates) are normalized recursively."""
    dt_val = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    result = normalize_metadata({"outer": {"inner": {"created": dt_val, "count": 3}}})
    assert result == {"outer": {"inner": {"created": dt_val.isoformat(), "count": 3}}}


def test_normalize_metadata_converts_list_tuple_and_set_to_lists():
    """Verify list, tuple, and set collections are all converted to lists."""
    assert normalize_metadata(["a", "b", "c"]) == ["a", "b", "c"]
    assert normalize_metadata(("a", "b", "c")) == ["a", "b", "c"]
    # Sets are unordered; use a single-element set to keep the assertion deterministic.
    assert normalize_metadata({"solo"}) == ["solo"]


def test_normalize_metadata_recurses_into_list_elements():
    """Verify elements within a list are individually normalized."""
    dt_val = datetime(2026, 5, 5, 5, 5, 5, tzinfo=timezone.utc)
    result = normalize_metadata([dt_val, {"nested_key": dt_val}, "plain"])
    assert result == [dt_val.isoformat(), {"nested_key": dt_val.isoformat()}, "plain"]


def test_normalize_metadata_unsupported_top_level_type_raises_typeerror():
    """Verify an unsupported top-level type raises TypeError naming the offending type."""

    class CustomObject:
        pass

    with pytest.raises(TypeError, match="Metadata value of type 'CustomObject' is not JSON-compatible."):
        normalize_metadata(CustomObject())


def test_normalize_metadata_unsupported_type_nested_in_list_raises_typeerror():
    """Verify an unsupported type nested inside a list is also rejected."""

    class CustomObject:
        pass

    with pytest.raises(TypeError, match="Metadata value of type 'CustomObject' is not JSON-compatible."):
        normalize_metadata(["ok", CustomObject()])


# ---------------------------------------------------------------------------
# Additional BlockchainNodeAdapter.broadcast_transaction metadata tests
# ---------------------------------------------------------------------------


def test_broadcast_transaction_normalizes_datetime_metadata_without_raising():
    """Verify broadcast_transaction can encode entries whose metadata contains raw datetime values."""
    node = BlockchainNodeAdapter()
    now = datetime.now(timezone.utc)
    entry = TimeSeriesTransactionEntry(
        transaction_id="tx_broadcast_dt",
        account_id="acc_vault_01",
        asset_symbol="ETH",
        amount=3.0,
        timestamp=now,
        metadata={"created_at": datetime(2026, 2, 2, tzinfo=timezone.utc)},
    )

    result = node.broadcast_transaction(entry)

    assert result["tx_hash"].startswith("0x")
    on_chain = node.get_on_chain_transaction(result["tx_hash"])
    assert on_chain is not None
    assert "2026-02-02" in on_chain["payload"]


def test_broadcast_transaction_raises_typeerror_for_unsupported_metadata():
    """Verify broadcast_transaction propagates TypeError for non-JSON-compatible metadata."""

    class CustomObject:
        pass

    node = BlockchainNodeAdapter()
    now = datetime.now(timezone.utc)
    entry = TimeSeriesTransactionEntry(
        transaction_id="tx_broadcast_invalid",
        account_id="acc_vault_01",
        asset_symbol="ETH",
        amount=3.0,
        timestamp=now,
        metadata={"bad": CustomObject()},
    )

    with pytest.raises(TypeError, match="Metadata value of type 'CustomObject' is not JSON-compatible."):
        node.broadcast_transaction(entry)


# ---------------------------------------------------------------------------
# Additional DualWriteBlockchainSyncService.process_new_transaction metadata tests
# ---------------------------------------------------------------------------


def test_process_new_transaction_defaults_metadata_to_empty_dict():
    """Verify omitting metadata results in an empty normalized dict, not None."""
    db_adapter = TimescaleDBAdapter()
    node_adapter = BlockchainNodeAdapter()
    service = DualWriteBlockchainSyncService(db_adapter=db_adapter, node_adapter=node_adapter)

    entry = service.process_new_transaction(
        transaction_id="tx_no_meta",
        account_id="acc_vault_01",
        asset_symbol="BTC",
        amount=0.5,
        timestamp=datetime.now(timezone.utc),
    )

    assert entry.metadata == {}
    assert entry.sync_state == SyncState.CHAIN_CONFIRMED


def test_process_new_transaction_non_dict_metadata_raises_typeerror():
    """Verify a top-level non-dict metadata value (e.g. a list) is rejected before persisting."""
    db_adapter = TimescaleDBAdapter()
    node_adapter = BlockchainNodeAdapter()
    service = DualWriteBlockchainSyncService(db_adapter=db_adapter, node_adapter=node_adapter)

    with pytest.raises(TypeError, match="Metadata must be a dictionary."):
        service.process_new_transaction(
            transaction_id="tx_list_meta",
            account_id="acc_vault_01",
            asset_symbol="BTC",
            amount=1.0,
            timestamp=datetime.now(timezone.utc),
            metadata=["not", "a", "dict"],
        )

    assert db_adapter.get_transaction("tx_list_meta") is None


def test_process_new_transaction_normalizes_non_string_metadata_keys():
    """Verify integer dict keys in metadata are stringified before being stored."""
    db_adapter = TimescaleDBAdapter()
    node_adapter = BlockchainNodeAdapter()
    service = DualWriteBlockchainSyncService(db_adapter=db_adapter, node_adapter=node_adapter)

    entry = service.process_new_transaction(
        transaction_id="tx_int_key_meta",
        account_id="acc_vault_01",
        asset_symbol="BTC",
        amount=1.0,
        timestamp=datetime.now(timezone.utc),
        metadata={1: "priority_one"},
    )

    assert entry.metadata == {"1": "priority_one"}
    assert entry.sync_state == SyncState.CHAIN_CONFIRMED
