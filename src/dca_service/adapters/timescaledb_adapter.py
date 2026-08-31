"""Adapter layer for Percona Server for PostgreSQL / TimescaleDB and Blockchain Synchronisation.

This module provides simulated persistence adapters for TimescaleDB hypertables,
chunk archiving managers, and dual-write blockchain synchroniser service.
"""

import hashlib
import json
import math
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from dca_service.core.blockchain_sync import (
    HypertableArchivingPolicy,
    HypertableChunkInfo,
    HypertableChunkState,
    SyncState,
    TimeSeriesTransactionEntry,
)


def normalize_metadata(val: Any) -> Any:
    """Recursively validate and normalise metadata into a JSON-compatible value tree.

    Supports primitive JSON types, Decimal (converted to str), datetime and date objects
    (converted to ISO-formatted strings), and nested dictionaries, lists, tuples, and sets.
    """
    if val is None or isinstance(val, (bool, int, str)):
        return val
    elif isinstance(val, float):
        if not math.isfinite(val):
            raise ValueError(f"Non-finite float value '{val}' is not allowed in metadata.")
        return val
    elif isinstance(val, Decimal):
        return str(val)
    elif isinstance(val, (datetime, date)):
        return val.isoformat()
    elif isinstance(val, dict):
        normalized_dict = {}
        for k, v in val.items():
            if not isinstance(k, str):
                raise TypeError(f"Metadata dictionary key '{k}' of type '{type(k).__name__}' is not a string.")
            normalized_dict[k] = normalize_metadata(v)
        return normalized_dict
    elif isinstance(val, (list, tuple)):
        return [normalize_metadata(item) for item in val]
    elif isinstance(val, set):
        normalized_items = [normalize_metadata(item) for item in val]
        normalized_items.sort(key=lambda x: json.dumps(x, sort_keys=True))
        return normalized_items
    else:
        raise TypeError(f"Metadata value of type '{type(val).__name__}' is not JSON-compatible.")


