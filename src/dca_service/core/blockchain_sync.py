"""Core domain entities and interfaces for Blockchain Synchronisation and TimescaleDB Ledger.

Concentric Clean Architecture Principle:
This module contains pure domain entities and business logic with zero external dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Dict, Optional, Union


class SyncState(Enum):
    """Lifecycle states of dual-written blockchain transactions."""
    DB_RECORDED = auto()
    PENDING_BLOCKCHAIN = auto()
    CHAIN_CONFIRMED = auto()
    SYNC_FAILED = auto()


class HypertableChunkState(Enum):
    """Storage states for TimescaleDB hypertable time-series chunks."""
    ACTIVE_UNCOMPRESSED = auto()
    COMPRESSED = auto()
    ARCHIVED_COLD_STORAGE = auto()


@dataclass(frozen=True)
class TimeSeriesTransactionEntry:
    """Represents a time-stamped transaction entry stored in TimescaleDB hypertable."""
    transaction_id: str
    account_id: str
    asset_symbol: str
    amount: Union[Decimal, float]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    sync_state: SyncState = SyncState.DB_RECORDED
    block_id: Optional[int] = None
    tx_hash: Optional[str] = None
    retry_count: int = 0
    failure_reason: Optional[str] = None


@dataclass
class HypertableChunkInfo:
    """Represents metadata for a TimescaleDB hypertable chunk."""
    chunk_name: str
    range_start: datetime
    range_end: datetime
    record_count: int
    state: HypertableChunkState = HypertableChunkState.ACTIVE_UNCOMPRESSED
    compressed_size_bytes: Optional[int] = None


@dataclass
class HypertableArchivingPolicy:
    """Policy governing TimescaleDB hypertable compression and archiving."""
    hypertable_name: str
    compress_after_days: int = 7
    archive_after_days: int = 90
    max_chunk_records: int = 100000
