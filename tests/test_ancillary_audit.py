"""Tests for ancillary rails and immutable audit logger."""

from decimal import Decimal
from dca_service.core.ancillary_audit import (
    AuditLogger,
    TokenizedCollateralAsset,
)


def test_audit_logger_event_immutability():
    """Verify audit logger protects event records from external mutation."""
    logger = AuditLogger()
    details = {"amount": "100.0", "asset": "USDC"}

    event = logger.log(
        event_id="e1",
        action="DEPOSIT",
        actor_id="client-1",
        details=details
    )

    # Mutate source details dict
    details["amount"] = "999999.0"

    events = logger.get_events()
    assert len(events) == 1
    assert events[0].details["amount"] == "100.0"

    # Mutate retrieved event details
    events[0].details["amount"] = "888888.0"

    events_second_fetch = logger.get_events()
    assert events_second_fetch[0].details["amount"] == "100.0"


def test_tokenized_collateral_valuation():
    """Verify tokenised collateral asset correctly validates full backing requirement."""
    asset = TokenizedCollateralAsset(
        asset_id="rwa-1",
        client_id="client-corp",
        token_symbol="USD-TBILL",
        total_supply=Decimal("1000000.00"),
        underlying_rwa_valuation=Decimal("1050000.00")
    )
    assert asset.is_fully_collateralised()