class TimescaleDBAdapter:
    """Adapter simulating Percona Server for PostgreSQL with TimescaleDB hypertables."""

    def __init__(self, hypertable_name: str = "blockchain_transactions"):
        self.hypertable_name = hypertable_name
        self._records: dict[str, TimeSeriesTransactionEntry] = {}
        self._chunks: list[HypertableChunkInfo] = []

    def insert_transaction(self, entry: TimeSeriesTransactionEntry) -> TimeSeriesTransactionEntry:
        """Insert a transaction into the TimescaleDB hypertable idempotently."""
        if entry.transaction_id in self._records:
            existing = self._records[entry.transaction_id]
            # If entry matches existing ID and payload parameters, return existing (idempotent retry)
            if (
                existing.account_id == entry.account_id
                and existing.asset_symbol == entry.asset_symbol
                and existing.amount == entry.amount
                and existing.timestamp == entry.timestamp
            ):
                return existing
            raise ValueError(f"Transaction ID '{entry.transaction_id}' already exists with different payload.")

        self._records[entry.transaction_id] = entry
        return entry

    def update_sync_state(
        self,
        transaction_id: str,
        new_state: SyncState,
        block_id: int | None = None,
        tx_hash: str | None = None,
        failure_reason: str | None = None,
    ) -> TimeSeriesTransactionEntry:
        """Update transaction sync state in the hypertable."""
        if transaction_id not in self._records:
            raise KeyError(f"Transaction ID {transaction_id} not found in hypertable.")

        existing = self._records[transaction_id]
        updated = TimeSeriesTransactionEntry(
            transaction_id=existing.transaction_id,
            account_id=existing.account_id,
            asset_symbol=existing.asset_symbol,
            amount=existing.amount,
            timestamp=existing.timestamp,
            metadata=existing.metadata,
            sync_state=new_state,
            block_id=block_id if block_id is not None else existing.block_id,
            tx_hash=tx_hash if tx_hash is not None else existing.tx_hash,
            retry_count=existing.retry_count if failure_reason is None else existing.retry_count + 1,
            failure_reason=failure_reason if failure_reason is not None else existing.failure_reason,
        )
        self._records[transaction_id] = updated
        return updated

    def get_transaction(self, transaction_id: str) -> TimeSeriesTransactionEntry | None:
        """Retrieve a transaction by ID."""
        return self._records.get(transaction_id)

    def query_pending_sync(self) -> list[TimeSeriesTransactionEntry]:
        """Query transactions pending blockchain sync."""
        return [
            rec for rec in self._records.values()
            if rec.sync_state in (SyncState.DB_RECORDED, SyncState.PENDING_BLOCKCHAIN, SyncState.SYNC_FAILED)
        ]

    def get_all_transactions(self) -> list[TimeSeriesTransactionEntry]:
        """Return all stored transaction entries."""
        return list(self._records.values())

    def add_chunk_info(self, chunk: HypertableChunkInfo) -> None:
        """Register a chunk in the hypertable catalog."""
        self._chunks.append(chunk)

    def get_chunks(self) -> list[HypertableChunkInfo]:
        """Return all registered hypertable chunks."""
        return list(self._chunks)

    def apply_archiving_policy(self, policy: HypertableArchivingPolicy, now: datetime) -> dict[str, int]:
        """Apply chunk compression and archiving policies based on age."""
        if policy.hypertable_name != self.hypertable_name:
            raise ValueError(
                f"Policy hypertable name '{policy.hypertable_name}' does not match adapter hypertable '{self.hypertable_name}'."
            )

        compressed_count = 0
        archived_count = 0

        for chunk in self._chunks:
            age_days = (now - chunk.range_end).days
            if age_days >= policy.archive_after_days and chunk.state != HypertableChunkState.ARCHIVED_COLD_STORAGE:
                chunk.state = HypertableChunkState.ARCHIVED_COLD_STORAGE
                archived_count += 1
            elif (
                age_days >= policy.compress_after_days
                and chunk.state == HypertableChunkState.ACTIVE_UNCOMPRESSED
            ):
                chunk.state = HypertableChunkState.COMPRESSED
                chunk.compressed_size_bytes = max(100, chunk.record_count * 15)
                compressed_count += 1

        return {"compressed": compressed_count, "archived": archived_count}


class BlockchainNodeAdapter:
    """Adapter simulating a blockchain node RPC connection (BTC / ETH / L2)."""

    def __init__(self, current_block: int = 100000):
        self.current_block = current_block
        self._on_chain_ledger: dict[str, dict] = {}
        self.should_fail = False

    def compute_tx_hash(self, entry: TimeSeriesTransactionEntry) -> str:
        """Compute stable transaction hash digest for payload."""
        if not isinstance(entry.metadata, dict):
            raise TypeError("Metadata must be a dictionary.")

        normalized_meta = normalize_metadata(entry.metadata)
        payload_dict = {
            "account_id": entry.account_id,
            "amount": str(entry.amount) if isinstance(entry.amount, Decimal) else entry.amount,
            "asset_symbol": entry.asset_symbol,
            "metadata": normalized_meta,
            "timestamp": entry.timestamp.isoformat(),
            "transaction_id": entry.transaction_id,
        }
        raw_payload = json.dumps(payload_dict, sort_keys=True)
        return "0x" + hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    def broadcast_transaction(self, entry: TimeSeriesTransactionEntry) -> dict[str, str]:
        """Broadcast transaction to blockchain node."""
        if self.should_fail:
            raise RuntimeError("Blockchain node broadcast network error.")

        if not isinstance(entry.metadata, dict):
            raise TypeError("Metadata must be a dictionary.")

        normalized_meta = normalize_metadata(entry.metadata)
        payload_dict = {
            "account_id": entry.account_id,
            "amount": str(entry.amount) if isinstance(entry.amount, Decimal) else entry.amount,
            "asset_symbol": entry.asset_symbol,
            "metadata": normalized_meta,
            "timestamp": entry.timestamp.isoformat(),
            "transaction_id": entry.transaction_id,
        }
        raw_payload = json.dumps(payload_dict, sort_keys=True)
        tx_hash = "0x" + hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

        self.current_block += 1
        record = {
            "tx_hash": tx_hash,
            "block_id": self.current_block,
            "timestamp": datetime.now(UTC).isoformat(),
            "payload": raw_payload,
            "reverted": False,
        }
        self._on_chain_ledger[tx_hash] = record
        return {"tx_hash": tx_hash, "block_id": str(self.current_block)}

    def get_on_chain_transaction(self, tx_hash: str) -> dict | None:
        """Fetch transaction record from on-chain storage."""
        return self._on_chain_ledger.get(tx_hash)


