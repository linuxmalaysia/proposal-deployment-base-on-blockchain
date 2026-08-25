"""
Ancillary Rails & Audit Logging Module for Digital Custody Asset Platform.

Provides interfaces for Staking & Tokenization collateral management,
alongside SOC-2 compliant immutable structured audit logging.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: str
    action: str
    actor_id: str
    details: Dict[str, Any]


class AuditLogger:
    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def log(self, event_id: str, action: str, actor_id: str, details: Dict[str, Any]) -> AuditEvent:
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            actor_id=actor_id,
            details=details
        )
        self._events.append(event)
        return event

    def get_events(self) -> List[AuditEvent]:
        return list(self._events)


@dataclass
class StakingDelegation:
    delegation_id: str
    client_id: str
    validator_address: str
    amount: Decimal
    asset_symbol: str
    is_active: bool = True


@dataclass
class TokenizedCollateralAsset:
    asset_id: str
    client_id: str
    token_symbol: str
    total_supply: Decimal
    underlying_rwa_valuation: Decimal

    def is_fully_collateralised(self) -> bool:
        return self.underlying_rwa_valuation >= self.total_supply
