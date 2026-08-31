"""
Ancillary Rails & Audit Logging Module for Digital Custody Asset Platform.

Provides interfaces for Staking & Tokenisation collateral management,
alongside SOC-2 compliant immutable structured audit logging.
"""

import copy
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: str
    action: str
    actor_id: str
    details: dict[str, Any]


class AuditLogger:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def log(self, event_id: str, action: str, actor_id: str, details: dict[str, Any]) -> AuditEvent:
        """
        Record an audit event with the current UTC timestamp.
        
        Parameters:
            details (dict[str, Any]): Additional event metadata.
        
        Returns:
            AuditEvent: A copy of the recorded audit event.
        """
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(UTC).isoformat(),
            action=action,
            actor_id=actor_id,
            details=copy.deepcopy(details)
        )
        self._events.append(event)
        return copy.deepcopy(event)

    def get_events(self) -> list[AuditEvent]:
        return [copy.deepcopy(e) for e in self._events]


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