class DualWriteBlockchainSyncService:
    """Orchestrates Dual-Write pattern: write to database first, then to blockchain."""

    def __init__(self, db_adapter: TimescaleDBAdapter, node_adapter: BlockchainNodeAdapter):
        self.db = db_adapter
        self.node = node_adapter

    def process_new_transaction(
        self,
        transaction_id: str,
        account_id: str,
        asset_symbol: str,
        amount: Decimal | float,
        timestamp: datetime,
        metadata: dict | None = None,
    ) -> TimeSeriesTransactionEntry:
        """Execute dual-write: write to TimescaleDB first, then broadcast to blockchain."""
        raw_metadata = {} if metadata is None else metadata
        if not isinstance(raw_metadata, dict):
            raise TypeError("Metadata must be a dictionary.")

        normalized_meta = normalize_metadata(raw_metadata)

        entry = TimeSeriesTransactionEntry(
            transaction_id=transaction_id,
            account_id=account_id,
            asset_symbol=asset_symbol,
            amount=amount,
            timestamp=timestamp,
            metadata=normalized_meta,
            sync_state=SyncState.DB_RECORDED,
        )
        self.db.insert_transaction(entry)

        return self.reconcile_and_sync(transaction_id)

    def reconcile_and_sync(self, transaction_id: str) -> TimeSeriesTransactionEntry:
        """Reconcile and sync transaction state, checking on-chain presence before retrying."""
        entry = self.db.get_transaction(transaction_id)
        if not entry:
            raise KeyError(f"Transaction ID {transaction_id} not found.")

        # Compute stable tx hash to check on-chain status
        stable_hash = self.node.compute_tx_hash(entry)
        on_chain = self.node.get_on_chain_transaction(stable_hash)

        if on_chain:
            if on_chain.get("reverted"):
                return self.db.update_sync_state(
                    transaction_id=transaction_id,
                    new_state=SyncState.SYNC_FAILED,
                    tx_hash=stable_hash,
                    failure_reason="TERMINAL_REVERT: On-chain transaction reverted.",
                )
            return self.db.update_sync_state(
                transaction_id=transaction_id,
                new_state=SyncState.CHAIN_CONFIRMED,
                block_id=int(on_chain["block_id"]),
                tx_hash=stable_hash,
            )

        # Transition to PENDING_BLOCKCHAIN state before broadcast
        self.db.update_sync_state(transaction_id, SyncState.PENDING_BLOCKCHAIN)

        try:
            res = self.node.broadcast_transaction(entry)
            tx_hash = res["tx_hash"]
            block_id = int(res["block_id"])

            updated_entry = self.db.update_sync_state(
                transaction_id=transaction_id,
                new_state=SyncState.CHAIN_CONFIRMED,
                block_id=block_id,
                tx_hash=tx_hash,
            )
            return updated_entry
        except Exception as exc:
            updated_entry = self.db.update_sync_state(
                transaction_id=transaction_id,
                new_state=SyncState.SYNC_FAILED,
                failure_reason=str(exc),
            )
            return updated_entry
